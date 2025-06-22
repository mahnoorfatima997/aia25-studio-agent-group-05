import json
import re
from rapidfuzz import process
import pycountry

def extract_location_from_message(message, client, model):
    """LLM call to extract city and country from user message."""
    system_prompt = """
You are a location extractor. Extract the city and country mentioned in the user's message and return them as JSON:
{ "city": "...", "country": "..." }

Examples:
- "Weather data for Milan" → { "city": "Milan", "country": "Italy" }
- "Climate for Austin" → { "city": "Austin", "country": "USA" }

If the city is known but the country is not explicitly mentioned, use the most common country.

If nothing is clear, return:
{ "city": null, "country": null }
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
    )

    content = response.choices[0].message.content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print(f"❌ LLM returned invalid JSON: {content}")
        return {"city": None, "country": None}

def normalize_country_name(name):
    """Convert full country name to ISO alpha-3 (e.g., Italy → ITA)."""
    try:
        return pycountry.countries.lookup(name).alpha_3
    except LookupError:
        return name.upper().strip()

def guess_country_from_city(city, index_path="knowledge/epw_index.json"):
    """Guess country from city name using the index, if LLM failed."""
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    matches = [entry for entry in index if entry["city"].lower() == city.lower()]
    if matches:
        return matches[0]["country"]
    return None

def normalize_city_for_match(name):
    """Normalize city name to improve fuzzy matching."""
    name = name.lower()
    name = name.replace(".", " ").replace("-", " ")
    name = re.sub(r"\s+", " ", name)
    return name.strip()

def get_zip_url(city, country, index_path="knowledge/epw_index.json", score_threshold=90):
    """Find the closest ZIP weather file URL by fuzzy matching city name."""
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    norm_country = normalize_country_name(country)
    print(f"🔍 Searching: {city}, {norm_country}")

    candidates = [
        (entry["city"], entry["country"], entry["url"])
        for entry in index
        if normalize_country_name(entry["country"]) == norm_country
    ]

    print(f"{len(candidates)} candidates in {norm_country}")

    if not candidates:
        return None

    # Normalize candidates for fuzzy match
    normalized_candidates = [(normalize_city_for_match(c[0]), c) for c in candidates]
    input_city_norm = normalize_city_for_match(city)

    best_match = process.extractOne(
        input_city_norm,
        [c[0] for c in normalized_candidates],
        score_cutoff=score_threshold
    )

    if best_match:
        matched_norm = best_match[0]
        for norm_name, original in normalized_candidates:
            if norm_name == matched_norm:
                print(f"✅ Match: {original[0]} ({best_match[1]}%)")
                return original[2]

    return None

def handle_zip_request(message, client, model, index_path="knowledge/epw_index.json"):
    """Processes a user message and returns the ZIP weather file URL."""
    location = extract_location_from_message(message, client, model)
    city, country = location.get("city"), location.get("country")
    print(f"LLM extracted: city={city}, country={country}")

    if not city:
        return "❌ I couldn't identify a city in your message."

    if not country:
        country = guess_country_from_city(city, index_path)
        if country:
            print(f"Guessed country: {country}")
        else:
            return f"❌ I couldn't determine the country for city '{city}'."

    zip_url = get_zip_url(city, country, index_path=index_path)

    if zip_url:
        return f"Here's the weather data ZIP for {city}, {country}:\n{zip_url}"
    else:
        return f"Sorry, I couldn't find weather data for {city}, {country}."
    

    
def extract_hoys_from_message(message, client, model):
    """Uses LLM to convert natural language time into a list of HOY (hour-of-year) integers."""
    
    system_prompt = """
You are a date parser for building simulation.

The user will describe a time or date range (e.g. "first week of January", "March 10–15", "mid August").
You must return a JSON list of corresponding **hour of year (HOY)** values.

HOY is the hour index of the year, assuming a non-leap year (0 to 8759).

Each day has 24 HOYs:
- January 1st = [0–23]
- January 2nd = [24–47]
- ...
- December 31st = [8736–8759]

Return only JSON like this:
[0, 1, 2, ..., 167]
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
    )

    content = response.choices[0].message.content.strip()
    
    try:
        hoys = json.loads(content)
        if isinstance(hoys, list) and all(isinstance(h, int) and 0 <= h <= 8759 for h in hoys):
            return hoys
        else:
            raise ValueError("Invalid HOY list format")
    except Exception as e:
        print("❌ Failed to parse LLM HOY output:", content)
        return []

def get_zip_and_hoys(location_message, hoy_message, client, model, index_path="knowledge/epw_index.json"):
    """Returns both the EPW ZIP URL and a list of HOY values based on two user messages."""
    
    # Step 1: Get weather file URL
    zip_response = handle_zip_request(location_message, client, model, index_path)
    if "http" not in zip_response:
        return {"error": "Could not determine ZIP URL."}
    
    zip_url = zip_response.strip().split("\n")[-1].strip()

    # Step 2: Get HOYs
    hoys = extract_hoys_from_message(hoy_message, client, model)
    if not hoys:
        return {"error": "Could not determine valid HOYs from message."}

    return {
        "zip_url": zip_url,
        "hoys": hoys
    }
