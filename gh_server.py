from flask import Flask, request, jsonify
from server.config import *
from llm_calls import *
from utils.rag_utils import rag_call
import json
import re

app = Flask(__name__)

@app.route('/llm_call/generate_concept', methods=['POST'])
def llm_call_generate_concept():
    data = request.get_json()
    concept_conversation = data.get('conversation')
    print("Received user input:", concept_conversation)
    
    generated_concept = generate_concept_with_conversation(concept_conversation)
    return jsonify({
        "concept": generated_concept
    })

@app.route('/llm_call/extract_attributes', methods=['POST'])
def llm_call_extract_attributes():
    data = request.get_json()
    attributes_conversation = data.get('conversation')
    attributes = extract_attributes_with_conversation(attributes_conversation)
    print("Received attributes:", attributes)
    # Robustly extract the first valid JSON object from the LLM output
    import re
    match = re.search(r'\{.*\}', attributes, re.DOTALL)
    if match:
        try:
            attributes_json = json.loads(match.group(0))
        except Exception as e:
            print(f"Failed to parse attributes JSON: {e}")
            attributes_json = {}
    else:
        print("No JSON found in attributes output.")
        attributes_json = {}
    return jsonify({
        "attributes": attributes_json
    })

@app.route('/llm_call/generate_connections_targets', methods=['POST'])
def llm_call_generate_connections_targets():
    data = request.get_json()
    conversation = data.get('conversation')
    # Ensure conversation is a list of message dicts for LLM API
    if not isinstance(conversation, list):
        return jsonify({
            "error": "Conversation must be a list of message dicts."
        }), 400
    # Get connections
    raw_connections = extract_connections_with_conversation(conversation)
    # Robustly extract the first valid JSON object from the LLM output if needed
    if isinstance(raw_connections, str):
        match = re.search(r'\{.*\}', raw_connections, re.DOTALL)
        print("match", match)
        if match:
            try:
                connections = json.loads(match.group(0)).get("connections", [])
            except Exception as e:
                print(f"Failed to parse connections JSON: {e}")
                connections = []
        else:
            print("No JSON found in connections output.")
            connections = []
    else:
        connections = raw_connections
    print("Received connections:", connections)
    num_zones = len(connections)
    # Get targets (ensure same number as connections)
    raw_targets = extract_targets_with_conversation(conversation, num_zones=num_zones)
    if isinstance(raw_targets, str):
        match = re.search(r'\{.*\}', raw_targets, re.DOTALL)
        if match:
            try:
                targets = json.loads(match.group(0)).get("targets", [])
            except Exception as e:
                print(f"Failed to parse targets JSON: {e}")
                targets = []
        else:
            print("No JSON found in targets output.")
            targets = []
    else:
        targets = raw_targets
    print("Received targets:", targets)
    return jsonify({
        "connections": connections,
        "targets": targets
    })
    
@app.route('/llm_call/generate_spaces', methods=['POST'])
def llm_call_generate_spaces():
    data = request.get_json()
    space_conversation = data.get('conversation')
    print("Received user input:", space_conversation)

    generated_space = extract_spaces_with_conversation(space_conversation)
    # Robustly extract the first valid JSON object from the LLM output
    if isinstance(generated_space, str):
        match = re.search(r'\{.*\}', generated_space, re.DOTALL)
        if match:
            try:
                spaces = json.loads(match.group(0)).get("spaces", [])
            except Exception as e:
                print(f"Failed to parse spaces JSON: {e}")
                spaces = []
        else:
            print("No JSON found in spaces output.")
            spaces = []
    else:
        spaces = generated_space
    print("Received spaces:", spaces)
    return jsonify({
        "spaces": spaces
    })

@app.route('/llm_call/generate_tree_types', methods=['POST'])
def llm_call_generate_tree_types():
    data = request.get_json()
    trees_conversation = data.get('conversation')
    print("Received user input:", trees_conversation)

    
    generated_PWR = extract_plant_water_requirement(trees_conversation)
    generated_trees = extract_tree_placement(trees_conversation)

    return jsonify({
        "trees": generated_trees,
        "PWR" : generated_PWR
    })

@app.route('/llm_call/generate_image_prompt', methods=['POST'])
def llm_call_generate_image_prompt():
    data = request.get_json()
    concept = data.get('concept', '')
    attributes = data.get('attributes', {})
    connections = data.get('connections', {})
    targets = data.get('targets', {})
    spaces = data.get('spaces', {})
    pwr = data.get('pwr', '')
    tree_placement = data.get('tree_placement', '')
    print("Received design data for image prompt generation:", data)

    prompt = generate_image_prompt(
        concept, attributes, connections, targets, spaces, pwr, tree_placement
    )
    return jsonify({
        "prompt": prompt
    })

if __name__ == '__main__':
    app.run(debug=True)