from flask import Blueprint, jsonify, request
from database.models import OrgCustomer, Slp
from database import db


org_bp = Blueprint('org_customers', __name__)


@org_bp.route('/<string:email>/add-to-org', methods=['POST'])
def add_slp_to_org(email):
    try:
        slp_email = email
        data = request.get_json()
        org_code = data.get('org_code')
        org = OrgCustomer.query.filter_by(org_code=org_code).first()

        if slp_email in org.slps:
            slp = Slp.query.filter_by(email=slp_email).first()
            slp.org_id = org.id
            slp.sub_end = org.sub_end
            slp.sub_type = 3
            db.session.commit()
        else:
            print(f"The user email: {email} was not found as a part of: {org.name}")
            return jsonify({"message": f"The user email: {email} was not found as a part of: {org.name}"}), 404
        return jsonify({"message": f"Access through the following organization: {org.name}"}), 200
    except Exception as e:
        print(f"Unable to verify user is part of org: {e}")
        return jsonify({"error": 'Bad payload'}), 500


