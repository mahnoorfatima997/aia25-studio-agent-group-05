from server.config import client, completion_model
from epw_handler import handle_zip_request, extract_location_from_message, extract_hoys_from_message

def utci_epw():
    while True:
        message = input("Enter a location message (or type 'exit'): ")
        if message.lower() == "exit":
            break

        # Step 1: Extract location
        location = extract_location_from_message(message, client, completion_model)
        city = location.get("city")
        country = location.get("country")

        if not city or not country:
            print("❌ Could not extract a valid location. Please try again.\n")
            continue

        print(f"📍 Location found: {city}, {country}")

        # Step 2: Find the ZIP URL
        response = handle_zip_request(message, client=client, model=completion_model)
        print("Response:", response)

        # Step 3: Ask for HOY only if location was successful
        time_message = input("Enter time period for analysis (or 'skip'): ")
        if time_message.lower() == "skip":
            continue

        hoys = extract_hoys_from_message(time_message, client, completion_model)
        print("HOYs:", hoys)
        print(f"Total hours: {len(hoys)}\n")

if __name__ == "__main__":
    utci_epw()
