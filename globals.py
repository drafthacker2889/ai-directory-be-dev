from pymongo import MongoClient
import os

SECRET_KEY = 'com661-is-my-favourite-module'

try:
    client = MongoClient("mongodb://127.0.0.1:27017")
    db = client.aidirDB 
    
    print("MongoDB connected successfully.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    db = None