from server.config import client, completion_model
from epw_handler import handle_zip_request, extract_hoys_from_message

def get_location_and_epw(location_message):
    response = handle_zip_request(location_message, client=client, model=completion_model)

    if not response.get("success"):
        return {"success": False, "error": response.get("error", "Unknown error")}

    return {
        "success": True,
        "location": {
            "city": response["city"],
            "country": response["country"]
        },
        "zip_response": {
            "zip_url": response["zip_url"]
        }
    }

def analyze_hoys(time_message, zip_url=None):
    if time_message.lower() == "skip":
        return {"success": True, "hoys": [], "total_hours": 0}

    hoys = extract_hoys_from_message(time_message, client=client, model=completion_model)

    return {
        "success": True,
        "hoys": hoys,
        "total_hours": len(hoys)
    }
