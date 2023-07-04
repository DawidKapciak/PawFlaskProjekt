import os
import tempfile
import pytest
from random import randrange

from app import app, User

with app.app_context():
    user = User.query.first()
    api_key = user.api_key
    email = user.email


@pytest.fixture
def client():
    db_fd, app.config['SQLALCHEMY_DATABASE_URI'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    client = app.test_client()

    yield client


def test_login_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Zaloguj' in response.data


def test_invalid_login(client):
    response = client.post('/', data=dict(email='invalid@example.com', password='password'), follow_redirects=True)
    assert response.status_code == 200
    assert b'lub takie konto z takim adresem email nie istnieje.' in response.data


def test_valid_login(client):
    response = client.post('/', data=dict(email=email, password='adminn'))
    assert response.status_code == 200
    assert b'Dodaj notatk' in response.data


def test_signup(client):
    response = client.post('/signup', data=dict(email=(str(randrange(9999)) + email), password='password',
                                                password2='password'), follow_redirects=True)
    assert response.status_code == 200
    assert b'Utworzono konto' in response.data


def test_forgot_password(client):
    client.post('/signup', data=dict(email=email, password='password',
                                     password2='password'), follow_redirects=True)
    response = client.post('/forgot', data=dict(email=email), follow_redirects=True)
    assert response.status_code == 200
    assert b'dalsze instrukcje.' in response.data


def test_update_profile_pic(client):
    test_valid_login(client)
    with client.session_transaction() as session:
        session['user'] = email

    response = client.post('/settings',
                           data=dict(profile_pic=(open('instance/test.jpg', 'rb'), 'test.jpg'),
                                     follow_redirects=True))
    assert response.status_code == 200
    assert b'Dodano zdj' in response.data


def test_download_profile_pic(client):
    with client.session_transaction() as session:
        session['user'] = email

    response = client.get('/download_profile_pic', follow_redirects=True)
    if b'Wyst\xc4\x85pi\xc5\x82 b\xc5\x82\xc4\x85d\n' in response.data:
        client.post('/settings', data=dict(profile_pic=(open('instance/test.jpg', 'rb'), 'test.jpg'),
                                           follow_redirects=True))
        response = client.get('/download_profile_pic', follow_redirects=True)
    assert response.status_code == 200
    assert b'Pobrano' in response.data


def test_get_notes_rest(client):
    response = client.get(f'/notes?api_key={api_key}')
    assert response.status_code == 200
    assert b'{"notes": [' in response.data


def test_get_note_rest(client):
    response = client.get(f'/notes?api_key={api_key}')
    notes = response.json.get('notes')

    if len(notes) == 0:
        assert len(notes) > 0
    else:

        note_id = notes[0]['id']

        response = client.get(f'/notes/{note_id}?api_key={api_key}')
        assert response.status_code == 200
        assert b'"date_added": "' in response.data


def test_post_rest(client):
    data = {
        "title": "Test Note",
        "text": "This is a test note"
    }
    response = client.post(f'/notes?api_key={api_key}', json=data,
                           follow_redirects=True)
    assert response.status_code == 200

    assert b'{"title": "Test Note",' in response.data


def test_put_rest(client):
    with client.session_transaction() as session:
        session['user'] = email
    response = client.get(f'/notes?api_key={api_key}')
    notes = response.json.get('notes')

    if len(notes) == 0:
        assert len(notes) > 0
    else:

        note_id = notes[0]['id']

        data = {
            "title": "Updated Note",
            "text": "This note has been updated"
        }
        response = client.put(f'/notes/{note_id}?api_key={api_key}', json=data,
                              follow_redirects=True)
        assert response.status_code == 200
        assert b'Updated Note' in response.data
        assert b'This note has been updated' in response.data


def test_delete_rest(client):
    with client.session_transaction() as session:
        session['user'] = email

    response = client.get(f'/notes?api_key={api_key}')
    notes = response.json.get('notes')

    if len(notes) == 0:
        assert len(notes) > 0
    else:
        note_id = notes[0]['id']

        response = client.delete(f'/notes/{note_id}?api_key={api_key}', follow_redirects=True)
        assert response.status_code == 200
        assert b'"message": "Note deleted!"' in response.data


if __name__ == '__main__':
    pytest.main()
