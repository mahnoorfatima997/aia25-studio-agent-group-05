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

# Extract data from query results (flexible approach)
if query_data and isinstance(query_data, dict):
    try:
        raw_data = query_data['query_results']['raw_data']
        
        if raw_data and len(raw_data) > 0:
            # Get all unique values from the first entry (assuming it's representative)
            first_entry = raw_data[0]
            print(f"📋 Available keys in data: {list(first_entry.keys())}")
            
            # Extract all unique values from all entries
            all_values = []
            for entry in raw_data:
                for key, value in entry.items():
                    if value is not None and str(value).strip():  # Skip empty values
                        all_values.append(str(value))
            
            # Remove duplicates and sort
            window_names = sorted(list(set(all_values)))
            print(f"✅ Extracted {len(window_names)} unique values: {window_names}")
        else:
            window_names = ["No data available"]
            print("⚠️ Raw data is empty")
    except KeyError as e:
        window_names = [f"KeyError: {e}"]
        print(f"❌ KeyError: {e}")
    except Exception as e:
        window_names = [f"Error: {e}"]
        print(f"❌ Error extracting data: {e}")
else:
    window_names = ["No valid query data"]
    print("⚠️ No valid query data received")

# Output list of unique values
a = window_names 