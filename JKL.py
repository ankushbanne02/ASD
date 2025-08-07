import json
import os
from pymongo import MongoClient

# --- MongoDB Connection ---
MONGO_URI = "mongodb+srv://ankushbanne23:Ankush1316@asd.qj6if.mongodb.net/ASD?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["ASD"]

# --- JSON Upload Logic ---
def upload_json_file(file_path: str):
    if not os.path.exists(file_path):
        print("❌ File does not exist.")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Use file name (without extension) as collection name
        collection_name = os.path.splitext(os.path.basename(file_path))[0]

        # Insert into MongoDB
        if isinstance(data, list):
            db[collection_name].insert_many(data)
        elif isinstance(data, dict):
            db[collection_name].insert_one(data)
        else:
            print("❌ Unsupported JSON format.")
            return

        print(f"✅ Data uploaded successfully to collection: '{collection_name}'")

    except Exception as e:
        print("❌ Error uploading file:", e)

# --- Run Upload ---
if __name__ == "__main__":
    file_path = input("Enter path to JSON file: ").strip()
    upload_json_file(file_path)
