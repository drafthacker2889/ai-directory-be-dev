import globals
import random
from pymongo import MongoClient

print("Connecting to database...")
try:
    devices_collection = globals.db.devices
    
    if devices_collection.count_documents({}) == 0:
        print("Error: 'devices' collection is empty. Please import your data first.")
        exit()

    print(f"Found {devices_collection.count_documents({})} devices. Adding locations...")

    for device in devices_collection.find():
        

        new_location = {
            "type": "Point",
            "coordinates": [
                random.uniform(-10.5, 1.5),
                random.uniform(50.0, 58.5)   
            ]
        }
        
        devices_collection.update_one(
            { "_id": device['_id'] },
            { "$set": { "location": new_location } }
        )

    print("Successfully added 'location' field to all devices.")
    print("Creating '2dsphere' index on 'location' field...")
    devices_collection.create_index({ "location": "2dsphere" })
    print("Index created successfully. Database is ready for geo-queries.")

except Exception as e:
    print(f"An error occurred: {e}")