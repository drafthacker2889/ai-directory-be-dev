import globals

print("Connecting to database...")
try:
    devices_collection = globals.db.devices

    if devices_collection.count_documents({}) == 0:
        print("Error: 'devices' collection is empty. Please import your data first.")
        exit()

    print("Creating text index on 'name', 'category', and 'processor' fields...")

    devices_collection.create_index([
        ("name", "text"),
        ("category", "text"),
        ("processor", "text")
    ])

    print("Text index created successfully. Database is ready for text search.")

except Exception as e:
    print(f"An error occurred: {e}")