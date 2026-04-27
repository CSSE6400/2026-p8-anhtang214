import logging
import watchtower
from flask import has_request_context, request

# Custom formatter that wraps logs in JSON objects with metadata,
# making them easier to ssearch and filter in CloudWatch
class StructuredFormatter(watchtower.CloudWatchLogFormatter):
    def format(self, record):
        # Replace the plain log message with a structured JSON object
        record.msg = {
            'timestamp': record.created,    # Unix timestamp of when the log was created
            'location': record.name,        # Logger name (e.g., 'sqlalchemy.engine', 'werkzeug')
            'message': record.msg,          # Original log message
        }
        # Inject HTTP request metadata if we're inside a Flask request context
        if has_request_context():
            # Unique ID for tracing the request
            record.msg['request_id'] = request.environ.get('REQUEST_ID')
            # URL path that was hit
            record.msg['url'] = request.environ.get('PATH_INFO')
            # HTTP method (GET, POST, etc.)
            record.msg['method'] = request.environ.get('REQUEST_METHOD')
        # Delegate final formatting to the parent CloudWatch formatter
        return super().format(record)