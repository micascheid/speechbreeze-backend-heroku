from flask import Blueprint, jsonify, request
from database.models import Slp
from database import db


slp_bp = Blueprint('slp', __name__)


@slp_bp.route('/<string:slp_uid>/check', methods=['GET'])
def slp_check(slp_uid):
    try:
        slp_exist = Slp.check_slp_exist(slp_uid) is not None
        return jsonify({"exists": slp_exist}), 200
    except Exception as e:
        print(f"unable to check user: {slp_uid} with error: {e}")
        return jsonify({"error": f"unable to check user: {slp_uid} with error: {e}"}), 500


@slp_bp.route('/add', methods=['POST'])
def add_slp():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    slp_id = data.get('slp_id')
    name = data.get('name')
    email = data.get('email')

    if not all([slp_id, name, email]):
        return jsonify({"error": "Missing required fields (slp_id, name, email)"}), 400

    try:
        # Assuming you have a function to add an SLP and check for duplicates
        existing_slp = Slp.query.filter_by(slp_id=slp_id).first()
        if existing_slp:
            return jsonify({"error": "An SLP with the given ID already exists"}), 409

        # Adding the new SLP
        new_slp = Slp(slp_id=slp_id, name=name, email=email)
        db.session.add(new_slp)
        db.session.commit()

        return jsonify({"success": "SLP added successfully", "slp_id": new_slp.slp_id}), 201

    except Exception as e:
        db.session.rollback()
        print(f"Failed to add SLP: {slp_id} with error: {e}")
        return jsonify({"error": f"Failed to add SLP: {slp_id} with error: {e}"}), 500


@slp_bp.route('/<string:slp_uid>', methods=['GET'])
def slp_info(slp_uid):
    try:
        slp = Slp.check_slp_exist(slp_uid)
        if slp:
            return jsonify(slp.to_dict()), 200
        else:
            return jsonify({"error": f"No SLP found with the provided UID: {slp_uid}"}), 404
    except Exception as e:
        print(f"unable to check user: {slp_uid} with error: {e}")
        return jsonify({"error": f"unable to find slp: {slp_uid} with error: {e}"}), 500