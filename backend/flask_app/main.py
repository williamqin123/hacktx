from flask import (
    Blueprint,
    current_app,
    jsonify,
    make_response,
    redirect,
    request,
    url_for,
)

main_bp = Blueprint("main", __name__)

@main_bp.route("/") # user arrives here after logging out -> redirect to frontend homepage
def home():
    return redirect("http://localhost:5173")