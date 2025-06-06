from flask import Flask, request, jsonify
from server.config import *
from llm_calls import *
from utils.rag_utils import rag_call
import json
import re
import networkx as nx
import matplotlib.pyplot as plt
from graph import generate_network_graph
import io
import base64
import threading
import sys
from llm_calls import route_query_to_function
from ui_pyqt import FlaskClientChatUI  
from PyQt5.QtWidgets import QApplication
app = Flask(__name__)

area = None
external_functions = None


@app.route('/plot_area', methods=['GET', 'POST'])
def get_plot_area():
    global area
    if request.method == 'POST':
        data = request.get_json()
        area = data.get('input')
        print("Received user input:", area)
        return jsonify({"area": area})
    else:  # GET
        return jsonify({"area": area})
    
# @app.route('/send_to_grasshopper', methods=['POST', 'GET'])
# def send_to_grasshopper():
#     global external_functions

#     if request.method == 'POST':
#         data = request.get_json()
#         external_functions = data.get("functions", [])
#         print("Received functions from UI:", external_functions)
#     # Do something with functions, e.g., pass to Grasshopper
#     return jsonify(external_functions)


@app.route('/external_functions', methods=['POST', 'GET'])
def handle_external_functions():
    global external_functions
    if request.method == 'POST':
        data = request.get_json()
        external_functions = data.get('functions', [])
        print("Received functions from UI:", external_functions)
        return jsonify({"status": "Functions updated successfully."})
    elif request.method == 'GET':
        if external_functions is None:
            return jsonify({"error": "No functions available. Please call POST first."})
        else:
            return jsonify({"external_functions": external_functions})
        

@app.route('/spaces', methods=['POST', 'GET'])
def handle_generated_spaces():
    global generated_spaces
    if request.method == 'POST':
        data = request.get_json()
        generated_spaces = data.get('spaces', [])
        print("Received spaces from UI:", generated_spaces)
        return jsonify({"status": "Spaces updated successfully."})
    elif request.method == 'GET':
        if generated_spaces is None:
            return jsonify({"error": "No spaces available. Please call POST first."})
        else:
            return jsonify({"spaces_generated": generated_spaces})
        


@app.route('/geometry_data', methods=['POST', 'GET'])
def handle_geometry_data():
    global geometry_data
    if request.method == 'POST':
        data = request.get_json()
        geometry_data = data.get('geometry_data', [])
        print("Received spaces from UI:", geometry_data)
        return jsonify({"status": "Spaces updated successfully."})
    elif request.method == 'GET':
        if geometry_data is None:
            return jsonify({"error": "No geometry_data available. Please call POST first."})
        else:
            return jsonify({"geometry_data": geometry_data})
    

@app.route('/graph/generate_courtyard_graph', methods=['POST'])
def generate_courtyard_graph():
    data = request.get_json()
    print("Received graph data:", data)

    # Generate the graph image and get the file path
    output_path = "static/network_graph.png"  # or any path you prefer
    generate_network_graph(data, output_path=output_path)

    # Read the image and encode as base64 for UI embedding
    with open(output_path, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode('utf-8')

    return jsonify({"graph_image": img_base64})

# <img src="data:image/png;base64,{{ graph_image }}" /> for use in ui


def run_flask():
    app.run(debug=False, use_reloader=False)  # Run Flask server in a separate thread

if __name__ == '__main__':
    # app.run(debug=True)
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Start PyQt application
    app = QApplication(sys.argv)
    app.setStyleSheet("QWidget { font-size: 14px; }") 
    window = FlaskClientChatUI()
    window.show()
    sys.exit(app.exec_())


# @app.route('/chat', methods=['POST'])
# def chat():
#     data = request.get_json()
#     message = data.get("message", "")
#     # Optionally: conversation = data.get("conversation", [])
#     if not message:
#         return jsonify({"error": "No message provided."}), 400

#     # Route the query to the correct function
#     answer = route_query_to_function(message)

#     # If the answer is a string and contains JSON, extract the first JSON object
#     if isinstance(answer, str):
#         import re, json
#         match = re.search(r'\{.*\}', answer, re.DOTALL)
#         if match:
#             try:
#                 json_obj = json.loads(match.group(0))
#                 return jsonify(json_obj)
#             except Exception as e:
#                 print(f"Failed to parse JSON in chat endpoint: {e}")
#                 # Fall back to returning the raw answer as text
#                 return jsonify({"answer": answer})
#         else:
#             return jsonify({"answer": answer})
#     else:
#         # If answer is already a dict or list, return as JSON
#         return jsonify({"answer": answer})

# @app.route('/llm_call/generate_concept', methods=['POST'])
# def llm_call_generate_concept():
#     data = request.get_json()
#     concept_conversation = data.get('conversation')
#     print("Received user input:", concept_conversation)
    
#     generated_concept = generate_concept_with_conversation(concept_conversation)
#     return jsonify({
#         "concept": generated_concept
#     })

# @app.route('/llm_call/extract_attributes', methods=['POST'])
# def llm_call_extract_attributes():
#     data = request.get_json()
#     attributes_conversation = data.get('conversation')
#     attributes = extract_attributes_with_conversation(attributes_conversation)
#     print("Received attributes:", attributes)
#     # Robustly extract the first valid JSON object from the LLM output
#     import re
#     match = re.search(r'\{.*\}', attributes, re.DOTALL)
#     if match:
#         try:
#             attributes_json = json.loads(match.group(0))
#         except Exception as e:
#             print(f"Failed to parse attributes JSON: {e}")
#             attributes_json = {}
#     else:
#         print("No JSON found in attributes output.")
#         attributes_json = {}
#     return jsonify({
#         "attributes": attributes_json
#     })

# @app.route('/llm_call/generate_connections_targets', methods=['POST'])
# def llm_call_generate_connections_targets():
#     data = request.get_json()
#     conversation = data.get('conversation')
#     # Ensure conversation is a list of message dicts for LLM API
#     if not isinstance(conversation, list):
#         return jsonify({
#             "error": "Conversation must be a list of message dicts."
#         }), 400
#     # Get connections
#     raw_connections = extract_connections_with_conversation(conversation)
#     # Robustly extract the first valid JSON object from the LLM output if needed
#     if isinstance(raw_connections, str):
#         match = re.search(r'\{.*\}', raw_connections, re.DOTALL)
#         print("match", match)
#         if match:
#             try:
#                 connections = json.loads(match.group(0)).get("connections", [])
#             except Exception as e:
#                 print(f"Failed to parse connections JSON: {e}")
#                 connections = []
#         else:
#             print("No JSON found in connections output.")
#             connections = []
#     else:
#         connections = raw_connections
#     print("Received connections:", connections)
#     num_zones = len(connections)
#     # Get targets (ensure same number as connections)
#     raw_targets = extract_targets_with_conversation(conversation, num_zones=num_zones)
#     if isinstance(raw_targets, str):
#         match = re.search(r'\{.*\}', raw_targets, re.DOTALL)
#         if match:
#             try:
#                 targets = json.loads(match.group(0)).get("targets", [])
#             except Exception as e:
#                 print(f"Failed to parse targets JSON: {e}")
#                 targets = []
#         else:
#             print("No JSON found in targets output.")
#             targets = []
#     else:
#         targets = raw_targets
#     print("Received targets:", targets)
#     return jsonify({
#         "connections": connections,
#         "targets": targets
#     })
    
# @app.route('/llm_call/generate_spaces', methods=['POST'])
# def llm_call_generate_spaces():
#     data = request.get_json()
#     space_conversation = data.get('conversation')
#     print("Received user input:", space_conversation)

#     generated_space = extract_spaces_with_conversation(space_conversation)
#     # Robustly extract the first valid JSON object from the LLM output
#     if isinstance(generated_space, str):
#         match = re.search(r'\{.*\}', generated_space, re.DOTALL)
#         if match:
#             try:
#                 spaces = json.loads(match.group(0)).get("spaces", [])
#             except Exception as e:
#                 print(f"Failed to parse spaces JSON: {e}")
#                 spaces = []
#         else:
#             print("No JSON found in spaces output.")
#             spaces = []
#     else:
#         spaces = generated_space
#     print("Received spaces:", spaces)
#     return jsonify({
#         "spaces": spaces
#     })

# @app.route('/llm_call/generate_tree_types', methods=['POST'])
# def llm_call_generate_tree_types():
#     data = request.get_json()
#     trees_conversation = data.get('conversation')
#     print("Received user input:", trees_conversation)

    
#     generated_PWR = extract_plant_water_requirement(trees_conversation)
#     generated_trees = extract_tree_placement(trees_conversation)

#     return jsonify({
#         "trees": generated_trees,
#         "PWR" : generated_PWR
#     })

# @app.route('/llm_call/generate_image_prompt', methods=['POST'])
# def llm_call_generate_image_prompt():
#     data = request.get_json()
#     concept = data.get('concept', '')
#     attributes = data.get('attributes', {})
#     connections = data.get('connections', {})
#     targets = data.get('targets', {})
#     spaces = data.get('spaces', {})
#     pwr = data.get('pwr', '')
#     tree_placement = data.get('tree_placement', '')
#     print("Received design data for image prompt generation:", data)

#     prompt = generate_image_prompt(
#         concept, attributes, connections, targets, spaces, pwr, tree_placement
#     )
#     return jsonify({
#         "prompt": prompt
#     })


