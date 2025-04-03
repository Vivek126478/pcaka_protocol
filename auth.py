import jwt
import time
from flask import request, jsonify

SECRET_KEY = 'super_secret_key'

def generate_jwt(username):
    payload = {
        'username': username,
        'timestamp': time.time()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def token_required(f):
    def wrap(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        try:
            jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 403
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap