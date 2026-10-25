import os
from flask import Flask, json
from flask_cors import CORS

import firebase_admin
from firebase_admin import credentials, firestore

creds_env = os.environ.get('FIREBASE_CREDENTIALS_JSON')

# 1. Check if the app is already initialized to avoid duplicate app errors
if creds_env and not firebase_admin._apps:
    creds_dict = json.loads(creds_env)
    cred = credentials.Certificate(creds_dict)
    firebase_admin.initialize_app(cred)



def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ["AUTH0_SECRET"]

    CORS(
        app,
        origins=["http://localhost:5173"],
        supports_credentials=True,
    )
    
    # Imports blueprints locally to prevent circular imports
    from flask_app.auth import auth_bp, init_auth
    
    init_auth(app)
    app.register_blueprint(auth_bp)

    from flask_app.main import main_bp
    app.register_blueprint(main_bp)

    from flask_app.user import user_bp
    app.register_blueprint(user_bp)

    from flask_app.meals import walmart_bp
    app.register_blueprint(walmart_bp)
    
    return app