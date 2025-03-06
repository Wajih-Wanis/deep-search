from functools import wraps
from flask import jsonify, request
from bson import ObjectId
import json
import logging

def json_response(data=None, status=200, message=None):
    """Standardize API response format"""
    return jsonify({
        'success': status in [200, 201],
        'data': data,
        'message': message
    }), status

def validate_object_id(id_name):
    """MongoDB ObjectID validation decorator"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                kwargs[id_name] = ObjectId(kwargs[id_name])
            except:
                return json_response(
                    message=f"Invalid {id_name.replace('_', ' ')} ID format",
                    status=400
                )
            return f(*args, **kwargs)
        return wrapper
    return decorator

def handle_errors(f):
    """Global error handler decorator"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {f.__name__}: {str(e)}")
            return json_response(
                message="An unexpected error occurred",
                status=500
            )
    return wrapper

def parse_json(schema=None):
    """Enhanced JSON parsing with optional schema validation"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json(force=True)
                if schema:
                    validate_schema(data, schema)
                request.parsed_data = data
            except json.JSONDecodeError:
                return json_response(message="Invalid JSON format", status=400)
            except ValueError as e:
                return json_response(message=str(e), status=400)
            return f(*args, **kwargs)
        return wrapper
    return decorator

def validate_schema(data, schema):
    """Custom schema validation logic"""
    # Implement your schema validation logic here
    # Example: check required fields, data types, etc.
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")