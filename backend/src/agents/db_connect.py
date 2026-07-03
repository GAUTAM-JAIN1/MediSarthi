import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

def get_database():
    try:
        client = MongoClient(MONGO_URI)
        db = client["medical_db"]
        print("✅ MongoDB Connected Successfully!")
        return db
    except Exception as e:
        print("❌ Connection Error:", e)

if __name__ == "__main__":
    db = get_database()
    print("Current DB Name:", db.name)