from functools import wraps
from flask import request, jsonify
from jsonschema import validate, ValidationError

def validate_json(schema):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400
            try:
                validate(instance=request.json, schema=schema)
            except ValidationError as e:
                return jsonify({'error': e.message}), 400
            return f(*args, **kwargs)
        return wrapper
    return decorator