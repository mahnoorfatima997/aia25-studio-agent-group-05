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
brainstorm = generate_concept_with_conversation([
    {"role": "user", "content": user_message}
])
print("\nConcept generated:\n", brainstorm)
input("Press Enter to continue to attribute extraction...")

# Step 3: Attributes
attributes = extract_attributes_with_conversation([
    {"role": "user", "content": brainstorm}
])
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

# Step 4: connections
connections = extract_connections_with_conversation([
    {"role": "user", "content": user_message}
])
print("\nGenerated connections (raw):\n", connections)
# connections is now a list, not a string
connections_json = {"connections": connections}
print("Parsed connections (JSON):\n", json.dumps(connections_json, indent=2))
input("Press Enter to continue to locations...")

# Step 5: targets
targets = extract_targets_with_conversation([
    {"role": "user", "content": user_message}
], num_zones=len(connections))
print("\nGenerated targets (raw):\n", targets)
targets_json = {"targets": targets}
print("Parsed targets (JSON):\n", json.dumps(targets_json, indent=2))
input("Press Enter to continue to question generation...")

# Step 6: spaces
spaces = extract_spaces_with_conversation([
    {"role": "user", "content": user_message}
])
print("\nSpaces generated:\n", spaces)
input("Press Enter to continue...")

# Step 8: PWR
pwr = extract_plant_water_requirement([
    {"role": "user", "content": user_message}
])
print("\nPWR:\n", pwr)
input("Press Enter to continue...")

# Step 9: tree placement
tree_placement = extract_tree_placement([
    {"role": "user", "content": user_message}
])
print("\tree placement:\n", tree_placement)
input("Press Enter to continue...")


# Step 6: Question and RAG
context_info = f"User input: {user_message}\n" \
              f"Concept: {brainstorm}\n" \
              f"Attributes: {attributes}\n" \
              f"Weights: {connections}\n" \
              f"Locations: {targets}\n"
courtyard_question = create_question(context_info)
print("\nGenerated question for RAG:\n", courtyard_question)
input("Press Enter to get RAG results...")

rag_result = rag_call(courtyard_question, embeddings="knowledge/merged.json", n_results=10)
print("\nRAG result:\n", rag_result)