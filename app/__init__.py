from flask import Flask
from flask_cors import CORS
from app.extensions import db, cors
from app.blueprints.stripe_webhooks import stripe_bp
from app.blueprints.lsas import lsas_bp
from app.blueprints.org_users import org_bp
from app.blueprints.slp import slp_bp
from app.blueprints.patients import patients_bp
from app.blueprints.lsa import lsa_bp
from app.blueprints.general import general_bp
import os

DEBUG_MODE = os.getenv('DEBUG_MODE', False)


def db_url_jank_fix():
    original_db_url = os.getenv("DATABASE_URL")

    if original_db_url and original_db_url.startswith('postgres://'):
        modified_db_url = original_db_url.replace('postgres://', 'postgresql://', 1)
        os.environ["DATABASE_URL"] = modified_db_url
    else:
        modified_db_url = original_db_url

    return modified_db_url


def create_app():
    app = Flask(__name__)
    app.debug = os.getenv("DEBUG_MODE", False) == "True"
    cors.init_app(app)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url_jank_fix()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    app.register_blueprint(stripe_bp, url_prefix='/stripe')
    app.register_blueprint(org_bp, url_prefix='/org-customers')
    app.register_blueprint(lsas_bp, url_prefix='/lsas')
    app.register_blueprint(slp_bp, url_prefix='/slp')
    app.register_blueprint(patients_bp, url_prefix='/patients')
    app.register_blueprint(lsa_bp, url_prefix='/lsa')
    app.register_blueprint(general_bp)

    return app
