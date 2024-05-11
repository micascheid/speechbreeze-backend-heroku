from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    CORS(app)
    db.init_app(app)
    return app