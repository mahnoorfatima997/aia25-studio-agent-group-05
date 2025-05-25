from server.config import *
from llm_calls import *
from utils.rag_utils import rag_call
import json
import requests
import re

user_message = input("Describe your courtyard design: ")

# Step 1: Router
router_output = classify_input(user_message)
if router_output == "Refuse to answer":
    print("Sorry, I can only answer questions about architecture.")
    exit()

# Step 2: Concept
brainstorm = generate_concept(user_message)
print("\nConcept generated:\n", brainstorm)
input("Press Enter to continue to attribute extraction...")

# Step 3: Attributes
attributes = extract_attributes(brainstorm)
print("\nExtracted attributes (raw):\n", attributes)
# Try to parse JSON
try:
    attributes_json = json.loads(attributes)
    print("Parsed attributes (JSON):\n", json.dumps(attributes_json, indent=2))
except Exception as e:
    print("Could not parse attributes as JSON:", e)
    attributes_json = None
user_mod = input("Modify attributes (paste JSON) or press Enter to continue: ")
if user_mod.strip():
    try:
        attributes_json = json.loads(user_mod)
        print("Using user-modified attributes (JSON):\n", json.dumps(attributes_json, indent=2))
    except Exception as e:
        print("Could not parse user-modified attributes as JSON:", e)

# Step 4: Weights
weights = generate_weights(user_message)
print("\nGenerated weights (raw):\n", weights)
# Try to extract JSON from weights
match = re.search(r'\{.*\}', weights, re.DOTALL)
if match:
    try:
        weights_json = json.loads(match.group(0))
        print("Parsed weights (JSON):\n", json.dumps(weights_json, indent=2))
    except Exception as e:
        print("Could not parse weights as JSON:", e)
        weights_json = None
else:
    print("No JSON found in weights output.")
    weights_json = None
input("Press Enter to continue to locations...")

# Step 5: Locations
locations = generate_locations(user_message)
print("\nGenerated locations (raw):\n", locations)
match = re.search(r'\{.*\}', locations, re.DOTALL)
if match:
    try:
        locations_json = json.loads(match.group(0))
        print("Parsed locations (JSON):\n", json.dumps(locations_json, indent=2))
    except Exception as e:
        print("Could not parse locations as JSON:", e)
        locations_json = None
else:
    print("No JSON found in locations output.")
    locations_json = None
input("Press Enter to continue to question generation...")

# Step 6: Question and RAG
context_info = f"User input: {user_message}\n" \
              f"Concept: {brainstorm}\n" \
              f"Attributes: {attributes}\n" \
              f"Weights: {weights}\n" \
              f"Locations: {locations}\n"
courtyard_question = create_question(context_info)
print("\nGenerated question for RAG:\n", courtyard_question)
input("Press Enter to get RAG results...")

rag_result = rag_call(courtyard_question, embeddings="knowledge/merged.json", n_results=10)
print("\nRAG result:\n", rag_result)