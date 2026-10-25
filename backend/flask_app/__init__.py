import os
from flask import Flask
from flask_cors import CORS

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

    from flask_app.WalmartEP import walmart_bp
    app.register_blueprint(walmart_bp)
    
    return app