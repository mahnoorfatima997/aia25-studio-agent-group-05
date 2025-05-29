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
# Try to extract JSON from connections
match = re.search(r'\{.*\}', connections, re.DOTALL)
if match:
    try:
        connections_json = json.loads(match.group(0))
        print("Parsed connections (JSON):\n", json.dumps(connections_json, indent=2))
    except Exception as e:
        print("Could not parse weights as JSON:", e)
        connections_json = None
else:
    print("No JSON found in connections output.")
    connections_json = None
input("Press Enter to continue to locations...")

# Step 5: targets
targets = extract_targets_with_conversation([
    {"role": "user", "content": user_message}
])
print("\nGenerated targets (raw):\n", targets)
match = re.search(r'\{.*\}', targets, re.DOTALL)
if match:
    try:
        targets_json = json.loads(match.group(0))
        print("Parsed targets (JSON):\n", json.dumps(targets_json, indent=2))
    except Exception as e:
        print("Could not parse targets as JSON:", e)
        targets_json = None
else:
    print("No JSON found in targets output.")
    targets_json = None
input("Press Enter to continue to question generation...")

# Step 6: spaces
spaces = extract_spaces_with_conversation([
    {"role": "user", "content": user_message}
])
print("\nSpaces generated:\n", spaces)
input("Press Enter to continue...")

# Step 7: treetypes
tree_types = extract_tree_types([
    {"role": "user", "content": user_message}
])
print("\ntree_types:\n", tree_types)
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