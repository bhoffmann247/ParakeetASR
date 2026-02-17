from flask import Blueprint

home_blueprint = Blueprint('home_blueprint', __name__)

@home_blueprint.route('/', methods=['GET'])
def home():
    return "Parakeet API - IntouchCX", 200
