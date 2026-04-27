import os
import boto3
import watchtower, logging
import uuid
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy 
from .log_formatter import StructuredFormatter

def create_app(config_overrides=None):
    logging.basicConfig(level=logging.INFO)

    app = Flask(__name__, static_folder='app', static_url_path="/") 
 
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///db.sqlite")
    if config_overrides: 
        app.config.update(config_overrides)
 
    # Send logs to AWS CloudWatch under the "taskoverflow" log group
    handler = watchtower.CloudWatchLogHandler(
            log_group_name="taskoverflow",
            boto3_client=boto3.client("logs", region_name="us-east-1")
    )
    handler.setFormatter(StructuredFormatter())

    # Attach CloudWatch handler to all relevant loggers
    app.logger.addHandler(handler)      # Flask app logs
    logging.getLogger().addHandler(handler) # Root logger (catches everything)
    logging.getLogger('werkzeug').addHandler(handler)   # HTTP request logs
    logging.getLogger("sqlalchemy.engine").addHandler(handler)  # SQL query logs
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)   # Enable SQL query logging at INFO level

    # Logger for tracking individual HTTP requests
    requests = logging.getLogger("requests")
    requests.addHandler(handler)

    # Assign a unique correlation ID to each request for tracing,
    # and log when requests start and finish
    @app.before_request()
    def before_request():
        request.environ['REQUEST_ID'] = str(uuid.uuid4())
        requests.info("Request started")

    @app.after_request
    def after_request(response):
        requests.info("Request finished")
        return response

    # Load the models 
    from todo.models import db 
    from todo.models.todo import Todo 
    db.init_app(app) 
 
    # Create the database tables 
    with app.app_context(): 
        db.create_all() 
        db.session.commit() 
 
    # Register the blueprints 
    from todo.views.routes import api 
    app.register_blueprint(api) 

    app.add_url_rule('/', 'index', lambda: app.send_static_file('index.html'))
 
    return app
