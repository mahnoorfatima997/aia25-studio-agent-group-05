import requests
from llm_calls import *
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QTextBrowser, QHBoxLayout,
    QTabWidget, QTextEdit, QComboBox, QMessageBox, QApplication
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QObject
import re
from graph_gh import GraphEditor, MainWindow, QApplication
import csv
import os
import random
import json
import threading
import time
import base64
from datetime import datetime
from plan_export import export_courtyard_plan, PlanExportTab

class ImageGenerationSignals(QObject):
    """Signals for safely updating UI from background threads"""
    status_update = pyqtSignal(str)
    image_update = pyqtSignal(str)
    error_update = pyqtSignal(str)
    plan_image_update = pyqtSignal(str)
    plan_error_update = pyqtSignal(str)

class FlaskClientChatUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Courtyard Design Copilot")
        
        # Initialize signals for image generation
        self.image_signals = ImageGenerationSignals()
        self.image_signals.status_update.connect(self.update_image_status)
        self.image_signals.image_update.connect(self.update_image_display)
        self.image_signals.error_update.connect(self.update_image_error)
        self.image_signals.plan_image_update.connect(self.update_plan_image_display)
        self.image_signals.plan_error_update.connect(self.update_plan_image_error)
        
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

        # Create the image generation tab
        self.create_image_generation_tab()

        # Create the plan export tab using the PlanExportTab class
        self.plan_export_tab = PlanExportTab(self.tab_widget, self)

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
        self.setGeometry(200, 200, 1600, 1200)
        
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
                # Process the data first
                llm_response = extract_external_functions(self.phases[self.current_phase])
                json_llm_response = extract_json(llm_response)
                self.extracted_functions = json_llm_response["external_functions"]
                self.set_extracted_functions()
                # Generate human-like response
                assistant_message = generate_human_functions_response(self.extracted_functions)
            elif self.current_phase == "attributes":
                # Process the data first
                llm_response = extract_attributes_with_conversation(self.phases[self.current_phase], self.concept)
                json_llm_response = extract_json(llm_response)
                self.attributes = json_llm_response
                # Generate human-like response
                assistant_message = generate_human_attributes_response(self.attributes)
                
                # Send geometry and tree data to server
                self.geometry_data()
                self.get_tree_data()
                # Update plan summary in Plan Export tab
                if hasattr(self, 'plan_export_tab'):
                    self.plan_export_tab.update_plan_summary()
                
                # Send geometry data to server with proper headers
                headers = {
                    'Content-Type': 'application/json'
                }
                geometry_data_response = requests.post(
                    "http://127.0.0.1:5000/geometry_data",
                    json={"geometry_data": self.design_data},
                    headers=headers,
                    timeout=10  
                )
                
                if geometry_data_response.status_code == 200:
                    func_data = geometry_data_response.json()
                    self.chat_display.append(self.create_assistant_message(
                        "Excellent! I've successfully sent all your design data to the visualization system. Your courtyard concept is now ready to be brought to life in the next phase!", 
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

            # Update advisor tip
            self.update_advisor_tip()

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
            
            # Update advisor tip for the new phase
            self.update_advisor_tip()
            
            if self.current_phase == 'graph':
                self.graph()
                self.export_csv_button.setVisible(True)  # Show export button when in graph phase
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
            
            # Update advisor tip for the previous phase
            self.update_advisor_tip()
            
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

    def send_external_function_placement(self, placement_data):
        """
        Send external function placement data to the server.
        This data will be retrieved by Grasshopper via GET request.
        """
        try:
            headers = {
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                "http://127.0.0.1:5000/external_function_placement",
                json={"external_function_placement": placement_data},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("External function placement data sent successfully to server")
                return True
            else:
                print(f"Warning: Failed to send external function placement data: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error sending external function placement data: {e}")
            return False
        except requests.exceptions.Timeout as e:
            print(f"Timeout error sending external function placement data: {e}")
            return False
        except Exception as e:
            print(f"Error sending external function placement data: {e}")
            return False

    def geometry_data(self):
        """
        Aggregate all relevant data from all phases, calculating and using bounded positions.
        Creates a rectangular boundary box with external functions as anchor points at corners.
        """
        try:
            # Standard data extraction
            spaces = extract_json(extract_spaces(self.concept, self.extracted_functions, self.attributes))
            links = extract_json(extract_links(self.concept, self.extracted_functions))
            positions = extract_json(extract_positions(self.concept, self.extracted_functions))
            cardinal_directions = extract_json(extract_cardinal_directions(self.concept, self.extracted_functions, self.attributes))
            weights = extract_json(extract_weights(self.concept, self.extracted_functions, self.attributes))
            anchors = extract_json(extract_anchors(self.concept, self.extracted_functions, self.attributes))
            
            # --- Enhanced Rectangular Boundary Box System ---
            
            # 1. Fetch corner data from Grasshopper via the server
            corners = []
            calculated_placements = {}
            final_pos = {}
            boundary_box = {}

            try:
                placement_response = requests.get("http://127.0.0.1:5000/external_function_placement", timeout=5)
                if placement_response.status_code == 200:
                    placement_data = placement_response.json()
                    data_from_gh = placement_data.get("external_function_placement", {})
                    corners = data_from_gh.get("coordinates", [])
                    print(f"Received {len(corners)} coordinates from Grasshopper.")
                else:
                    print("⚠️ Could not fetch data from Grasshopper. Proceeding without bounded placement.")
            except Exception as e:
                print(f"⚠️ Error fetching GH data: {e}. Proceeding without bounded placement.")

            # 2. If we have corners, create a proper rectangular boundary box
            if corners and len(corners) >= 4:
                # --- Enhanced boundary box calculation ---

                # a. Calculate the bounding box limits
                min_x = min(p[0] for p in corners)
                max_x = max(p[0] for p in corners)
                min_y = min(p[1] for p in corners)
                max_y = max(p[1] for p in corners)

                # Store boundary box information
                boundary_box = {
                    "min_x": min_x,
                    "max_x": max_x,
                    "min_y": min_y,
                    "max_y": max_y,
                    "width": max_x - min_x,
                    "height": max_y - min_y,
                    "center": [(min_x + max_x) / 2, (min_y + max_y) / 2]
                }

                print(f"Created boundary box: {boundary_box}")

                # b. Find the actual corner points closest to ideal corners
                def find_closest_point(ideal_coord, point_list):
                    ideal_x, ideal_y = ideal_coord
                    return min(point_list, key=lambda p: ((p[0] - ideal_x)**2 + (p[1] - ideal_y)**2))

                # Define ideal corner positions
                ideal_corners = {
                    'NW': (min_x, max_y),  # Northwest corner
                    'NE': (max_x, max_y),  # Northeast corner
                    'SW': (min_x, min_y),  # Southwest corner
                    'SE': (max_x, min_y)   # Southeast corner
                }

                # Find actual corner points closest to ideal positions
                actual_corner_points = {
                    'NW': find_closest_point(ideal_corners['NW'], corners),
                    'NE': find_closest_point(ideal_corners['NE'], corners),
                    'SW': find_closest_point(ideal_corners['SW'], corners),
                    'SE': find_closest_point(ideal_corners['SE'], corners)
                }

                print(f"Actual corner points: {actual_corner_points}")

                # c. Enhanced corner assignment with priority system
                direction_to_corner_preference = {
                    'N': ['NE', 'NW'],      # North-facing functions prefer east or west corners
                    'E': ['SE', 'NE'],      # East-facing functions prefer south or north corners
                    'S': ['SW', 'SE'],      # South-facing functions prefer west or east corners
                    'W': ['NW', 'SW']       # West-facing functions prefer north or south corners
                }

                # d. Assign external functions to corners as anchor points
                used_corners = set()
                external_anchors = {}
                
                for name, direction in self.extracted_functions.items():
                    direction_key = direction.upper()[0] if direction else 'N'
                    
                    assigned_corner_key = None
                    
                    # Try to assign to preferred corner based on direction
                    if direction_key in direction_to_corner_preference:
                        for corner_key in direction_to_corner_preference[direction_key]:
                            if corner_key not in used_corners:
                                assigned_corner_key = corner_key
                                break
                    
                    # If no preferred corner available, pick any unused corner
                    if not assigned_corner_key:
                        available_corners = set(actual_corner_points.keys()) - used_corners
                        if available_corners:
                            assigned_corner_key = available_corners.pop()

                    if assigned_corner_key:
                        point = actual_corner_points[assigned_corner_key]
                        calculated_placements[name] = [point[0], point[1]]
                        external_anchors[name] = {
                            "corner": assigned_corner_key,
                            "position": [point[0], point[1]],
                            "direction": direction
                        }
                        used_corners.add(assigned_corner_key)
                        print(f"Assigned {name} to {assigned_corner_key} corner at {point}")
                    else:
                        print(f"Warning: No available corner for function '{name}'. All corners are assigned.")
                
                print(f"External anchors: {external_anchors}")
                print("Calculated fixed placements for external functions:", calculated_placements)
                
                # Call the enhanced extract_pos function with boundary information
                pos_response = extract_pos(self.concept, self.extracted_functions, corners, calculated_placements)
                final_pos = extract_json(pos_response)

            else:
                # Fallback to unbounded position generation
                print("Falling back to unbounded position generation.")
                pos_response = extract_pos(self.concept, self.extracted_functions, [], {})
                final_pos = extract_json(pos_response)
                boundary_box = {}

            # Store enhanced design data with boundary information
            self.design_data = {
                "spaces": spaces["spaces"],
                "links": links["links"],
                "positions": positions["positions"],
                "cardinal_directions": cardinal_directions["cardinal_directions"],
                "weights": weights["weights"],
                "anchors": anchors["anchors"],
                "external_functions": self.extracted_functions,
                "pos": final_pos.get("pos", {}),
                "boundary_box": boundary_box,
                "external_anchors": external_anchors if 'external_anchors' in locals() else {}
            }
            print("Enhanced design data aggregated with boundary box:", self.design_data)

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
                    # Removed the success message - tree data generation happens silently
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

        # Update plan summary in Plan Export tab
        if hasattr(self, 'plan_export_tab'):
            self.plan_export_tab.update_plan_summary()

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
            
            # Add boundary box data to the graph if available
            if "boundary_box" in self.design_data and self.design_data["boundary_box"]:
                llm_output_json["boundary_box"] = self.design_data["boundary_box"]
                print("Added boundary box to graph data:", self.design_data["boundary_box"])
            
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
                    "Fantastic! I've created a visual layout of your courtyard and sent it to the 3D modeling system. You can now see how all your spaces work together and make adjustments to perfect the flow. Use the Export button when you're happy with the layout!",
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

        # Advisor's Corner
        advisor_label = QLabel("💡 Advisor's Corner:")
        advisor_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        chat_layout.addWidget(advisor_label)

        self.advisor_panel = QTextEdit()
        self.advisor_panel.setReadOnly(True)
        self.advisor_panel.setPlaceholderText("Helpful tips will appear here as you design...")
        self.advisor_panel.setFixedHeight(80) # A compact height for 1-2 sentences
        self.advisor_panel.setStyleSheet("""
            QTextEdit {
                background-color: #FFFDE7; /* A warm, parchment-like yellow */
                border: 1px solid #FFF9C4;
                border-radius: 8px;
                padding: 10px;
                font-size: 17px;
                font-style: italic;
                color: #5D4037; /* A soft brown for the text */
            }
        """)
        chat_layout.addWidget(self.advisor_panel)

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

    def create_image_generation_tab(self):
        """Creates the tab for AI image generation."""
        image_gen_widget = QWidget()
        layout = QVBoxLayout(image_gen_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("AI-Powered Image Generation")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        # Description
        description = QLabel(
            "Generate 3D visualizations and plan views of your courtyard design using AI. "
            "The 3D view shows all features in realistic detail, while the plan view provides a precise top-down layout."
        )
        description.setWordWrap(True)
        description.setStyleSheet("font-size: 16px; margin-bottom: 15px;")
        layout.addWidget(description)

        # Generate Both Views Button
        self.generate_both_views_button = QPushButton("📸 Generate Both Views (3D + Plan)")
        self.generate_both_views_button.setStyleSheet("""
            QPushButton {
                background-color: #673AB7; /* A deep purple for creativity */
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
                font-weight: bold;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #512DA8;
            }
            QPushButton:pressed {
                background-color: #311B92;
            }
        """)
        self.generate_both_views_button.clicked.connect(self.handle_generate_both_views)
        layout.addWidget(self.generate_both_views_button)

        # Individual view buttons
        view_buttons_container = QWidget()
        view_buttons_layout = QHBoxLayout(view_buttons_container)
        view_buttons_layout.setContentsMargins(0, 0, 0, 0)
        view_buttons_layout.setSpacing(10)

        # 3D View Button
        self.generate_3d_button = QPushButton("🎭 Generate 3D View")
        self.generate_3d_button.setStyleSheet("""
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
        """)
        self.generate_3d_button.clicked.connect(self.handle_generate_3d_view)
        view_buttons_layout.addWidget(self.generate_3d_button)

        # Plan View Button
        self.generate_plan_button = QPushButton("📋 Generate Plan View")
        self.generate_plan_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        self.generate_plan_button.clicked.connect(self.handle_generate_plan_view)
        view_buttons_layout.addWidget(self.generate_plan_button)

        layout.addWidget(view_buttons_container)

        # Status Display
        self.image_gen_status_display = QTextBrowser()
        self.image_gen_status_display.setPlaceholderText("Status updates will appear here...")
        self.image_gen_status_display.setFixedHeight(100)
        self.image_gen_status_display.setStyleSheet("""
            QTextBrowser {
                background-color: #f0f0f0;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                font-size: 16px;
            }
        """)
        layout.addWidget(self.image_gen_status_display)

        # Image Display Area with tabs
        self.image_tab_widget = QTabWidget()
        self.image_tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E0E0E0;
                background-color: white;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #F5F5F5;
                color: #666;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #2196F3;
                color: white;
            }
        """)

        # 3D View Tab
        self.image_3d_display_label = QLabel("3D view will appear here.")
        self.image_3d_display_label.setAlignment(Qt.AlignCenter)
        self.image_3d_display_label.setMinimumHeight(600)
        self.image_3d_display_label.setMinimumWidth(800)
        self.image_3d_display_label.setStyleSheet("""
            QLabel {
                background-color: #e8e8e8;
                border: 2px dashed #cccccc;
                border-radius: 8px;
                color: #888888;
                font-size: 16px;
            }
        """)
        self.image_tab_widget.addTab(self.image_3d_display_label, "🎭 3D View")

        # Plan View Tab
        self.image_plan_display_label = QLabel("Plan view will appear here.")
        self.image_plan_display_label.setAlignment(Qt.AlignCenter)
        self.image_plan_display_label.setMinimumHeight(600)
        self.image_plan_display_label.setMinimumWidth(800)
        self.image_plan_display_label.setStyleSheet("""
            QLabel {
                background-color: #e8e8e8;
                border: 2px dashed #cccccc;
                border-radius: 8px;
                color: #888888;
                font-size: 16px;
            }
        """)
        self.image_tab_widget.addTab(self.image_plan_display_label, "📋 Plan View")

        layout.addWidget(self.image_tab_widget, 1)  # Give it stretch factor

        self.tab_widget.addTab(image_gen_widget, "🖼️ Image Generation")

    def update_image_status(self, message):
        """Update the image generation status display (called from main thread)"""
        self.image_gen_status_display.setText(message)

    def update_image_display(self, image_path):
        """Update the image display (called from main thread)"""
        try:
            pixmap = QPixmap(image_path)
            self.image_3d_display_label.setPixmap(pixmap.scaled(
                self.image_3d_display_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
        except Exception as e:
            self.image_3d_display_label.setText(f"Failed to load image: {e}")

    def update_plan_image_display(self, image_path):
        """Update the plan view image display (called from main thread)"""
        try:
            pixmap = QPixmap(image_path)
            self.image_plan_display_label.setPixmap(pixmap.scaled(
                self.image_plan_display_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
        except Exception as e:
            self.image_plan_display_label.setText(f"Failed to load image: {e}")

    def update_image_error(self, error_message):
        """Update the image display with an error (called from main thread)"""
        self.image_3d_display_label.setText(error_message)

    def update_plan_image_error(self, error_message):
        """Update the plan view image display with an error (called from main thread)"""
        self.image_plan_display_label.setText(error_message)

    def update_advisor_tip(self):
        """Fetches and displays a proactive design tip from the AI advisor."""
        try:
            # Gather the current context for the advisor
            # We can expand this with more design_data as needed for richer tips
            context_data = {
                "concept": self.concept if hasattr(self, 'concept') else "Not yet defined.",
                "functions": self.phases.get("functions", []),
                "attributes": self.phases.get("attributes", [])
            }

            # Call the new LLM function to get a tip
            tip = generate_design_tip(self.current_phase, self.concept, context_data)
            
            # Display the tip
            self.advisor_panel.setText(tip)

        except Exception as e:
            print(f"Error updating advisor tip: {e}")
            # Silently fail, as this is a non-critical feature

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

        # Send to Grasshopper button (initially hidden)
        self.send_query_to_gh_button = QPushButton("Send Query Results to Grasshopper")
        self.send_query_to_gh_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        self.send_query_to_gh_button.clicked.connect(self.send_query_results_to_grasshopper)
        self.send_query_to_gh_button.setVisible(False)  # Initially hidden
        query_layout.addWidget(self.send_query_to_gh_button)

        # Clear Results button (initially hidden)
        self.clear_results_button = QPushButton("Clear Results")
        self.clear_results_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QPushButton:pressed {
                background-color: #424242;
            }
        """)
        self.clear_results_button.clicked.connect(self.clear_query_results_and_display)
        self.clear_results_button.setVisible(False)  # Initially hidden
        query_layout.addWidget(self.clear_results_button)

        # Add the query tab to the tab widget
        self.tab_widget.addTab(query_widget, "Graph Query")

    def load_graph_data(self):
        """Load CSV data into Neo4j and initialize the query engine"""
        try:
            # Hide the send button when loading new data
            self.send_query_to_gh_button.setVisible(False)
            self.clear_results_button.setVisible(False)
            
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
                    self.query_results.append("💡 Tip: After running a query, you can send the results to Grasshopper using the 'Send Query Results to Grasshopper' button.")
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
                    
                    # Show the "Send to Grasshopper" button after successful query
                    self.send_query_to_gh_button.setVisible(True)
                    self.clear_results_button.setVisible(True)
                    
                    # Store the query results for later use
                    self.current_query_results = {
                        "question": question,
                        "cypher_query": cypher_query,
                        "raw_data": raw_data,
                        "human_answer": human_answer
                    }
                    
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
        
        # Also update the advisor tip on startup
        self.update_advisor_tip()
        
        return greeting

    def send_query_results_to_grasshopper(self):
        """Handler for the "Send Query Results to Grasshopper" button"""
        try:
            # Check if we have query results to send
            if not hasattr(self, 'current_query_results') or not self.current_query_results:
                self.query_results.append(self.create_assistant_message(
                    "❌ No query results available to send. Please run a query first.",
                    "error"
                ))
                return
            
            # Send the stored query results to the server endpoint
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Send to the query_results endpoint
            send_response = requests.post(
                "http://127.0.0.1:5000/query_results",
                json={"query_results": self.current_query_results},
                headers=headers,
                timeout=10
            )
            
            if send_response.status_code == 200:
                self.query_results.append(self.create_assistant_message(
                    "✅ Query results sent to Grasshopper successfully!\n"
                    "The results are now available for your Grasshopper model to read.\n"
                    f"Question: {self.current_query_results['question']}\n"
                    f"Results contain: {len(self.current_query_results.get('raw_data', []))} data points",
                    "success"
                ))
            else:
                raise Exception(f"Server returned status code {send_response.status_code}")
                
        except requests.exceptions.ConnectionError as e:
            self.query_results.append(self.create_assistant_message(
                f"⚠️ Server connection failed. Query results not sent to Grasshopper.\nError: {str(e)}",
                "warning"
            ))
        except requests.exceptions.Timeout as e:
            self.query_results.append(self.create_assistant_message(
                "⚠️ Server timeout. Query results not sent to Grasshopper.",
                "warning"
            ))
        except Exception as e:
            self.query_results.append(self.create_assistant_message(
                f"❌ Error sending query results to Grasshopper: {str(e)}",
                "error"
            ))

    def clear_query_results(self):
        """Clear stored query results and hide the send button"""
        if hasattr(self, 'current_query_results'):
            delattr(self, 'current_query_results')
        self.send_query_to_gh_button.setVisible(False)

    def handle_generate_both_views(self):
        """Generate both 3D and plan views using text-to-image."""
        self.image_signals.status_update.emit("🔄 Generating both 3D and plan views from design data... Please wait.")
        QApplication.processEvents()

        def _task():
            try:
                # Check if we have design data
                if not hasattr(self, 'design_data') or not self.design_data:
                    self.image_signals.status_update.emit("⚠️ No design data available. Please complete the design process first.")
                    return

                # Generate 3D view first
                self.image_signals.status_update.emit("🎭 Generating 3D view...")
                
                concept = getattr(self, 'concept', 'A beautiful courtyard design')
                attributes = getattr(self, 'attributes', {})
                tree_data = getattr(self, 'tree_data', {})
                
                from image_gen import generate_3d_view_from_text, generate_detailed_3d_courtyard_prompt
                from image_gen import generate_plan_view_from_text, generate_detailed_plan_courtyard_prompt
                
                # Generate 3D view
                three_d_prompt = generate_detailed_3d_courtyard_prompt(concept, self.design_data, tree_data, attributes)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                three_d_filename = f"3d_view_{timestamp}.png"
                
                success_3d, output_path_3d, message_3d = generate_3d_view_from_text(three_d_prompt, three_d_filename)
                
                if success_3d:
                    self.image_signals.image_update.emit(output_path_3d)
                
                # Generate plan view
                self.image_signals.status_update.emit("📋 Generating plan view...")
                
                plan_prompt = generate_detailed_plan_courtyard_prompt(concept, self.design_data, tree_data, attributes)
                plan_filename = f"plan_view_{timestamp}.png"
                
                success_plan, output_path_plan, message_plan = generate_plan_view_from_text(plan_prompt, plan_filename)
                
                if success_plan:
                    self.image_signals.plan_image_update.emit(output_path_plan)
                
                # Show results
                if success_3d and success_plan:
                    success_html = self.create_assistant_message("✅ Both views generated successfully! Check the tabs above for your 3D visualization and plan layout.")
                    self.chat_display.append(success_html)
                    self.chat_display.verticalScrollBar().setValue(
                        self.chat_display.verticalScrollBar().maximum()
                    )
                    self.image_signals.status_update.emit("✅ Both views generated successfully! Check the tabs above.")
                else:
                    error_messages = []
                    if not success_3d:
                        error_messages.append(f"3D view: {message_3d}")
                    if not success_plan:
                        error_messages.append(f"Plan view: {message_plan}")
                    
                    error_html = self.create_assistant_message(f"❌ Some views failed to generate: {'; '.join(error_messages)}", "error")
                    self.chat_display.append(error_html)
                    self.image_signals.status_update.emit(f"❌ Some views failed to generate")

            except Exception as e:
                self.image_signals.status_update.emit(f"❌ Error generating views: {str(e)}")
                print(f"Error in generate both views: {e}")

        threading.Thread(target=_task).start()

    def handle_generate_3d_view(self):
        """Generate 3D view using text-to-image with detailed courtyard features."""
        self.image_signals.status_update.emit("🎭 Generating 3D view from design data... Please wait.")
        QApplication.processEvents()

        def _task():
            try:
                # Check if we have design data
                if not hasattr(self, 'design_data') or not self.design_data:
                    self.image_signals.status_update.emit("⚠️ No design data available. Please complete the design process first.")
                    return

                # Generate 3D view prompt from design data
                self.image_signals.status_update.emit("📝 Analyzing design data and generating 3D view prompt...")
                
                concept = getattr(self, 'concept', 'A beautiful courtyard design')
                attributes = getattr(self, 'attributes', {})
                tree_data = getattr(self, 'tree_data', {})
                
                from image_gen import generate_3d_view_from_text, generate_detailed_3d_courtyard_prompt
                
                # Generate comprehensive 3D view prompt with detailed courtyard features
                three_d_prompt = generate_detailed_3d_courtyard_prompt(concept, self.design_data, tree_data, attributes)
                
                print(f"Generated 3D view prompt: {three_d_prompt}")
                
                # Generate 3D view using text-to-image
                self.image_signals.status_update.emit("🎨 Generating 3D view with AI...")
                
                # Generate unique output filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"3d_view_{timestamp}.png"
                
                success, output_path, message = generate_3d_view_from_text(three_d_prompt, output_filename)
                
                if success:
                    # Display the generated 3D view in the Image Generation tab
                    self.image_signals.image_update.emit(output_path)
                    
                    # Add success message to chat
                    success_html = self.create_assistant_message("✅ 3D view generated successfully! Here's your realistic courtyard visualization with all features.")
                    self.chat_display.append(success_html)
                    
                    # Scroll to bottom to show the new message
                    self.chat_display.verticalScrollBar().setValue(
                        self.chat_display.verticalScrollBar().maximum()
                    )
                    
                    self.image_signals.status_update.emit(f"✅ 3D view generated successfully!")
                else:
                    error_html = self.create_assistant_message(message, "error")
                    self.chat_display.append(error_html)
                    self.image_signals.status_update.emit(message)

            except Exception as e:
                print(f"DEBUG: Exception in 3D view generation: {e}")
                error_html = self.create_assistant_message(f"❌ Error generating 3D view: {str(e)}", "error")
                self.chat_display.append(error_html)
                self.image_signals.status_update.emit(f"❌ Error generating 3D view: {str(e)}")
                print(f"Error in generate 3D view: {e}")

        threading.Thread(target=_task).start()

    def handle_generate_plan_view(self):
        """Generate plan view using text-to-image from design data with coordinates."""
        self.image_signals.status_update.emit("📋 Generating plan view from design data... Please wait.")
        QApplication.processEvents()

        def _task():
            try:
                # Check if we have design data
                if not hasattr(self, 'design_data') or not self.design_data:
                    self.image_signals.status_update.emit("⚠️ No design data available. Please complete the design process first.")
                    return

                # Generate plan view prompt from design data
                self.image_signals.status_update.emit("📝 Analyzing design data and generating plan view prompt...")
                
                concept = getattr(self, 'concept', 'A beautiful courtyard design')
                attributes = getattr(self, 'attributes', {})
                tree_data = getattr(self, 'tree_data', {})
                
                from image_gen import generate_plan_view_from_text, generate_detailed_plan_courtyard_prompt
                
                # Generate comprehensive plan view prompt with coordinates and realistic details
                plan_prompt = generate_detailed_plan_courtyard_prompt(concept, self.design_data, tree_data, attributes)
                
                print(f"Generated plan view prompt: {plan_prompt}")
                
                # Generate plan view using text-to-image
                self.image_signals.status_update.emit("🎨 Generating plan view with AI...")
                
                # Generate unique output filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"plan_view_{timestamp}.png"
                
                success, output_path, message = generate_plan_view_from_text(plan_prompt, output_filename)
                
                if success:
                    # Display the generated plan view in the Image Generation tab
                    self.image_signals.plan_image_update.emit(output_path)
                    
                    # Add success message to chat
                    success_html = self.create_assistant_message("✅ Plan view generated successfully! Here's your precise top-down courtyard layout with coordinates.")
                    self.chat_display.append(success_html)
                    
                    # Scroll to bottom to show the new message
                    self.chat_display.verticalScrollBar().setValue(
                        self.chat_display.verticalScrollBar().maximum()
                    )
                    
                    self.image_signals.status_update.emit(f"✅ Plan view generated successfully!")
                else:
                    error_html = self.create_assistant_message(message, "error")
                    self.chat_display.append(error_html)
                    self.image_signals.status_update.emit(message)

            except Exception as e:
                print(f"DEBUG: Exception in plan view generation: {e}")
                error_html = self.create_assistant_message(f"❌ Error generating plan view: {str(e)}", "error")
                self.chat_display.append(error_html)
                self.image_signals.status_update.emit(f"❌ Error generating plan view: {str(e)}")
                print(f"Error in generate plan view: {e}")

        threading.Thread(target=_task).start()

    def handle_generate_concept_view(self):
        """Generate concept view using text-to-image from design data."""
        # This function is deprecated - concept view has been removed
        pass

    def process_image_with_ai(self, image_path, view_type, display_name):
        """Process an image with AI enhancement based on view type."""
        try:
            # Check if file exists and has content
            if not image_path or not os.path.exists(image_path):
                self.image_signals.status_update.emit(f"⚠️ Screenshot file not found for {display_name}. Please try again.")
                return
            
            if os.path.getsize(image_path) == 0:
                self.image_signals.status_update.emit(f"⚠️ Screenshot file is empty for {display_name}. Please try again.")
                return

            # Display the captured image
            if view_type == "3d":
                self.image_signals.image_update.emit(image_path)
            else:  # concept view
                self.image_signals.concept_image_update.emit(image_path)

            # Generate appropriate prompt based on view type with CRTYRD trigger word
            try:
                if hasattr(self, 'design_data') and self.design_data:
                    concept = getattr(self, 'concept', 'A beautiful courtyard design')
                    attributes = getattr(self, 'attributes', {})
                    
                    from llm_calls import generate_image_prompt
                    
                    connections = self.design_data.get("links", {})
                    targets = self.design_data.get("positions", {})
                    spaces = self.design_data.get("spaces", {})
                    pwr = getattr(self, 'tree_data', {}).get("PWR", {})
                    tree_placement = getattr(self, 'tree_data', {}).get("tree_placement", {})
                    
                    # Generate base prompt
                    base_prompt = generate_image_prompt(concept, attributes, connections, targets, spaces, pwr, tree_placement)
                    
                    # Enhance prompt based on view type with CRTYRD trigger word
                    if view_type == "3d":
                        enhanced_prompt = f"CRTYRD, {base_prompt}, architectural 3D visualization, dramatic lighting, photorealistic rendering, cinematic composition, high quality, detailed textures, natural materials, immersive atmosphere, professional architectural photography, golden hour lighting, depth of field, atmospheric perspective, preserve original camera angle, maintain perspective, enhance without rotation"
                    else:  # plan view
                        enhanced_prompt = f"CRTYRD, {base_prompt}, architectural plan view, technical drawing style, clean lines, professional layout, top-down perspective, minimalist design, precise measurements, clear zone boundaries, elegant spatial composition"
                    
                    self.image_signals.status_update.emit(f"🎨 Generating AI-enhanced {display_name}...")
                    
                    # Call the image generation function
                    from image_gen import generate_ai_enhanced_image
                    
                    # Generate unique output filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_filename = f"ai_enhanced_{view_type}_{timestamp}.png"
                    
                    # Pass design data for detailed architectural description
                    success, output_path, message = generate_ai_enhanced_image(
                        image_path, enhanced_prompt, output_filename, self.design_data
                    )
                    
                    if success:
                        # Display the generated image in the appropriate tab
                        if view_type == "3d":
                            self.image_signals.image_update.emit(output_path)
                        else:  # concept view
                            self.image_signals.concept_image_update.emit(output_path)
                        
                        self.image_signals.status_update.emit(f"✅ {display_name} generated successfully!")
                    else:
                        self.image_signals.status_update.emit(message)
                        
                else:
                    self.image_signals.status_update.emit("⚠️ No design data available for prompt generation. Please complete the design process first.")
                    
            except Exception as e:
                self.image_signals.status_update.emit(f"⚠️ Error generating AI visualization for {display_name}: {str(e)}")
                print(f"Error in AI image generation for {view_type}: {e}")
            
        except Exception as e:
            self.image_signals.status_update.emit(f"Failed to process {display_name}: {e}")
            if view_type == "3d":
                self.image_signals.error_update.emit(f"Failed to load {display_name}.")
            else:
                self.image_signals.concept_error_update.emit(f"Failed to load {display_name}.")

    def clear_query_results_and_display(self):
        """Clear stored query results, hide buttons, and clear the display"""
        self.clear_query_results()
        self.clear_results_button.setVisible(False)
        self.query_results.clear()
        self.query_results.append("Query results cleared. You can ask a new question.")

    def update_concept_image_display(self, image_path):
        """Update the concept view image display (called from main thread)"""
        # This function is deprecated - concept view has been removed
        pass

    def update_concept_image_error(self, error_message):
        """Update the concept view image display with an error (called from main thread)"""
        # This function is deprecated - concept view has been removed
        pass

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
