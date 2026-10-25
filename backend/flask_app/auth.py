import os
from functools import wraps
from urllib.parse import urlencode
import logging
import requests
from flask import (
    Blueprint,
    current_app,
    make_response,
    redirect,
    request,
    url_for,
    jsonify,
)
from authlib.integrations.flask_client import OAuth
from authlib.jose import jwt, JsonWebKey

auth_bp = Blueprint("auth", __name__)

oauth = OAuth()
auth0 = None


def init_auth(app):
    """Initialize Auth0 with the Flask application."""
    global auth0

    domain = os.environ["AUTH0_DOMAIN"]
    oauth.init_app(app)

    auth0 = oauth.register(
        name="auth0",
        client_id=os.environ["AUTH0_CLIENT_ID"],
        client_secret=os.environ["AUTH0_CLIENT_SECRET"],
        server_metadata_url=(
            f"https://{domain}/.well-known/openid-configuration"
        ),
        client_kwargs={"scope": "openid profile email"},
    )


def get_jwks():
    """Fetch Auth0's public signing keys."""
    domain = os.environ["AUTH0_DOMAIN"]
    response = requests.get(
        f"https://{domain}/.well-known/jwks.json",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()["keys"]


def verify_token(token):
    """Verify the Auth0 ID token signature and essential claims."""
    domain = os.environ["AUTH0_DOMAIN"]
    issuer = f"https://{domain}/"
    audience = os.environ["AUTH0_CLIENT_ID"]

    # Parse the JWT header without verifying the signature.
    header_segment = token.split(".")[0]

    import base64
    import json

    padded = header_segment + "=" * (-len(header_segment) % 4)
    header = json.loads(
        base64.urlsafe_b64decode(padded).decode("utf-8")
    )

    if header.get("alg") != "RS256":
        raise ValueError("Unexpected JWT algorithm")

    key_data = next(
        (
            key for key in get_jwks()
            if key["kid"] == header.get("kid")
        ),
        None,
    )

    if key_data is None:
        raise ValueError("Signing key not found")

    key = JsonWebKey.import_key(key_data)

    # Verify the signature using the trusted public key.
    claims = jwt.decode(token, key)
    claims.validate()

    if claims.get("iss") != issuer:
        raise ValueError("Invalid issuer")

    token_aud = claims.get("aud")
    if audience not in (
        token_aud if isinstance(token_aud, list) else [token_aud]
    ):
        raise ValueError("Invalid audience")

    return claims


def login_required(f):
    """Protect a Flask endpoint using the auth_token cookie."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("auth_token")

        if not token:
            return jsonify({"error": "Unauthorized"}), 401

        try:
            request.current_user = verify_token(token)
        except Exception:
            logging.error("Token verification failed", exc_info=True)
            response = make_response(
                jsonify({"error": "Invalid or expired token"}),
                401,
            )
            response.delete_cookie("auth_token", path="/")
            return response

        return f(*args, **kwargs)

    return decorated


@auth_bp.route("/login")
def login():
    return auth0.authorize_redirect(
        redirect_uri=url_for("auth.callback", _external=True)
    )


@auth_bp.route("/callback")
def callback():
    token = auth0.authorize_access_token()
    id_token = token["id_token"]

    # Store the ID token in an HTTP-only cookie.
    response = make_response(redirect("http://localhost:5173/logged-in-app/studio"))
    response.set_cookie(
        "auth_token",
        id_token,
        httponly=True,
        secure=not current_app.debug,
        samesite="Lax",
        path="/",
    )
    return response

@auth_bp.route("/logout")
def logout():
    domain = os.environ["AUTH0_DOMAIN"]
    client_id = os.environ["AUTH0_CLIENT_ID"]
    return_to = url_for("main.home", _external=True)

    logout_url = (
        f"https://{domain}/v2/logout?"
        + urlencode({
            "client_id": client_id,
            "returnTo": return_to,
        })
    )

    response = make_response(redirect(logout_url))
    response.delete_cookie("auth_token", path="/")
    return response