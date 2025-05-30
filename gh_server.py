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
    try:
        attributes_json = json.loads(attributes)
    except json.JSONDecodeError as e:
        print(f"Failed to parse attributes JSON: {e}")
        attributes_json = {}
    return jsonify({
        "attributes": attributes_json
    })

@app.route('/llm_call/generate_connections_targets', methods=['POST'])
def llm_call_generate_connections_targets():
    data = request.get_json()
    conversation = data.get('conversation')
    # Get connections
    connections_result = extract_connections_with_conversation(conversation)
    print("Received connections:", connections_result)
    connections_match = re.search(r'\{.*\}', connections_result, re.DOTALL)
    if connections_match:
        try:
            connections_json = json.loads(connections_match.group(0))
        except Exception as e:
            print(f"Could not parse connections JSON: {e}")
            connections_json = {"connections": []}
    else:
        connections_json = {"connections": []}
    # Get targets
    targets_result = extract_targets_with_conversation(connections_result)
    print("Received targets:", targets_result)
    targets_match = re.search(r'\{.*\}', targets_result, re.DOTALL)
    if targets_match:
        try:
            targets_json = json.loads(targets_match.group(0))
        except Exception as e:
            print(f"Could not parse targets JSON: {e}")
            targets_json = {"targets": []}
    else:
        targets_json = {"targets": []}
    return jsonify({
        "connections": connections_json.get("connections", []),
        "targets": targets_json.get("targets", [])
    })
    
@app.route('/llm_call/generate_spaces', methods=['POST'])
def llm_call_generate_spaces():
    data = request.get_json()
    space_conversation = data.get('conversation')
    print("Received user input:", space_conversation)
    
    generated_space = extract_spaces_with_conversation(space_conversation)
    return jsonify({
        "spaces": generated_space
    })

@app.route('/llm_call/generate_tree_types', methods=['POST'])
def llm_call_generate_tree_types():
    data = request.get_json()
    trees_conversation = data.get('conversation')
    print("Received user input:", trees_conversation)
    
    generated_trees = extract_tree_types(trees_conversation)
    return jsonify({
        "trees": generated_trees
    })

@app.route('/llm_call/generate_PWR_locations', methods=['POST'])
def llm_call_generate_PWR_locations():
    data = request.get_json()
    trees_conversation = data.get('conversation')
    print("Received user input:", trees_conversation)

    trees_PWR = data.get('conversation')
    print("Received user input:", trees_PWR)
    
    generated_PWR = extract_plant_water_requirement(trees_PWR)
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
    tree_types = data.get('tree_types', '')
    pwr = data.get('pwr', '')
    tree_placement = data.get('tree_placement', '')
    print("Received design data for image prompt generation:", data)

    prompt = generate_prompt_with_context(
        concept, attributes, connections, targets, spaces, tree_types, pwr, tree_placement
    )
    return jsonify({
        "prompt": prompt
    })

if __name__ == '__main__':
    app.run(debug=True)