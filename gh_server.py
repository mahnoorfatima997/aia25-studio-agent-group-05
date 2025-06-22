from flask import Flask, request, jsonify
from server.config import *
from llm_calls import *
from utils.rag_utils import rag_call
import threading
import sys
from ui_pyqt import FlaskClientChatUI  
from PyQt5.QtWidgets import QApplication
from graph_query import GraphQueryEngine
import os
import datetime
from flask_cors import CORS
import json


app = Flask(__name__)
CORS(app)

area = None
external_functions = None
external_function_placement = None  # New global variable for external function placement
generated_spaces = None
geometry_data = None
design_data = None
tree_data = None
graph_data = None
width = None
length = None
query_engine = None  # Global variable for the graph query engine
query_results = None  # Global variable to store the latest query results

# --- Global In-Memory Storage ---
# Simple dictionary to hold the latest data received from Grasshopper
# In a production scenario, you might replace this with a database or a more robust solution
latest_data = {
    "plot_area": {"area": "400", "width": "20", "length": "20"},
    "external_functions": {},
    "geometry_data": {},
    "graph_data": {},
    "tree_data": {},
    "query_results": {},
    "external_function_placement": {}
}

# --- New Command Queue for Screenshot ---
command_queue = {"command": None, "payload": {}}
command_status = {"status": "idle", "result": {}}
command_lock = threading.Lock()

@app.route('/plot_area', methods=['GET', 'POST'])
def get_plot_area():
    global area
    if request.method == 'POST':
        data = request.get_json()
        area = data.get('input')
        print("Received user input:", area)
        return jsonify({"area": area, "width": width, "length": length})
    else:  # GET
        return jsonify(latest_data.get("plot_area", {}))
    
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

@app.route('/external_function_placement', methods=['GET', 'POST'])
def handle_external_function_placement():
    """Handle external function placement data for Grasshopper"""
    global external_function_placement
    if request.method == 'POST':
        data = request.get_json()
        external_function_placement = data.get('external_function_placement', {})
        print("Received external function placement data:", external_function_placement)
        return jsonify({"status": "External function placement data updated successfully."})
    else:  # GET
        if external_function_placement is None:
            return jsonify({"error": "No external function placement data available. Please set placement data first."})
        else:
            return jsonify({"external_function_placement": external_function_placement})

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
        
@app.route('/geometry_data', methods=['POST'])
def set_geometry_data():
    global design_data
    print("Received JSON:", request.json)
    design_data = request.json.get('geometry_data', {})
    # print("Updated design_data:", design_data)
    return jsonify({"status": "ok"})

@app.route('/geometry_data', methods=['GET'])
def get_geometry_data():
    return jsonify({"geometry_data": design_data})
 
@app.route('/send_tree_data', methods=['GET','POST'])
def set_tree_data():
    global tree_data
    if request.method == 'POST':
        # Only UI or Python app should POST here, not Grasshopper
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json. Please POST JSON from your UI or Python app, not from Grasshopper."}), 415
        print("Received JSON tree:", request.json)
        # Accept both formats: direct tree_data or wrapped in send_tree_data
        tree_data = request.json.get('send_tree_data', request.json)
        print("Stored tree_data:", tree_data)
        return jsonify({"status": "ok", "tree_data": tree_data})
    else:
        # Grasshopper should only GET here to retrieve the latest tree data
        print("Returning tree_data:", tree_data)
        return jsonify({
            "tree_placement": tree_data.get("tree_placement", {}) if tree_data else {},
            "PWR": tree_data.get("PWR", {}) if tree_data else {}
        })
    
@app.route('/graph_data', methods=['GET', 'POST'])
def handle_graph_data():
    global graph_data
    if request.method == 'POST':
        print("POST request received for graph data. Raw JSON:", request.json)
        graph_data = request.json.get('graph_data', request.json)
        print("Stored graph_data:", graph_data)
        return jsonify({"status": "ok", "graph_data": graph_data})
    else:  # GET
        print("GET request received for graph data. Current data:", graph_data)
        if graph_data is None:
            return jsonify({"error": "No graph data available. Please generate a graph first."})
        # Return the entire graph data structure as one JSON object
        return jsonify(graph_data)  # Send the complete graph data structure


# Graph Query Endpoints
@app.route('/graph_query/load_data', methods=['POST'])
def load_graph_data():
    """Load CSV data into Neo4j for graph querying"""
    global query_engine
    try:
        # Initialize the query engine
        query_engine = GraphQueryEngine()
        
        if not query_engine.driver:
            return jsonify({
                "success": False,
                "error": "Failed to connect to Neo4j database. Please ensure Neo4j is running."
            }), 500
        
        # Load CSV data
        if query_engine.load_csv_to_neo4j():
            return jsonify({
                "success": True,
                "message": "Graph data loaded successfully!"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to load graph data. Please ensure CSV files exist."
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error loading graph data: {str(e)}"
        }), 500


@app.route('/graph_query/sample_questions', methods=['GET'])
def get_sample_questions():
    """Get sample questions for the loaded graph"""
    global query_engine
    try:
        if not query_engine:
            return jsonify({
                "success": False,
                "error": "Please load graph data first."
            }), 400
        
        sample_questions = query_engine.get_sample_questions()
        return jsonify({
            "success": True,
            "questions": sample_questions
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error getting sample questions: {str(e)}"
        }), 500


@app.route('/graph_query/ask', methods=['POST'])
def ask_graph_question():
    """Ask a question about the graph data"""
    global query_engine, query_results
    try:
        if not query_engine:
            return jsonify({
                "success": False,
                "error": "Please load graph data first."
            }), 400
        
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                "success": False,
                "error": "Question cannot be empty."
            }), 400
        
        # Get response from query engine
        human_answer, cypher_query, raw_data = query_engine.ask_question(question)
        
        # Store the query results globally for sending to Grasshopper
        query_results = {
            "question": question,
            "cypher_query": cypher_query,
            "raw_data": raw_data,
            "human_answer": human_answer,
            "timestamp": str(datetime.datetime.now())
        }
        
        return jsonify({
            "success": True,
            "question": question,
            "cypher_query": cypher_query,
            "raw_data": raw_data,
            "human_answer": human_answer
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error processing question: {str(e)}"
        }), 500


@app.route('/graph_query/status', methods=['GET'])
def get_query_status():
    """Get the status of the graph query engine"""
    global query_engine
    try:
        if not query_engine:
            return jsonify({
                "connected": False,
                "message": "Graph Query Engine not initialized"
            })
        
        if not query_engine.driver:
            return jsonify({
                "connected": False,
                "message": "Neo4j not connected"
            })
        
        # Test connection
        try:
            with query_engine.driver.session() as session:
                session.run("RETURN 1")
            return jsonify({
                "connected": True,
                "message": "Connected to Neo4j"
            })
        except:
            return jsonify({
                "connected": False,
                "message": "Neo4j connection failed"
            })
            
    except Exception as e:
        return jsonify({
            "connected": False,
            "message": f"Error: {str(e)}"
        })


@app.route('/query_results', methods=['POST'])
def set_query_results():
    """Set query results to be sent to Grasshopper"""
    global query_results
    print("Received query results JSON:", request.json)
    query_results = request.json.get('query_results', request.json)
    print("Stored query_results:", query_results)
    return jsonify({"status": "ok", "query_results": query_results})

@app.route('/query_results', methods=['GET'])
def get_query_results():
    """Get the latest query results for Grasshopper"""
    global query_results
    if query_results is None:
        return jsonify({"error": "No query results available. Please run a query first."})
    return jsonify({"query_results": query_results})

# --- New Endpoints for Screenshot Command System ---

@app.route('/command', methods=['GET', 'POST', 'DELETE'])
def handle_command():
    """Endpoint for the UI to send commands and for Grasshopper to fetch them."""
    global command_queue, command_status
    with command_lock:
        if request.method == 'POST':
            data = request.get_json()
            command_queue['command'] = data.get('command')
            command_queue['payload'] = data.get('payload', {})
            # Reset status for the new command
            command_status['status'] = 'pending'
            command_status['result'] = {}
            print(f"Received command: {command_queue['command']}")
            return jsonify({"success": True, "message": "Command queued."})
        
        elif request.method == 'GET':
            return jsonify(command_queue)
            
        elif request.method == 'DELETE':
            command_queue['command'] = None
            command_queue['payload'] = {}
            print("Command queue cleared.")
            return jsonify({"success": True, "message": "Command cleared."})

@app.route('/command_status', methods=['GET', 'POST'])
def handle_command_status():
    """Endpoint for Grasshopper to report command status and for UI to check it."""
    global command_status
    with command_lock:
        if request.method == 'POST':
            data = request.get_json()
            command_status['status'] = data.get('status', 'complete')
            command_status['result'] = data.get('result', {})
            print(f"Received command status update: {command_status['status']}")
            return jsonify({"success": True, "message": "Status updated."})

        elif request.method == 'GET':
            return jsonify(command_status)

def run_flask():
    app.run(debug=False, use_reloader=False)  # Run Flask server in a separate thread


if __name__ == '__main__':
    # app.run(debug=True)
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Start PyQt application
    app = QApplication(sys.argv)
    app.setStyleSheet("QWidget { font-size: 16px; }") 
    window = FlaskClientChatUI()
    window.show()
    sys.exit(app.exec_())




