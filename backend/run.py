import os
from flask import Flask, redirect, url_for, session, make_response, request
from authlib.integrations.flask_client import OAuth
from jose import jwt # pip install python-jose

app = Flask(__name__)
app.secret_key = os.environ.get("AUTH0_SECRET")

oauth = OAuth(app)
auth0 = oauth.register(...) # Keep your same oauth config from step 2

# Helper function to decode the JWT string on-the-fly
def get_current_user():
    token_string = request.cookies.get("auth_token")
    if not token_string:
        return None
    try:
        # Decode without verification just to read info, 
        # or download Auth0 JWKS keys to securely verify signature.
        return jwt.get_unverified_claims(token_string)
    except Exception:
        return None

@app.route("/callback")
def callback():
    token = auth0.authorize_access_token()
    
    # 1. Grab the raw ID Token string (the JWT)
    id_token_jwt = token.get("id_token") 
    
    # 2. Redirect to profile but append the JWT to a secure cookie
    response = make_response(redirect(url_for("profile")))
    response.set_cookie(
        "auth_token", 
        id_token_jwt, 
        httponly=True,   # Protects against XSS
        secure=False,    # Change to True in production (HTTPS)
        samesite="Lax"
    )
    return response

@app.route("/profile")
def profile():
    userinfo = get_current_user()
    if not userinfo:
        return redirect(url_for("login"))
        
    return f"Logged in as {userinfo.get('name')}"

@app.route("/logout")
def logout():
    # Clear the cookie on logout
    response = make_response(redirect(f"https://{os.environ.get('AUTH0_DOMAIN')}/v2/logout?..."))
    response.delete_cookie("auth_token")
    return response
