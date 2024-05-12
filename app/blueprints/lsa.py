from flask import Blueprint, jsonify, request
from app.database.models import Lsa
from app.extensions import db
from datetime import datetime
lsa_bp = Blueprint('lsa', __name__)


@lsa_bp.route('/<int:lsaId>', methods=['GET'])
def lsa(lsaId):
    lsa_id = lsaId

    try:
        lsa_obj = Lsa.get_lsa_by_id(lsa_id).to_dict()
        return jsonify(lsa_obj)
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An error occurred retrieving patients"}), 500


@lsa_bp.route('/create-lsa', methods=['POST'])
def create_lsa():
    patient_id = request.json.get('patient_id')
    lsa_name = request.json.get('name')
    audio_type = request.json.get('audio_type')
    transcription_automated = request.json.get('transcription_automated')
    current_date = datetime.utcnow()
    print(current_date)

    formatted_date = current_date.strftime('%Y-%m-%d')
    if not all([patient_id, lsa_name]):
        return jsonify({"error": "Missing required LSA info"}), 400
    try:
        new_lsa = Lsa.create_lsa(patient_id=patient_id, name=lsa_name, transcription_automated=transcription_automated,
                       audio_type=audio_type,
                       timestamp=current_date)
        return jsonify({"message": "Lsa added successfully", "lsa_id": new_lsa.lsa_id}), 201
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Failed to add Lsa"}), 500


@lsa_bp.route('/<string:lsa_id>/delete', methods=['DELETE'])
def delete_lsa(lsa_id):
    try:
        lsa_obj = Lsa.get_lsa_by_id(lsa_id)
        if lsa_obj:
            db.session.delete(lsa_obj)
            db.session.commit()
            return jsonify({"message": f"Deleted LSA with id {lsa_id}"}), 200
    except Exception as e:
        print(f"An error occurred deleting LSA: {e}")
        return jsonify({"error": f"An error occured deleting the LSA {e}"}), 500
