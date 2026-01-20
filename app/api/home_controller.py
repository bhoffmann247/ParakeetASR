from app.app import app, oidc
from flask import Blueprint, request

home_blueprint = Blueprint('home_blueprint', __name__)

@home_blueprint.route('/', methods=['GET'])
def home():
    return "Parakeet API - IntouchCX", 200
