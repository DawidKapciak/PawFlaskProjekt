# PawFlaskProjekt

To get this thing started you need a `.env` file with the following content:

```dotenv
# Firebase Configuration
API_KEY=YOUR_API_KEY  # Your Firebase API Key
AUTH_DOMAIN=YOUR_AUTH_DOMAIN  # Your Firebase Auth Domain
DATABASE_URL=YOUR_DATABASE_URL  # Your Firebase Database URL
PROJECT_ID=YOUR_PROJECT_ID  # Your Firebase Project ID
STORAGE_BUCKET=YOUR_STORAGE_BUCKET  # Your Firebase Storage Bucket
MESSAGING_SENDER_ID=YOUR_MESSAGING_SENDER_ID  # Your Firebase Messaging Sender ID
APP_ID=YOUR_APP_ID  # Your Firebase App ID
SQLALCHEMY_DATABASE_URI=YOUR_DB_PATH # Your Database Path

# Flask Configuration
SECRET_KEY=YOUR_SECRET_KEY  # Secret key for Flask app

# SQlite Configuration
SQLALCHEMY_DATABASE_URI=sqlite:///paw.db
