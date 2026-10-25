from flask import (
    Blueprint,
    current_app,
    make_response,
    redirect,
    request,
    url_for,
    jsonify
)
import logging
from .auth import login_required
from firebase_admin import firestore

user_bp = Blueprint("user", __name__)


@user_bp.route("/set-profile-info", methods=["POST"])
@login_required
def set_profile_info():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Missing profile data"}), 400

        user_id = request.current_user["sub"]

        db = firestore.client()
        user_ref = db.collection("users").document(user_id)

        user_doc = user_ref.get()

        profile = {
            "name": data.get("name", ""),
            "age": data.get("age"),
            "sex": data.get("sex", ""),
            "height": data.get("height"),
            "weight": data.get("weight"),
            "dietaryRestrictions": data.get("dietaryRestrictions", []),
            "goal": data.get("goal", "maintain"),
        }

        user_data = {"profile": profile}

        if not user_doc.exists:
            user_data["createdAt"] = firestore.SERVER_TIMESTAMP

        user_ref.set(user_data, merge=True)

        return jsonify({
            "message": "Profile saved successfully"
        }), 200

    except Exception as e:
        logging.error(e)
        return jsonify({"error": "Failed to save profile"}), 500
    
@user_bp.route("/get-profile-info", methods=["GET"])
@login_required
def get_profile_info():
    try:
        user_id = request.current_user["sub"]

        db = firestore.client()
        user_ref = db.collection("users").document(user_id)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return jsonify({"error": "User not found"}), 404

        user_data = user_doc.to_dict()
        profile = user_data.get("profile")

        if not profile:
            return jsonify({"error": "Profile not found"}), 404

        return jsonify(profile), 200

    except Exception as e:
        logging.error(e)
        return jsonify({"error": "Failed to load profile"}), 500