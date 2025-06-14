from flask import Flask, request, jsonify
from server.config import *
from llm_calls import *
from utils.rag_utils import rag_call
import threading
import sys
from ui_pyqt import FlaskClientChatUI  
from PyQt5.QtWidgets import QApplication


app = Flask(__name__)

area = None
external_functions = None
generated_spaces = None
geometry_data = None
design_data = None
tree_data = None
graph_data = None
width = None
length = None

@app.route('/plot_area', methods=['GET', 'POST'])
def get_plot_area():
    global area
    if request.method == 'POST':
        data = request.get_json()
        area = data.get('input')
        print("Received user input:", area)
        return jsonify({"area": area, "width": width, "length": length})
    else:  # GET
        return jsonify({"area": area, "width": width, "length": length})
    
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




