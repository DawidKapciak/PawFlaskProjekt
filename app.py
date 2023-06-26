import os
from datetime import datetime

import pyrebase
import requests
from dotenv import load_dotenv
from flask import Flask, session, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, Email, Length
from werkzeug.utils import secure_filename
from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/static/swagger.json'  # Our API url (can of course be a local resource)

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Test application"
    },
    # oauth_config={  # OAuth config. See https://github.com/swagger-api/swagger-ui#oauth2-configuration .
    #    'clientId': "your-client-id",
    #    'clientSecret': "your-client-secret-if-required",
    #    'realm': "your-realms",
    #    'appName': "your-app-name",
    #    'scopeSeparator': " ",
    #    'additionalQueryStringParams': {'test': "hello"}
    # }
)

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

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.secret_key = os.getenv("SECRET_KEY")
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024
app.register_blueprint(swaggerui_blueprint)
db = SQLAlchemy(app)


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
    profile_pic = FileField('Zdjęcie profilowe', validators=[FileAllowed(['jpg', 'png'], 'Tylko zdjęcia!'), FileRequired()])
    send = SubmitField('Wyślij')


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(50), nullable=False)
    text = db.Column(db.String(200), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)


class NoteForm(FlaskForm):
    title = StringField("Tytuł notatki", validators=[DataRequired()])
    text = StringField("Treść notatki", validators=[DataRequired()])
    save = SubmitField("Zapisz")


@app.route('/add', methods=['GET', 'POST'])
def add_note():
    form = NoteForm()
    our_notes = Note.query.order_by(Note.date_added)
    if form.validate_on_submit():
        note = Note(user_id=2, title=form.title.data, text=form.text.data)
        try:
            db.session.add(note)
            db.session.commit()
            form.title.data = ''
            form.text.data = ''
            flash("Dodano notatkę!")
            return render_template("index.html", our_notes=our_notes)
        except Exception as e:
            print(e)
            flash("Wystąpił błąd")
    return render_template("add_note.html",
                           form=form)


@app.route('/notes/add', methods=['POST'])
def add_note_rest():
    note = Note(title=request.json['title'], text=request.json['text'])

    db.session.add(note)
    db.session.commit()

    return {'id': note.id, 'title': note.title, 'text': note.text}


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_note(id):
    form = NoteForm()
    our_notes = Note.query.filter_by(user=session['user'])
    note_to_update = Note.query.get_or_404(id)
    if request.method == "POST":
        note_to_update.title = request.form['title']
        note_to_update.text = request.form['text']
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


@app.route('/notes/edit/<int:id>', methods=['PUT'])
def edit_note_rest(id):
    note_to_update = Note.query.get(id)
    if note_to_update is None:
        return {'error': 'note not found'}
    else:
        note_to_update.title = request.json['title']
        note_to_update.text = request.json['text']
        db.session.commit()

    return {'id': note_to_update.id, 'title': note_to_update.title, 'text': note_to_update.text}


@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete_note(id):
    our_notes = Note.query.order_by(Note.date_added)
    note_to_delete = Note.query.get_or_404(id)
    try:
        db.session.delete(note_to_delete)
        db.session.commit()
        flash("Usunięto notatkę!")
    except Exception as e:
        print(e)
        flash("Wystąpił błąd")
    finally:
        return render_template("index.html",
                               our_notes=our_notes)


@app.route('/notes/delete/<int:id>', methods=['DELETE'])
def delete_note_rest(id):
    note_to_delete = Note.query.get(id)
    if note_to_delete is None:
        return {'error': 'note not found'}
    db.session.delete(note_to_delete)
    db.session.commit()
    return {'message': 'note deleted!'}


def create_name(email):
    index = email.find('@')
    name = email
    if index != -1:
        name = email[:index]
    return name


@app.route('/', methods=['POST', 'GET'])
def login():
    email = None
    password = None
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            acc_info = auth.get_account_info(user['idToken'])
            if acc_info['users'][0]['emailVerified']:
                session['user'] = email
                session['name'] = create_name(email)
                session['idToken'] = user['idToken']
                img_url = storage.child(f"images/profile_pic_{session['user']}.jpg").get_url(None)
                response = requests.get(img_url)
                if response.status_code == 200:
                    session['img_url'] = img_url

            else:
                flash("Zweryfikuj swoje konto email.")

        except Exception as e:
            print(e)
            if "TOO_MANY_ATTEMPTS_TRY_LATER" in str(e):
                flash("Zbyt dużo prób, spróbuj ponownie później.")
            elif "EMAIL_NOT_FOUND" or "INVALID_PASSWORD" or "INVALID_EMAIL" in str(e):
                flash("Podałeś błędne hasło lub takie konto z takim adresem email nie istnieje.")

    if 'user' in session:
        our_notes = Note.query.filter_by(user=session['user'])
        return render_template('index.html', our_notes=our_notes)

    return render_template('login.html', email=email, password=password, form=form)


@app.route('/logout')
def logout():
    if 'user' in session:
        session.clear()
    return redirect('/')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    email = None
    password = None
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        password2 = form.password2.data
        if password == password2:
            try:
                user = auth.create_user_with_email_and_password(email, password)
                auth.send_email_verification(user['idToken'])
                flash("Utworzono konto, potwierdź je na mailu.")
                return render_template('login.html')
            except Exception as e:
                if "EMAIL_EXISTS" in str(e):
                    flash("Konto z takim adresem email już istnieje.")
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


@app.route('/update_profile_pic', methods=['POST', 'GET'])
def update_profile_pic():
    form = ProfilePicForm()
    session['img_url'] = storage.child(f"images/profile_pic_{session['user']}.jpg").get_url(None)
    if form.validate_on_submit():
        try:
            pic_data = form.profile_pic.data
            filename = secure_filename(pic_data.filename)
            pic_data.save(os.path.join(app.instance_path, filename))
            storage.child(f"images/profile_pic_{session['user']}.jpg").put(f"instance/{filename}", session['idToken'])
            os.remove(f"{app.instance_path}/{filename}")
            session['img_url'] = storage.child(f"images/profile_pic_{session['user']}.jpg").get_url(None)
            flash("Dodano zdjęcie!")
            print(session['img_url'])
            return render_template('update_profile_pic.html', form=form, img_url=session['img_url'])
        except Exception as e:
            print(e)
            flash("Wystąpił błąd")
    return render_template('update_profile_pic.html', form=form, img_url=session['img_url'])


@app.route('/download_profile_pic', methods=['POST', 'GET'])
def download_profile_pic():
    form = ProfilePicForm()
    try:
        storage.child(f"images/profile_pic_{session['user']}.jpg").download(path="", filename="static/your_profile_pic.jpg")
        flash("Pobrano zdjęcie!")
    except Exception as e:
        print(e)
        flash("Wystąpił błąd")
    return render_template('update_profile_pic.html', form=form)


@app.route('/notes')
def get_notes():
    notes = Note.query.all()

    output = []
    for note in notes:
        note_data = {
            'id': note.id, 'user': note.user, 'title': note.title,
            'text': note.text, 'date_added': note.date_added
        }
        output.append(note_data)
    return {'notes': output}


@app.route('/notes/<id>')
def get_note(id):
    note = Note.query.get_or_404(id)

    return {
        'id': note.id, 'user': note.user, 'title': note.title,
        'text': note.text, 'date_added': note.date_added
    }


if __name__ == '__main__':
    app.run()
