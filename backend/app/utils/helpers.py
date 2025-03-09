# Fixed helpers.py
from functools import wraps
from flask import jsonify, request
from bson import ObjectId
import json
import logging
from jsonschema import validate, ValidationError

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
            except ValidationError as e:
                return json_response(message=f"Schema validation error: {e.message}", status=400)
            return f(*args, **kwargs)
        return wrapper
    return decorator

def validate_schema(data, schema):
    """Proper schema validation with jsonschema"""
    # First check required fields
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Then validate property types if specified
    properties = schema.get('properties', {})
    for field, field_schema in properties.items():
        if field in data:
            if field_schema.get('type') == 'object' and not isinstance(data[field], dict):
                raise ValueError(f"Field '{field}' must be an object")
            elif field_schema.get('type') == 'array' and not isinstance(data[field], list):
                raise ValueError(f"Field '{field}' must be an array")
            elif field_schema.get('type') == 'string' and not isinstance(data[field], str):
                raise ValueError(f"Field '{field}' must be a string")
            elif field_schema.get('type') == 'number' and not isinstance(data[field], (int, float)):
                raise ValueError(f"Field '{field}' must be a number")
    
    # Use jsonschema for more complex validations
    if 'jsonschema' in schema:
        validate(instance=data, schema=schema['jsonschema'])