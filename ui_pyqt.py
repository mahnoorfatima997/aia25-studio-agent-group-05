import requests
from llm_calls import *
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QTextBrowser, QHBoxLayout
)
import re
from graph_gh import GraphEditor
import csv
import os

class FlaskClientChatUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Courtyard Design Copilot")

        # Now create a QLabel for a pretty title inside the window
        title_label = QLabel("🧠 Courtyard Design Copilot")
        title_label.setStyleSheet("font-size: 30px; font-weight: bold; margin-bottom: 10px;")
        self.setGeometry(200, 200, 800, 800)
        self.phases = {
            "concept": [],
            "functions": [],
            "attributes": [],
            "graph": [],
            "criticism": [],
        }
        self.current_phase = "concept"
        self.design_data = {}  # Store all extracted design data globally
        self.tree_data = {}

        self.phase_questions = {
            "concept": "What is your main design concept or idea?",
            "functions": "What functions or spaces does your building include?",
            "attributes": "What are the key attributes or requirements you would like to add?",
            "graph": "A graph will be shown. You can interact with the graph to create a different layout.",
            "criticism": "Would you like me to offer some advice about your design?"
        }
        
        
        # Main layout
        layout = QVBoxLayout()

        # Chat display area
        self.chat_display = QTextBrowser()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        # Input and send button layout
        input_layout = QHBoxLayout()

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.setStyleSheet("font-size: 18px; height: 40px;")
        input_layout.addWidget(self.input_field)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("font-size: 18px; height: 40px; padding: 8px 20px;")
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        # Continue button (hidden by default)
        self.continue_button = QPushButton("Continue")
        self.continue_button.clicked.connect(self.handle_continue)
        self.continue_button.setStyleSheet("font-size: 18px; height: 40px; padding: 8px 20px;")
        self.continue_button.hide()  # Hide initially
        layout.addWidget(self.continue_button)

        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.handle_back)
        self.back_button.setStyleSheet("font-size: 18px; height: 40px; padding: 8px 20px;")
        self.back_button.hide()  # Hide initially
        layout.addWidget(self.back_button)

        
        # Set central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.update_phase_buttons()
        self.show_phase_question()

        # Make the window and fonts bigger
        self.setGeometry(200, 200, 1000, 900)  # Larger window
        self.chat_display.setStyleSheet("font-size: 18px; padding: 10px;")
        self.input_field.setStyleSheet("font-size: 18px; height: 40px;")
        self.send_button.setStyleSheet("font-size: 18px; height: 40px; padding: 8px 20px;")
        self.continue_button.setStyleSheet("font-size: 18px; height: 40px; padding: 8px 20px;")
        self.back_button.setStyleSheet("font-size: 18px; height: 40px; padding: 8px 20px;")

    def show_phase_question(self):
        question = self.phase_questions.get(self.current_phase)
        if question:
            assistant_html = (
            '<table width="100%" cellspacing="0" cellpadding="10">'
            '<tr><td align="left">'
            '<div style="background-color:#d4edda; padding:12px; border-radius:15px; max-width: 60%; display:inline-block; font-size: 16px;">'
            '{}</div>'
            '</td></tr></table>'
        ).format(question)
        self.chat_display.append(assistant_html)


    def send_message(self):
        message = self.input_field.text().strip()
        if not message:
            self.chat_display.append("<span style='color: red;'>Please enter a message.</span>")
            return

        try:
            if (self.current_phase == "concept"):
                plot_area = self.get_plot_area()
                message = f"{message}. Make sure the plot area is {plot_area['area']} m²."
            
            self.input_field.clear()

            self.phases[self.current_phase].append({'role': 'user', 'content': message})
            assistant_message = None


            if (self.current_phase == "concept"):
                assistant_message = generate_concept_with_conversation(self.phases[self.current_phase])
                self.concept = assistant_message
            elif (self.current_phase == "functions"):
                assistant_message = extract_external_functions(self.phases[self.current_phase])
                json_llm_response = extract_json(assistant_message)
                self.extracted_functions = json_llm_response["external_functions"]
                self.set_extracted_functions()

                assistant_message = f"Your requirements have been saved as follows: {json_llm_response}<br>Does this look good? If so, press continue."
            elif (self.current_phase == "attributes"):
                assistant_message = extract_attributes_with_conversation(self.phases[self.current_phase], self.concept)
                json_llm_response = extract_json(assistant_message)
                self.attributes = json_llm_response
               
                assistant_message = f"I have added your requirements to the total list of attributes. {json_llm_response}Is this okay? If so, press continue."
            elif (self.current_phase == "criticism"):
                assistant_message = criticize_courtyard_graph(self.phases[self.current_phase])
                self.attributes = assistant_message

            # Display the user's message in the chat window
            user_html = f"""
            <table width="100%" cellspacing="0" cellpadding="10">
            <tr>
                <td align="right">
                <div style="
                    background-color:#d1ecf1;
                    padding:12px;
                    border-radius:15px;
                    max-width: 60%;
                    display:inline-block;
                    font-size: 16px;">
                    {message}
                </div>
                </td>
            </tr>
            </table>
            """
            self.chat_display.append(user_html)

            # Display the server's response in the chat window
            assistant_html = f"""
            <table width="100%" cellspacing="0" cellpadding="10">
            <tr>
                <td align="left">
                <div style="
                    background-color:#d4edda;
                    padding:12px;
                    border-radius:15px;
                    max-width: 60%;
                    display:inline-block;
                    font-size: 16px;">
                    {assistant_message}
                </div>
                </td>
            </tr>
            </table>
            """
            self.chat_display.append(assistant_html)


            self.continue_button.show()  # Show continue button for next phase
            self.update_phase_buttons()

            if self.current_phase == "attributes":
                self.geometry_data()
                self.get_tree_data()
        
                geometry_data_response = requests.post(
                    "http://127.0.0.1:5000/geometry_data",
                    json={"geometry_data": self.design_data}
                )
                func_data = geometry_data_response.json()
                self.chat_display.append(f"<i>Sent geometry data to server. Response: {func_data}</i>")

                tree_data_response = requests.post(
                    "http://127.0.0.1:5000/send_tree_data",
                    json={"tree_data": self.tree_data}
                )
                self.chat_display.append(f"<i>Sent geometry data to server. Response: {tree_data_response.json()}</i>")


        except Exception as e:
            self.chat_display.append("<span style='color: red;'>Error connecting to the server.</span>")
            print(f"Error: {e}")
        

    def handle_continue(self):
        phases = list(self.phases.keys())
        current_index = list(phases).index(self.current_phase)
        should_show_graph = self.current_phase == "attributes"
        if current_index < len(phases) - 1:
            self.current_phase = phases[current_index + 1]
            self.chat_display.append(f"<b>Phase changed to:</b> {self.current_phase}")
            self.continue_button.hide()
            self.show_phase_question()
            if self.current_phase == 'graph':
                self.graph()
                
                
        else:
            self.update_phase_buttons()

    def update_phase_buttons(self):
        phases = list(self.phases.keys())
        current_index = phases.index(self.current_phase)
        # Show "Back" if not at the first phase
        if current_index > 0:
            self.back_button.show()
        else:
            self.back_button.hide()
        # Show "Continue" if not at the last phase
        if current_index < len(phases) - 1:
            self.continue_button.show()
        else:
            self.continue_button.hide()

    def handle_back(self):
        phases = list(self.phases.keys())
        current_index = phases.index(self.current_phase)
        if current_index > 0:
            self.current_phase = phases[current_index - 1]
            self.chat_display.append(f"<b>Returned to phase:</b> {self.current_phase}")
            self.show_phase_question()
        self.update_phase_buttons()

    def get_plot_area(self):
        try:
            plot_area_response = requests.get("http://127.0.0.1:5000/plot_area")
            print(f"Plot area response status: {plot_area_response.status_code}")
            plot_area = plot_area_response.json()
            print("plot_area", plot_area)
            
            # If all values are None, use default values
            if all(v is None for v in [plot_area.get("area"), plot_area.get("width"), plot_area.get("length")]):
                print("Using default plot dimensions")
                return {
                    "area": "400",
                    "width": "20",
                    "length": "20"
                }
            
            # Calculate width and length from area if not provided
            if plot_area.get("width") is None or plot_area.get("length") is None:
                area = float(plot_area.get("area", "400"))
                # Assume a square plot if dimensions not provided
                side_length = (area ** 0.5)  # Square root of area
                plot_area["width"] = str(side_length)
                plot_area["length"] = str(side_length)
                print("Calculated dimensions:", plot_area)
            
            return plot_area
        except Exception as e:
            self.chat_display.append("<span style='color: red;'>Error fetching plot area from Grasshopper.</span>")
            print(f"Error fetching plot area: {e}")
            # Return default values if there's an error
            return {
                "area": "400",
                "width": "20",
                "length": "20"
            }
    
    def set_extracted_functions(self):
        try:
            response = requests.post(
                "http://localhost:5000/external_functions",
                json={"functions": self.extracted_functions}),
        except Exception as e:
            self.chat_display.append("<span style='color: red;'>Error extracting functions.</span>")
            print(f"Error setting functions: {e}")
            return


    def geometry_data(self):
        """
        Aggregate all relevant data from all phases, store in self.design_data, and persist to JSON DB.
        """
        try:
            spaces = extract_json(extract_spaces(self.concept, self.extracted_functions, self.attributes))
            links = extract_json(extract_links(self.concept, self.extracted_functions))
            positions = extract_json(extract_positions(self.concept, self.extracted_functions))
            cardinal_directions = extract_json(extract_cardinal_directions(self.concept, self.extracted_functions, self.attributes))
            weights = extract_json(extract_weights(self.concept, self.extracted_functions, self.attributes))
            anchors = extract_json(extract_anchors(self.concept, self.extracted_functions, self.attributes))
            pos = extract_json(extract_pos(self.concept, self.extracted_functions))

            self.design_data = {
                "spaces": spaces["spaces"],
                "links": links["links"],
                "positions": positions["positions"],
                "cardinal_directions": cardinal_directions["cardinal_directions"],
                "weights": weights["weights"],
                "anchors": anchors["anchors"],
                "external_functions": self.extracted_functions,
                "pos": pos["pos"]
            }
            print("Design data aggregated:", self.design_data)

        except Exception as e:
            self.chat_display.append("<span style='color: red;'>Error extracting geometry data.</span>")
            print(f"Error in geometry_data: {e}")


    def get_tree_data(self):
        """
        Aggregate all relevant data from all phases, store in self.design_data, and persist to JSON DB.
        """
        try:
            tree_placement = extract_json(extract_tree_placement(self.concept, self.attributes))
            PWR = extract_json(extract_plant_water_requirement(self.concept, self.attributes, tree_placement))

            self.tree_data = {
                "tree_placement": tree_placement["tree_placement"],
                "PWR": PWR["pwr"],                
            }
            print("Tree data aggregated:", self.tree_data)

        except Exception as e:
            self.chat_display.append("<span style='color: red;'>Error extracting geometry data.</span>")
            print(f"Error in tree_data: {e}")

    def create_networkx_graph(self, graph_json):
        """
        This function is now deprecated. All graph visualization is handled by GraphEditor.
        """
        pass  # No longer used

    def graph(self):
        try:
            llm_output = assemble_courtyard_graph(
                self.design_data["spaces"],
                self.design_data["external_functions"],
                self.design_data["weights"],
                self.design_data["anchors"],
                self.design_data["positions"],
                self.design_data["links"],
                self.design_data["cardinal_directions"],
                self.design_data["pos"]
            )
            llm_output_json = extract_json(llm_output)
            print("GRAPH INFO", llm_output_json)
            export_graph_to_csv(llm_output_json)
            # Show the interactive graph editor pop-up
            self.show_graph(llm_output_json)
        except Exception as e:
            self.chat_display.append("<span style='color: red;'>Error generating graph.</span>")
            print(f"Error generating graph: {e}")

    def show_graph(self, graph_json):
        # Create a new window for the graph editor
        self.graph_window = QMainWindow(self)
        self.graph_window.setWindowTitle("Graph Editor")
        self.graph_window.setGeometry(250, 250, 1000, 800)

        # Create the GraphEditor widget (from user-provided code)
        self.graph_editor = GraphEditor(graph_json)

        # Add a Save button
        save_button = QPushButton("Save and Send to Grasshopper")
        save_button.setStyleSheet("font-size: 16px; padding: 8px 20px;")
        save_button.clicked.connect(self.save_and_send_graph)

        # Layout for the graph window
        graph_layout = QVBoxLayout()
        graph_layout.addWidget(self.graph_editor)
        graph_layout.addWidget(save_button)

        container = QWidget()
        container.setLayout(graph_layout)
        self.graph_window.setCentralWidget(container)
        self.graph_window.show()

    def save_and_send_graph(self):
        # Save the edited graph to JSON
        edited_graph = self.graph_editor.get_graph_json()
        # Convert the edited graph back to design_data_post 
        design_data_post = self.graph_editor.convert_graph_to_design_data(edited_graph)

        try:
            response = requests.post(
                "http://127.0.0.1:5000/geometry_data_post",
                json={"geometry_data_post": design_data_post}
            )
            if response.status_code == 200:
                self.chat_display.append("<span style='color: green;'>Edited design data sent to Grasshopper.</span>")
            else:
                self.chat_display.append(f"<span style='color: red;'>Failed to send edited data: {response.status_code}</span>")
        except Exception as e:
            self.chat_display.append("<span style='color: red;'>Error sending edited data.</span>")
            print(f"Error sending edited data: {e}")
        self.graph_window.close()


    def get_graph_json(self):
        nodes = []
        for nid, item in self.nodes.items():
            x, y = item.scenePos().x(), item.scenePos().y()
            node_data = {
                "id": nid,
                "pos": {"x": round(x, 2), "y": round(y, 2)},
                "anchor": item.anchor
            }
            if not item.anchor:
                node_data["weight"] = round(item.radius / 1.5, 1)
            nodes.append(node_data)
        links = [{"source": e.node1.node_id, "target": e.node2.node_id} for e in self.edges]
        return {"nodes": nodes, "links": links}
    
    def convert_graph_to_design_data(self, graph_json):
        # Example: reconstruct design_data_post from graph_json
        design_data_post = {
            "spaces": [node["id"] for node in graph_json["nodes"]],
            "positions": {node["id"]: node["pos"] for node in graph_json["nodes"]},
            "anchors": {node["id"]: node.get("anchor", False) for node in graph_json["nodes"]},
            "weights": {node["id"]: node.get("weight", 20) for node in graph_json["nodes"]},
            "links": graph_json["links"],
            # Add other fields as needed
        }
        return design_data_post


def extract_json(body):
    # if body is json then return
    if isinstance(body, dict):
        return body  # Already a JSON object
    json_response = None
    match = re.search(r'\{.*\}', body, re.DOTALL)
    if match:
        try:
            json_response = json.loads(match.group(0))
        except Exception as e:
            print(f"Failed to parse JSON: {e}")
            print("body:", body)
    else:
        print("No JSON found in body.")
        print("body:", body)
    return json_response

def export_graph_to_csv(graph_json, out_dir=None):
    """
    Exports two CSV files: nodes.csv and edges.csv from the given graph_json.
    """
    if out_dir is None:
        out_dir = os.path.expanduser("~/Downloads")
    nodes_path = os.path.join(out_dir, "nodes.csv")
    edges_path = os.path.join(out_dir, "edges.csv")

    # Write nodes
    with open(nodes_path, "w", newline='') as f_nodes:
        if not graph_json["nodes"]:
            return
        fieldnames = list(graph_json["nodes"][0].keys())
        # Flatten pos if present
        if "pos" in fieldnames:
            fieldnames.remove("pos")
            fieldnames += ["x", "y"]
        writer = csv.DictWriter(f_nodes, fieldnames=fieldnames)
        writer.writeheader()
        for node in graph_json["nodes"]:
            row = node.copy()
            if "pos" in row:
                row["x"] = row["pos"].get("x", "")
                row["y"] = row["pos"].get("y", "")
                del row["pos"]
            writer.writerow(row)

    # Write edges
    with open(edges_path, "w", newline='') as f_edges:
        writer = csv.DictWriter(f_edges, fieldnames=["source", "target"])
        writer.writeheader()
        for edge in graph_json["links"]:
            writer.writerow({"source": edge["source"], "target": edge["target"]})

    print(f"✅ Nodes CSV saved to: {nodes_path}")
    print(f"✅ Edges CSV saved to: {edges_path}")



