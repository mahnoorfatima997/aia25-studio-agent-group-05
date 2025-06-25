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
from datetime import datetime


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
query_engine = None  
query_results = None  
climate_data = None 
utci_values = None  


# Simple dictionary to hold the latest data received from Grasshopper
latest_data = {
    "plot_area": {"area": None, "width": None, "length": None},
    "external_functions": {},
    "geometry_data": {},
    "graph_data": {},
    "tree_data": {},
    "query_results": {},
    "external_function_placement": {},
    "climate_data": {},
    "utci_values": [],
    "utci_values_flat": [],
    "heatmap_data": [],
    "concept": "General courtyard design",
    "heatmap_analysis": {}
}

# --- New Command Queue for Screenshot ---
command_queue = {"command": None, "payload": {}}
command_status = {"status": "idle", "result": {}}
command_lock = threading.Lock()

@app.route('/plot_area', methods=['GET', 'POST'])
def get_plot_area():
    if request.method == 'POST':
        data = request.get_json()
        plot_area_data = data.get('input', {})
        
        # Store the plot area data in the latest_data dictionary
        if isinstance(plot_area_data, dict):
            latest_data["plot_area"] = {
                "area": plot_area_data.get('area'),
                "width": plot_area_data.get('width'),
                "length": plot_area_data.get('length')
            }
        else:
            # If input is just a string/number, treat it as area
            latest_data["plot_area"] = {
                "area": str(plot_area_data),
                "width": None,
                "length": None
            }
        
        print("Received plot area data:", latest_data["plot_area"])
        return jsonify(latest_data["plot_area"])
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
            "timestamp": str(datetime.now())
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

@app.route('/climate_data', methods=['GET', 'POST'])
def handle_climate_data():
    """Handle climate analysis data for Grasshopper"""
    global climate_data
    if request.method == 'POST':
        # UI sends climate data to be stored for Grasshopper
        data = request.get_json()
        climate_data = data.get('climate_data', data)
        print("Received climate data from UI:", climate_data)
        
        # Update the latest_data dictionary
        latest_data["climate_data"] = climate_data
        
        return jsonify({
            "status": "Climate data updated successfully.",
            "climate_data": climate_data
        })
    else:  
        # Grasshopper retrieves the latest climate data
        if climate_data is None:
            return jsonify({
                "error": "No climate data available. Please run climate analysis first."
            })
        else:
            return jsonify({
                "climate_data": climate_data,
                "timestamp": str(datetime.now())
            })

@app.route('/epw_file', methods=['GET', 'POST'])
def handle_epw_file():
    """Handle EPW file data for Ladybug Tools in Grasshopper"""
    global climate_data
    
    if request.method == 'POST':
        # UI sends EPW file data to be stored for Grasshopper
        data = request.get_json()
        epw_data = data.get('epw_data', data)
        print("Received EPW file data from UI")
        
        # Update the latest_data dictionary
        latest_data["epw_file"] = epw_data
        
        return jsonify({
            "status": "EPW file data updated successfully.",
            "file_size": len(epw_data.get('content', '')) if epw_data else 0
        })
    else:  # GET
        # Grasshopper retrieves the EPW file data for Ladybug Tools
        epw_data = latest_data.get("epw_file")
        if epw_data is None:
            return jsonify({
                "error": "No EPW file data available. Please run climate analysis first."
            })
        else:
            return jsonify({
                "epw_file": epw_data,
                "timestamp": str(datetime.now())
            })

@app.route('/climate/hoy_analysis', methods=['POST'])
def analyze_hoy():
    """Analyze HOY (Hour of Year) from time message and EPW URL"""
    try:
        data = request.get_json()
        time_message = data.get('time_message', '')
        zip_url = data.get('zip_url', '')
        
        if not time_message or not zip_url:
            return jsonify({
                "success": False,
                "error": "Both time_message and zip_url are required"
            })
        
        # Import the analysis function
        from epw_analysis import get_hoys_from_intent
        from server.config import client, completion_model
        
        # Get HOYs from the time message
        hoys = get_hoys_from_intent(time_message, zip_url, client, completion_model)
        
        if hoys:
            return jsonify({
                "success": True,
                "hoys": hoys,
                "time_message": time_message,
                "zip_url": zip_url,
                "total_hours": len(hoys)
            })
        else:
            return jsonify({
                "success": False,
                "error": "Could not extract HOYs from the time message"
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Analysis failed: {str(e)}"
        })

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

@app.route('/utci_values', methods=['GET', 'POST'])
def handle_utci_values():
    if request.method == 'POST':
        data = request.get_json()
        utci_values = data.get('utci_values', [])
        utci_values_flat = data.get('utci_values_flat', [])
        
        # Store both sets of values
        latest_data['utci_values'] = utci_values
        latest_data['utci_values_flat'] = utci_values_flat
        
        print("Received UTCI values from Grasshopper:")
        print(f"  With trees: {utci_values}")
        print(f"  Without trees: {utci_values_flat}")
        
        return jsonify({"status": "UTCI values received successfully"})
    else:  # GET
        utci_with_trees = latest_data.get('utci_values', [])
        utci_without_trees = latest_data.get('utci_values_flat', [])
        
        # Calculate averages
        avg_with_trees = 0
        avg_without_trees = 0
        
        if utci_with_trees:
            try:
                avg_with_trees = sum(float(x) for x in utci_with_trees) / len(utci_with_trees)
            except (ValueError, TypeError):
                avg_with_trees = 0
        
        if utci_without_trees:
            try:
                avg_without_trees = sum(float(x) for x in utci_without_trees) / len(utci_without_trees)
            except (ValueError, TypeError):
                avg_without_trees = 0
        
        # Calculate improvement
        improvement = avg_without_trees - avg_with_trees if avg_without_trees > avg_with_trees else avg_with_trees - avg_without_trees
        
        # Generate improvement tips based on the comparison
        tips = []
        if avg_with_trees < avg_without_trees:
            # Trees are helping (lower UTCI is better)
            if improvement > 5:
                tips.append("🌳 Trees are providing excellent thermal comfort! Consider adding more shade trees for even better results.")
            elif improvement > 2:
                tips.append("🌳 Trees are helping with thermal comfort. You could add more deciduous trees for seasonal benefits.")
            else:
                tips.append("🌳 Trees are providing some thermal benefit. Consider denser tree planting for greater impact.")
        else:
            # Trees might not be helping as expected
            tips.append("🌳 Consider optimizing tree placement or adding different tree species for better shade coverage.")
        
        # Additional tips based on average UTCI values
        if avg_with_trees > 30:
            tips.append("🌺 Add more flowering plants and ground cover to reduce surface temperatures.")
        if avg_with_trees > 25:
            tips.append("💧 Consider adding water features like fountains or ponds for evaporative cooling.")
        if avg_with_trees > 20:
            tips.append("🏗️ Optimize building orientation and add pergolas for additional shade.")
        
        # If no specific tips, provide general improvement suggestions
        if not tips:
            tips.append("🌱 Consider adding more vegetation, water features, or shade structures to improve thermal comfort.")
        
        return jsonify({
            "utci_values": utci_with_trees,
            "utci_values_flat": utci_without_trees,
            "average_with_trees": round(avg_with_trees, 2),
            "average_without_trees": round(avg_without_trees, 2),
            "improvement": round(improvement, 2),
            "trees_helping": avg_with_trees < avg_without_trees,
            "tips": tips
        })

@app.route("/upload_screenshot", methods=["POST"])
def upload_screenshot():
    """Receive screenshot from Grasshopper and save it"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'}), 400
        
        image = request.files['image']
        
        # Create save directory
        save_dir = os.path.expanduser("~/Downloads/gh_screenshots")
        os.makedirs(save_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gh_screenshot_{timestamp}.png"
        save_path = os.path.join(save_dir, filename)
        
        # Save the image
        image.save(save_path)
        
        print(f"✅ Screenshot saved: {save_path}")
        
        return jsonify({
            'success': True, 
            'screenshot_path': save_path,
            'message': 'Screenshot uploaded successfully'
        })
        
    except Exception as e:
        print(f"❌ Error uploading screenshot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/take_screenshot", methods=["POST"])
def take_screenshot():
    """Endpoint to trigger screenshot capture (for UI compatibility)"""
    try:
        # This endpoint is called by the UI to trigger screenshot
        # The actual screenshot is taken by Grasshopper and sent to /upload_screenshot
        
        # Check if we have a recent screenshot
        save_dir = os.path.expanduser("~/Downloads/gh_screenshots")
        if os.path.exists(save_dir):
            # Get the most recent screenshot
            files = [f for f in os.listdir(save_dir) if f.endswith('.png')]
            if files:
                # Sort by modification time (newest first)
                files.sort(key=lambda x: os.path.getmtime(os.path.join(save_dir, x)), reverse=True)
                latest_screenshot = os.path.join(save_dir, files[0])
                
                return jsonify({
                    'success': True,
                    'screenshot_path': latest_screenshot,
                    'message': 'Latest screenshot found'
                })
        
        return jsonify({
            'success': False,
            'error': 'No screenshot found. Please capture a screenshot from Grasshopper first.'
        })
        
    except Exception as e:
        print(f"❌ Error in take_screenshot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/concept', methods=['GET', 'POST'])
def handle_concept():
    """Handle concept storage for heatmap analysis"""
    global latest_data
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            concept = data.get('concept', 'General courtyard design')
            
            # Store the concept
            latest_data['concept'] = concept
            
            print(f"Received concept from UI: {concept}")
            
            return jsonify({
                'success': True,
                'message': 'Concept stored successfully',
                'concept': concept
            })
            
        except Exception as e:
            print(f"Error storing concept: {e}")
            return jsonify({
                'success': False,
                'error': f'Failed to store concept: {str(e)}'
            }), 500
    
    else:  # GET request
        concept = latest_data.get('concept', 'No concept defined')
        return jsonify({
            'concept': concept,
            'has_concept': bool(concept and concept != 'No concept defined')
        })

@app.route('/heatmap_analysis', methods=['GET', 'POST'])
def handle_heatmap_analysis():
    """Endpoint for analyzing heatmap data and providing activity recommendations"""
    global latest_data
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            heatmap_data = data.get('heatmap_data', [])
            
            # Get concept from the UI (stored in latest_data) instead of from Grasshopper
            concept = latest_data.get('concept', 'General courtyard design')
            
            # Validate heatmap data format
            if not isinstance(heatmap_data, list):
                return jsonify({
                    'success': False, 
                    'error': 'heatmap_data must be a list of [coordinate, utci_value] tuples'
                }), 400
            
            # Validate each data point
            validated_data = []
            for i, point in enumerate(heatmap_data):
                if not isinstance(point, (list, tuple)) or len(point) != 2:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid data point at index {i}. Expected [coordinate, utci_value]'
                    }), 400
                
                coord, utci_value = point
                try:
                    # Ensure coordinates are numeric
                    if isinstance(coord, (list, tuple)) and len(coord) >= 2:
                        x, y = float(coord[0]), float(coord[1])
                    else:
                        x, y = float(coord), 0.0
                    
                    # Ensure UTCI value is numeric
                    utci = float(utci_value)
                    
                    validated_data.append([[x, y], utci])
                except (ValueError, TypeError) as e:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid numeric values at index {i}: {e}'
                    }), 400
            
            # Store the heatmap data
            latest_data['heatmap_data'] = validated_data
            
            print(f"Received heatmap data: {len(validated_data)} points")
            print(f"Using concept from UI: {concept}")
            
            # Analyze the heatmap data using the LLM function
            try:
                from llm_calls import analyze_heatmap_activities
                analysis_result = analyze_heatmap_activities(concept, validated_data)
                
                # Store the analysis result
                latest_data['heatmap_analysis'] = analysis_result
                
                return jsonify({
                    'success': True,
                    'message': 'Heatmap analysis completed successfully',
                    'analysis': analysis_result
                })
                
            except Exception as e:
                print(f"Error in heatmap analysis: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Analysis failed: {str(e)}'
                }), 500
                
        except Exception as e:
            print(f"Error processing heatmap data: {e}")
            return jsonify({
                'success': False,
                'error': f'Request processing failed: {str(e)}'
            }), 500
    
    else:  # GET request
        # Return the latest analysis results
        heatmap_data = latest_data.get('heatmap_data', [])
        concept = latest_data.get('concept', 'No concept defined')
        analysis = latest_data.get('heatmap_analysis', {})
        
        return jsonify({
            'heatmap_data_points': len(heatmap_data),
            'concept': concept,
            'analysis': analysis,
            'has_analysis': bool(analysis)
        })

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




