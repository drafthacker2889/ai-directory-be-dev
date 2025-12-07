from flask import Blueprint, request, jsonify, make_response
from bson import ObjectId
import globals 
import json
import datetime 
from decorators import jwt_required, admin_required 

devices_bp = Blueprint("devices_bp", __name__)

try:
    devices_collection = globals.db.devices
except AttributeError:
    print("Error: Database not connected. Cannot get 'devices' collection.")
    devices_collection = None

@devices_bp.route("/devices/stats/average-latency", methods=["GET"])
def get_latency_stats():
    pipeline = [
        {"$group": {"_id": "$category", "average_latency": {"$avg": "$avg_inference_latency_ms"}, "device_count": {"$sum": 1}}},
        {"$sort": {"average_latency": 1}}
    ]
    try:
        stats = list(devices_collection.aggregate(pipeline))
        return make_response(jsonify(stats), 200)
    except Exception as e:
        return make_response(jsonify({"error": f"Aggregation error: {str(e)}"}), 500)

@devices_bp.route("/devices/search", methods=["GET"])
def search_devices():
    query = request.args.get('q')
    if not query:
        return make_response(jsonify({"error": "Missing 'q' query parameter"}), 400)
    data_to_return = []
    try:
        for device in devices_collection.find(
            { "$text": { "$search": query } }
        ):
            device['_id'] = str(device['_id'])
            if 'reviews' in device:
                for review in device['reviews']:
                    if '_id' in review: 
                        review['_id'] = str(review['_id'])
            data_to_return.append(device)
        return make_response(jsonify(data_to_return), 200)
    except Exception as e:
        return make_response(jsonify({"error": f"Database error: {str(e)}"}), 500)

@devices_bp.route("/devices/nearme", methods=["GET"])
def get_devices_near_me():
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
    except (TypeError, ValueError):
        return make_response(jsonify({"error": "Missing or invalid 'lat'/'lon' query parameters"}), 400)
    pipeline = [
        {
            '$geoNear': {
                'near': {'type': 'Point', 'coordinates': [lon, lat]},
                'distanceField': "distance_meters", 'maxDistance': 1000 * 1000,
                'minDistance': 1, 'spherical': True
            }
        },
        { '$limit': 10 }
    ]
    try:
        nearby_devices = list(devices_collection.aggregate(pipeline))
        for device in nearby_devices:
            device['_id'] = str(device['_id'])
            if 'reviews' in device:
                for review in device['reviews']:
                    if '_id' in review:
                        review['_id'] = str(review['_id'])
        return make_response(jsonify(nearby_devices), 200)
    except Exception as e:
        return make_response(jsonify({"error": f"Geo-query error: {str(e)}"}), 500)

@devices_bp.route("/devices/", methods=["GET"]) 
def get_all_devices():
    try:
        page_num = int(request.args.get('pn', 1)) 
        page_size = int(request.args.get('ps', 10))
    except ValueError:
        return make_response(jsonify({"error": "Invalid page number/size"}), 400)
    page_start = (page_size * (page_num - 1))
    query = {} 
    if 'category' in request.args:
        query['category'] = request.args['category']
    if 'manufacturer' in request.args:
        query['manufacturer.name'] = request.args['manufacturer']
    if 'ram_gb' in request.args:
        try:
            query['ram_gb'] = int(request.args.get('ram_gb'))
        except:
             return make_response(jsonify({"error": "Invalid ram_gb value"}), 400)
    data_to_return = []
    try:
        for device in devices_collection.find(query).skip(page_start).limit(page_size):
            device['_id'] = str(device['_id'])
            if 'reviews' in device:
                for review in device['reviews']:
                    if '_id' in review: 
                        review['_id'] = str(review['_id'])
            data_to_return.append(device)
        return make_response(jsonify(data_to_return), 200)
    except Exception as e:
        return make_response(jsonify({"error": f"Database error: {str(e)}"}), 500)

@devices_bp.route("/devices/add", methods=["POST"])
@jwt_required
@admin_required
def add_device(current_user):
    name = request.form.get("name")
    category = request.form.get("category")
    if not name or name.strip() == "":
        return make_response(jsonify({"error": "Validation failed: 'name' is required"}), 400)
    if not category or category.strip() == "":
        return make_response(jsonify({"error": "Validation failed: 'category' is required"}), 400)
    try:
        ram_gb = int(request.form.get("ram_gb", 0))
        price_usd = int(request.form.get("price_usd", 0))
        if ram_gb < 0 or price_usd < 0:
            return make_response(jsonify({"error": "Validation failed: RAM and Price must be positive"}), 400)
    except ValueError:
        return make_response(jsonify({"error": "Validation failed: RAM and Price must be integers"}), 400)
    try:
        new_device = {
            "name": name, "category": category,
            "processor": request.form.get("processor", ""), "ram_gb": ram_gb,
            "manufacturer": {"name": request.form.get("manufacturer_name", "Unknown"), "country": request.form.get("manufacturer_country", "Unknown")},
            "storage": request.form.get("storage", ""), "avg_inference_latency_ms": int(request.form.get("avg_inference_latency_ms", 0)),
            "power_watts": int(request.form.get("power_watts", 0)), "price_usd": price_usd,
            "release_year": int(request.form.get("release_year", 2025)), "image_url": "placeholder.png",
            "benchmarks": {"resnet50_fps": float(request.form.get("resnet50_fps", 0.0)), "bert_latency_ms": int(request.form.get("bert_latency_ms", 0)), "power_efficiency_fps_per_watt": float(request.form.get("power_efficiency_fps_per_watt", 0.0))},
            "reviews": [] 
        }
        result = devices_collection.insert_one(new_device)
        new_device_link = f"/api/v1.0/devices/{str(result.inserted_id)}"
        return make_response(jsonify({"url": new_device_link}), 201)
    except Exception as e:
        return make_response(jsonify({"error": f"Database error: {str(e)}"}), 500)

@devices_bp.route("/devices/<string:id>", methods=["GET"])
def get_one_device(id):
    if not ObjectId.is_valid(id):
        return make_response(jsonify({"error": "Invalid device ID format"}), 400)
    try:
        device = devices_collection.find_one({'_id': ObjectId(id)})
        if device:
            device['_id'] = str(device['_id'])
            if 'reviews' in device:
                for review in device['reviews']:
                    if '_id' in review:
                        review['_id'] = str(review['_id'])
            return make_response(jsonify(device), 200)
        else:
            return make_response(jsonify({"error": "Device not found"}), 404)
    except Exception as e:
        return make_response(jsonify({"error": f"Database error: {str(e)}"}), 500)

@devices_bp.route("/devices/update/<string:id>", methods=["PUT"])
@jwt_required
@admin_required
def update_device(current_user, id):
    if not ObjectId.is_valid(id):
        return make_response(jsonify({"error": "Invalid device ID format"}), 400)
    try:
        update_data = {}
        if "name" in request.form:
            name = request.form["name"]
            if not name or name.strip() == "":
                return make_response(jsonify({"error": "Validation failed: 'name' cannot be blank"}), 400)
            update_data["name"] = name
        if "category" in request.form:
            category = request.form["category"]
            if not category or category.strip() == "":
                return make_response(jsonify({"error": "Validation failed: 'category' cannot be blank"}), 400)
            update_data["category"] = category
        if "price_usd" in request.form:
            try:
                price_usd = int(request.form["price_usd"])
                if price_usd < 0:
                    return make_response(jsonify({"error": "Validation failed: 'price_usd' must be positive"}), 400)
                update_data["price_usd"] = price_usd
            except ValueError:
                return make_response(jsonify({"error": "Validation failed: 'price_usd' must be integer"}), 400)
        if "processor" in request.form:
             update_data["processor"] = request.form["processor"]
        if not update_data:
            return make_response(jsonify({"error": "No update data provided"}), 400)
        result = devices_collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        if result.matched_count == 1:
            edited_device_link = f"/api/v1.0/devices/{id}"
            return make_response(jsonify({"url": edited_device_link}), 200)
        else:
            return make_response(jsonify({"error": "Device not found"}), 404)
    except Exception as e:
        return make_response(jsonify({"error": f"Database error: {str(e)}"}), 500)

## Route: /api/v1.0/devices/delete/<id>
@devices_bp.route("/devices/delete/<string:id>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_device(current_user, id):
    if not ObjectId.is_valid(id):
        return make_response(jsonify({"error": "Invalid device ID format"}), 400)
    try:
        result = devices_collection.delete_one({'_id': ObjectId(id)})
        if result.deleted_count == 1:
            return make_response(jsonify({}), 204)
        else:
            return make_response(jsonify({"error": "Device not found"}), 404)
    except Exception as e:
        return make_response(jsonify({"error": f"Database error: {str(e)}"}), 500)

@devices_bp.route("/devices/all", methods=["GET"])
def get_all_devices_no_pagination():
    try:
        # Fetch all devices from the collection
        # We exclude the '_id' field or convert it to string to make it JSON serializable
        devices = list(devices_collection.find({}))
        
        for device in devices:
            device['_id'] = str(device['_id'])
            if 'reviews' in device:
                for review in device['reviews']:
                    if '_id' in review:
                        review['_id'] = str(review['_id'])
                        
        return make_response(jsonify(devices), 200)
    except Exception as e:
        return make_response(jsonify({"error": f"Database error: {str(e)}"}), 500)

@devices_bp.route("/devices/stats/top-rated-by-manufacturer", methods=["GET"])
def get_top_rated_by_manufacturer():

    pipeline = [
        {
            "$unwind": "$reviews"
        },
        {
            "$group": {
                "_id": "$manufacturer.name",
                "average_rating": { "$avg": "$reviews.rating" },
                "review_count": { "$sum": 1 }
            }
        },
        {
            "$sort": { "average_rating": -1 }
        }
    ]

    try:
        stats = list(devices_collection.aggregate(pipeline))
        return make_response(jsonify(stats), 200)

    except Exception as e:
        return make_response(jsonify({"error": f"Database error: {str(e)}"}), 500)