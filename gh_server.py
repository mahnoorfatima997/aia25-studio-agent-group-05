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

@app.route('/llm_call/generate_weights', methods=['POST'])
def llm_call_generate_weights():
    data = request.get_json()
    weights_conversation = data.get('conversation')
    weights = extract_weights_with_conversation(weights_conversation)
    print("Received weights:", weights)
    try:
        weights_json = json.loads(weights)
    except json.JSONDecodeError as e:
        print(f"Failed to parse attributes JSON: {e}")
        weights_json = {}
    return jsonify({
        "weights": weights_json
    })

@app.route('/llm_call/generate_locations', methods=['POST'])
def llm_call_generate_locations():
    data = request.get_json()
    locations_conversation = data.get('conversation')
    locations = extract_locations_with_conversation(locations_conversation)
        # Parse locations JSON
    locations_match = re.search(r'\{.*\}', locations, re.DOTALL)
    if locations_match:
        try:
            locations_json = json.loads(locations_match.group(0))
        except Exception as e:
            print(f"Could not parse locations JSON: {e}")
            locations_json = {}
    else:
        locations_json = {}
    print("Received locations:", locations)
    return jsonify({
        "locations": locations_json
    })

@app.route('/llm_call/generate_connections', methods=['POST'])
def llm_call_generate_connections():
    data = request.get_json()
    connections_conversation = data.get('conversation')
    result = extract_connections_with_conversation(connections_conversation)
    print("Received connections:", result)
        # Parse connections JSON
    connections_match = re.search(r'\{.*\}', result, re.DOTALL)
    if connections_match:
        try:
            connections_json = json.loads(connections_match.group(0))
        except Exception as e:
            print(f"Could not parse connections JSON: {e}")
            connections_json = {}
    else:
        connections_json = {}
    return jsonify({
        "connections": connections_json["connections"],
    })

@app.route('/llm_call/generate_targets', methods=['POST'])
def llm_call_generate_targets():
    data = request.get_json()
    targets_conversation = data.get('conversation')
    targets = extract_targets_with_conversation(targets_conversation)
        # Parse targets JSON
    targets_match = re.search(r'\{.*\}', targets, re.DOTALL)
    if targets_match:
        try:
            targets_json = json.loads(targets_match.group(0))
        except Exception as e:
            print(f"Could not parse targets JSON: {e}")
            targets_json = {}
    else:
        targets_json = {}
    print("Received targets:", targets)
    return jsonify({
        "targets": targets_json
    })

if __name__ == '__main__':
    app.run(debug=True)