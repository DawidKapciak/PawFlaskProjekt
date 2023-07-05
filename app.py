import os
import secrets
import sqlite3
from datetime import datetime

import pyrebase
import requests
from flask_socketio import SocketIO
from dotenv import load_dotenv
from threading import Lock
from flask import Flask, session, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, Email, Length
from werkzeug.utils import secure_filename
from flask_restx import Api, Resource, Namespace, fields

load_dotenv()

firebase_config = {
    "apiKey": os.getenv("API_KEY"),
    "authDomain": os.getenv("AUTH_DOMAIN"),
    "databaseURL": os.getenv("DATABASE_URL"),
    "projectId": os.getenv("PROJECT_ID"),
    "storageBucket": os.getenv("STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("MESSAGING_SENDER_ID"),
    "appId": os.getenv("APP_ID")
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
storage = firebase.storage()

thread = None
thread_lock = Lock()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.secret_key = os.getenv("SECRET_KEY")
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins='*')


@app.route('/', methods=['POST', 'GET'])
def login():
    email = None
    password = None
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        password = form.password.data
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            acc_info = auth.get_account_info(user['idToken'])
            if acc_info['users'][0]['emailVerified']:
                session['user'] = email
                session['name'] = create_name(email)
                session['idToken'] = user['idToken']
                user = User.query.filter_by(email=session['user']).first()
                user_id = user.user_id
                if requests.get(
                        f"https://firebasestorage.googleapis.com/v0/b/paw-1-32b63.appspot.com/o/images%2Fprofile_pic_{user_id}.jpg?alt=media").status_code == 200:
                    session['user_id'] = user_id
                else:
                    session['user_id'] = None

            else:
                flash("Zweryfikuj swoje konto email.")

        except Exception as e:
            print(e)
            if "TOO_MANY_ATTEMPTS_TRY_LATER" in str(e):
                flash("Zbyt dużo prób, spróbuj ponownie później.")
            elif "EMAIL_NOT_FOUND" or "INVALID_PASSWORD" or "INVALID_EMAIL" in str(e):
                flash("Podałeś błędne hasło lub takie konto z takim adresem email nie istnieje.")

    if 'user' in session:
        user = User.query.filter_by(email=session['user']).first()
        user_id = user.user_id
        if user:
            our_notes = Note.query.filter_by(user_id=user_id).all()
        else:
            return "Błąd"
        return render_template('index.html', our_notes=our_notes)

    return render_template('login.html', email=email, password=password, form=form)


api = Api(app, doc="/docs/", title="Note App Api", version="0.4")

ns = Namespace("notes", description="Everything about notes")
api.add_namespace(ns)

note_model = api.model("Note", {
    'title': fields.String(description="Title of note", required=True),
    'text': fields.String(description="Text of note", required=True),
})


class LoginForm(FlaskForm):
    email = EmailField('Adres email ', validators=[DataRequired(), Email()])
    password = PasswordField('Hasło ', validators=[DataRequired()])
    login = SubmitField('Zaloguj')


class RegisterForm(FlaskForm):
    email = EmailField('Adres email ', validators=[DataRequired(), Email()])
    password = PasswordField('Hasło ', validators=[DataRequired(),
                                                   Length(min=6,
                                                          max=30)])
    password2 = PasswordField('Hasło ', validators=[DataRequired()])
    register = SubmitField('Zarejestruj')


class ForgotForm(FlaskForm):
    email = EmailField('Adres email ', validators=[DataRequired(), Email()])
    send = SubmitField('Wyślij')


class ProfilePicForm(FlaskForm):
    profile_pic = FileField('Zdjęcie profilowe',
                            validators=[FileAllowed(['jpg', 'png'], 'Tylko zdjęcia!'), FileRequired()])
    send = SubmitField('Wyślij')


class Note(db.Model):
    __tablename__ = 'note'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_info.user_id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model):
    __tablename__ = 'user_info'
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    api_key = db.Column(db.String(255), nullable=False)
    notes = db.relationship('Note', backref='user', lazy=True)
    total_requests = db.Column(db.Integer, default=0)
    last_request_timestamp = db.Column(db.DateTime)


class NoteForm(FlaskForm):
    title = StringField("Tytuł notatki", validators=[DataRequired()])
    text = StringField("Treść notatki", validators=[DataRequired()])
    save = SubmitField("Zapisz")


@app.route('/add', methods=['GET', 'POST'])
def add_note():
    form = NoteForm()
    user = User.query.filter_by(email=session['user']).first()
    if form.validate_on_submit():
        note = Note(user_id=user.user_id, title=form.title.data, text=form.text.data)
        try:
            db.session.add(note)
            db.session.commit()
            form.title.data = ''
            form.text.data = ''
            if user:
                our_notes = Note.query.filter_by(user_id=user.user_id).all()
            else:
                return "Błąd"
            flash("Dodano notatkę!")
            return render_template("index.html", our_notes=our_notes)
        except Exception as e:
            print(e)
            flash("Wystąpił błąd")
    return render_template("add_note.html",
                           form=form)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_note(id):
    form = NoteForm()
    user = User.query.filter_by(email=session['user']).first()
    note_to_update = Note.query.get_or_404(id)
    if request.method == "POST":
        note_to_update.title = request.form['title']
        note_to_update.text = request.form['text']
        if user:
            our_notes = Note.query.filter_by(user_id=user.user_id).all()
        else:
            return "Błąd"
        try:
            db.session.commit()
            flash("Zmodyfikowano notatkę.")
            return render_template("index.html",
                                   our_notes=our_notes)
        except Exception as e:
            print(e)
            flash("Wystąpił błąd")
    else:
        return render_template("edit_note.html",
                               form=form,
                               note_to_update=note_to_update)


@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete_note(id):
    note_to_delete = Note.query.get_or_404(id)
    try:
        db.session.delete(note_to_delete)
        db.session.commit()
        flash("Usunięto notatkę!")
    except Exception as e:
        print(e)
        flash("Wystąpił błąd")
    finally:
        user = User.query.filter_by(email=session['user']).first()
        if user:
            our_notes = Note.query.filter_by(user_id=user.user_id).all()
        else:
            return "Błąd"
        return render_template("index.html",
                               our_notes=our_notes)


def create_name(email):
    index = email.find('@')
    name = email
    if index != -1:
        name = email[:index]
    return name


def generate_api_key():
    api_key = secrets.token_hex(16)
    return api_key


@app.route('/logout')
def logout():
    if 'user' in session:
        session.clear()
    return redirect('/')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    form = RegisterForm()
    if 'user' in session:
        return "Najpierw się wyloguj!"
    email = None
    password = None
    if form.validate_on_submit():
        email = form.email.data.lower()
        password = form.password.data
        password2 = form.password2.data
        if password == password2:
            try:
                user = auth.create_user_with_email_and_password(email, password)
                user_info = User(email=email, api_key=generate_api_key())
                try:
                    db.session.add(user_info)
                    db.session.commit()
                except sqlite3.IntegrityError as e:
                    print(e)
                auth.send_email_verification(user['idToken'])
                flash("Utworzono konto, potwierdź je na mailu.")
                return render_template('login.html', form=LoginForm())
            except Exception as e:
                if "EMAIL_EXISTS" in str(e):
                    flash("Konto z takim adresem email już istnieje.")
                else:
                    print(e)
        else:
            flash("Hasła nie są takie same!")
    return render_template('signup.html', email=email, password=password, form=form)


@app.route('/forgot', methods=['POST', 'GET'])
def forgot():
    email = None
    form = ForgotForm()
    if form.validate_on_submit():
        email = form.email.data
        try:
            auth.send_password_reset_email(email)
            flash("Na email zostały wysłane dalsze instrukcje.")
        except Exception as e:
            if "EMAIL_NOT_FOUND" in str(e):
                flash("Nie istnieje konto z takim adresem email.")

    return render_template('forgot.html', email=email, form=form)


@app.route('/settings', methods=['POST', 'GET'])
def update_profile_pic():
    form = ProfilePicForm()
    user = User.query.filter_by(email=session['user']).first()

    api_key = user.api_key
    if form.validate_on_submit():
        try:
            pic_data = form.profile_pic.data
            filename = secure_filename(pic_data.filename)
            pic_data.save(os.path.join(app.instance_path, filename))
            user = User.query.filter_by(email=session['user']).first()
            user_id = user.user_id
            storage.child(f"images/profile_pic_{user_id}.jpg").put(f"instance/{filename}", session['idToken'])
            response = requests.get(f"https://firebasestorage.googleapis.com/v0/b/paw-1-32b63.appspot.com/o/images%2Fprofile_pic_{user_id}.jpg?alt=media")
            if response.status_code == 200:
                session['user_id'] = user_id
            else:
                session['user_id'] = None

            os.remove(f"{app.instance_path}/{filename}")
            flash("Dodano zdjęcie!")
        except Exception as e:
            print(e)
            flash("Wystąpił błąd")

    return render_template('settings.html', form=form, api_key=api_key)


@app.route('/download_profile_pic', methods=['POST', 'GET'])
def download_profile_pic():
    form = ProfilePicForm()
    try:
        user = User.query.filter_by(email=session['user']).first()
        user_id = user.user_id
        response = requests.get(
            f"https://firebasestorage.googleapis.com/v0/b/paw-1-32b63.appspot.com/o/images%2Fprofile_pic_{user_id}.jpg?alt=media")
        if response.status_code == 200:
            storage.child(f"images/profile_pic_{user_id}.jpg").download(path="",
                                                                        filename="static/your_profile_pic.jpg")
            flash("Pobrano zdjęcie!")
        else:
            flash("Nie masz swojego zdjęcia!")
    except Exception as e:
        print(e)
        flash("Wystąpił błąd")
    return render_template('settings.html', form=form)


@app.before_request
def update_user_stats():
    api_key = request.args.get('api_key')
    if api_key:
        user = User.query.filter_by(api_key=api_key).first()
        if user:
            user.total_requests += 1
            user.last_request_timestamp = datetime.now()
            db.session.commit()


def verify_api_key(api_key):
    user = User.query.filter_by(api_key=api_key).first()
    if api_key is None:
        return None
    if api_key != user.api_key:
        return None
    else:
        return user


@ns.response(200, "Success")
@ns.response(401, "Unauthorized api key")
@ns.response(404, "Notes doesn't exist")
@ns.route("")
@ns.param('api_key', 'Api Key')
class JsonAllNotes(Resource):

    def get(self):
        api_key = request.args.get('api_key')
        user = verify_api_key(api_key)
        if user:
            notes = Note.query.filter_by(user_id=user.user_id).all()
            output = []
            for note in notes:
                note_data = {
                    'id': note.id, 'title': note.title, 'text': note.text,
                    'date_added': note.date_added.strftime('%Y-%m-%d %H:%M:%S')
                }
                output.append(note_data)
            return {'notes': output}
        else:
            return {'message': 'Unauthorized api key'}, 401

    @ns.expect(note_model)
    @ns.marshal_with(note_model, code=200)
    def post(self):
        api_key = request.args.get('api_key')
        user = verify_api_key(api_key)
        if user:
            user = User.query.filter_by(api_key=api_key).first()
            note = Note(title=ns.payload["title"], text=ns.payload["text"], user_id=user.user_id)
            db.session.add(note)
            db.session.commit()
            return note
        else:
            return {'message': 'Unauthorized api key'}, 401


@ns.param("id", "Note ID")
@ns.response(404, "Note with that ID doesn't exist")
@ns.response(401, "Unauthorized api key")
@ns.response(200, "Success")
@ns.route("/<id>")
@ns.param('api_key', 'Api Key')
class JsonOneNote(Resource):

    def get(self, id):
        api_key = request.args.get('api_key')
        user = verify_api_key(api_key)
        if user:
            note = Note.query.filter_by(user_id=user.user_id, id=id).first()
            if note:
                return {
                    'id': note.id, 'title': note.title,
                    'text': note.text, 'date_added': note.date_added.strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                return {'message': 'Note not found'}, 404
        else:
            return {'message': 'Unauthorized api key'}, 401

    def delete(self, id):
        api_key = request.args.get('api_key')
        user = verify_api_key(api_key)
        if user:
            note_to_delete = Note.query.filter_by(user_id=user.user_id, id=id).first()
            if note_to_delete:
                db.session.delete(note_to_delete)
                db.session.commit()
                return {'message': 'Note deleted!'}
            else:
                return {'message': 'Note not found'}, 404
        else:
            return {'message': 'Unauthorized api key'}, 401

    @ns.expect(note_model)
    @ns.marshal_with(note_model)
    def put(self, id):
        api_key = request.args.get('api_key')
        user = verify_api_key(api_key)
        if user:
            note_to_update = Note.query.filter_by(user_id=user.user_id, id=id).first()

            if note_to_update:
                note_to_update.title = ns.payload["title"]
                note_to_update.text = ns.payload["text"]
                db.session.commit()
                return note_to_update
            else:
                return {'message': 'Note not found'}, 404
        else:
            return {'message': 'Unauthorized api key'}, 401


def get_current_datetime():
    now = datetime.now()
    return now.strftime("%H:%M:%S")


def background_thread():
    while True:
        sum = 0
        with app.app_context():
            users = User.query.all()
        for user in users:
            sum += user.total_requests
        value = sum
        socketio.emit('updateData', {'value': value, "date": get_current_datetime()})
        socketio.sleep(5)


@app.route('/websocket')
def websocket():
    if 'user' in session:
        return render_template('websocket.html')
    return "Najpierw się zaloguj!"


@socketio.on('connect')
def connect():
    print('Połączono')

    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)


if __name__ == '__main__':
    app.run()
