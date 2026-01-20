from app.app import app
from app.api.transcription_controller import transcription_blueprint
from app.api.home_controller import home_blueprint

app.register_blueprint(transcription_blueprint, url_prefix='/transcriptions')
app.register_blueprint(home_blueprint)
