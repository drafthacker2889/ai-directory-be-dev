from flask import Flask
from flask_cors import CORS
from blueprints.devices.devices import devices_bp
from blueprints.auth.auth import auth_bp
from blueprints.reviews.reviews import reviews_bp 
import globals 

app = Flask(__name__)
app.config['SECRET_KEY'] = globals.SECRET_KEY

CORS(app)

app.register_blueprint(devices_bp, url_prefix='/api/v1.0')
app.register_blueprint(auth_bp, url_prefix='/api/v1.0/auth')
app.register_blueprint(reviews_bp, url_prefix='/api/v1.0')

if __name__ == "__main__":
    app.run(debug=True,use_reloader=False)