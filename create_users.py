import bcrypt
import globals 

try:
    users_collection = globals.db.users
    
    users_collection.delete_many({})

    user_list = [
        {
            "name": "Admin User",
            "username": "admin",
            "password": b"admin_pass",
            "email": "admin@admin.com",
            "admin": True
        },
        {
            "name": "Normal User",
            "username": "user",
            "password": b"user_pass",
            "email": "user@user.com",
            "admin": False
        }
    ]

    for new_user in user_list:
        new_user["password"] = bcrypt.hashpw(
            new_user["password"], bcrypt.gensalt()
        )
        users_collection.insert_one(new_user)

    print(f"Successfully created {len(user_list)} users.")

except Exception as e:
    print(f"Error creating users: {e}")