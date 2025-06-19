import requests
from llm_calls import *
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QTextBrowser, QHBoxLayout,
    QTabWidget, QTextEdit, QComboBox, QMessageBox
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
                font-size: 16px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 16px;
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
                font-size: 16px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
            QTextBrowser {
                border: none;
                background-color: white;
                border-radius: 8px;
                font-size: 16px;
            }
            QTabWidget::pane {
                border: 1px solid #E0E0E0;
                background-color: white;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #F5F5F5;
                color: #666;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 16px;
            }
            QTabBar::tab:selected {
                background-color: #2196F3;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #1976D2;
                color: white;
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
        title_label = QLabel("Courtyard Design Copilot")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 30px;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(title_label)
        main_layout.addWidget(title_container)

        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Create the main chat tab
        self.create_chat_tab()
        
        # Create the graph query tab
        self.create_query_tab()

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
            "functions": "What functions or spaces does your building include?",
            "attributes": "What are the key attributes or requirements you would like to add?",
            "graph": "A graph will be shown. You can interact with the graph to create a different layout.",
            "criticism": "Would you like me to offer some advice about your design?"
        }

        # Set window size and show
        self.setGeometry(200, 200, 1200, 900)
        
        # Initialize button states
        self.update_phase_buttons()
        # Restore automatic phase question display
        self.show_phase_question()
        
        # Check server health on startup
        self.check_server_health()

        # Show LLM-powered greeting on first open
        greeting = self.llm_greeting()
        self.chat_display.append(self.create_assistant_message(greeting))

    def create_assistant_message(self, message, message_type="info"):
        """Helper function to create plain assistant message styling: black text on white background, left-aligned, larger font."""
        return f"""
        <div style='margin: 10px 0; text-align: left;'>
            <div style='background: white; color: black; padding: 10px 15px; border-radius: 8px; font-size: 24px; line-height: 1.6; display: inline-block; max-width: 70%;'>
                {message}
            </div>
        </div>
        """

    def show_phase_question(self):
        question = self.phase_questions.get(self.current_phase)
        if question:
            assistant_html = self.create_assistant_message(question)
            self.chat_display.append(assistant_html)

    def send_message(self):
        message = self.input_field.text().strip()
        if not message:
            return

        # Clear input field
        self.input_field.clear()

        # Add user message to chat with enhanced styling
        user_html = f"""
        <div style='margin: 10px 0; text-align: right;'>
            <div style='background: white; color: black; padding: 10px 15px; border-radius: 8px; font-size: 24px; line-height: 1.6; display: inline-block; max-width: 70%;'>
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
                
                # Send geometry data to server with proper headers
                headers = {
                    'Content-Type': 'application/json'
                }
                geometry_data_response = requests.post(
                    "http://127.0.0.1:5000/geometry_data",
                    json={"geometry_data": self.design_data},
                    headers=headers,
                    timeout=10  # Add timeout
                )
                
                if geometry_data_response.status_code == 200:
                    func_data = geometry_data_response.json()
                    self.chat_display.append(self.create_assistant_message(
                        f"Geometry data sent successfully to server. Response: {func_data}", 
                        "success"
                    ))
                else:
                    raise Exception(f"Server returned status code {geometry_data_response.status_code}")
                    
            elif self.current_phase == "criticism":
                assistant_message = criticize_courtyard_graph(self.phases[self.current_phase])
                self.attributes = assistant_message

            # Add assistant message to chat with styling
            assistant_html = self.create_assistant_message(assistant_message)
            self.chat_display.append(assistant_html)

            # Add assistant message to current phase
            self.phases[self.current_phase].append({"role": "assistant", "content": assistant_message})

            # Show continue button if needed
            if self.current_phase in ["functions", "attributes"]:
                self.continue_button.setVisible(True)

        except Exception as e:
            error_html = self.create_assistant_message(f"Error: {str(e)}", "error")
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
            # Remove phase change message but keep phase question
            # self.chat_display.append(f"<b>Phase changed to:</b> {self.current_phase}")
            self.continue_button.setVisible(False)
            # Restore automatic phase question display
            self.show_phase_question()
            if self.current_phase == 'graph':
                self.graph()
                self.export_csv_button.setVisible(True)  # Show export button when in graph phase
                self.continue_button.setVisible(True)    # Show continue button in graph phase
            elif self.current_phase == 'criticism':
                self.export_csv_button.setVisible(False) # Hide export button in criticism phase
                self.continue_button.setVisible(False)   # Hide continue button in criticism phase
            else:
                self.export_csv_button.setVisible(False)
                self.continue_button.setVisible(True)
        else:
            self.update_phase_buttons()

    def update_phase_buttons(self):
        phases = list(self.phases.keys())
        current_index = phases.index(self.current_phase)
        # Show "Back" if not at the first phase
        self.back_button.setVisible(current_index > 0)
        # Show "Continue" if not at the last phase
        if self.current_phase == 'graph':
            self.continue_button.setVisible(True)
            self.export_csv_button.setVisible(True)
        else:
            self.continue_button.setVisible(current_index < len(phases) - 1)
            self.export_csv_button.setVisible(False)
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
            # Show/hide export and continue buttons appropriately
            self.update_phase_buttons()
            # Remove phase change message but keep phase question
            # phase_change_html = self.create_assistant_message(f"Returned to phase: {self.current_phase}", "info")
            # self.chat_display.append(phase_change_html)
            # Restore automatic phase question display
            self.show_phase_question()
            # If we're going back from graph phase, close the graph window
            if phases[current_index] == 'graph' and hasattr(self, 'graph_window'):
                self.graph_window.close()
                delattr(self, 'graph_window')

    def get_plot_area(self):
        try:
            plot_area_response = requests.get("http://127.0.0.1:5000/plot_area", timeout=5)
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
            
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error fetching plot area: {e}")
            # Return default values if there's a connection error
            return {
                "area": "400",
                "width": "20",
                "length": "20"
            }
        except requests.exceptions.Timeout as e:
            print(f"Timeout error fetching plot area: {e}")
            # Return default values if there's a timeout
            return {
                "area": "400",
                "width": "20",
                "length": "20"
            }
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
                json={"functions": self.extracted_functions},
                timeout=10
            )
            if response.status_code != 200:
                print(f"Warning: Failed to set external functions on server: {response.status_code}")
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error setting external functions: {e}")
            # Continue without failing the entire process
        except requests.exceptions.Timeout as e:
            print(f"Timeout error setting external functions: {e}")
            # Continue without failing the entire process
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

            # Send tree data to server with proper headers and error handling
            headers = {
                'Content-Type': 'application/json'
            }
            print("Sending tree data to server:", self.tree_data)
            
            try:
                tree_data_response = requests.post(
                    "http://127.0.0.1:5000/send_tree_data",
                    json=self.tree_data,
                    headers=headers,
                    timeout=10  # Add timeout
                )
                
                if tree_data_response.status_code == 200:
                    response_data = tree_data_response.json()
                    print("Server response:", response_data)
                    self.chat_display.append(self.create_assistant_message(
                        f"Tree data sent successfully to server. Response: {response_data}", 
                        "success"
                    ))
                else:
                    raise Exception(f"Server returned status code {tree_data_response.status_code}")
                    
            except requests.exceptions.ConnectionError as e:
                # Handle connection errors gracefully
                print(f"Connection error sending tree data: {e}")
                self.chat_display.append(self.create_assistant_message(
                    f"⚠️ Server connection failed. Tree data saved locally but not sent to Grasshopper.\nError: {str(e)}\nYou can continue with the design process.",
                    "warning"
                ))
                return  # Continue without failing the entire process
                
            except requests.exceptions.Timeout as e:
                print(f"Timeout error sending tree data: {e}")
                self.chat_display.append(self.create_assistant_message(
                    f"⚠️ Server timeout. Tree data saved locally but not sent to Grasshopper.\nYou can continue with the design process.",
                    "warning"
                ))
                return  # Continue without failing the entire process

        except Exception as e:
            error_html = self.create_assistant_message(
                f"Error processing tree data: {str(e)}\nYou can continue with the design process.",
                "error"
            )
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
                headers=headers,
                timeout=10  # Add timeout
            )
            
            if graph_response.status_code == 200:
                self.chat_display.append(self.create_assistant_message(
                    "Initial graph layout sent to Grasshopper. You can now modify the layout and use the Export button to save your changes.",
                    "success"
                ))
            else:
                raise Exception(f"Server returned status code {graph_response.status_code}")
            
        except requests.exceptions.ConnectionError as e:
            # Handle connection errors gracefully
            print(f"Connection error sending graph data: {e}")
            self.chat_display.append(self.create_assistant_message(
                f"⚠️ Server connection failed. Graph visualization opened but data not sent to Grasshopper.\nError: {str(e)}\nYou can still modify the graph and export to CSV.",
                "warning"
            ))
            return  # Continue without failing the entire process
            
        except requests.exceptions.Timeout as e:
            print(f"Timeout error sending graph data: {e}")
            self.chat_display.append(self.create_assistant_message(
                "⚠️ Server timeout. Graph visualization opened but data not sent to Grasshopper.\nYou can still modify the graph and export to CSV.",
                "warning"
            ))
            return  # Continue without failing the entire process

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

    def export_graph_to_csv_button_handler(self):
        """Handler for the Export Graph to CSV button in the graph phase."""
        try:
            # Get the current graph data from the editor after user modifications
            if not hasattr(self, 'graph_window') or not self.graph_window.editor:
                raise Exception("No graph data available to export")
            # Get the current state of the graph from the editor
            current_graph_data = self.graph_window.editor.get_graph_data()
            if not current_graph_data:
                raise Exception("No graph data available in editor")
            print("Exporting current graph state:", current_graph_data)  # Debug log
            # Export to CSV using the standalone function
            export_graph_to_csv(current_graph_data)
            # Show success message
            success_html = self.create_assistant_message(
                "Current graph layout exported successfully.\n- Nodes and edges CSVs saved in Downloads/courtyard_graph\n- Graph state updated for Grasshopper",
                "success"
            )
            self.chat_display.append(success_html)
        except Exception as e:
            error_html = self.create_assistant_message(
                f"Error exporting graph to CSV: {str(e)}",
                "error"
            )
            self.chat_display.append(error_html)
            print(f"Error exporting graph to CSV: {e}")

    def create_chat_tab(self):
        """Create the main chat interface tab"""
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(15, 15, 15, 15)
        chat_layout.setSpacing(15)

        # Chat display area with custom styling
        self.chat_display = QTextBrowser()
        self.chat_display.setStyleSheet("""
            QTextBrowser {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 15px;
                font-size: 22px;
                line-height: 1.6;
            }
        """)
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(400)
        chat_layout.addWidget(self.chat_display)

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
                font-size: 22px;
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
                font-size: 22px;
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

        chat_layout.addWidget(input_container)

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
                font-size: 22px;
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
                font-size: 22px;
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
                font-size: 22px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:pressed {
                background-color: #4A148C;
            }
        """)
        self.export_csv_button.clicked.connect(self.export_graph_to_csv_button_handler)
        self.export_csv_button.setVisible(False)  # Initially hidden
        control_layout.addWidget(self.export_csv_button)

        chat_layout.addWidget(control_container)

        # Add the chat tab to the tab widget
        self.tab_widget.addTab(chat_widget, "Design Assistant")

    def create_query_tab(self):
        """Create the graph query interface tab"""
        query_widget = QWidget()
        query_layout = QVBoxLayout(query_widget)
        query_layout.setContentsMargins(15, 15, 15, 15)
        query_layout.setSpacing(15)

        # Status and connection section
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(10)

        # Connection status label
        self.connection_status = QLabel("Not Connected")
        self.connection_status.setStyleSheet("""
            QLabel {
                color: #F44336;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 4px;
                background-color: #FFEBEE;
            }
        """)
        status_layout.addWidget(self.connection_status)

        # Load Data button
        self.load_data_button = QPushButton("Load Graph Data")
        self.load_data_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self.load_data_button.clicked.connect(self.load_graph_data)
        status_layout.addWidget(self.load_data_button)

        # Sample questions dropdown
        self.sample_questions_combo = QComboBox()
        self.sample_questions_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
                min-width: 200px;
                font-size: 16px;
            }
            QComboBox:focus {
                border-color: #2196F3;
            }
        """)
        self.sample_questions_combo.addItem("Select a sample question...")
        self.sample_questions_combo.currentTextChanged.connect(self.on_sample_question_selected)
        status_layout.addWidget(self.sample_questions_combo)

        query_layout.addWidget(status_container)

        # Query input section
        query_input_container = QWidget()
        query_input_layout = QHBoxLayout(query_input_container)
        query_input_layout.setContentsMargins(0, 0, 0, 0)
        query_input_layout.setSpacing(10)

        # Query input field
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Ask a question about your graph data...")
        self.query_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #E0E0E0;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 22px;
                background-color: #F5F5F5;
            }
            QLineEdit:focus {
                border-color: #2196F3;
                background-color: white;
            }
        """)
        query_input_layout.addWidget(self.query_input)

        # Ask button
        self.ask_button = QPushButton("Ask")
        self.ask_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 25px;
                font-weight: bold;
                font-size: 22px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.ask_button.clicked.connect(self.ask_graph_question)
        query_input_layout.addWidget(self.ask_button)

        query_layout.addWidget(query_input_container)

        # Results display
        self.query_results = QTextBrowser()
        self.query_results.setStyleSheet("""
            QTextBrowser {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 15px;
                font-size: 22px;
                line-height: 1.6;
            }
        """)
        self.query_results.setReadOnly(True)
        self.query_results.setMinimumHeight(400)
        query_layout.addWidget(self.query_results)

        # Add the query tab to the tab widget
        self.tab_widget.addTab(query_widget, "Graph Query")

    def load_graph_data(self):
        """Load CSV data into Neo4j and initialize the query engine"""
        try:
            # Call the server endpoint to load data
            response = requests.post("http://127.0.0.1:5000/graph_query/load_data")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.connection_status.setText("Connected")
                    self.connection_status.setStyleSheet("""
                        QLabel {
                            color: #4CAF50;
                            font-weight: bold;
                            padding: 5px 10px;
                            border-radius: 4px;
                            background-color: #E8F5E9;
                        }
                    """)
                    
                    # Update sample questions
                    self.update_sample_questions()
                    
                    self.query_results.append("✅ Graph data loaded successfully!")
                    self.query_results.append("You can now ask questions about your graph data.")
                else:
                    self.query_results.append(f"❌ {result.get('error', 'Unknown error')}")
            else:
                self.query_results.append(f"❌ Server error: {response.status_code}")
                
        except Exception as e:
            self.query_results.append(f"❌ Error loading graph data: {str(e)}")
    
    def update_sample_questions(self):
        """Update the sample questions dropdown based on the loaded graph"""
        try:
            # Get sample questions from server
            response = requests.get("http://127.0.0.1:5000/graph_query/sample_questions")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    # Clear existing items
                    self.sample_questions_combo.clear()
                    self.sample_questions_combo.addItem("Select a sample question...")
                    
                    # Add sample questions to dropdown
                    for question in result.get("questions", []):
                        self.sample_questions_combo.addItem(question)
                else:
                    print(f"Error getting sample questions: {result.get('error')}")
            else:
                print(f"Server error getting sample questions: {response.status_code}")
                
        except Exception as e:
            print(f"Error updating sample questions: {e}")
    
    def on_sample_question_selected(self, question):
        """Handle selection of a sample question"""
        if question and question != "Select a sample question...":
            self.query_input.setText(question)
    
    def ask_graph_question(self):
        """Ask a question about the graph data"""
        question = self.query_input.text().strip()
        if not question:
            return
        
        try:
            # Clear input
            self.query_input.clear()
            
            # Add user question to results
            self.query_results.append(f"<b>Question:</b> {question}")
            
            # Send question to server
            response = requests.post(
                "http://127.0.0.1:5000/graph_query/ask",
                json={"question": question}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    # Display results
                    cypher_query = result.get("cypher_query")
                    raw_data = result.get("raw_data")
                    human_answer = result.get("human_answer")
                    
                    if cypher_query:
                        self.query_results.append(f"<b>Generated Cypher Query:</b>")
                        self.query_results.append(f"<code>{cypher_query}</code>")
                    
                    if raw_data:
                        self.query_results.append(f"<b>Raw Results:</b>")
                        self.query_results.append(f"<pre>{json.dumps(raw_data, indent=2)}</pre>")
                    
                    if human_answer:
                        self.query_results.append(f"<b>Answer:</b>")
                        self.query_results.append(human_answer)
                else:
                    self.query_results.append(f"❌ {result.get('error', 'Unknown error')}")
            else:
                self.query_results.append(f"❌ Server error: {response.status_code}")
            
            self.query_results.append("<hr>")
            
        except Exception as e:
            self.query_results.append(f"❌ Error processing question: {str(e)}")
    
    def closeEvent(self, event):
        """Handle application close event"""
        # No need to close query_engine as it's managed by the server
        event.accept()

    def check_server_health(self):
        """Check if the server is running and accessible"""
        try:
            response = requests.get("http://127.0.0.1:5000/plot_area", timeout=3)
            if response.status_code == 200:
                print("✅ Server is running and accessible")
            else:
                print(f"⚠️ Server responded with status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("❌ Server is not running or not accessible")
            self.chat_display.append(self.create_assistant_message(
                "⚠️ Server connection check failed. Some features may not work properly.\nMake sure gh_server.py is running.",
                "warning"
            ))
        except requests.exceptions.Timeout:
            print("⚠️ Server connection timeout")
        except Exception as e:
            print(f"⚠️ Server health check error: {e}")

    def llm_greeting(self):
        """Call the LLM to generate a friendly greeting and ask what the user wants to see in the courtyard design."""
        try:
            from llm_calls import client, completion_model
            response = client.chat.completions.create(
                model=completion_model,
                messages=[
                    {"role": "system", "content": "You are a friendly, helpful courtyard design assistant. Greet the user, introduce yourself as their design copilot, and ask what they would like to see or achieve in their courtyard design. Keep it short and welcoming."}
                ]
            )
            greeting = response.choices[0].message.content
        except Exception as e:
            greeting = "Hello! I'm your courtyard design copilot. What would you like to see in your courtyard design?"
        return greeting

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
        out_dir = os.path.expanduser("~/Downloads/courtyard_graph")
    os.makedirs(out_dir, exist_ok=True)
    nodes_path = os.path.join(out_dir, "nodes.csv")
    edges_path = os.path.join(out_dir, "edges.csv")
    json_path = os.path.join(out_dir, "network_graph.json")

    # Write nodes
    with open(nodes_path, "w", newline='') as f_nodes:
        if not graph_json["nodes"]:
            return
        # Collect all possible keys from all nodes
        fieldnames = set()
        for node in graph_json["nodes"]:
            fieldnames.update(node.keys())
        fieldnames = list(fieldnames)
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

    # Build a lookup for node positions
    node_pos = {n["id"]: (float(n.get("x", 0)), float(n.get("y", 0))) for n in graph_json["nodes"] if "x" in n and "y" in n}

    # Write edges with distance
    with open(edges_path, "w", newline='') as f_edges:
        writer = csv.DictWriter(f_edges, fieldnames=["source", "target", "distance"])
        writer.writeheader()
        for edge in graph_json["links"]:
            source = edge["source"]
            target = edge["target"]
            # Calculate Euclidean distance if possible
            dist = ""
            if source in node_pos and target in node_pos:
                x1, y1 = node_pos[source]
                x2, y2 = node_pos[target]
                dist = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                dist = round(dist, 3)
            writer.writerow({"source": source, "target": target, "distance": dist})

    # Write full JSON for Grasshopper
    with open(json_path, "w") as f_json:
        json.dump(graph_json, f_json, indent=2)

    print(f"✅ Nodes CSV saved to: {nodes_path}")
    print(f"✅ Edges CSV saved to: {edges_path}")
    print(f"✅ Full graph JSON saved to: {json_path}")


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # Create the application
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = FlaskClientChatUI()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec_())



