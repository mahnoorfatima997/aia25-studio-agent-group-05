import json
import re
from rapidfuzz import process
import pycountry

def extract_location_from_message(message, client, model):
    system_prompt = """
You are a location extractor. Extract the city and country mentioned in the user's message and return them as JSON:
{ "city": "...", "country": "..." }

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
    try:
        return pycountry.countries.lookup(name).alpha_3
    except LookupError:
        return name.upper().strip()


def guess_country_from_city(city, index_path="knowledge/epw_index.json"):
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)
    matches = [entry for entry in index if entry["city"].lower() == city.lower()]
    return matches[0]["country"] if matches else None


def normalize_city_for_match(name):
    name = name.lower()
    name = name.replace(".", " ").replace("-", " ")
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def get_zip_url(city, country, index_path="knowledge/epw_index.json", score_threshold=90):
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
    location = extract_location_from_message(message, client, model)
    city, country = location.get("city"), location.get("country")
    print(f"LLM extracted: city={city}, country={country}")

    if not city:
        return {
            "success": False,
            "error": "I couldn't identify a city in your message.",
            "city": None,
            "country": None
        }

    if not country:
        country = guess_country_from_city(city, index_path)
        if country:
            print(f"Guessed country: {country}")
        else:
            return {
                "success": False,
                "error": f"I couldn't determine the country for city '{city}'.",
                "city": city,
                "country": None
            }

    zip_url = get_zip_url(city, country, index_path=index_path)
    if zip_url:
        return {
            "success": True,
            "zip_url": zip_url,
            "city": city,
            "country": country
        }
    else:
        return {
            "success": False,
            "error": f"Sorry, I couldn't find weather data for {city}, {country}.",
            "city": city,
            "country": country
        }


def extract_hoys_from_message(message, client, model):
    system_prompt = """
You are a date parser for building simulation.

The user will describe a time or range (e.g. "hottest hour", "mid-July").
You MUST return only a raw JSON list of HOY integers — no explanation or markdown.

Correct format:
[4675, 4676, 4677]

Do NOT include extra text or code blocks.
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
        raise ValueError("Invalid HOY list")
    except Exception as e:
        print("❌ Failed to parse HOYs:", content)
        return []
