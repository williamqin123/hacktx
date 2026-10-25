import os
from flask import Flask, json
from flask_cors import CORS

import firebase_admin
from firebase_admin import credentials, firestore

PUBLIC_FRONTEND_ORIGIN = 'https://prandium-ai.onrender.com'

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
        origins=[PUBLIC_FRONTEND_ORIGIN],
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

    from flask_app.recipe_catalog import recipe_bp
    app.register_blueprint(recipe_bp)

    from flask_app.kroger import kroger_bp
    app.register_blueprint(kroger_bp)

    from flask_app.kroger_cart import kroger_cart_bp
    app.register_blueprint(kroger_cart_bp)
    
    return app