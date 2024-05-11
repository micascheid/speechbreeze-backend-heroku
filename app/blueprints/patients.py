from flask import Blueprint, jsonify, request
from app.app import Patient
from app.app import db

patients_bp = Blueprint('patients', __name__)


@patients_bp.route('/<string:uid>', methods=['GET'])
def get_patients(uid):
    slp_uid = uid

    try:
        patients = Patient.get_patients(slp_uid)
        patients_list = [patient.to_dict() for patient in patients]
        return jsonify(patients_list)
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An error occurred retrieving patients"}), 500


@patients_bp.route('/add-patient', methods=['POST'])
def add_patient():
    # Extracting patient data from the request
    slp_id = request.json.get('slp_id')
    name = request.json.get('name')
    age = request.json.get('age')
    print(f"slp: {slp_id}, name: {name}, age: {age}")
    # Input validation (simplified for brevity; consider more comprehensive checks)
    if not all([slp_id, name, age]):
        return jsonify({"error": "Missing required patient data"}), 400
    try:
        Patient.add_patient(slp_id, name, age)
        return jsonify({"message": "Patient added successfully"}), 201
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": f"Failed to add patient: {e}"}), 500


@patients_bp.route('/<string:patient_id>/delete', methods=['DELETE'])
def delete_patient(patient_id):
    try:
        patient_obj = Patient.get_patient_for_delete(patient_id)
        if patient_obj:
            db.session.delete(patient_obj)
            db.session.commit()
            return jsonify({"message": f"Deleted patient with id {patient_id}"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"An error occurred deleting patient: {e}")
        return jsonify({"error": f"An error occurred deleting the patient {e}"}), 500

