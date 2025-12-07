from flask import Blueprint, request, jsonify, make_response
from bson import ObjectId
import globals 
import json
import datetime
from decorators import jwt_required, admin_required 

reviews_bp = Blueprint("reviews_bp", __name__)

try:
    devices_collection = globals.db.devices
except AttributeError:
    print("Error: Database not connected. Cannot get 'devices' collection.")
    devices_collection = None

@reviews_bp.route("/devices/<string:id>/reviews/", methods=["GET"])
def get_all_reviews(id):
    if not ObjectId.is_valid(id):
        return make_response(jsonify({"error": "Invalid device ID format"}), 400)
    try:
        data = devices_collection.find_one(
            { "_id": ObjectId(id) },
            { "reviews": 1, "_id": 0 }
        )
        if data and 'reviews' in data:
            for review in data.get('reviews', []):
                if '_id' in review:
                    review['_id'] = str(review['_id'])
            return make_response(jsonify(data['reviews']), 200)
        elif data: 
             return make_response(jsonify([]), 200) 
        else:
            return make_response(jsonify({"error": "Device not found"}), 404)
    except Exception as e:
        return make_response(jsonify({"error": f"Database error: {str(e)}"}), 500)

@reviews_bp.route("/devices/<string:id>/reviews/add", methods=["POST"])
@jwt_required
def add_new_review(current_user, id):
    if not ObjectId.is_valid(id):
        return make_response(jsonify({"error": "Invalid device ID format"}), 400)
    if "comment" not in request.form or "rating" not in request.form:
        return make_response(jsonify({"error": "Missing form data"}), 400)
    try:
        try:
            rating = int(request.form["rating"])
            if not 1 <= rating <= 5:
                return make_response(jsonify({"error": "Rating must be between 1 and 5"}), 400)
        except ValueError:
            return make_response(jsonify({"error": "Invalid rating, must be an integer"}), 400)

        new_review = {
            "_id": ObjectId(), 
            "user": current_user['user'], 
            "comment": request.form["comment"],
            "rating": rating, 
            "date": datetime.datetime.now(datetime.UTC)
        }
        result = devices_collection.update_one(
            { "_id": ObjectId(id) },
            { "$push": { "reviews": new_review } }
        )
        if result.matched_count == 1:
            new_review_link = f"/api/v1.0/devices/{id}/reviews/{str(new_review['_id'])}"
            return make_response(jsonify({"url": new_review_link}), 201)
        else:
            return make_response(jsonify({"error": "Device not found"}), 404)
    except Exception as e:
        return make_response(jsonify({"error": f"Database error: {str(e)}"}), 500)

@reviews_bp.route("/devices/<string:id>/reviews/update/<string:review_id>", methods=["PUT"])
@jwt_required
def update_review(current_user, id, review_id):
    if not ObjectId.is_valid(id) or not ObjectId.is_valid(review_id):
        return make_response(jsonify({"error": "Invalid ID format"}), 400)
    
    if "comment" not in request.form and "rating" not in request.form:
        return make_response(jsonify({"error": "No update data provided"}), 400)
    try:
        update_data = {}
        if "comment" in request.form:
            update_data["reviews.$.comment"] = request.form["comment"]
        if "rating" in request.form:
            try:
                rating = int(request.form["rating"])
                if not 1 <= rating <= 5:
                    return make_response(jsonify({"error": "Rating must be between 1 and 5"}), 400)
                update_data["reviews.$.rating"] = rating
            except ValueError:
                return make_response(jsonify({"error": "Invalid rating, must be an integer"}), 400)

        query = { 
            "_id": ObjectId(id), 
            "reviews._id": ObjectId(review_id) 
        }
        if not current_user['admin']:
            query["reviews.user"] = current_user['user']

        result = devices_collection.update_one(
            query,
            { "$set": update_data }
        )
        
        if result.matched_count == 1:
            edited_review_link = f"/api/v1.0/devices/{id}/reviews/{review_id}"
            return make_response(jsonify({"url": edited_review_link}), 200)
        else:
            return make_response(jsonify({"error": "Review not found or user not authorized"}), 404)
    except Exception as e:
        return make_response(jsonify({"error": f"Database error: {str(e)}"}), 500)

@reviews_bp.route("/devices/<string:id>/reviews/delete/<string:review_id>", methods=["DELETE"])
@jwt_required
def delete_review(current_user, id, review_id):
    if not ObjectId.is_valid(id) or not ObjectId.is_valid(review_id):
        return make_response(jsonify({"error": "Invalid ID format"}), 400)
    try:
        query = { "_id": ObjectId(id) } 
        if current_user['admin']:
            update_query = { "$pull": { "reviews": { "_id": ObjectId(review_id) } } }
        else:
            update_query = { "$pull": { "reviews": { "_id": ObjectId(review_id), "user": current_user['user'] } } }
        
        result = devices_collection.update_one(query, update_query)

        if result.modified_count == 1:
            return make_response(jsonify({}), 204) 
        else:
            return make_response(jsonify({"error": "Review not found or user not authorized"}), 404)
    except Exception as e:
        return make_response(jsonify({"error": f"Database error: {str(e)}"}), 500)

@reviews_bp.route("/devices/<string:id>/stats", methods=["GET"])
def get_review_stats(id):
    if not ObjectId.is_valid(id):
        return make_response(jsonify({"error": "Invalid device ID format"}), 400)
            
    pipeline = [
        { "$match": { "_id": ObjectId(id) } },
        { "$unwind": "$reviews" },
        {
            "$group": {
                "_id": "$_id",
                "average_rating": { "$avg": "$reviews.rating" },
                "review_count": { "$sum": 1 }
            }
        }
    ]
    
    try:
        stats = list(devices_collection.aggregate(pipeline))
        
        if not stats:
            return make_response(jsonify({
                "device_id": id,
                "average_rating": None,
                "review_count": 0
            }), 200)
        
        result = stats[0]
        result['device_id'] = str(result.pop('_id'))
        
        return make_response(jsonify(result), 200)
        
    except Exception as e:
        return make_response(jsonify({"error": f"Database error: {str(e)}"}), 500)