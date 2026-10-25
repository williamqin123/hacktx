import os
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ["AUTH0_SECRET"]
    
    # Imports blueprints locally to prevent circular imports
    from flask_app.auth import auth_bp, init_auth
    
    init_auth(app)
    app.register_blueprint(auth_bp)
    
    return app