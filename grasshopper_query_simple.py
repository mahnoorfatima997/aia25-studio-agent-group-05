# requirements: requests
import requests
import json

# Define the URL for the Flask server endpoint
url = 'http://127.0.0.1:5000/query_results'

# Initialize the output variable
query_data = None

# Check if the script should run
if run:
    try:
        # Send a GET request to fetch the data
        response = requests.get(url)
        
        # Check the response status code
        if response.status_code == 200:
            # Get the complete query data structure
            query_data = response.json()
            print("✅ Successfully received query data")
        else:
            print(f"❌ Failed to connect: {response.status_code}")
            query_data = None
    except Exception as e:
        print(f"❌ Error: {e}")
        query_data = None

# Extract window names from the query results
if query_data and isinstance(query_data, dict):
    try:
        # FIXED: Access the correct path - query_data['query_results']['raw_data']
        raw_data = query_data['query_results']['raw_data']
        
        # Extract window names, remove duplicates
        window_names = list({entry['w.query'] for entry in raw_data})
        print(f"✅ Found {len(window_names)} unique window names: {window_names}")
    except KeyError as e:
        window_names = [f"KeyError: {e} - Check data structure"]
        print(f"❌ KeyError: {e}")
        print(f"Available keys: {list(query_data.keys()) if query_data else 'None'}")
    except Exception as e:
        window_names = [f"Error: {e}"]
        print(f"❌ Error parsing query data: {e}")
else:
    window_names = ["No valid query data"]
    print("⚠️ No valid query data received")

# Output list of unique window IDs
a = window_names 