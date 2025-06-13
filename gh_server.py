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

@app.route('/geometry_data_post', methods=['GET','POST'])
def set_geometry_data_post():
    global design_data_post
    if request.method == 'POST':
        design_data_post = request.json.get('geometry_data_post', {})
        return jsonify({"status": "ok"})
    else: 
        # Return the last posted geometry_data_post
        return jsonify({"geometry_data_post": design_data_post if 'design_data_post' in globals() else {}})
    




@app.route('/send_tree_data', methods=['GET','POST'])
def set_tree_data():
    global tree_data
    print("Received JSON tree:", request.json)
    if request.method == 'POST':
        tree_data = request.json.get('send_tree_data', {})
        return jsonify({"status": "ok"})
    else:  # GET
        # Return the last posted tree_data
        return jsonify({"send_tree_data": tree_data if 'tree_data' in globals() else {}})
    




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




