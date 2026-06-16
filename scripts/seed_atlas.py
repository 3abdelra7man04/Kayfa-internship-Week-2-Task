import sys
import os
import certifi

# Add the parent directory to sys.path so we can import modules if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from pymongo.mongo_client import MongoClient

# Need to parse TOML manually since st.secrets is not available without running via streamlit
import tomli

def get_mongo_uri():
    secrets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.streamlit', 'secrets.toml')
    try:
        with open(secrets_path, "rb") as f:
            secrets = tomli.load(f)
            return secrets.get("MONGO_URI"), secrets.get("MONGO_DB", "kayfa_elearning")
    except Exception as e:
        print(f"Error loading secrets.toml: {e}")
        return None, None

def seed_atlas():
    uri, db_name = get_mongo_uri()
    if not uri:
        print("MONGO_URI not found. Exiting.")
        return

    print(f"Connecting to MongoDB Atlas (DB: {db_name})...")
    client = MongoClient(uri, tlsCAFile=certifi.where())
    db = client[db_name]
    
    cleaned_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Cleaned_Datasets")
    
    if not os.path.exists(cleaned_dir):
        print(f"Cleaned_Datasets directory not found at {cleaned_dir}")
        return
        
    for filename in os.listdir(cleaned_dir):
        if filename.endswith(".csv"):
            filepath = os.path.join(cleaned_dir, filename)
            collection_name = filename.replace(".csv", "").replace("cleaned_", "")
            
            print(f"\nProcessing {filename} -> collection: '{collection_name}'")
            
            print(f"Dropping existing '{collection_name}' collection if it exists...")
            db[collection_name].drop()
            collection = db[collection_name]

            print(f"Loading {filepath}...")
            data = pd.read_csv(filepath)
            
            # Convert dataframe to list of dicts for mongo
            records = data.to_dict("records")
            if records:
                print(f"Uploading {len(records)} records to Atlas...")
                result = collection.insert_many(records)
                print(f"Successfully inserted {len(result.inserted_ids)} records into '{db_name}.{collection_name}'")
            else:
                print(f"No records to insert for '{collection_name}'")

if __name__ == "__main__":
    seed_atlas()
