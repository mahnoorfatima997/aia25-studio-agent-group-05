from flask import Flask, request, jsonify
from server.config import *
from llm_calls import *
from utils.rag_utils import rag_call
import json
import re

app = Flask(__name__)



# def design_step(design_state, user_input):
#     print("Current design state:", design_state)
#     print("User input:", user_input)
#     message = ""
#     # Allow user to restart or start a new concept at any time
#     if user_input.lower() == "restart":
#         design_state = {
#             "user_input": None,
#             "concept": None,
#             "attributes": None,
#             "parameters": None,
#             "weights": None,
#             "locations": None,
#             "rag_result": None,
#             "imageprompt": None,
#             "stage": "start"
#         }
#         message = "Session restarted. Please enter a new design prompt."
#         return design_state, message
#     # If user enters a new design prompt at any stage, treat as new concept
#     if design_state["stage"] != "start" and user_input.strip() and user_input.lower() not in ["next", "restart"] and not user_input.lower().startswith("change "):
#         print("Detected new design prompt. Restarting from concept.")
#         design_state = {
#             "user_input": user_input,
#             "concept": None,
#             "attributes": None,
#             "parameters": None,
#             "weights": None,
#             "locations": None,
#             "rag_result": None,
#             "imageprompt": None,
#             "stage": "start"
#         }
#     if design_state["stage"] == "start":
#         router_output = classify_input(user_input)
#         if router_output == "Refuse to answer":
#             message = "Sorry, I can only answer questions about architecture."
#             return design_state, message
#         concept = generate_concept(user_input)
#         design_state["concept"] = concept
#         message = f"Concept: {concept}"
#         design_state["stage"] = "attributes"

#     elif design_state["stage"] == "attributes":
#         # Allow user to modify concept at this stage
#         if user_input.strip() and user_input.lower() not in ["next", "restart"] and not user_input.lower().startswith("change "):
#             concept = generate_concept(user_input)
#             design_state["concept"] = concept
#             message = f"Concept updated: {concept}"
#         attributes = extract_attributes(design_state["concept"])
#         try:
#             attributes = json.loads(attributes)
#         except json.JSONDecodeError as e:
#             message = f"Failed to parse attributes: {e}"
#             return design_state, message
#         print("Attributes:", attributes)
#         parameters = None
#         if isinstance(attributes, dict) and "parameters" in attributes:
#             parameters = attributes["parameters"]
#             design_state["parameters"] = parameters
#         else:
#             design_state["parameters"] = None
#         design_state["attributes"] = attributes
#         # Eagerly generate weights and locations here
#         weights_raw = generate_weights(design_state["concept"])
#         match_w = re.search(r'\{.*\}', weights_raw, re.DOTALL)
#         if match_w:
#             try:
#                 weights = json.loads(match_w.group(0))
#             except Exception as e:
#                 print(f"Could not parse weights JSON: {e}")
#                 weights = None
#         else:
#             print("No valid JSON found in weights.")
#             weights = None
#         design_state["weights"] = weights
#         locations_raw = generate_locations(design_state["concept"])
#         match_l = re.search(r'\{.*\}', locations_raw, re.DOTALL)
#         if match_l:
#             try:
#                 locations = json.loads(match_l.group(0))
#             except Exception as e:
#                 print(f"Could not parse locations JSON: {e}")
#                 locations = None
#         else:
#             print("No valid JSON found in locations.")
#             locations = None
#         design_state["locations"] = locations
#         message = message + "\nAttributes, weights, and locations extracted. You can now modify shape, theme, materials, or parameters. Type 'next' to continue or modify something like 'change material to timber'"
#         design_state["stage"] = "modify"

#     elif design_state["stage"] == "modify":
#         if user_input.lower() == "next":
#             design_state["stage"] = "weights"
#             return design_state, "Proceeding to weights."
#         match = re.search(r'change (\w+) to (.+)', user_input.lower())
#         if match:
#             key, value = match.groups()
#             if key in design_state["attributes"]:
#                 design_state["attributes"][key] = value
#                 message = f"Updated {key} to {value}"
#             else:
#                 message = f"Unknown attribute '{key}'"
#         else:
#             message = "No recognized modification. Type 'next' to continue or use 'change X to Y'."
#         return design_state, message

#     elif design_state["stage"] == "weights":
#         # Allow user to regenerate weights with a new prompt
#         if user_input.strip() and user_input.lower() not in ["next", "restart"] and not user_input.lower().startswith("change "):
#             print("Regenerating concept and weights from new prompt.")
#             concept = generate_concept(user_input)
#             design_state["concept"] = concept
#         weights_raw = generate_weights(design_state["concept"])
#         match = re.search(r'\{.*\}', weights_raw, re.DOTALL)
#         if match:
#             try:
#                 weights = json.loads(match.group(0))
#             except Exception as e:
#                 message = f"Could not parse weights JSON: {e}"
#                 weights = None
#         else:
#             message = "No valid JSON found in weights."
#             weights = None
#         design_state["weights"] = weights
#         message = f"Weights: {weights}"
#         print("Weights:", weights) 
#         design_state["stage"] = "locations"

#     elif design_state["stage"] == "locations":
#         # Allow user to regenerate locations with a new prompt
#         if user_input.strip() and user_input.lower() not in ["next", "restart"] and not user_input.lower().startswith("change "):
#             print("Regenerating concept and locations from new prompt.")
#             concept = generate_concept(user_input)
#             design_state["concept"] = concept
#         locations_raw = generate_locations(design_state["concept"])
#         match = re.search(r'\{.*\}', locations_raw, re.DOTALL)
#         if match:
#             try:
#                 locations = json.loads(match.group(0))
#             except Exception as e:
#                 message = f"Could not parse locations JSON: {e}"
#                 locations = None
#         else:
#             message = "No valid JSON found in locations."
#             locations = None
#         design_state["locations"] = locations
#         message = f"Locations: {locations}"
#         print("Locations:", locations)  
#         design_state["stage"] = "rag"

#     elif design_state["stage"] == "rag":
#         theme = design_state["attributes"].get("theme", "") if design_state["attributes"] else ""
#         question = create_question(theme)
#         rag_result = rag_call(question, embeddings="knowledge/merged.json", n_results=10)
#         message = f"RAG output:\n{rag_result}"
#         design_state["rag_result"] = rag_result
#         design_state["stage"] = "complete"

#     elif design_state["stage"] == "complete":
#         message = "Design session complete. Type 'restart' to begin a new one or enter a new prompt to start over."
#     return design_state, message

# @app.route('/llm_call/', methods=['POST'])
# def llm_call():
#     data = request.get_json()
#     user_input = data.get('input', '')
#     design_state = data.get('state', {
#         "user_input": None,
#         "concept": None,
#         "attributes": None,
#         "weights": None,
#         "locations": None,
#         "rag_result": None,
#         "stage": "start"
#     })
#     print("Received design state:", design_state)
#     print("Received user input:", user_input)
#     new_state, message = design_step(design_state, user_input)
#     return jsonify({
#         "state": new_state,
#         "message": message,
#         "concept": new_state.get("concept"),
#         "attributes": new_state.get("attributes"),
#         "parameters": new_state.get("parameters"),
#         "weights": new_state.get("weights"),
#         "locations": new_state.get("locations"),
#         "rag_result": new_state.get("rag_result"),
#         "imageprompt": new_state.get("imageprompt")
#     })

@app.route('/llm_call/generate_concept', methods=['POST'])
def llm_call_generate_concept():
    data = request.get_json()
    user_input = data.get('input', '')
    print("Received user input:", user_input)

    
    generated_concept = generate_concept(user_input)
    return jsonify({
        "concept": generated_concept
    })

@app.route('/llm_call/extract_attributes', methods=['POST'])
def llm_call_extract_attributes():
    data = request.get_json()
    concept = data.get('concept', '')
    print("Received concept:", concept)
    attributes = extract_attributes(concept)
    try:
        attributes_json = json.loads(attributes)
    except json.JSONDecodeError as e:
        print(f"Failed to parse attributes JSON: {e}")
        attributes_json = {}
    return jsonify({
        "attributes": attributes_json
    })

@app.route('/llm_call/generate_locations', methods=['POST'])
def llm_call_generate_locations():
    data = request.get_json()
    concept = data.get('concept', '')
    user_input = data.get('user_input', '')

    
    current_locations = data.get('current_locations', '')
    current_weights = data.get('current_weights', '')


    locations = generate_locations(concept, user_input=user_input, current_locations=current_locations)
    print("Received locations:", locations)
    weights = generate_weights(concept, user_input=user_input, current_weights=current_weights)
    print("Received weights:", weights)

    locations_match = re.search(r'\{.*\}', locations, re.DOTALL)
    if locations_match:
        try:
            locations_json = json.loads(locations_match.group(0))
        except Exception as e:
            print(f"Could not parse locations JSON: {e}")
            locations_json = {}
    else:
        print("No valid JSON found in locations.")
        locations_json = {}

    weights_match = re.search(r'\{.*\}', weights, re.DOTALL)
    if weights_match:
        try:
            weights_json = json.loads(weights_match.group(0))
        except Exception as e:
            print(f"Could not parse weights JSON: {e}")
            weights_json = {}
    else:
        print("No valid JSON found in weights.")
        weights_json = {}
    return jsonify({
        "locations": locations_json,
        "weights": weights_json
    })

# @app.route('/llm_call', methods=['POST'])
# def llm_call():
#     data = request.get_json()
#     input_string = data.get('input', '')

#     classification = classify_input(input_string)
#     print('Classification:', classification)

#     concept = generate_concept(classification)
#     print('Concept: ', concept)
#     imageprompt = generate_prompt(concept)
#     print('Image Prompt:', imageprompt)
#     # Extract the attributes from the generated concept
#     attributes = extract_attributes(concept)
#     print('Attributes:', attributes)

#     weights = generate_weights(concept)
#     print('Weights:', weights)
#     locations = generate_locations(concept)
#     print('Locations:', locations)

#     # Extract and parse JSON for attributes, weights, and locations in a loop
#     parsed_results = {}
#     for key, value in [('attributes', attributes), ('weights', weights), ('locations', locations)]:
#         match = re.search(r'\{.*\}', value, re.DOTALL)
#         if match:
#             json_string = match.group(0)
#             try:
#                 parsed_json = json.loads(json_string)
#                 parsed_results[key] = parsed_json
#             except json.JSONDecodeError as e:
#                 print(f"JSON decoding error in {key}:", e)
#                 parsed_results[key] = None
#         else:
#             print(f"No valid JSON found in the string for {key}.")
#             parsed_results[key] = None

#     # Update the return statement to include the parsed JSON objects
#     return jsonify({
#         'classification': classification,
#         'attributes': parsed_results['attributes'],
#         'imageprompt': imageprompt,
#         'weights': parsed_results['weights'],
#         'locations': parsed_results['locations']
#     })

if __name__ == '__main__':
    app.run(debug=True)