

from flask import Flask
from modules.app_bs import BSModule
from modules.app_admin import AdminModule
from modules.app_analytics import AnalyticsModule
from modules.app_shorten import ShortenModule

class MainApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.register_modules()
        self.register_routes()

    def register_modules(self):
        self.app.register_blueprint(BSModule().get_blueprint())
        self.app.register_blueprint(AdminModule().get_blueprint())
        self.app.register_blueprint(AnalyticsModule().get_blueprint())
        self.app.register_blueprint(ShortenModule().get_blueprint())

    def register_routes(self):
        @self.app.route("/")
        def home():
            return "Welcome to the Main App!"
        
    def get_app(self):
        return self.app
    

# This code initializes a Flask application and registers multiple modules (blueprints) to it.
# Each module is defined in its own file within the `modules` directory.
# The `MainApp` class encapsulates the application setup, including the registration of blueprints.
# The `get_app` method returns the Flask application instance.    
