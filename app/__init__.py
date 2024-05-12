from flask import Flask
from flask_cors import CORS
from .database import db
from .blueprints.stripe_webhooks import stripe_bp
from .blueprints.lsas import lsas_bp
from .blueprints.org_users import org_bp
from .blueprints.slp import slp_bp
from .blueprints.patients import patients_bp
from .blueprints.lsa import lsa_bp
import os

def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    app.register_blueprint(stripe_bp, url_prefix='/stripe')
    app.register_blueprint(org_bp, url_prefix='/org-customers')
    app.register_blueprint(lsas_bp, url_prefix='/lsas')
    app.register_blueprint(slp_bp, url_prefix='/slp')
    app.register_blueprint(patients_bp, url_prefix='/patients')
    app.register_blueprint(lsa_bp, url_prefix='/lsa')

    return app
