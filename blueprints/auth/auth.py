from flask import Blueprint, request, jsonify, make_response
from werkzeug.security import check_password_hash, generate_password_hash
import jwt
import datetime
from bson import ObjectId
import globals 
from decorators import jwt_required, admin_required 

auth_bp = Blueprint("auth_bp", __name__)

# --- Database Connection Setup ---
try:
    users_collection = globals.db.users
    blacklist_collection = globals.db.blacklist
    devices_collection = globals.db.devices
except AttributeError:
    print("Error: DB not connected. Cannot get 'users' or 'blacklist' collection.")
    users_collection = None
    blacklist_collection = None
    devices_collection = None

# --- Routes ---

@auth_bp.route("/register", methods=["POST"])
def register():
    if "username" not in request.form or "password" not in request.form:
        return make_response(jsonify({"error": "Username and password required"}), 400)
    
    username = request.form["username"]
    password = request.form["password"]
    
    # Check if user already exists
    # Note: Consistency fix - searching by "user" field as that is what is inserted below
    existing_user = users_collection.find_one({"user": username})
    if existing_user:
        return make_response(jsonify({"error": "Username already exists"}), 409)

    # Hash password and create user
    new_user = {
        "user": username,
        "password": generate_password_hash(password), # Uses werkzeug.security
        "email": request.form.get("email", ""), # Optional
        "admin": False # Default to normal user
    }
    
    users_collection.insert_one(new_user)
    
    return make_response(jsonify({"message": "User created successfully"}), 201)

@auth_bp.route("/login", methods=["GET"])
def login():
    auth = request.authorization
    
    if not auth or not auth.username or not auth.password:
        return make_response(
            'Could not verify', 
            401, 
            {'WWW-Authenticate': 'Basic realm="Login required!"'}
        )
        
    # Consistency fix: Searching for "user" field, not "username"
    user = users_collection.find_one({'user': auth.username})
    
    if not user:
        return make_response(
            'Could not verify', 
            401, 
            {'WWW-Authenticate': 'Basic realm="Login required!"'}
        )
        
    # Use Werkzeug to check hash
    if check_password_hash(user["password"], auth.password):
        token = jwt.encode({
            'user': auth.username,
            'admin': user.get('admin', False),
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=30)
        },
        globals.SECRET_KEY,
        algorithm="HS256")
        
        return make_response(jsonify({'token': token}), 200)
    
    return make_response(
        'Could not verify', 
        401, 
        {'WWW-Authenticate': 'Basic realm="Login required!"'}
    )

@auth_bp.route("/logout", methods=["GET"])
@jwt_required
def logout(current_user):
    token = request.headers['x-access-token']
    blacklist_collection.insert_one({"token": token})
    return make_response(jsonify({'message': 'Logout successful'}), 200)

@auth_bp.route("/profile", methods=["GET", "PUT", "DELETE"])
@jwt_required
def user_profile(current_user):
    username = current_user['user']
    
    if request.method == "GET":
        user_data = users_collection.find_one(
            {'user': username},
            { 'password': 0 }
        )
        if not user_data:
            return make_response(jsonify({"error": "User not found"}), 404)
        
        user_data['_id'] = str(user_data['_id'])
        return make_response(jsonify(user_data), 200)

    elif request.method == "PUT":
        try:
            update_data = {}
            if "name" in request.form:
                update_data["name"] = request.form["name"]
            if "email" in request.form:
                update_data["email"] = request.form["email"]
            
            if not update_data:
                return make_response(jsonify({"error": "No update data provided"}), 400)
            
            result = users_collection.update_one(
                {'user': username},
                { "$set": update_data }
            )
            
            if result.matched_count == 1:
                return make_response(jsonify({"message": "Profile updated"}), 200)
            else:
                return make_response(jsonify({"error": "User not found"}), 404)
                
        except Exception as e:
            return make_response(jsonify({"error": f"Database error: {str(e)}"}), 500)

    elif request.method == "DELETE":
        try:
            token = request.headers['x-access-token']
            blacklist_collection.insert_one({"token": token})
            
            result = users_collection.delete_one({'user': username})
            
            if result.deleted_count == 1:
                return make_response(jsonify({"message": "User deleted"}), 200)
            else:
                return make_response(jsonify({"error": "User not found"}), 404)
                
        except Exception as e:
            return make_response(jsonify({"error": f"Database error: {str(e)}"}), 500)

@auth_bp.route("/myreviews", methods=["GET"])
@jwt_required
def get_my_reviews(current_user):
    username = current_user['user']

    pipeline = [
        { "$unwind": "$reviews" },
        { "$match": { "reviews.user": username } },
        {
            "$project": {
                "_id": 0,
                "device_name": "$name",
                "device_id": "$_id",
                "review_id": "$reviews._id",
                "rating": "$reviews.rating",
                "comment": "$reviews.comment",
                "date": "$reviews.date"
            }
        }
    ]
    
    try:
        my_reviews = list(devices_collection.aggregate(pipeline))

        for review in my_reviews:
            review['device_id'] = str(review['device_id'])
            review['review_id'] = str(review['review_id'])
            
        return make_response(jsonify(my_reviews), 200)
        
    except Exception as e:
        return make_response(jsonify({"error": f"Database error: {str(e)}"}), 500)

@auth_bp.route("/admin/users", methods=["GET"])
@jwt_required
@admin_required
def get_all_users(current_user):
    try:
        users = []
        for user in users_collection.find({}, { 'password': 0 }):
            user['_id'] = str(user['_id'])
            users.append(user)

        return make_response(jsonify(users), 200)

    except Exception as e:
        return make_response(jsonify({"error": f"Database error: {str(e)}"}), 500)

@auth_bp.route("/admin/users/delete/<string:id>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_user(current_user, id):
    if not ObjectId.is_valid(id):
        return make_response(jsonify({"error": "Invalid user ID format"}), 400)

    try:
        user_to_delete = users_collection.find_one({'_id': ObjectId(id)})
        if not user_to_delete:
            return make_response(jsonify({"error": "User not found"}), 404)

        if user_to_delete['user'] == current_user['user']:
            return make_response(jsonify({"error": "Admin cannot delete their own account"}), 400)

        result = users_collection.delete_one({'_id': ObjectId(id)})

        if result.deleted_count == 1:
            return make_response(jsonify({}), 204)
        else:
            return make_response(jsonify({"error": "User not found"}), 404)

    except Exception as e:
        return make_response(jsonify({"error": f"Database error: {str(e)}"}), 500)