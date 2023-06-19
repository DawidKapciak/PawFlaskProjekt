from flask import Flask, session, render_template, request, redirect, flash
import pyrebase
import os

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

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

app.secret_key = os.getenv("SECRET_KEY")


@app.route('/', methods=['POST', 'GET'])
def login():
    # auth.create_user_with_email_and_password('test@gmail.com', 'password')

    if('user' in session):
        return render_template('index.html')
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session['user'] = email
        except Exception as e:
            if "EMAIL_NOT_FOUND" in str(e):
                flash("Podałeś błędne hasło lub takie konto z takim adresem email nie istnieje")

    return render_template('login.html')


@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user')
    return redirect('/')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        if password == password2:
            try:
                user = auth.create_user_with_email_and_password(email, password)
                session['user'] = email
                auth.send_email_verification(user['idToken'])
                flash("Utworzono konto")
            except Exception as e:
                if "EMAIL_EXISTS" in str(e):
                    flash("Konto z takim adresem email już istnieje")
        else:
            flash("Hasła nie są takie same!")
    return render_template('signup.html')


@app.route('/forgot', methods=['POST', 'GET'])
def forgot():
    if request.method == "POST":
        try:
            email = request.form.get('email')
            auth.send_password_reset_email(email)
            flash("Na email zostały wysłane dalsze instrukcje")
        except Exception as e:
            if "EMAIL_NOT_FOUND" in str(e):
                flash("Nie istnieje konto z takim adresem email")

    return render_template('forgot.html')


if __name__ == '__main__':
    app.run()
