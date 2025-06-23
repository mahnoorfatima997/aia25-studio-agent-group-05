import json
import re
import requests
import io
import os
import pandas as pd
from rapidfuzz import process
import pycountry

### --- Location & EPW ZIP Retrieval --- ###

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
    name = name.lower().replace(".", " ").replace("-", " ")
    return re.sub(r"\s+", " ", name).strip()


def get_zip_url(city, country, index_path="knowledge/epw_index.json", score_threshold=90):
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    norm_country = normalize_country_name(country)
    candidates = [
        (entry["city"], entry["country"], entry["url"])
        for entry in index
        if normalize_country_name(entry["country"]) == norm_country
    ]
    if not candidates:
        return None

    normalized_candidates = [(normalize_city_for_match(c[0]), c) for c in candidates]
    input_city_norm = normalize_city_for_match(city)

    best_match = process.extractOne(
        input_city_norm, [c[0] for c in normalized_candidates],
        score_cutoff=score_threshold
    )
    if best_match:
        for norm_name, original in normalized_candidates:
            if norm_name == best_match[0]:
                return original[2]
    return None


def handle_zip_request(message, client, model, index_path="knowledge/epw_index.json"):
    location = extract_location_from_message(message, client, model)
    city, country = location.get("city"), location.get("country")

    if not city:
        return {"success": False, "error": "City not found", "city": None, "country": None}

    if not country:
        country = guess_country_from_city(city, index_path)
        if not country:
            return {"success": False, "error": f"Could not find country for {city}", "city": city, "country": None}

    zip_url = get_zip_url(city, country, index_path=index_path)
    if zip_url:
        return {"success": True, "zip_url": zip_url, "city": city, "country": country}
    else:
        return {"success": False, "error": "ZIP not found", "city": city, "country": country}


### --- Intent Detection --- ###

def classify_hoy_query(message, client, model):
    system_prompt = """
You are an environmental query interpreter.

Your job is to understand what type of EPW data analysis is being requested.
Given a message like "the hottest hour of the year", return a JSON object:

{
  "intent": "hottest",         // or "coldest", or "custom"
  "duration": "hour",          // or "day", "week", "month", "year"
  "range": null                // e.g. "July 4" or "first week of August"
}

If the user asks for a custom date or range (e.g. "July 4"), return:

{
  "intent": "custom",
  "duration": null,
  "range": "July 4"
}

Only return the JSON object. No explanation, markdown, or extra text.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
    )

    content = response.choices[0].message.content.strip()
    print("🔎 LLM intent classification returned:", content)

    try:
        parsed = json.loads(content)
        return parsed
    except Exception as e:
        print("❌ Failed to parse LLM response as JSON")
        raise ValueError(f"LLM returned invalid JSON:\n{content}")


### --- HOY Utilities --- ###

def extract_hoys_from_message(message, client, model):
    system_prompt = """
You are a date parser for building simulation.

The user will describe a time or range (e.g. "July 4", "first week of August").
You MUST return only a raw JSON list of HOY integers — no explanation or markdown.

Example:
[4675, 4676, 4677]
"""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": message}]
    )
    try:
        hoys = json.loads(response.choices[0].message.content.strip())
        if isinstance(hoys, list) and all(isinstance(h, int) and 0 <= h <= 8759 for h in hoys):
            return hoys
    except Exception as e:
        print("❌ Failed to parse HOYs:", e)
    return []


from zipfile import ZipFile

def load_epw_dataframe(zip_url):
    """Download a .zip containing an EPW file and return a DataFrame of the EPW data."""
    try:
        res = requests.get(zip_url)
        res.raise_for_status()

        with ZipFile(io.BytesIO(res.content)) as zf:
            epw_filename = [name for name in zf.namelist() if name.lower().endswith('.epw')][0]
            with zf.open(epw_filename) as epw_file:
                lines = epw_file.read().decode("utf-8", errors="ignore").splitlines()[8:]
                df = pd.read_csv(io.StringIO("\n".join(lines)), header=None)
                return df

    except Exception as e:
        print(f"❌ Failed to read EPW from ZIP: {e}")
        raise



### --- Extract HOYs from Intent --- ###

def get_hoys_from_intent(message, zip_url, client, model):
    intent = classify_hoy_query(message, client, model)
    intent_type = intent.get("intent")
    duration = intent.get("duration")
    custom_range = intent.get("range")

    if intent_type in ["hottest", "coldest"]:
        if not zip_url:
            return []

        df = load_epw_dataframe(zip_url)

        if intent_type == "hottest" and duration == "hour":
            return [int(df[6].idxmax())]
        if intent_type == "coldest" and duration == "hour":
            return [int(df[6].idxmin())]

        if duration == "week":
            df['rolling'] = df[6].rolling(168).mean()
            end = df['rolling'].idxmax() if intent_type == "hottest" else df['rolling'].idxmin()
            return list(range(end - 167, end + 1))

        if duration == "year":
            return list(range(8760))

    elif intent_type == "custom" and custom_range:
        return extract_hoys_from_message(custom_range, client, model)

    return []
