import requests
from llm_calls import *
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QTextBrowser, QHBoxLayout
)
import re
from graph_gh import GraphEditor, MainWindow, QApplication
import csv
import os
import random
import json

class FlaskClientChatUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Courtyard Design Copilot")
        
        # Set window style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QLineEdit {
                border: 2px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
            QTextBrowser {
                border: none;
                background-color: white;
                border-radius: 8px;
            }
        """)

        # Create a container widget for the main content
        container = QWidget()
        self.setCentralWidget(container)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title section with icon and gradient background
        title_container = QWidget()
        title_container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                          stop:0 #2196F3, stop:1 #1976D2);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(20, 15, 20, 15)

        # Title with icon
        title_label = QLabel("🧠 Courtyard Design Copilot")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(title_label)
        main_layout.addWidget(title_container)

        # Chat display area with custom styling
        self.chat_display = QTextBrowser()
        self.chat_display.setStyleSheet("""
            QTextBrowser {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 15px;
                font-size: 14px;
                line-height: 1.5;
            }
        """)
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(500)
        main_layout.addWidget(self.chat_display)

        # Input area container
        input_container = QWidget()
        input_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(10)

        # Input field with placeholder and styling
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: 2px solid #E0E0E0;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 14px;
                background-color: #F5F5F5;
            }
            QLineEdit:focus {
                border-color: #2196F3;
                background-color: white;
            }
        """)
        input_layout.addWidget(self.input_field)

        # Send button with icon
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 25px;
                font-weight: bold;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        main_layout.addWidget(input_container)

        # Control buttons container
        control_container = QWidget()
        control_layout = QHBoxLayout(control_container)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(10)

        # Back button (create first so it's on the left)
        self.back_button = QPushButton("Back")
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QPushButton:pressed {
                background-color: #424242;
            }
        """)
        self.back_button.clicked.connect(self.handle_back)
        self.back_button.setVisible(False)  # Initially hidden
        control_layout.addWidget(self.back_button)

        # Continue button
        self.continue_button = QPushButton("Continue")
        self.continue_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:pressed {
                background-color: #1B5E20;
            }
        """)
        self.continue_button.clicked.connect(self.handle_continue)
        self.continue_button.setVisible(False)  # Initially hidden
        control_layout.addWidget(self.continue_button)

        # Add Export CSV button to control container
        self.export_csv_button = QPushButton("Export Graph to CSV")
        self.export_csv_button.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:pressed {
                background-color: #4A148C;
            }
        """)
        self.export_csv_button.clicked.connect(self.export_graph_to_csv)
        self.export_csv_button.setVisible(False)  # Initially hidden
        control_layout.addWidget(self.export_csv_button)

        main_layout.addWidget(control_container)

        # Initialize other properties
        self.phases = {
            "concept": [],
            "functions": [],
            "attributes": [],
            "graph": [],
            "criticism": [],
        }
        self.current_phase = "concept"
        self.design_data = {}
        self.tree_data = {}

        self.phase_questions = {
            "concept": "What is your main design concept or idea?",
            "functions": "What functions or spaces does your building include?",
            "attributes": "What are the key attributes or requirements you would like to add?",
            "graph": "A graph will be shown. You can interact with the graph to create a different layout.",
            "criticism": "Would you like me to offer some advice about your design?"
        }

        # Set window size and show
        self.setGeometry(200, 200, 1000, 800)
        
        # Initialize button states
        self.update_phase_buttons()
        self.show_phase_question()

    def show_phase_question(self):
        question = self.phase_questions.get(self.current_phase)
        if question:
            assistant_html = f"""
            <div style="margin: 10px 0;">
                <div style="
                    background-color: #F5F5F5;
                    color: #212121;
                    padding: 12px 20px;
                    border-radius: 15px;
                    border-top-left-radius: 5px;
                    margin-right: 20%;
                    margin-left: 0;
                    display: inline-block;
                    max-width: 70%;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                    font-size: 14px;
                    line-height: 1.5;
                ">
                    {question}
                </div>
            </div>
            """
            self.chat_display.append(assistant_html)

    def send_message(self):
        message = self.input_field.text().strip()
        if not message:
            return

        # Clear input field
        self.input_field.clear()

        # Add user message to chat with styling
        user_html = f"""
        <div style="margin: 10px 0;">
            <div style="
                background-color: #E3F2FD;
                color: #1565C0;
                padding: 12px 20px;
                border-radius: 15px;
                border-top-right-radius: 5px;
                margin-left: 20%;
                margin-right: 0;
                display: inline-block;
                max-width: 70%;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                font-size: 14px;
                line-height: 1.5;
            ">
                {message}
            </div>
        </div>
        """
        self.chat_display.append(user_html)

        try:
            if self.current_phase == "concept":
                # Add plot area to the message
                plot_area = self.get_plot_area()
                message = f"{message}. Make sure the plot area is {plot_area['area']} m²."
            
            # Add message to current phase
            self.phases[self.current_phase].append({"role": "user", "content": message})

            # Process message based on current phase
            if self.current_phase == "concept":
                assistant_message = generate_concept_with_conversation(self.phases[self.current_phase])
                self.concept = assistant_message
            elif self.current_phase == "functions":
                assistant_message = extract_external_functions(self.phases[self.current_phase])
                json_llm_response = extract_json(assistant_message)
                self.extracted_functions = json_llm_response["external_functions"]
                self.set_extracted_functions()
                assistant_message = f"Your requirements have been saved as follows: {json_llm_response}<br>Does this look good? If so, press continue."
            elif self.current_phase == "attributes":
                assistant_message = extract_attributes_with_conversation(self.phases[self.current_phase], self.concept)
                json_llm_response = extract_json(assistant_message)
                self.attributes = json_llm_response
                assistant_message = f"I have added your requirements to the total list of attributes. {json_llm_response}Is this okay? If so, press continue."
                
                # Send geometry and tree data to server
                self.geometry_data()
                self.get_tree_data()
                
                # Post geometry data to server with proper headers
                headers = {
                    'Content-Type': 'application/json'
                }
                geometry_data_response = requests.post(
                    "http://127.0.0.1:5000/geometry_data",
                    json={"geometry_data": self.design_data},
                    headers=headers
                )
                
                if geometry_data_response.status_code == 200:
                    func_data = geometry_data_response.json()
                    self.chat_display.append(f"""
                    <div style="margin: 10px 0;">
                        <div style="
                            background-color: #E8F5E9;
                            color: #2E7D32;
                            padding: 12px 20px;
                            border-radius: 15px;
                            margin: 0 20%;
                            display: inline-block;
                            max-width: 60%;
                            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                            font-size: 14px;
                            font-style: italic;
                        ">
                            Geometry data sent successfully to server. Response: {func_data}
                        </div>
                    </div>
                    """)
                else:
                    raise Exception(f"Server returned status code {geometry_data_response.status_code}")
                
            elif self.current_phase == "criticism":
                assistant_message = criticize_courtyard_graph(self.phases[self.current_phase])
                self.attributes = assistant_message

            # Add assistant message to chat with styling
            assistant_html = f"""
            <div style="margin: 10px 0;">
                <div style="
                    background-color: #F5F5F5;
                    color: #212121;
                    padding: 12px 20px;
                    border-radius: 15px;
                    border-top-left-radius: 5px;
                    margin-right: 20%;
                    margin-left: 0;
                    display: inline-block;
                    max-width: 70%;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                    font-size: 14px;
                    line-height: 1.5;
                ">
                    {assistant_message}
                </div>
            </div>
            """
            self.chat_display.append(assistant_html)

            # Add assistant message to current phase
            self.phases[self.current_phase].append({"role": "assistant", "content": assistant_message})

            # Show continue button if needed
            if self.current_phase in ["functions", "attributes"]:
                self.continue_button.setVisible(True)

        except Exception as e:
            error_html = f"""
            <div style="margin: 10px 0;">
                <div style="
                    background-color: #FFEBEE;
                    color: #C62828;
                    padding: 12px 20px;
                    border-radius: 15px;
                    margin: 0 20%;
                    display: inline-block;
                    max-width: 60%;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                    font-size: 14px;
                ">
                    Error: {str(e)}
                </div>
            </div>
            """
            self.chat_display.append(error_html)

        # Scroll to bottom
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def handle_continue(self):
        phases = list(self.phases.keys())
        current_index = list(phases).index(self.current_phase)
        should_show_graph = self.current_phase == "attributes"
        if current_index < len(phases) - 1:
            self.current_phase = phases[current_index + 1]
            self.chat_display.append(f"<b>Phase changed to:</b> {self.current_phase}")
            self.continue_button.setVisible(False)
            self.show_phase_question()
            if self.current_phase == 'graph':
                self.graph()
                self.export_csv_button.setVisible(True)  # Show export button when in graph phase
                
        else:
            self.update_phase_buttons()

    def update_phase_buttons(self):
        phases = list(self.phases.keys())
        current_index = phases.index(self.current_phase)
        
        # Show "Back" if not at the first phase
        self.back_button.setVisible(current_index > 0)
        
        # Show "Continue" if not at the last phase
        self.continue_button.setVisible(current_index < len(phases) - 1)
        
        # Force update the layout
        self.back_button.parent().updateGeometry()
        self.continue_button.parent().updateGeometry()

    def handle_back(self):
        phases = list(self.phases.keys())
        current_index = phases.index(self.current_phase)
        if current_index > 0:
            # Clear the chat display
            self.chat_display.clear()
            
            # Go back to previous phase
            self.current_phase = phases[current_index - 1]
            
            # Hide export button if not in graph phase
            self.export_csv_button.setVisible(self.current_phase == 'graph')
            
            # Show phase change message
            phase_change_html = f"""
            <div style="margin: 10px 0;">
                <div style="
                    background-color: #FFF3E0;
                    color: #E65100;
                    padding: 12px 20px;
                    border-radius: 15px;
                    margin: 0 20%;
                    display: inline-block;
                    max-width: 60%;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                    font-size: 14px;
                    font-weight: bold;
                ">
                    Returned to phase: {self.current_phase}
                </div>
            </div>
            """
            self.chat_display.append(phase_change_html)
            
            # Show the phase question
            self.show_phase_question()
            
            # Update button visibility
            self.update_phase_buttons()
            
            # If we're going back from graph phase, close the graph window
            if phases[current_index] == 'graph' and hasattr(self, 'graph_window'):
                self.graph_window.close()
                delattr(self, 'graph_window')

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
            print("Extracted tree placement:", tree_placement)
            PWR = extract_json(extract_plant_water_requirement(self.concept, self.attributes, tree_placement))
            print("Extracted PWR:", PWR)

            self.tree_data = {
                "tree_placement": tree_placement["tree_placement"],
                "PWR": PWR["pwr"],                
            }
            print("Tree data prepared for sending:", self.tree_data)

            # Send tree data to server with proper headers
            headers = {
                'Content-Type': 'application/json'
            }
            print("Sending tree data to server:", self.tree_data)
            tree_data_response = requests.post(
                "http://127.0.0.1:5000/send_tree_data",
                json=self.tree_data,
                headers=headers
            )
            
            if tree_data_response.status_code == 200:
                response_data = tree_data_response.json()
                print("Server response:", response_data)
                self.chat_display.append(f"""
                <div style="margin: 10px 0;">
                    <div style="
                        background-color: #E8F5E9;
                        color: #2E7D32;
                        padding: 12px 20px;
                        border-radius: 15px;
                        margin: 0 20%;
                        display: inline-block;
                        max-width: 60%;
                        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                        font-size: 14px;
                        font-style: italic;
                    ">
                        Tree data sent successfully to server. Response: {response_data}
                    </div>
                </div>
                """)
            else:
                raise Exception(f"Server returned status code {tree_data_response.status_code}")

        except Exception as e:
            error_html = f"""
            <div style="margin: 10px 0;">
                <div style="
                    background-color: #FFEBEE;
                    color: #C62828;
                    padding: 12px 20px;
                    border-radius: 15px;
                    margin: 0 20%;
                    display: inline-block;
                    max-width: 60%;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                    font-size: 14px;
                ">
                    Error sending tree data: {str(e)}
                </div>
            </div>
            """
            self.chat_display.append(error_html)
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
            print("Initial graph layout:", llm_output_json)
            
            # Create and show the graph window using MainWindow from graph_gh.py
            self.graph_window = MainWindow(graph_data=llm_output_json)
            self.graph_window.show()
            
            # Send initial graph data to Grasshopper via server
            headers = {
                'Content-Type': 'application/json'
            }
            graph_response = requests.post(
                "http://127.0.0.1:5000/graph_data",
                json={"graph_data": llm_output_json},
                headers=headers
            )
            
            if graph_response.status_code == 200:
                self.chat_display.append(f"""
                <div style="margin: 10px 0;">
                    <div style="
                        background-color: #E8F5E9;
                        color: #2E7D32;
                        padding: 12px 20px;
                        border-radius: 15px;
                        margin: 0 20%;
                        display: inline-block;
                        max-width: 60%;
                        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                        font-size: 14px;
                        font-style: italic;
                    ">
                        Initial graph layout sent to Grasshopper. You can now modify the layout and use the Export button to save your changes.
                    </div>
                </div>
                """)
            else:
                raise Exception(f"Server returned status code {graph_response.status_code}")
            
        except Exception as e:
            error_html = f"""
            <div style="margin: 10px 0;">
                <div style="
                    background-color: #FFEBEE;
                    color: #C62828;
                    padding: 12px 20px;
                    border-radius: 15px;
                    margin: 0 20%;
                    display: inline-block;
                    max-width: 60%;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                    font-size: 14px;
                ">
                    Error generating or sending graph: {str(e)}
                </div>
            </div>
            """
            self.chat_display.append(error_html)
            print(f"Error generating graph: {e}")

    def get_graph_json(self):
        nodes = []
        for nid, item in self.nodes.items():
            x = item.scenePos().x()
            y = item.scenePos().y()
            if x is None or y is None:
                x = random.uniform(0, 1)
                y = random.uniform(0, 1)
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

    def export_graph_to_csv(self):
        """Export the current graph data to CSV format"""
        try:
            # Get the current graph data from the editor after user modifications
            if not hasattr(self, 'graph_window') or not self.graph_window.editor:
                raise Exception("No graph data available to export")
            
            # Get the current state of the graph from the editor
            current_graph_data = self.graph_window.editor.get_graph_data()
            if not current_graph_data:
                raise Exception("No graph data available in editor")
            
            print("Exporting current graph state:", current_graph_data)  # Debug log
            
            # Create export directory if it doesn't exist
            export_dir = os.path.expanduser("~/Downloads/courtyard_graph")
            os.makedirs(export_dir, exist_ok=True)
            
            # Export to CSV using the function from llm_calls
            nodes_csv, edges_csv = export_graph_to_csv(current_graph_data)
            
            if nodes_csv and edges_csv:
                # Save nodes CSV
                nodes_path = os.path.join(export_dir, "nodes.csv")
                with open(nodes_path, 'w') as f:
                    f.write(nodes_csv)
                
                # Save edges CSV
                edges_path = os.path.join(export_dir, "edges.csv")
                with open(edges_path, 'w') as f:
                    f.write(edges_csv)
                
                # Also save the current graph state to the server for Grasshopper
                headers = {
                    'Content-Type': 'application/json'
                }
                graph_response = requests.post(
                    "http://127.0.0.1:5000/graph_data",
                    json={"graph_data": current_graph_data},
                    headers=headers
                )
                
                if graph_response.status_code != 200:
                    raise Exception(f"Failed to update server with current graph state: {graph_response.status_code}")
                
                # Show success message
                success_html = f"""
                <div style="margin: 10px 0;">
                    <div style="
                        background-color: #E8F5E9;
                        color: #2E7D32;
                        padding: 12px 20px;
                        border-radius: 15px;
                        margin: 0 20%;
                        display: inline-block;
                        max-width: 60%;
                        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                        font-size: 14px;
                        font-style: italic;
                    ">
                        Current graph layout exported successfully:<br>
                        - Nodes: {nodes_path}<br>
                        - Edges: {edges_path}<br>
                        - Graph state updated on server for Grasshopper
                    </div>
                </div>
                """
                self.chat_display.append(success_html)
            else:
                raise Exception("Failed to generate CSV data")
                
        except Exception as e:
            error_html = f"""
            <div style="margin: 10px 0;">
                <div style="
                    background-color: #FFEBEE;
                    color: #C62828;
                    padding: 12px 20px;
                    border-radius: 15px;
                    margin: 0 20%;
                    display: inline-block;
                    max-width: 60%;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                    font-size: 14px;
                ">
                    Error exporting graph to CSV: {str(e)}
                </div>
            </div>
            """
            self.chat_display.append(error_html)
            print(f"Error exporting graph to CSV: {e}")


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
    Also saves the full JSON for Grasshopper to read.
    """
    if out_dir is None:
        out_dir = os.path.expanduser("~/Downloads")
    nodes_path = os.path.join(out_dir, "nodes.csv")
    edges_path = os.path.join(out_dir, "edges.csv")
    json_path = os.path.join(out_dir, "network_graph.json")

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

    # Write full JSON for Grasshopper
    with open(json_path, "w") as f_json:
        json.dump(graph_json, f_json, indent=2)

    print(f"✅ Nodes CSV saved to: {nodes_path}")
    print(f"✅ Edges CSV saved to: {edges_path}")
    print(f"✅ Full graph JSON saved to: {json_path}")



