from epw_analysis import handle_zip_request, get_hoys_from_intent
from server.config import client, completion_model


def get_location_and_epw(location_message):
    result = handle_zip_request(location_message, client, completion_model)

    if not result["success"]:
        return {
            "success": False,
            "error": result.get("error", "Unknown error")
        }

    return {
        "success": True,
        "location": {
            "city": result["city"],
            "country": result["country"]
        },
        "zip_response": {
            "zip_url": result["zip_url"]
        }
    }


def analyze_hoys(time_message, zip_url=None):
    hoys = get_hoys_from_intent(time_message, zip_url, client, completion_model)

    if not hoys:
        return {
            "success": False,
            "error": "Failed to extract HOYs from message."
        }

    return {
        "success": True,
        "hoys": hoys,
        "total_hours": len(hoys)
    }