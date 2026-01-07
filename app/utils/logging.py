import logging
import sys
import os
from pythonjsonlogger import jsonlogger
from flask import request, has_request_context

class RequestFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(RequestFormatter, self).add_fields(log_record, record, message_dict)
        if has_request_context():
            log_record['ip'] = request.remote_addr
            log_record['method'] = request.method
            log_record['path'] = request.path
        else:
            log_record['ip'] = None
            log_record['method'] = None
            log_record['path'] = None

def configure_logging(app):
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    handler = logging.StreamHandler(sys.stdout)
    
    if not app.debug:
        formatter = RequestFormatter('%(asctime)s %(levelname)s %(message)s %(ip)s %(method)s %(path)s')
        handler.setFormatter(formatter)
    else:
        # Simple text logging for debug
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))

    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)
