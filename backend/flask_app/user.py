from flask import (
    Blueprint,
    current_app,
    make_response,
    redirect,
    request,
    url_for,
)

user_bp = Blueprint("user", __name__)

@user_bp.route("/set-profile-info", methods=['POST'])
def set_profile_info():
    data = request.json
    current_app.logger.info("Received profile info: %s", data)
    return ''