from functools import wraps
from flask import request, jsonify, make_response
import jwt
import globals

try:
    blacklist_collection = globals.db.blacklist
except AttributeError:
    print("Error: DB not connected. Cannot get 'blacklist' collection.")
    blacklist_collection = None

def jwt_required(func):
    @wraps(func)
    def jwt_required_wrapper(*args, **kwargs):
        token = None
        
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        
        if not token:
            return make_response(jsonify({'message': 'Token is missing'}), 401)
        
        if blacklist_collection is not None and blacklist_collection.find_one({"token": token}):
            return make_response(jsonify({'message': 'Token has been cancelled'}), 401)
            
        try:
            data = jwt.decode(
                token, 
                globals.SECRET_KEY, 
                algorithms=["HS256"]
            )
            current_user = data 
        except:
            return make_response(jsonify({'message': 'Token is invalid'}), 401)
            
        return func(current_user, *args, **kwargs)
    return jwt_required_wrapper

def admin_required(func):
    @wraps(func)
    def admin_required_wrapper(*args, **kwargs):
        token = request.headers['x-access-token']
        data = jwt.decode(
            token, 
            globals.SECRET_KEY, 
            algorithms=["HS256"]
        )
        
        if data["admin"]:
            return func(*args, **kwargs) 
        else:
            return make_response(jsonify({'message': 'Admin access required'}), 403)
    return admin_required_wrapper