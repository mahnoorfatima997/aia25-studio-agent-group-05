import requests
from llm_calls import *
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QTextBrowser, QHBoxLayout,
    QTabWidget, QTextEdit, QComboBox, QMessageBox, QApplication, QGridLayout, QGroupBox, QScrollArea
)
from PyQt5.QtGui import QPixmap, QIcon
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
from datetime import datetime, timedelta
from plan_export import export_courtyard_plan, PlanExportTab
from epw_analysis import handle_zip_request, get_hoys_from_intent, load_epw_dataframe
from server.config import client, completion_model
from fallback_utils import (
    safe_extract_json, get_fallback_spaces, get_fallback_links,
    get_fallback_positions, get_fallback_cardinal_directions,
    get_fallback_weights, get_fallback_anchors, get_fallback_pos,
    create_robust_geometry_data
)

class ImageGenerationSignals(QObject):
    """Signals for safely updating UI from background threads"""
    status_update = pyqtSignal(str)
    image_update = pyqtSignal(str)
    error_update = pyqtSignal(str)
    plan_image_update = pyqtSignal(str)
    plan_error_update = pyqtSignal(str)
    climate_results_update = pyqtSignal(str)

class FlaskClientChatUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Captain CAT - Courtyard Advisory Tool")
        
        # Initialize signals for image generation
        self.image_signals = ImageGenerationSignals()
        # self.image_signals.status_update.connect(self.update_image_status)  # Function removed
        self.image_signals.image_update.connect(self.update_image_display)
        self.image_signals.error_update.connect(self.update_image_error)
        self.image_signals.plan_image_update.connect(self.update_plan_image_display)
        self.image_signals.plan_error_update.connect(self.update_plan_image_error)
        self.image_signals.climate_results_update.connect(self.update_climate_results)
        
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

        # Set window icon
        self.setWindowIcon(QIcon("cat_icon.png"))
        
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

        # Add icon to the title bar
        icon_label = QLabel()
        icon_pixmap = QPixmap("cat_icon.png").scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(icon_pixmap)
        icon_label.setFixedSize(48, 48)
        title_layout.addWidget(icon_label)

        # Title with icon
        title_label = QLabel("Captain CAT - Courtyard Advisory Tool")
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

        # Create the welcome tab first
        self.create_welcome_tab()

        # Create the main chat tab
        self.create_chat_tab()
        
        # Create the graph query tab
        self.create_query_tab()

        # Create the image generation tab
        self.create_image_generation_tab()

        # Create the climate analysis tab
        self.create_climate_analysis_tab()

        # Create the plan export tab using the PlanExportTab class (moved to end)
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
        self.chat_display.append(self.create_assistant_message(greeting, is_bold=True))

    def create_welcome_tab(self):
        """Create the welcome/introductory tab"""
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setContentsMargins(40, 40, 40, 40)
        welcome_layout.setSpacing(30)

        # Center the content
        welcome_layout.setAlignment(Qt.AlignCenter)

        # Large cat image
        cat_image_label = QLabel()
        try:
            cat_pixmap = QPixmap("cat_icon.png").scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            cat_image_label.setPixmap(cat_pixmap)
        except:
            # Fallback if image not found
            cat_image_label.setText("🐱")
            cat_image_label.setStyleSheet("font-size: 200px; text-align: center;")
        
        cat_image_label.setAlignment(Qt.AlignCenter)
        cat_image_label.setFixedSize(300, 300)
        welcome_layout.addWidget(cat_image_label)

        # Welcome title
        welcome_title = QLabel("Welcome to Captain CAT - Courtyard Advisory Tool!")
        welcome_title.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #2196F3;
                text-align: center;
                margin: 20px 0;
            }
        """)
        welcome_title.setAlignment(Qt.AlignCenter)
        welcome_title.setWordWrap(True)
        welcome_layout.addWidget(welcome_title)

        # Welcome message
        welcome_message = QLabel("Hope you enjoy relieving the building of its concrete load")
        welcome_message.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: #666;
                text-align: center;
                font-style: italic;
                margin: 20px 0;
            }
        """)
        welcome_message.setAlignment(Qt.AlignCenter)
        welcome_message.setWordWrap(True)
        welcome_layout.addWidget(welcome_message)

        # Add some spacing
        spacer = QWidget()
        spacer.setFixedHeight(50)
        welcome_layout.addWidget(spacer)

        # Add the welcome tab to the tab widget
        self.tab_widget.addTab(welcome_widget, "Welcome")

    def create_assistant_message(self, message, message_type="info", is_bold=False):
        """Helper function to create assistant message styling: white background with black text, left-aligned."""
        font_weight = "bold" if is_bold else "normal"
        font_style = "normal" if is_bold else "italic"
        
        return f"""
        <div style='margin: 10px 0; text-align: left;'>
            <div style='background: white; color: black; padding: 10px 15px; border-radius: 8px; font-size: 24px; font-weight: {font_weight}; font-style: {font_style}; line-height: 1.6; display: inline-block; max-width: 80%;'>
                {message}
            </div>
        </div>
        """

    def show_phase_question(self):
        question = self.phase_questions.get(self.current_phase)
        if question:
            assistant_html = self.create_assistant_message(question, is_bold=True)
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
            <div style='background: white; color: black; padding: 10px 15px; border-radius: 8px; font-size: 24px; font-weight: normal; line-height: 1.6; display: inline-block; max-width: 80%;'>
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
                # Send concept to server for heatmap analysis
                self.send_concept_to_server()
            elif self.current_phase == "functions":
                # Process the data first with fallback protection
                try:
                    from fallback_utils import safe_extract_json
                    
                    llm_response = extract_external_functions(self.phases[self.current_phase])
                    json_llm_response = safe_extract_json(llm_response, {"external_functions": {}}, "external_functions")
                    self.extracted_functions = json_llm_response["external_functions"]
                    print("✅ External functions extracted successfully:", self.extracted_functions)
                except Exception as e:
                    print(f"❌ Error extracting external functions: {e}")
                    # Use empty external functions as fallback
                    self.extracted_functions = {}
                    print("✅ Using fallback external functions (empty)")
                
                self.set_extracted_functions()
                # Generate human-like response
                assistant_message = generate_human_functions_response(self.extracted_functions)
            elif self.current_phase == "attributes":
                # Process the data first with fallback protection
                try:
                    from fallback_utils import safe_extract_json, get_fallback_attributes
                    
                    llm_response = extract_attributes_with_conversation(self.phases[self.current_phase], self.concept)
                    json_llm_response = safe_extract_json(llm_response, get_fallback_attributes(), "attributes")
                    self.attributes = json_llm_response
                    print("✅ Attributes extracted successfully:", self.attributes)
                except Exception as e:
                    print(f"❌ Error extracting attributes: {e}")
                    from fallback_utils import get_fallback_attributes
                    self.attributes = get_fallback_attributes()
                    print("✅ Using fallback attributes:", self.attributes)
                
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
            
            # Check if we have valid plot area data
            area = plot_area.get("area")
            width = plot_area.get("width")
            length = plot_area.get("length")
            
            # If all values are None or empty, use default values
            if not area and not width and not length:
                print("No plot area data available, using default values")
                return {
                    "area": "400",
                    "width": "20",
                    "length": "20"
                }
            
            # If we have area but missing dimensions, calculate them
            if area and (not width or not length):
                try:
                    area_float = float(area)
                    # Assume a square plot if dimensions not provided
                    side_length = (area_float ** 0.5)  # Square root of area
                    plot_area["width"] = str(side_length)
                    plot_area["length"] = str(side_length)
                    print("Calculated dimensions from area:", plot_area)
                except (ValueError, TypeError):
                    print("Could not calculate dimensions from area, using defaults")
                    plot_area["width"] = "20"
                    plot_area["length"] = "20"
            
            # If we have dimensions but missing area, calculate it
            if (width and length) and not area:
                try:
                    width_float = float(width)
                    length_float = float(length)
                    area_calculated = width_float * length_float
                    plot_area["area"] = str(area_calculated)
                    print("Calculated area from dimensions:", plot_area)
                except (ValueError, TypeError):
                    print("Could not calculate area from dimensions, using default")
                    plot_area["area"] = "400"
            
            # Ensure all values are strings for consistency
            return {
                "area": str(plot_area.get("area", "400")),
                "width": str(plot_area.get("width", "20")),
                "length": str(plot_area.get("length", "20"))
            }
            
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
            self.chat_display.append(self.create_assistant_message("Error fetching plot area from Grasshopper.", "error"))
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
            self.chat_display.append(self.create_assistant_message("Error extracting functions.", "error"))
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
        Uses fallback values if LLM calls fail or return incomplete data.
        """
        try:
            # Import fallback utilities
            from fallback_utils import (
                safe_extract_json, get_fallback_spaces, get_fallback_links,
                get_fallback_positions, get_fallback_cardinal_directions,
                get_fallback_weights, get_fallback_anchors, get_fallback_pos,
                create_robust_geometry_data
            )
            
            print("🔄 Extracting geometry data with fallback protection...")
            
            # Standard data extraction with fallback protection
            try:
                spaces_response = extract_spaces(self.concept, self.extracted_functions, self.attributes)
                spaces = safe_extract_json(spaces_response, get_fallback_spaces(), "spaces")
            except Exception as e:
                print(f"❌ Error extracting spaces: {e}")
                spaces = get_fallback_spaces()
            
            try:
                links_response = extract_links(self.concept, self.extracted_functions)
                links = safe_extract_json(links_response, get_fallback_links(), "links")
            except Exception as e:
                print(f"❌ Error extracting links: {e}")
                links = get_fallback_links()
            
            try:
                positions_response = extract_positions(self.concept, self.extracted_functions)
                positions = safe_extract_json(positions_response, get_fallback_positions(), "positions")
            except Exception as e:
                print(f"❌ Error extracting positions: {e}")
                positions = get_fallback_positions()
            
            try:
                cardinal_directions_response = extract_cardinal_directions(self.concept, self.extracted_functions, self.attributes)
                cardinal_directions = safe_extract_json(cardinal_directions_response, get_fallback_cardinal_directions(), "cardinal_directions")
            except Exception as e:
                print(f"❌ Error extracting cardinal directions: {e}")
                cardinal_directions = get_fallback_cardinal_directions()
            
            try:
                weights_response = extract_weights(self.concept, self.extracted_functions, self.attributes)
                weights = safe_extract_json(weights_response, get_fallback_weights(), "weights")
            except Exception as e:
                print(f"❌ Error extracting weights: {e}")
                weights = get_fallback_weights()
            
            try:
                anchors_response = extract_anchors(self.concept, self.extracted_functions, self.attributes)
                anchors = safe_extract_json(anchors_response, get_fallback_anchors(), "anchors")
            except Exception as e:
                print(f"❌ Error extracting anchors: {e}")
                anchors = get_fallback_anchors()
            
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
                try:
                    pos_response = extract_pos(self.concept, self.extracted_functions, corners, calculated_placements)
                    final_pos = safe_extract_json(pos_response, get_fallback_pos(), "pos")
                except Exception as e:
                    print(f"❌ Error extracting positions with boundaries: {e}")
                    final_pos = get_fallback_pos()

            else:
                # Fallback to unbounded position generation
                print("Falling back to unbounded position generation.")
                try:
                    pos_response = extract_pos(self.concept, self.extracted_functions, [], {})
                    final_pos = safe_extract_json(pos_response, get_fallback_pos(), "pos")
                except Exception as e:
                    print(f"❌ Error extracting positions without boundaries: {e}")
                    final_pos = get_fallback_pos()
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
            print("✅ Enhanced design data aggregated with boundary box and fallback protection:", self.design_data)

        except Exception as e:
            print(f"❌ Critical error in geometry_data: {e}")
            print("🔄 Using robust fallback geometry data...")
            
            # Use the robust fallback system as a last resort
            try:
                from fallback_utils import create_robust_geometry_data
                self.design_data = create_robust_geometry_data(
                    self.concept, 
                    self.extracted_functions or {}, 
                    self.attributes or {}
                )
                print("✅ Fallback geometry data created successfully")
            except Exception as fallback_error:
                print(f"❌ Even fallback system failed: {fallback_error}")
                self.chat_display.append("<span style='color: red;'>Error extracting geometry data. Please try again.</span>")


    def get_tree_data(self):
        """
        Aggregate all relevant data from all phases, store in self.design_data, and persist to JSON DB.
        Uses fallback values if LLM calls fail or return incomplete data.
        """
        try:
            # Import fallback utilities
            from fallback_utils import (
                safe_extract_json, get_fallback_tree_placement, get_fallback_pwr,
                create_robust_tree_data
            )
            
            print("🔄 Extracting tree data with fallback protection...")
            
            # Extract tree placement with fallback protection
            try:
                tree_placement_response = extract_tree_placement(self.concept, self.attributes)
                tree_placement = safe_extract_json(tree_placement_response, get_fallback_tree_placement(), "tree_placement")
                print("✅ Extracted tree placement:", tree_placement)
            except Exception as e:
                print(f"❌ Error extracting tree placement: {e}")
                tree_placement = get_fallback_tree_placement()
            
            # Extract PWR with fallback protection
            try:
                pwr_response = extract_plant_water_requirement(self.concept, self.attributes, tree_placement)
                PWR = safe_extract_json(pwr_response, get_fallback_pwr(), "PWR")
                print("✅ Extracted PWR:", PWR)
            except Exception as e:
                print(f"❌ Error extracting PWR: {e}")
                PWR = get_fallback_pwr()

            self.tree_data = {
                "tree_placement": tree_placement["tree_placement"],
                "PWR": PWR["pwr"],                
            }
            print("✅ Tree data prepared for sending:", self.tree_data)

            # Send tree data to server with proper headers and error handling
            headers = {
                'Content-Type': 'application/json'
            }
            print("🔄 Sending tree data to server:", self.tree_data)
            
            try:
                tree_data_response = requests.post(
                    "http://127.0.0.1:5000/send_tree_data",
                    json=self.tree_data,
                    headers=headers,
                    timeout=10  # Add timeout
                )
                
                if tree_data_response.status_code == 200:
                    response_data = tree_data_response.json()
                    print("✅ Server response:", response_data)
                    # Removed the success message - tree data generation happens silently
                else:
                    raise Exception(f"Server returned status code {tree_data_response.status_code}")
                    
            except requests.exceptions.ConnectionError as e:
                # Handle connection errors gracefully
                print(f"⚠️ Connection error sending tree data: {e}")
                self.chat_display.append(self.create_assistant_message(
                    f"⚠️ Server connection failed. Tree data saved locally but not sent to Grasshopper.\nError: {str(e)}\nYou can continue with the design process.",
                    "warning"
                ))
            except Exception as e:
                print(f"❌ Error sending tree data: {e}")
                self.chat_display.append(self.create_assistant_message(
                    f"❌ Error sending tree data to Grasshopper: {str(e)}",
                    "error"
                ))

        except Exception as e:
            print(f"❌ Critical error in get_tree_data: {e}")
            print("🔄 Using robust fallback tree data...")
            
            # Use the robust fallback system as a last resort
            try:
                from fallback_utils import create_robust_tree_data
                self.tree_data = create_robust_tree_data(
                    self.concept, 
                    self.attributes or {}
                )
                print("✅ Fallback tree data created successfully")
                
                # Try to send the fallback data
                try:
                    headers = {'Content-Type': 'application/json'}
                    tree_data_response = requests.post(
                        "http://127.0.0.1:5000/send_tree_data",
                        json=self.tree_data,
                        headers=headers,
                        timeout=10
                    )
                    if tree_data_response.status_code == 200:
                        print("✅ Fallback tree data sent successfully")
                    else:
                        print(f"⚠️ Could not send fallback tree data: {tree_data_response.status_code}")
                except Exception as send_error:
                    print(f"⚠️ Could not send fallback tree data: {send_error}")
                    
            except Exception as fallback_error:
                print(f"❌ Even fallback system failed: {fallback_error}")
                self.chat_display.append("<span style='color: red;'>Error extracting tree data. Please try again.</span>")

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
        advisor_label = QLabel("🐱 CAT's Corner:")
        advisor_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        chat_layout.addWidget(advisor_label)

        self.advisor_panel = QTextEdit()
        self.advisor_panel.setReadOnly(True)
        self.advisor_panel.setPlaceholderText("Captain CAT's helpful tips will appear here as you design...")
        self.advisor_panel.setFixedHeight(100) # Increased height for better readability
        self.advisor_panel.setStyleSheet("""
            QTextEdit {
                background-color: #FFFDE7; /* A warm, parchment-like yellow */
                border: 1px solid #FFF9C4;
                border-radius: 8px;
                padding: 12px;
                font-size: 18px;
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
        """Creates the tab for concept image generation and courtyard plan screenshot."""
        image_gen_widget = QWidget()
        layout = QVBoxLayout(image_gen_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("Image Generation")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        # Description
        description = QLabel(
            "Generate concept images and enhanced plan views of your courtyard design. "
            "Concept images are inspirational text-to-image generations, while plan views enhance Grasshopper screenshots with AI."
        )
        description.setWordWrap(True)
        description.setStyleSheet("font-size: 16px; margin-bottom: 15px;")
        layout.addWidget(description)

        # Tab widget for Concept Images and Courtyard Plan
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

        # --- Concept Images Tab ---
        self.concept_images = []  # List of (filepath, QPixmap)
        concept_widget = QWidget()
        concept_layout = QVBoxLayout(concept_widget)
        concept_layout.setSpacing(10)

        # Display area for the latest concept image
        self.concept_image_label = QLabel("Concept image will appear here.")
        self.concept_image_label.setAlignment(Qt.AlignCenter)
        self.concept_image_label.setMinimumHeight(400)
        self.concept_image_label.setStyleSheet("""
            QLabel {
                background-color: #e8e8e8;
                border: 2px dashed #cccccc;
                border-radius: 8px;
                color: #888888;
                font-size: 16px;
            }
        """)
        concept_layout.addWidget(self.concept_image_label)

        # Button row for concept images
        btn_row = QHBoxLayout()
        self.generate_concept_btn = QPushButton("🎨 Generate New Concept Image")
        self.generate_concept_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.generate_concept_btn.clicked.connect(self.handle_generate_concept_image)
        btn_row.addWidget(self.generate_concept_btn)

        self.save_concept_btn = QPushButton("💾 Save Image")
        self.save_concept_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        self.save_concept_btn.clicked.connect(self.handle_save_concept_image)
        self.save_concept_btn.setEnabled(False)
        btn_row.addWidget(self.save_concept_btn)
        concept_layout.addLayout(btn_row)

        # Gallery of previous concept images (thumbnails)
        self.concept_gallery_label = QLabel("<b>Gallery:</b>")
        self.concept_gallery_label.setStyleSheet("font-size: 16px; margin-top: 10px;")
        concept_layout.addWidget(self.concept_gallery_label)
        self.concept_gallery = QScrollArea()
        self.concept_gallery.setWidgetResizable(True)
        self.concept_gallery_widget = QWidget()
        self.concept_gallery_layout = QHBoxLayout(self.concept_gallery_widget)
        self.concept_gallery_layout.setSpacing(10)
        self.concept_gallery.setWidget(self.concept_gallery_widget)
        concept_layout.addWidget(self.concept_gallery)

        self.image_tab_widget.addTab(concept_widget, "Concept Images")

        # --- Courtyard Plan Tab ---
        plan_widget = QWidget()
        plan_layout = QVBoxLayout(plan_widget)
        plan_layout.setSpacing(10)

        self.plan_image_label = QLabel("Plan view will appear here.")
        self.plan_image_label.setAlignment(Qt.AlignCenter)
        self.plan_image_label.setMinimumHeight(400)
        self.plan_image_label.setStyleSheet("""
            QLabel {
                background-color: #e8e8e8;
                border: 2px dashed #cccccc;
                border-radius: 8px;
                color: #888888;
                font-size: 16px;
            }
        """)
        plan_layout.addWidget(self.plan_image_label)

        # Button row for plan views
        plan_btn_row = QHBoxLayout()
        
        self.take_screenshot_btn = QPushButton("📸 Take Grasshopper Screenshot")
        self.take_screenshot_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self.take_screenshot_btn.clicked.connect(self.take_grasshopper_screenshot)
        plan_btn_row.addWidget(self.take_screenshot_btn)
        
        self.generate_plan_btn = QPushButton("📋 Generate Plan View")
        self.generate_plan_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.generate_plan_btn.clicked.connect(self.handle_generate_plan_view)
        self.generate_plan_btn.setEnabled(False)  # Enable only after screenshot is taken
        plan_btn_row.addWidget(self.generate_plan_btn)

        self.save_plan_btn = QPushButton("💾 Save Plan View")
        self.save_plan_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        self.save_plan_btn.clicked.connect(self.handle_save_plan_image)
        self.save_plan_btn.setEnabled(False)
        plan_btn_row.addWidget(self.save_plan_btn)
        
        plan_layout.addLayout(plan_btn_row)

        self.image_tab_widget.addTab(plan_widget, "Courtyard Plan")

        layout.addWidget(self.image_tab_widget, 1)
        self.tab_widget.addTab(image_gen_widget, "Image Generation")

    def handle_generate_concept_image(self):
        """Generate a new concept image and add it to the gallery."""
        self.generate_concept_btn.setEnabled(False)
        self.concept_image_label.setText("Generating concept image...")
        QApplication.processEvents()

        def _task():
            try:
                # Generate concept image using the correct function
                from image_gen import generate_concept_view_from_text
                concept = getattr(self, 'concept', 'A beautiful courtyard design')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"concept_{timestamp}.png"
                success, output_path, message = generate_concept_view_from_text(concept, filename)
                if success:
                    pixmap = QPixmap(output_path)
                    scaled_pixmap = pixmap.scaled(
                        self.concept_image_label.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.concept_image_label.setPixmap(scaled_pixmap)
                    self.save_concept_btn.setEnabled(True)
                    
                    # Add to concept images list
                    self.concept_images.append((output_path, pixmap))
                    
                    # Update the gallery
                    self.update_concept_gallery()
                    
                    print(f"✅ Concept image generated and added to gallery: {output_path}")
                else:
                    self.concept_image_label.setText(f"Failed to generate image: {message}")
            except Exception as e:
                self.concept_image_label.setText(f"Error: {str(e)}")
                print(f"Error generating concept image: {e}")
            finally:
                self.generate_concept_btn.setEnabled(True)

        threading.Thread(target=_task).start()

    def handle_save_concept_image(self):
        """Save the latest concept image to disk."""
        if not self.concept_images:
            return
        from PyQt5.QtWidgets import QFileDialog
        latest_path, latest_pixmap = self.concept_images[-1]
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Concept Image", latest_path, "PNG Files (*.png);;All Files (*)", options=options)
        if file_path:
            latest_pixmap.save(file_path)

    def update_concept_gallery(self):
        """Update the gallery of concept images."""
        # Clear layout
        for i in reversed(range(self.concept_gallery_layout.count())):
            widget = self.concept_gallery_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        # Add thumbnails
        for idx, (path, pixmap) in enumerate(self.concept_images):
            thumb = QLabel()
            thumb.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            thumb.setFixedSize(100, 100)
            thumb.setStyleSheet("border: 2px solid #2196F3; border-radius: 6px; margin: 2px;")
            thumb.mousePressEvent = lambda e, p=path: self.show_full_concept_image(p)
            self.concept_gallery_layout.addWidget(thumb)

    def show_full_concept_image(self, path):
        """Show the full-size concept image when a thumbnail is clicked."""
        pixmap = QPixmap(path)
        self.concept_image_label.setPixmap(pixmap.scaled(
            self.concept_image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))
        self.save_concept_btn.setEnabled(True)

    def handle_save_plan_image(self):
        """Save the latest plan view to disk."""
        from PyQt5.QtWidgets import QFileDialog
        if not hasattr(self, 'latest_plan_path') or not self.latest_plan_path:
            return
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Plan View", self.latest_plan_path, "PNG Files (*.png);;All Files (*)", options=options)
        if file_path:
            QPixmap(self.latest_plan_path).save(file_path)

    def update_plan_image(self, image_path):
        """Update the plan view display and enable save."""
        pixmap = QPixmap(image_path)
        self.plan_image_label.setPixmap(pixmap.scaled(
            self.plan_image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))
        self.latest_plan_path = image_path
        self.save_plan_btn.setEnabled(True)

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
            self.plan_image_label.setPixmap(pixmap.scaled(
                self.plan_image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
        except Exception as e:
            self.plan_image_label.setText(f"Failed to load image: {e}")

    def update_image_error(self, error_message):
        """Update the image display with an error (called from main thread)"""
        self.image_3d_display_label.setText(error_message)

    def update_plan_image_error(self, error_message):
        """Update the plan view image display with an error (called from main thread)"""
        self.plan_image_label.setText(error_message)

    def update_advisor_tip(self):
        """Fetches and displays a proactive design tip from Captain CAT."""
        try:
            context_data = {
                "concept": self.concept if hasattr(self, 'concept') else "Not yet defined.",
                "functions": self.phases.get("functions", []),
                "attributes": self.phases.get("attributes", [])
            }
            tip = generate_design_tip(self.current_phase, self.concept, context_data)
            # Captain Cat speaks directly - no prefix needed
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
        """Generate both concept and plan views using text-to-image."""
        self.image_signals.status_update.emit("🔄 Generating both concept and plan views from design data... Please wait.")
        QApplication.processEvents()

        def _task():
            try:
                # Check if we have design data
                if not hasattr(self, 'design_data') or not self.design_data:
                    self.image_signals.status_update.emit("⚠️ No design data available. Please complete the design process first.")
                    return

                # Generate concept view first
                self.image_signals.status_update.emit("🎨 Generating concept view...")
                
                concept = getattr(self, 'concept', 'A beautiful courtyard design')
                attributes = getattr(self, 'attributes', {})
                tree_data = getattr(self, 'tree_data', {})
                
                from image_gen import generate_concept_view_from_text
                from image_gen import generate_plan_view_from_text, generate_detailed_plan_courtyard_prompt
                
                # Generate concept view
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                concept_filename = f"concept_{timestamp}.png"
                
                success_concept, output_path_concept, message_concept = generate_concept_view_from_text(concept, concept_filename)
                
                if success_concept:
                    self.image_signals.image_update.emit(output_path_concept)
                
                # Generate plan view
                self.image_signals.status_update.emit("📋 Generating plan view...")
                
                plan_prompt = generate_detailed_plan_courtyard_prompt(concept, self.design_data, tree_data, attributes)
                plan_filename = f"plan_view_{timestamp}.png"
                
                success_plan, output_path_plan, message_plan = generate_plan_view_from_text(plan_prompt, plan_filename)
                
                if success_plan:
                    self.image_signals.plan_image_update.emit(output_path_plan)
                    
                    # Also update the plan image in the plan tab
                    self.update_plan_image(output_path_plan)
                
                # Show results
                if success_concept and success_plan:
                    success_html = self.create_assistant_message("✅ Both views generated successfully! Check the tabs above for your concept visualization and plan layout.")
                    self.chat_display.append(success_html)
                    self.chat_display.verticalScrollBar().setValue(
                        self.chat_display.verticalScrollBar().maximum()
                    )
                    self.image_signals.status_update.emit("✅ Both views generated successfully! Check the tabs above.")
                else:
                    error_messages = []
                    if not success_concept:
                        error_messages.append(f"Concept view: {message_concept}")
                    if not success_plan:
                        error_messages.append(f"Plan view: {message_plan}")
                    
                    error_html = self.create_assistant_message(f"❌ Some views failed to generate: {'; '.join(error_messages)}", "error")
                    self.chat_display.append(error_html)
                    self.image_signals.status_update.emit(f"❌ Some views failed to generate")

            except Exception as e:
                self.image_signals.status_update.emit(f"❌ Error generating views: {str(e)}")
                print(f"Error in generate both views: {e}")

        threading.Thread(target=_task).start()

    def handle_generate_plan_view(self):
        """Generate plan view using image-to-image with Grasshopper screenshot."""
        if not hasattr(self, 'grasshopper_screenshot_path') or not self.grasshopper_screenshot_path:
            self.plan_image_label.setText("⚠️ Please take a Grasshopper screenshot first.")
            return
            
        if not os.path.exists(self.grasshopper_screenshot_path):
            self.plan_image_label.setText("⚠️ Screenshot file not found. Please take a new screenshot.")
            return

        self.image_signals.status_update.emit("📋 Generating enhanced plan view from Grasshopper screenshot... Please wait.")
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
                
                from image_gen import generate_plan_view_from_screenshot, generate_detailed_plan_courtyard_prompt
                
                # Generate comprehensive plan view prompt with coordinates and realistic details
                plan_prompt = generate_detailed_plan_courtyard_prompt(concept, self.design_data, tree_data, attributes)
                
                # Add building context to the prompt
                enhanced_prompt = f"{plan_prompt}, brown square building surrounding the courtyard, courtyard space inside the building perimeter, architectural plan view, technical drawing style, clean lines, professional layout, top-down perspective, precise measurements, clear zone boundaries, elegant spatial composition, coordinate system, realistic materials, professional architectural documentation"
                
                print(f"Generated plan view prompt: {enhanced_prompt}")
                
                # Generate plan view using image-to-image with screenshot
                self.image_signals.status_update.emit("🎨 Generating enhanced plan view with AI...")
                
                # Generate unique output filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"enhanced_plan_{timestamp}.png"
                
                success, output_path, message = generate_plan_view_from_screenshot(
                    self.grasshopper_screenshot_path, 
                    enhanced_prompt, 
                    output_filename
                )
                
                if success:
                    # Display the generated plan view in the Image Generation tab
                    self.image_signals.plan_image_update.emit(output_path)
                    
                    # Also update the plan image in the plan tab
                    self.update_plan_image(output_path)
                    
                    # Add success message to chat
                    success_html = self.create_assistant_message("✅ Enhanced plan view generated successfully! Here's your AI-enhanced courtyard layout based on the Grasshopper screenshot.")
                    self.chat_display.append(success_html)
                    
                    # Scroll to bottom to show the new message
                    self.chat_display.verticalScrollBar().setValue(
                        self.chat_display.verticalScrollBar().maximum()
                    )
                    
                    self.image_signals.status_update.emit(f"✅ Enhanced plan view generated successfully!")
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

            # Display the captured image (only concept views now)
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
                    
                    # Enhance prompt for concept view with CRTYRD trigger word
                    enhanced_prompt = f"CRTYRD, {base_prompt}, architectural concept visualization, inspirational design, artistic rendering, high quality, detailed, photorealistic, enhanced lighting, improved materials, refined textures, creative courtyard environment, brown square building surrounding the courtyard, courtyard space inside the building perimeter"
                    
                    self.image_signals.status_update.emit(f"🎨 Generating AI-enhanced {display_name}...")
                    
                    # Call the image generation function
                    from image_gen import generate_ai_enhanced_image
                    
                    # Generate unique output filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_filename = f"ai_enhanced_concept_{timestamp}.png"
                    
                    # Pass design data for detailed architectural description
                    success, output_path, message = generate_ai_enhanced_image(
                        image_path, enhanced_prompt, output_filename, self.design_data
                    )
                    
                    if success:
                        # Display the generated image in the concept tab
                        self.image_signals.concept_image_update.emit(output_path)
                        
                        self.image_signals.status_update.emit(f"✅ {display_name} generated successfully!")
                    else:
                        self.image_signals.status_update.emit(message)
                        
                else:
                    self.image_signals.status_update.emit("⚠️ No design data available for prompt generation. Please complete the design process first.")
                    
            except Exception as e:
                self.image_signals.status_update.emit(f"⚠️ Error generating AI visualization for {display_name}: {str(e)}")
                print(f"Error in AI image generation for concept view: {e}")
            
        except Exception as e:
            self.image_signals.status_update.emit(f"Failed to process {display_name}: {e}")
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

    def create_climate_analysis_tab(self):
        """Create the Climate Analysis tab with location input and analysis features."""
        climate_widget = QWidget()
        climate_layout = QVBoxLayout(climate_widget)
        climate_layout.setContentsMargins(20, 20, 20, 20)
        climate_layout.setSpacing(15)

        # Title section
        title_label = QLabel("Climate Analysis")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #1976D2;
                padding: 10px 0;
            }
        """)
        climate_layout.addWidget(title_label)

        # Create scrollable area for better layout
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(20)

        # Location Input Section
        location_group = QGroupBox("📍 Location Selection")
        location_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        location_layout = QGridLayout(location_group)

        # Location input
        location_label = QLabel("Enter location (city, country):")
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("e.g., London, UK or New York, USA")
        self.location_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
        """)
        
        self.find_location_btn = QPushButton("🔍 Find Weather Data")
        self.find_location_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.find_location_btn.clicked.connect(self.find_location_data)

        location_layout.addWidget(location_label, 0, 0)
        location_layout.addWidget(self.location_input, 0, 1)
        location_layout.addWidget(self.find_location_btn, 0, 2)

        # Location status display
        self.location_status = QLabel("Enter a location to begin analysis")
        self.location_status.setStyleSheet("""
            QLabel {
                padding: 10px;
                border-radius: 6px;
                background-color: #f5f5f5;
                color: #666;
                font-size: 14px;
            }
        """)
        location_layout.addWidget(self.location_status, 1, 0, 1, 3)

        scroll_layout.addWidget(location_group)

        # Analysis Section
        analysis_group = QGroupBox("📊 Climate Analysis")
        analysis_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        analysis_layout = QVBoxLayout(analysis_group)

        # Quick analysis buttons
        quick_analysis_label = QLabel("Quick Analysis:")
        quick_analysis_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        analysis_layout.addWidget(quick_analysis_label)

        # Create grid for quick analysis buttons
        quick_buttons_layout = QGridLayout()
        
        self.hottest_hour_btn = QPushButton("🔥 Hottest Hour")
        self.coldest_hour_btn = QPushButton("❄️ Coldest Hour")
        self.hottest_day_btn = QPushButton("🌡️ Hottest Day")
        self.coldest_day_btn = QPushButton("🧊 Coldest Day")
        
        # Style all quick analysis buttons
        for btn in [self.hottest_hour_btn, self.coldest_hour_btn, self.hottest_day_btn, self.coldest_day_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 12px 16px;
                    font-weight: bold;
                    font-size: 13px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
                QPushButton:pressed {
                    background-color: #0D47A1;
                }
                QPushButton:disabled {
                    background-color: #BDBDBD;
                    color: #757575;
                }
            """)
            btn.setEnabled(False)
            btn.clicked.connect(self.perform_quick_analysis)

        quick_buttons_layout.addWidget(self.hottest_hour_btn, 0, 0)
        quick_buttons_layout.addWidget(self.coldest_hour_btn, 0, 1)
        quick_buttons_layout.addWidget(self.hottest_day_btn, 1, 0)
        quick_buttons_layout.addWidget(self.coldest_day_btn, 1, 1)
        
        analysis_layout.addLayout(quick_buttons_layout)

        # Custom analysis section
        custom_analysis_label = QLabel("Custom Analysis:")
        custom_analysis_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 20px 0 10px 0;")
        analysis_layout.addWidget(custom_analysis_label)

        self.custom_query_input = QLineEdit()
        self.custom_query_input.setPlaceholderText("e.g., 'hottest week of July' or 'temperature on Christmas Day'")
        self.custom_query_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
        """)
        
        self.analyze_custom_btn = QPushButton("🔬 Analyze Custom Query")
        self.analyze_custom_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        self.analyze_custom_btn.setEnabled(False)
        self.analyze_custom_btn.clicked.connect(self.perform_custom_analysis)

        analysis_layout.addWidget(self.custom_query_input)
        analysis_layout.addWidget(self.analyze_custom_btn)

        # Time Period Selection for Grasshopper
        time_period_label = QLabel("Send to Grasshopper - Select Date & Time:")
        time_period_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 20px 0 10px 0;")
        analysis_layout.addWidget(time_period_label)

        # Date and time selection layout
        datetime_layout = QHBoxLayout()
        
        # Month dropdown
        self.month_combo = QComboBox()
        self.month_combo.addItem("Month")
        for i, month in enumerate(['January', 'February', 'March', 'April', 'May', 'June', 
                                 'July', 'August', 'September', 'October', 'November', 'December'], 1):
            self.month_combo.addItem(month, i)
        self.month_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                background-color: white;
                min-width: 120px;
            }
            QComboBox:focus {
                border-color: #2196F3;
            }
        """)
        
        # Day dropdown
        self.day_combo = QComboBox()
        self.day_combo.addItem("Day")
        for day in range(1, 32):
            self.day_combo.addItem(str(day), day)
        self.day_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                background-color: white;
                min-width: 80px;
            }
            QComboBox:focus {
                border-color: #2196F3;
            }
        """)
        
        # Hour dropdown
        self.hour_combo = QComboBox()
        self.hour_combo.addItem("Hour")
        for hour in range(24):
            self.hour_combo.addItem(f"{hour:02d}:00", hour)
        self.hour_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                background-color: white;
                min-width: 80px;
            }
            QComboBox:focus {
                border-color: #2196F3;
            }
        """)
        
        # Connect month change to update days
        self.month_combo.currentIndexChanged.connect(self.update_days_for_month)
        
        datetime_layout.addWidget(self.month_combo)
        datetime_layout.addWidget(self.day_combo)
        datetime_layout.addWidget(self.hour_combo)
        
        self.send_to_grasshopper_btn = QPushButton("📤 Send to Grasshopper")
        self.send_to_grasshopper_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        self.send_to_grasshopper_btn.setEnabled(False)
        self.send_to_grasshopper_btn.clicked.connect(self.send_datetime_to_grasshopper)
        
        datetime_layout.addWidget(self.send_to_grasshopper_btn)
        datetime_layout.addStretch()  # Add stretch to push widgets to the left
        
        analysis_layout.addLayout(datetime_layout)

        # UTCI Analysis Section
        utci_layout = QHBoxLayout()
        
        self.utci_analysis_btn = QPushButton("🌡️ Get UTCI Analysis")
        self.utci_analysis_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:pressed {
                background-color: #4A148C;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        self.utci_analysis_btn.setEnabled(False)
        self.utci_analysis_btn.clicked.connect(self.receive_utci_values)
        
        self.heatmap_analysis_btn = QPushButton("🗺️ Get Heatmap Analysis")
        self.heatmap_analysis_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #E64A19;
            }
            QPushButton:pressed {
                background-color: #BF360C;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        self.heatmap_analysis_btn.clicked.connect(self.receive_heatmap_analysis)
        
        utci_layout.addWidget(self.utci_analysis_btn)
        utci_layout.addWidget(self.heatmap_analysis_btn)
        utci_layout.addStretch()
        
        analysis_layout.addLayout(utci_layout)

        scroll_layout.addWidget(analysis_group)

        # Results Section
        results_group = QGroupBox("📈 Analysis Results")
        results_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        results_layout = QVBoxLayout(results_group)

        self.climate_results = QTextBrowser()
        self.climate_results.setStyleSheet("""
            QTextBrowser {
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                padding: 15px;
                background-color: white;
                font-size: 18px;
                line-height: 1.6;
                min-height: 200px;
            }
        """)
        self.climate_results.setHtml("""
            <div style='text-align: center; color: #666; padding: 40px;'>
                <h3>🌤️ Climate Analysis Results</h3>
                <p>Enter a location and select an analysis type to see results here.</p>
            </div>
        """)

        results_layout.addWidget(self.climate_results)
        scroll_layout.addWidget(results_group)

        # Set up scroll area
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        climate_layout.addWidget(scroll_area)
        self.tab_widget.addTab(climate_widget, "Climate Analysis")

        # Initialize state
        self.current_zip_url = None
        self.current_location = None

        # Add after custom analysis section in create_climate_analysis_tab
        # Removed: self.send_minimal_btn = QPushButton("Send Minimal Data to Grasshopper")
        # Removed: Button styling, connection, and layout addition

    def find_location_data(self):
        """Find weather data for the entered location."""
        location = self.location_input.text().strip()
        if not location:
            self.location_status.setText("⚠️ Please enter a location")
            self.location_status.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    border-radius: 6px;
                    background-color: #ffebee;
                    color: #c62828;
                    font-size: 14px;
                }
            """)
            return

        self.location_status.setText("🔍 Searching for weather data...")
        self.location_status.setStyleSheet("""
            QLabel {
                padding: 10px;
                border-radius: 6px;
                background-color: #e3f2fd;
                color: #1565c0;
                font-size: 14px;
            }
        """)
        self.find_location_btn.setEnabled(False)

        # Run in background thread
        def search_task():
            try:
                result = handle_zip_request(location, client, completion_model)
                
                if result["success"]:
                    self.current_zip_url = result["zip_url"]
                    self.current_location = f"{result['city']}, {result['country']}"
                    
                    # Update UI in main thread
                    self.location_status.setText(f"✅ Found weather data for {self.current_location}")
                    self.location_status.setStyleSheet("""
                        QLabel {
                            padding: 10px;
                            border-radius: 6px;
                            background-color: #e8f5e8;
                            color: #2e7d32;
                            font-size: 14px;
                        }
                    """)
                    
                    # Enable analysis buttons
                    for btn in [self.hottest_hour_btn, self.coldest_hour_btn, self.hottest_day_btn, self.coldest_day_btn, self.analyze_custom_btn]:
                        btn.setEnabled(True)
                    
                    # Enable Grasshopper controls
                    self.send_to_grasshopper_btn.setEnabled(True)
                    self.month_combo.setEnabled(True)
                    self.day_combo.setEnabled(True)
                    self.hour_combo.setEnabled(True)
                    self.utci_analysis_btn.setEnabled(True)
                        
                else:
                    self.location_status.setText(f"❌ {result['error']}")
                    self.location_status.setStyleSheet("""
                        QLabel {
                            padding: 10px;
                            border-radius: 6px;
                            background-color: #ffebee;
                            color: #c62828;
                            font-size: 14px;
                        }
                    """)
                    
            except Exception as e:
                self.location_status.setText(f"❌ Error: {str(e)}")
                self.location_status.setStyleSheet("""
                    QLabel {
                        padding: 10px;
                        border-radius: 6px;
                        background-color: #ffebee;
                        color: #c62828;
                        font-size: 14px;
                    }
                """)
            finally:
                self.find_location_btn.setEnabled(True)

        threading.Thread(target=search_task).start()

    def perform_quick_analysis(self):
        """Perform quick analysis based on button clicked and send to Grasshopper."""
        if not self.current_zip_url:
            return

        sender = self.sender()
        query_map = {
            self.hottest_hour_btn: "hottest hour of the year",
            self.coldest_hour_btn: "coldest hour of the year",
            self.hottest_day_btn: "hottest day of the year",
            self.coldest_day_btn: "coldest day of the year"
        }
        
        if sender in query_map:
            query = query_map[sender]
            
            # Show loading state
            self.climate_results.setHtml("""
                <div style='text-align: center; color: #1565c0; padding: 40px;'>
                    <h3>🔬 Analyzing Climate Data...</h3>
                    <p>Please wait while we process your request.</p>
                </div>
            """)

            # Run analysis in background thread
            def analysis_task():
                try:
                    # Get HOYs from intent
                    hoys = get_hoys_from_intent(query, self.current_zip_url, client, completion_model)
                    
                    if not hoys:
                        error_html = """
                            <div style='text-align: center; color: #c62828; padding: 20px;'>
                                <h3>❌ Analysis Failed</h3>
                                <p>Could not understand the time period in your query.</p>
                            </div>
                        """
                        self.image_signals.climate_results_update.emit(error_html)
                        return

                    # Load EPW data
                    df = load_epw_dataframe(self.current_zip_url)
                    
                    # Extract relevant data
                    dry_bulb_temp = df[6]  # Column 6 is dry bulb temperature
                    humidity = df[8]       # Column 8 is relative humidity
                    
                    # Calculate statistics for the selected hours
                    selected_temps = dry_bulb_temp.iloc[hoys]
                    selected_humidity = humidity.iloc[hoys]
                    
                    # Format results based on analysis type
                    if len(hoys) == 1:
                        # Single hour analysis
                        hour = hoys[0]
                        temp = selected_temps.iloc[0]
                        hum = selected_humidity.iloc[0]
                        
                        # Convert HOY to date/time
                        day_of_year = hour // 24 + 1
                        hour_of_day = hour % 24
                        
                        # Convert to month/day for display
                        from datetime import datetime
                        date_obj = datetime(2024, 1, 1) + timedelta(days=day_of_year-1)
                        month_name = date_obj.strftime('%B')
                        day_num = date_obj.day
                        
                        climate_data_for_gh = {
                            "location": self.current_location,
                            "query": query,
                            "analysis_type": "single_hour",
                            "is_single_hour": True,
                            "hour_of_year": hour,
                            "day_of_year": day_of_year,
                            "hour_of_day": hour_of_day,
                            "temperature": float(temp),
                            "humidity": float(hum),
                            "epw_url": self.current_zip_url,
                            "timestamp": str(datetime.now())
                        }
                        
                        result_html = f"""
                        <div style='padding: 20px; background-color: #f5f5f5; border-radius: 8px; margin: 10px 0;'>
                            <h3>📊 Quick Analysis Results for {self.current_location}</h3>
                            <h4>Query: {query}</h4>
                            <div style='background-color: white; padding: 15px; border-radius: 6px; margin: 10px 0;'>
                                <p><strong>Date/Time:</strong> {month_name} {day_num} at {hour_of_day:02d}:00</p>
                                <p><strong>Hour of Year (HOY):</strong> {hour}</p>
                                <p><strong>Temperature:</strong> {temp:.1f}°C</p>
                                <p><strong>Relative Humidity:</strong> {hum:.1f}%</p>
                            </div>
                        </div>
                        """
                    else:
                        # Time period analysis
                        avg_temp = selected_temps.mean()
                        max_temp = selected_temps.max()
                        min_temp = selected_temps.min()
                        avg_humidity = selected_humidity.mean()
                        
                        climate_data_for_gh = {
                            "location": self.current_location,
                            "query": query,
                            "analysis_type": "time_period",
                            "is_single_hour": False,
                            "hours_analyzed": len(hoys),
                            "hour_range": [min(hoys), max(hoys)],
                            "hour_of_day": -1,
                            "day_of_year": -1,
                            "hour_of_year": -1,
                            "temperature": float(avg_temp),
                            "humidity": float(avg_humidity),
                            "temperature_stats": {
                                "average": float(avg_temp),
                                "maximum": float(max_temp),
                                "minimum": float(min_temp)
                            },
                            "humidity_stats": {
                                "average": float(avg_humidity)
                            },
                            "epw_url": self.current_zip_url,
                            "timestamp": str(datetime.now())
                        }
                        
                        result_html = f"""
                        <div style='padding: 20px; background-color: #f5f5f5; border-radius: 8px; margin: 10px 0;'>
                            <h3>📊 Quick Analysis Results for {self.current_location}</h3>
                            <h4>Query: {query}</h4>
                            <div style='background-color: white; padding: 15px; border-radius: 6px; margin: 10px 0;'>
                                <p><strong>Time Period:</strong> {len(hoys)} hours</p>
                                <p><strong>Average Temperature:</strong> {avg_temp:.1f}°C</p>
                                <p><strong>Maximum Temperature:</strong> {max_temp:.1f}°C</p>
                                <p><strong>Minimum Temperature:</strong> {min_temp:.1f}°C</p>
                                <p><strong>Average Relative Humidity:</strong> {avg_humidity:.1f}%</p>
                            </div>
                        </div>
                        """
                    
                    # Send climate data to server for Grasshopper
                    try:
                        headers = {
                            'Content-Type': 'application/json'
                        }
                        print(f"🔍 Sending climate data to server: {climate_data_for_gh}")
                        
                        climate_response = requests.post(
                            "http://127.0.0.1:5000/climate_data",
                            json={"climate_data": climate_data_for_gh},
                            headers=headers,
                            timeout=10
                        )
                        
                        if climate_response.status_code == 200:
                            result_html += f"""
                            <div style='background-color: #e8f5e8; color: #2e7d32; padding: 10px; border-radius: 6px; margin-top: 10px;'>
                                ✅ Climate data sent to Grasshopper successfully!
                            </div>
                            """
                        else:
                            result_html += f"""
                            <div style='background-color: #ffebee; color: #c62828; padding: 10px; border-radius: 6px; margin-top: 10px;'>
                                ⚠️ Failed to send data to Grasshopper (Status: {climate_response.status_code})
                            </div>
                            """
                            
                    except Exception as e:
                        result_html += f"""
                        <div style='background-color: #ffebee; color: #c62828; padding: 10px; border-radius: 6px; margin-top: 10px;'>
                            ❌ Error sending data: {str(e)}
                        </div>
                        """
                    
                    # Use signal to update UI from main thread
                    self.image_signals.climate_results_update.emit(result_html)
                    
                except Exception as e:
                    error_html = f"""
                        <div style='text-align: center; color: #c62828; padding: 20px;'>
                            <h3>❌ Analysis Error</h3>
                            <p>Error: {str(e)}</p>
                        </div>
                    """
                    self.image_signals.climate_results_update.emit(error_html)

            threading.Thread(target=analysis_task).start()

    def perform_custom_analysis(self):
        """Perform custom analysis based on user input."""
        if not self.current_zip_url:
            return

        query = self.custom_query_input.text().strip()
        if not query:
            self.climate_results.setHtml("""
                <div style='text-align: center; color: #c62828; padding: 20px;'>
                    <h3>⚠️ Please enter a custom query</h3>
                </div>
            """)
            return

        self.analyze_climate_data(query)

    def analyze_climate_data(self, query):
        """Analyze climate data based on the query."""
        if not self.current_zip_url:
            return

        # Show loading state
        self.climate_results.setHtml("""
            <div style='text-align: center; color: #1565c0; padding: 40px;'>
                <h3>🔬 Analyzing Climate Data...</h3>
                <p>Please wait while we process your request.</p>
            </div>
        """)

        # Run analysis in background thread
        def analysis_task():
            try:
                # Get HOYs from intent
                hoys = get_hoys_from_intent(query, self.current_zip_url, client, completion_model)
                
                if not hoys:
                    error_html = """
                        <div style='text-align: center; color: #c62828; padding: 20px;'>
                            <h3>❌ Analysis Failed</h3>
                            <p>Could not understand the time period in your query.</p>
                        </div>
                    """
                    self.image_signals.climate_results_update.emit(error_html)
                    return

                # Load EPW data
                df = load_epw_dataframe(self.current_zip_url)
                
                # Extract relevant data
                dry_bulb_temp = df[6]  # Column 6 is dry bulb temperature
                humidity = df[8]       # Column 8 is relative humidity
                
                # Calculate statistics for the selected hours
                selected_temps = dry_bulb_temp.iloc[hoys]
                selected_humidity = humidity.iloc[hoys]
                
                # Format results based on time period
                if len(hoys) == 1:
                    hour = hoys[0]
                    temp = selected_temps.iloc[0]
                    hum = selected_humidity.iloc[0]
                    
                    # Convert HOY to date/time
                    day_of_year = hour // 24 + 1
                    hour_of_day = hour % 24
                    
                    # Create climate data for Grasshopper
                    climate_data_for_gh = {
                        "location": self.current_location,
                        "query": query,
                        "analysis_type": "single_hour",
                        "is_single_hour": True,
                        "hour_of_year": hour,
                        "day_of_year": day_of_year,
                        "hour_of_day": hour_of_day,
                        "temperature": float(temp),
                        "humidity": float(hum),
                        "epw_url": self.current_zip_url,
                        "timestamp": str(datetime.now())
                    }
                    
                    result_html = f"""
                    <div style='padding: 20px; background-color: #f5f5f5; border-radius: 8px; margin: 10px 0;'>
                        <h3>📊 Analysis Results for {self.current_location}</h3>
                        <h4>Query: {query}</h4>
                        <div style='background-color: white; padding: 15px; border-radius: 6px; margin: 10px 0;'>
                            <p><strong>Date/Time:</strong> Day {day_of_year}, Hour {hour_of_day:02d}:00</p>
                            <p><strong>Temperature:</strong> {temp:.1f}°C</p>
                            <p><strong>Relative Humidity:</strong> {hum:.1f}%</p>
                        </div>
                    </div>
                    """
                else:
                    avg_temp = selected_temps.mean()
                    max_temp = selected_temps.max()
                    min_temp = selected_temps.min()
                    avg_humidity = selected_humidity.mean()
                    
                    # Create climate data for Grasshopper
                    climate_data_for_gh = {
                        "location": self.current_location,
                        "query": query,
                        "analysis_type": "time_period",
                        "is_single_hour": False,
                        "hours_analyzed": len(hoys),
                        "hour_range": [min(hoys), max(hoys)],
                        "hour_of_day": -1,
                        "day_of_year": -1,
                        "hour_of_year": -1,
                        "temperature": float(avg_temp),
                        "humidity": float(avg_humidity),
                        "temperature_stats": {
                            "average": float(avg_temp),
                            "maximum": float(max_temp),
                            "minimum": float(min_temp)
                        },
                        "humidity_stats": {
                            "average": float(avg_humidity)
                        },
                        "epw_url": self.current_zip_url,
                        "timestamp": str(datetime.now())
                    }
                    
                    result_html = f"""
                    <div style='padding: 20px; background-color: #f5f5f5; border-radius: 8px; margin: 10px 0;'>
                        <h3>📊 Analysis Results for {self.current_location}</h3>
                        <h4>Query: {query}</h4>
                        <div style='background-color: white; padding: 15px; border-radius: 6px; margin: 10px 0;'>
                            <p><strong>Time Period:</strong> {len(hoys)} hours</p>
                            <p><strong>Average Temperature:</strong> {avg_temp:.1f}°C</p>
                            <p><strong>Maximum Temperature:</strong> {max_temp:.1f}°C</p>
                            <p><strong>Minimum Temperature:</strong> {min_temp:.1f}°C</p>
                            <p><strong>Average Relative Humidity:</strong> {avg_humidity:.1f}%</p>
                        </div>
                    </div>
                    """
                
                # Send climate data to server for Grasshopper
                try:
                    headers = {
                        'Content-Type': 'application/json'
                    }
                    print(f"🔍 Sending climate data to server: {climate_data_for_gh}")
                    
                    climate_response = requests.post(
                        "http://127.0.0.1:5000/climate_data",
                        json={"climate_data": climate_data_for_gh},
                        headers=headers,
                        timeout=10
                    )
                    
                    if climate_response.status_code == 200:
                        result_html += """
                        <div style='background-color: #e8f5e8; color: #2e7d32; padding: 10px; border-radius: 6px; margin-top: 10px;'>
                            ✅ Climate data sent to Grasshopper successfully!
                        </div>
                        """
                    else:
                        result_html += f"""
                        <div style='background-color: #ffebee; color: #c62828; padding: 10px; border-radius: 6px; margin-top: 10px;'>
                            ⚠️ Failed to send data to Grasshopper (Status: {climate_response.status_code})
                        </div>
                        """
                        
                except Exception as e:
                    result_html += f"""
                    <div style='background-color: #ffebee; color: #c62828; padding: 10px; border-radius: 6px; margin-top: 10px;'>
                        ❌ Error sending data: {str(e)}
                    </div>
                    """
                
                # Use signal to update UI from main thread
                self.image_signals.climate_results_update.emit(result_html)
                
            except Exception as e:
                error_html = f"""
                    <div style='text-align: center; color: #c62828; padding: 20px;'>
                        <h3>❌ Analysis Error</h3>
                        <p>Error: {str(e)}</p>
                    </div>
                """
                self.image_signals.climate_results_update.emit(error_html)

        threading.Thread(target=analysis_task).start()

    def update_climate_results(self, results):
        """Update the climate results display."""
        self.climate_results.setHtml(results)

    def send_minimal_data_to_grasshopper(self):
        # This function has been removed - no longer needed
        pass

    def update_days_for_month(self):
        """Update the days dropdown based on the selected month."""
        selected_month = self.month_combo.currentText()
        if selected_month == "Month":
            self.day_combo.clear()
            self.day_combo.addItem("Day")
            for day in range(1, 32):
                self.day_combo.addItem(str(day), day)
        else:
            self.day_combo.clear()
            self.day_combo.addItem("Day")
            days_in_month = {
                'January': 31, 'February': 28, 'March': 31, 'April': 30, 'May': 31, 'June': 30,
                'July': 31, 'August': 31, 'September': 30, 'October': 31, 'November': 30, 'December': 31
            }
            max_days = days_in_month[selected_month]
            for day in range(1, max_days + 1):
                self.day_combo.addItem(str(day), day)

    def datetime_to_hoy(self, month, day, hour):
        """Convert date and time to Hour of Year (HOY)."""
        try:
            # Convert month name to number
            month_names = ['January', 'February', 'March', 'April', 'May', 'June', 
                          'July', 'August', 'September', 'October', 'November', 'December']
            month_num = month_names.index(month) + 1
            
            # Extract hour number from string like "14:00"
            if ":" in str(hour):
                hour_num = int(str(hour).split(":")[0])
            else:
                hour_num = int(hour)
            
            # Calculate day of year
            from datetime import datetime
            date_obj = datetime(2024, month_num, int(day))  # Using 2024 as reference year
            day_of_year = date_obj.timetuple().tm_yday
            
            # Calculate Hour of Year (HOY)
            hoy = (day_of_year - 1) * 24 + hour_num
            
            print(f"DEBUG: month={month}, day={day}, hour={hour}, hour_num={hour_num}, day_of_year={day_of_year}, hoy={hoy}")
            
            return hoy
        except Exception as e:
            print(f"Error converting datetime to HOY: {e}")
            print(f"Input values: month={month}, day={day}, hour={hour}")
            return None

    def send_datetime_to_grasshopper(self):
        """Send date and time data to Grasshopper based on user selection."""
        if not self.current_zip_url or not self.current_location:
            self.climate_results.setHtml("""
                <div style='text-align: center; color: #c62828; padding: 20px;'>
                    <h3>⚠️ Please enter a location and find weather data first.</h3>
                </div>
            """)
            return

        # Get the data values from combo boxes
        month_index = self.month_combo.currentIndex()
        day_index = self.day_combo.currentIndex()
        hour_index = self.hour_combo.currentIndex()
        
        # Check if valid selections were made
        if month_index == 0 or day_index == 0 or hour_index == 0:
            self.climate_results.setHtml("""
                <div style='text-align: center; color: #c62828; padding: 20px;'>
                    <h3>⚠️ Please select a complete date and time.</h3>
                </div>
            """)
            return

        # Get the actual values
        month = self.month_combo.currentText()
        day = self.day_combo.currentData()
        hour = self.hour_combo.currentData()
        
        print(f"DEBUG: Selected values - month: {month}, day: {day}, hour: {hour}")

        # Convert to Hour of Year
        hoy = self.datetime_to_hoy(month, day, hour)
        if hoy is None:
            self.climate_results.setHtml("""
                <div style='text-align: center; color: #c62828; padding: 20px;'>
                    <h3>❌ Error converting date/time to Hour of Year.</h3>
                </div>
            """)
            return

        # Show loading state
        self.climate_results.setHtml(f"""
            <div style='text-align: center; color: #1565c0; padding: 40px;'>
                <h3>🔬 Analyzing Climate Data for {month} {day} at {hour:02d}:00...</h3>
                <p>Hour of Year: {hoy}</p>
                <p>Please wait while we process your request.</p>
            </div>
        """)

        # Run analysis in background thread
        def analysis_task():
            try:
                # Load EPW data
                df = load_epw_dataframe(self.current_zip_url)
                
                # Extract relevant data
                dry_bulb_temp = df[6]  # Column 6 is dry bulb temperature
                humidity = df[8]       # Column 8 is relative humidity
                
                # Get data for the specific hour
                if hoy < len(dry_bulb_temp):
                    temp = dry_bulb_temp.iloc[hoy]
                    hum = humidity.iloc[hoy]
                    
                    # Convert HOY back to date/time for display
                    day_of_year = hoy // 24 + 1
                    hour_of_day = hoy % 24
                    
                    climate_data_for_gh = {
                        "location": self.current_location,
                        "query": f"Climate data for {month} {day} at {hour:02d}:00",
                        "analysis_type": "single_hour",
                        "is_single_hour": True,
                        "hour_of_year": hoy,
                        "day_of_year": day_of_year,
                        "hour_of_day": hour_of_day,
                        "temperature": float(temp),
                        "humidity": float(hum),
                        "epw_url": self.current_zip_url,
                        "timestamp": str(datetime.now())
                    }
                    
                    result_html = f"""
                    <div style='padding: 20px; background-color: #f5f5f5; border-radius: 8px; margin: 10px 0;'>
                        <h3>📊 Climate Analysis Results for {self.current_location}</h3>
                        <h4>Date/Time: {month} {day} at {hour:02d}:00</h4>
                        <div style='background-color: white; padding: 15px; border-radius: 6px; margin: 10px 0;'>
                            <p><strong>Hour of Year (HOY):</strong> {hoy}</p>
                            <p><strong>Day of Year:</strong> {day_of_year}</p>
                            <p><strong>Hour of Day:</strong> {hour_of_day:02d}:00</p>
                            <p><strong>Temperature:</strong> {temp:.1f}°C</p>
                            <p><strong>Relative Humidity:</strong> {hum:.1f}%</p>
                        </div>
                    </div>
                    """
                else:
                    result_html = f"""
                    <div style='text-align: center; color: #c62828; padding: 20px;'>
                        <h3>❌ Invalid Hour of Year</h3>
                        <p>Hour of Year {hoy} is outside the valid range for this climate data.</p>
                    </div>
                    """
                    self.image_signals.climate_results_update.emit(result_html)
                    return
                
                # Send climate data to server for Grasshopper
                try:
                    headers = {
                        'Content-Type': 'application/json'
                    }
                    print(f"🔍 Sending climate data to server: {climate_data_for_gh}")
                    
                    climate_response = requests.post(
                        "http://127.0.0.1:5000/climate_data",
                        json={"climate_data": climate_data_for_gh},
                        headers=headers,
                        timeout=10
                    )
                    
                    if climate_response.status_code == 200:
                        result_html += f"""
                        <div style='background-color: #e8f5e8; color: #2e7d32; padding: 10px; border-radius: 6px; margin-top: 10px;'>
                            ✅ Climate data sent to Grasshopper successfully!
                        </div>
                        """
                    else:
                        result_html += f"""
                        <div style='background-color: #ffebee; color: #c62828; padding: 10px; border-radius: 6px; margin-top: 10px;'>
                            ⚠️ Failed to send data to Grasshopper (Status: {climate_response.status_code})
                        </div>
                        """
                        
                except Exception as e:
                    result_html += f"""
                    <div style='background-color: #ffebee; color: #c62828; padding: 10px; border-radius: 6px; margin-top: 10px;'>
                        ❌ Error sending data: {str(e)}
                    </div>
                    """
                
                # Use signal to update UI from main thread
                self.image_signals.climate_results_update.emit(result_html)
                
            except Exception as e:
                error_html = f"""
                    <div style='text-align: center; color: #c62828; padding: 20px;'>
                        <h3>❌ Analysis Error</h3>
                        <p>Error: {str(e)}</p>
                    </div>
                """
                self.image_signals.climate_results_update.emit(error_html)

        threading.Thread(target=analysis_task).start()

    def receive_utci_values(self):
        """Receive UTCI values from Grasshopper and display comparison with improvement tips."""
        try:
            print("🔍 Attempting to retrieve UTCI values from server...")
            
            # Get UTCI values from server
            response = requests.get("http://127.0.0.1:5000/utci_values", timeout=10)
            
            print(f"   Server response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Server response data: {data}")
                
                utci_with_trees = data.get("utci_values", [])
                utci_without_trees = data.get("utci_values_flat", [])
                avg_with_trees = data.get("average_with_trees", 0)
                avg_without_trees = data.get("average_without_trees", 0)
                improvement = data.get("improvement", 0)
                trees_helping = data.get("trees_helping", False)
                tips = data.get("tips", [])
                
                print(f"   UTCI with trees: {utci_with_trees}")
                print(f"   UTCI without trees: {utci_without_trees}")
                print(f"   Average with trees: {avg_with_trees}")
                print(f"   Average without trees: {avg_without_trees}")
                print(f"   Improvement: {improvement}")
                print(f"   Trees helping: {trees_helping}")
                print(f"   Tips: {tips}")
                
                if utci_with_trees and utci_without_trees:
                    # Determine thermal comfort categories
                    comfort_with_trees = self.get_thermal_comfort_category(avg_with_trees)
                    comfort_without_trees = self.get_thermal_comfort_category(avg_without_trees)
                    
                    print(f"   Comfort with trees: {comfort_with_trees}")
                    print(f"   Comfort without trees: {comfort_without_trees}")
                    
                    # Create comparison display
                    comparison_html = f"""
                    <div style='padding: 20px; background-color: #f5f5f5; border-radius: 8px; margin: 10px 0;'>
                        <h3 style='font-size: 24px; margin-bottom: 15px;'>🌡️ UTCI Thermal Comfort Analysis</h3>
                        <div style='background-color: white; padding: 20px; border-radius: 6px; margin: 10px 0;'>
                            <h4 style='font-size: 20px; margin-bottom: 15px;'>Design Performance Comparison:</h4>
                            
                            <div style='display: flex; gap: 20px; margin: 15px 0;'>
                                <div style='flex: 1; padding: 20px; background-color: #e8f5e8; border-radius: 6px; border-left: 4px solid #4caf50;'>
                                    <h5 style='margin: 0 0 15px 0; color: #2e7d32; font-size: 18px;'>🌳 With Trees</h5>
                                    <p style='font-size: 16px; margin: 8px 0;'><strong>Average UTCI:</strong> {avg_with_trees:.1f}°C</p>
                                    <p style='font-size: 16px; margin: 8px 0;'><strong>Thermal Comfort:</strong> {comfort_with_trees}</p>
                                    <p style='font-size: 16px; margin: 8px 0;'><strong>Measurements:</strong> {len(utci_with_trees)}</p>
                                </div>
                                
                                <div style='flex: 1; padding: 20px; background-color: #fff3e0; border-radius: 6px; border-left: 4px solid #ff9800;'>
                                    <h5 style='margin: 0 0 15px 0; color: #e65100; font-size: 18px;'>🏗️ Without Trees</h5>
                                    <p style='font-size: 16px; margin: 8px 0;'><strong>Average UTCI:</strong> {avg_without_trees:.1f}°C</p>
                                    <p style='font-size: 16px; margin: 8px 0;'><strong>Thermal Comfort:</strong> {comfort_without_trees}</p>
                                    <p style='font-size: 16px; margin: 8px 0;'><strong>Measurements:</strong> {len(utci_without_trees)}</p>
                                </div>
                            </div>
                            
                            <div style='margin-top: 20px; padding: 20px; background-color: {'#e8f5e8' if trees_helping else '#ffebee'}; border-radius: 6px; border-left: 4px solid {'#4caf50' if trees_helping else '#f44336'};'>
                                <h5 style='margin: 0 0 15px 0; color: {'#2e7d32' if trees_helping else '#c62828'}; font-size: 18px;'>
                                    {'✅' if trees_helping else '⚠️'} Tree Impact Analysis
                                </h5>
                                <p style='color: {'#2e7d32' if trees_helping else '#c62828'}; font-weight: bold; font-size: 16px; margin: 10px 0;'>
                                    Trees are providing {improvement:.1f}°C {'cooling' if trees_helping else 'warming'} effect
                                </p>
                                <p style='margin: 8px 0; font-size: 16px;'>
                                    <strong>Impact:</strong> {'Positive' if trees_helping else 'Negative'} - Your design is {improvement:.1f}°C {'cooler' if trees_helping else 'warmer'} with trees
                                </p>
                            </div>
                            
                            <div style='margin-top: 20px; padding: 20px; background-color: #f3e5f5; border-radius: 6px; border-left: 4px solid #9c27b0;'>
                                <h5 style='margin: 0 0 15px 0; color: #4a148c; font-size: 18px;'>💡 Improvement Suggestions</h5>
                                <ul style='margin: 0; padding-left: 25px;'>
                    """
                    
                    # Add tips to the HTML
                    for tip in tips:
                        comparison_html += f"<li style='margin: 8px 0; font-size: 16px;'>{tip}</li>"
                    
                    comparison_html += """
                                </ul>
                            </div>
                        </div>
                    </div>
                    """
                    
                    # Get current HTML content
                    current_html = self.climate_results.toHtml()
                    print(f"   Current HTML length: {len(current_html)}")
                    
                    # Check if UTCI analysis already exists
                    if "UTCI Thermal Comfort Analysis" not in current_html:
                        print("   Adding new UTCI analysis...")
                        # Add to existing results by combining HTML
                        if current_html.strip():
                            new_html = current_html + comparison_html
                        else:
                            new_html = comparison_html
                        self.climate_results.setHtml(new_html)
                    else:
                        print("   Replacing existing UTCI analysis...")
                        # Replace existing UTCI analysis
                        lines = current_html.split('\n')
                        new_lines = []
                        skip_utci = False
                        for line in lines:
                            if "UTCI Thermal Comfort Analysis" in line:
                                skip_utci = True
                            elif skip_utci and "</div>" in line and "background-color: #f5f5f5" in line:
                                skip_utci = False
                                continue
                            if not skip_utci:
                                new_lines.append(line)
                        
                        # Add new UTCI analysis
                        new_html = '\n'.join(new_lines) + comparison_html
                        self.climate_results.setHtml(new_html)
                    
                    print("   ✅ UTCI analysis displayed successfully!")
                    
                else:
                    print("   ⚠️ No UTCI values received from server")
                    # Create error message HTML
                    error_html = """
                        <div style='text-align: center; color: #c62828; padding: 20px;'>
                            <h3 style='font-size: 20px; margin-bottom: 15px;'>⚠️ No UTCI values received</h3>
                            <p style='font-size: 16px; margin: 8px 0;'>Please ensure Grasshopper is sending both UTCI data sets to the server.</p>
                            <p style='font-size: 16px; margin: 8px 0;'>Required: utci_values (with trees) and utci_values_flat (without trees)</p>
                        </div>
                    """
                    
                    # Add to existing results
                    current_html = self.climate_results.toHtml()
                    if current_html.strip():
                        new_html = current_html + error_html
                    else:
                        new_html = error_html
                    self.climate_results.setHtml(new_html)
                    
            else:
                print(f"   ❌ Server returned error status: {response.status_code}")
                error_html = f"""
                    <div style='text-align: center; color: #c62828; padding: 20px;'>
                        <h3 style='font-size: 20px; margin-bottom: 15px;'>❌ Failed to retrieve UTCI values</h3>
                        <p style='font-size: 16px; margin: 8px 0;'>Server returned status code: {response.status_code}</p>
                        <p style='font-size: 16px; margin: 8px 0;'>Response: {response.text}</p>
                    </div>
                """
                
                # Add to existing results
                current_html = self.climate_results.toHtml()
                if current_html.strip():
                    new_html = current_html + error_html
                else:
                    new_html = error_html
                self.climate_results.setHtml(new_html)
                
        except Exception as e:
            print(f"   ❌ Exception occurred: {str(e)}")
            error_html = f"""
                <div style='text-align: center; color: #c62828; padding: 20px;'>
                    <h3 style='font-size: 20px; margin-bottom: 15px;'>❌ Error retrieving UTCI values</h3>
                    <p style='font-size: 16px; margin: 8px 0;'>Error: {str(e)}</p>
                    <p style='font-size: 16px; margin: 8px 0;'>Please check if the server is running and accessible.</p>
                </div>
            """
            
            # Add to existing results
            current_html = self.climate_results.toHtml()
            if current_html.strip():
                new_html = current_html + error_html
            else:
                new_html = error_html
            self.climate_results.setHtml(new_html)

    def get_thermal_comfort_category(self, utci):
        """Get thermal comfort category based on UTCI value."""
        if utci < -40:
            return "Extreme Cold Stress"
        elif utci < -27:
            return "Very Strong Cold Stress"
        elif utci < -13:
            return "Strong Cold Stress"
        elif utci < 0:
            return "Moderate Cold Stress"
        elif utci < 9:
            return "Slight Cold Stress"
        elif utci < 26:
            return "No Thermal Stress"
        elif utci < 32:
            return "Moderate Heat Stress"
        elif utci < 38:
            return "Strong Heat Stress"
        elif utci < 46:
            return "Very Strong Heat Stress"
        else:
            return "Extreme Heat Stress"

    def calculate_city_utci_average(self):
        """Calculate average UTCI for the current city based on EPW data."""
        try:
            if not self.current_zip_url:
                return 0
                
            # Load EPW data
            df = load_epw_dataframe(self.current_zip_url)
            
            # Extract relevant data for UTCI calculation
            # Note: This is a simplified calculation. Full UTCI requires more parameters
            dry_bulb_temp = df[6]  # Column 6 is dry bulb temperature
            humidity = df[8]       # Column 8 is relative humidity
            wind_speed = df[21]    # Column 21 is wind speed
            global_radiation = df[14]  # Column 14 is global horizontal radiation
            
            # Simplified UTCI approximation (this is not the full UTCI formula)
            # In practice, you'd want to use a proper UTCI calculation library
            utci_values = []
            for i in range(len(dry_bulb_temp)):
                temp = dry_bulb_temp.iloc[i]
                hum = humidity.iloc[i]
                wind = wind_speed.iloc[i]
                rad = global_radiation.iloc[i]
                
                # Simplified approximation - in reality, UTCI is much more complex
                # This is just for demonstration purposes
                utci_approx = temp + (hum - 50) * 0.1 + (wind - 2) * 0.5 + (rad - 500) * 0.001
                utci_values.append(utci_approx)
            
            return sum(utci_values) / len(utci_values) if utci_values else 0
            
        except Exception as e:
            print(f"Error calculating city UTCI average: {e}")
            return 0

    def take_grasshopper_screenshot(self):
        """Take a screenshot from Grasshopper and store it for plan generation."""
        try:
            # Send screenshot command to Grasshopper via server
            response = requests.post("http://127.0.0.1:5000/take_screenshot", timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    screenshot_path = result.get("screenshot_path")
                    if screenshot_path and os.path.exists(screenshot_path):
                        # Store the screenshot path for plan generation
                        self.grasshopper_screenshot_path = screenshot_path
                        
                        # Display the screenshot in the plan tab
                        self.update_plan_image(screenshot_path)
                        
                        # Enable the generate plan button
                        self.generate_plan_btn.setEnabled(True)
                        
                        # Show success message
                        self.plan_image_label.setText("✅ Screenshot captured! Click 'Generate Plan View' to enhance it with AI.")
                        
                        print(f"✅ Screenshot captured: {screenshot_path}")
                    else:
                        self.plan_image_label.setText("⚠️ Screenshot file not found. Please try again.")
                else:
                    error_msg = result.get("error", "Unknown error")
                    self.plan_image_label.setText(f"❌ Screenshot failed: {error_msg}")
            else:
                self.plan_image_label.setText(f"❌ Server error: {response.status_code}")
                
        except Exception as e:
            self.plan_image_label.setText(f"❌ Error taking screenshot: {str(e)}")
            print(f"Error taking screenshot: {e}")

    def receive_heatmap_analysis(self):
        """Retrieve and display heatmap analysis results from the server"""
        try:
            print("🔍 Retrieving heatmap analysis...")
            
            response = requests.get("http://127.0.0.1:5000/heatmap_analysis", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Server response data: {data}")
                
                heatmap_points = data.get("heatmap_data_points", 0)
                concept = data.get("concept", "No concept defined")
                analysis = data.get("analysis", {})
                has_analysis = data.get("has_analysis", False)
                
                print(f"   Heatmap points: {heatmap_points}")
                print(f"   Concept: {concept}")
                print(f"   Has analysis: {has_analysis}")
                
                if has_analysis and analysis:
                    # Display the heatmap analysis results
                    self.display_heatmap_analysis(analysis, concept, heatmap_points)
                else:
                    print("   ⚠️ No heatmap analysis available")
                    # Create message to prompt for heatmap data
                    prompt_html = """
                        <div style='text-align: center; color: #1976d2; padding: 20px;'>
                            <h3 style='font-size: 20px; margin-bottom: 15px;'>🌡️ Heatmap Activity Analysis</h3>
                            <p style='font-size: 16px; margin: 8px 0;'>No heatmap data available for analysis.</p>
                            <p style='font-size: 16px; margin: 8px 0;'>Send mesh coordinates and UTCI values from Grasshopper to get activity recommendations.</p>
                            <p style='font-size: 14px; margin: 8px 0; color: #666;'>Format: [mesh_coordinate, utci_value]</p>
                        </div>
                    """
                    
                    # Add to existing results
                    current_html = self.climate_results.toHtml()
                    if current_html.strip():
                        new_html = current_html + prompt_html
                    else:
                        new_html = prompt_html
                    self.climate_results.setHtml(new_html)
                    
            else:
                print(f"   ❌ Server returned error status: {response.status_code}")
                error_html = f"""
                    <div style='text-align: center; color: #c62828; padding: 20px;'>
                        <h3 style='font-size: 20px; margin-bottom: 15px;'>❌ Failed to retrieve heatmap analysis</h3>
                        <p style='font-size: 16px; margin: 8px 0;'>Server returned status code: {response.status_code}</p>
                        <p style='font-size: 16px; margin: 8px 0;'>Response: {response.text}</p>
                    </div>
                """
                
                # Add to existing results
                current_html = self.climate_results.toHtml()
                if current_html.strip():
                    new_html = current_html + error_html
                else:
                    new_html = error_html
                self.climate_results.setHtml(new_html)
                
        except Exception as e:
            print(f"   ❌ Exception occurred: {str(e)}")
            error_html = f"""
                <div style='text-align: center; color: #c62828; padding: 20px;'>
                    <h3 style='font-size: 20px; margin-bottom: 15px;'>❌ Error retrieving heatmap analysis</h3>
                    <p style='font-size: 16px; margin: 8px 0;'>Error: {str(e)}</p>
                    <p style='font-size: 16px; margin: 8px 0;'>Please check if the server is running and accessible.</p>
                </div>
            """
            
            # Add to existing results
            current_html = self.climate_results.toHtml()
            if current_html.strip():
                new_html = current_html + error_html
            else:
                new_html = error_html
            self.climate_results.setHtml(new_html)

    def display_heatmap_analysis(self, analysis, concept, heatmap_points):
        """Display heatmap analysis results in the climate results panel"""
        try:
            # Extract analysis components from the actual server response format
            total_points = analysis.get("total_points", 0)
            average_utci = analysis.get("average_utci", 0)
            min_utci = analysis.get("min_utci", 0)
            max_utci = analysis.get("max_utci", 0)
            comfortable_zones = analysis.get("comfortable_zones", 0)
            hot_zones = analysis.get("hot_zones", 0)
            cold_zones = analysis.get("cold_zones", 0)
            comfort_percentage = analysis.get("comfort_percentage", 0)
            recommendations = analysis.get("recommendations", [])
            
            # Calculate percentages for display
            total_analyzed = comfortable_zones + hot_zones + cold_zones
            comfortable_percentage = (comfortable_zones / total_analyzed * 100) if total_analyzed > 0 else 0
            hot_percentage = (hot_zones / total_analyzed * 100) if total_analyzed > 0 else 0
            cold_percentage = (cold_zones / total_analyzed * 100) if total_analyzed > 0 else 0
            
            # Debug: Print the actual values
            print(f"DEBUG: comfort_percentage = {comfort_percentage}")
            print(f"DEBUG: average_utci = {average_utci}")
            print(f"DEBUG: comfortable_percentage = {comfortable_percentage}")
            
            # Create heatmap analysis display
            heatmap_html = f"""
            <div style='padding: 20px; background-color: #f8f9fa; border-radius: 8px; margin: 10px 0;'>
                <h3 style='font-size: 28px; margin-bottom: 20px; font-weight: bold;'>🗺️ Heatmap Activity Analysis</h3>
                <div style='background-color: white; padding: 25px; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                    <p style='font-size: 18px; margin: 12px 0;'><strong>Data Points Analyzed:</strong> {heatmap_points}</p>
                    <p style='font-size: 18px; margin: 12px 0;'><strong>UTCI Range:</strong> {min_utci:.1f}°C to {max_utci:.1f}°C</p>
                    <p style='font-size: 18px; margin: 12px 0;'><strong>Average UTCI:</strong> {average_utci:.1f}°C</p>
                    
                    <div style='margin: 25px 0;'>
                        <h4 style='font-size: 24px; margin-bottom: 20px; font-weight: bold;'>🌡️ Thermal Zone Distribution</h4>
                        <table style='width: 100%; border-collapse: collapse; font-size: 18px;'>
                            <thead>
                                <tr style='background-color: #f8f9fa;'>
                                    <th style='padding: 15px; text-align: left; border: 2px solid #dee2e6; font-weight: bold;'>Thermal Zone</th>
                                    <th style='padding: 15px; text-align: center; border: 2px solid #dee2e6; font-weight: bold;'>Percentage</th>
                                    <th style='padding: 15px; text-align: center; border: 2px solid #dee2e6; font-weight: bold;'>Count</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td style='padding: 15px; border: 2px solid #dee2e6; font-weight: bold;'>Comfortable (9-26°C)</td>
                                    <td style='padding: 15px; text-align: center; border: 2px solid #dee2e6; font-size: 20px;'>{comfortable_percentage:.1f}%</td>
                                    <td style='padding: 15px; text-align: center; border: 2px solid #dee2e6;'>{comfortable_zones}</td>
                                </tr>
                                <tr>
                                    <td style='padding: 15px; border: 2px solid #dee2e6; font-weight: bold;'>Heat Stress (>26°C)</td>
                                    <td style='padding: 15px; text-align: center; border: 2px solid #dee2e6; font-size: 20px;'>{hot_percentage:.1f}%</td>
                                    <td style='padding: 15px; text-align: center; border: 2px solid #dee2e6;'>{hot_zones}</td>
                                </tr>
                                <tr>
                                    <td style='padding: 15px; border: 2px solid #dee2e6; font-weight: bold;'>Cold Stress (<9°C)</td>
                                    <td style='padding: 15px; text-align: center; border: 2px solid #dee2e6; font-size: 20px;'>{cold_percentage:.1f}%</td>
                                    <td style='padding: 15px; text-align: center; border: 2px solid #dee2e6;'>{cold_zones}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <div style='margin: 25px 0;'>
                        <h4 style='font-size: 24px; margin-bottom: 20px; font-weight: bold;'>🎯 Design Recommendations</h4>
                        <div style='background-color: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #007bff;'>
                            <h5 style='font-size: 20px; margin-bottom: 15px; font-weight: bold;'>Based on your thermal analysis:</h5>
                            <ul style='margin: 0; padding-left: 20px; font-size: 18px;'>
            """
            
            # Add recommendations
            if recommendations:
                for recommendation in recommendations:
                    heatmap_html += f"<li style='margin: 10px 0;'>{recommendation}</li>"
            else:
                heatmap_html += """
                                <li style='margin: 10px 0;'>🌱 Consider adding more vegetation for better thermal comfort</li>
                                <li style='margin: 10px 0;'>💧 Add water features for evaporative cooling</li>
                                <li style='margin: 10px 0;'>🏗️ Optimize building orientation and add shade structures</li>
                """
            
            heatmap_html += f"""
                            </ul>
                        </div>
                    </div>
                    
                    <div style='margin: 25px 0;'>
                        <h4 style='font-size: 24px; margin-bottom: 20px; font-weight: bold;'>📋 Activity Zone Guidelines</h4>
                        <div style='background-color: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #28a745;'>
                            <h5 style='font-size: 20px; margin-bottom: 15px; font-weight: bold;'>Optimal Activity Placement:</h5>
                            <ul style='margin: 0; padding-left: 20px; font-size: 18px;'>
                                <li style='margin: 10px 0;'>🎯 Place high-activity functions in comfortable thermal zones ({comfortable_percentage:.1f}% of your space)</li>
                                <li style='margin: 10px 0;'>🌳 Use heat stress areas for water features and shade structures</li>
                                <li style='margin: 10px 0;'>☀️ Place seating and relaxation areas in zones with moderate temperatures</li>
                                <li style='margin: 10px 0;'>🕐 Consider time-of-day usage patterns when assigning activities</li>
                                <li style='margin: 10px 0;'>🔄 Create flexible spaces that can adapt to changing thermal conditions</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div style='margin: 25px 0;'>
                        <h4 style='font-size: 24px; margin-bottom: 20px; font-weight: bold;'>📊 Analysis Summary</h4>
                        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 20px;'>
                            <div style='background-color: #e3f2fd; padding: 20px; border-radius: 6px; text-align: center;'>
                                <h5 style='font-size: 18px; margin-bottom: 10px; font-weight: bold;'>Overall Comfort</h5>
                                <p style='font-size: 24px; font-weight: bold; color: #1976d2;'>{comfort_percentage:.1f}%</p>
                                <p style='font-size: 14px; color: #666;'>of space is thermally comfortable</p>
                            </div>
                            <div style='background-color: #fff3e0; padding: 20px; border-radius: 6px; text-align: center;'>
                                <h5 style='font-size: 18px; margin-bottom: 10px; font-weight: bold;'>Average Temperature</h5>
                                <p style='font-size: 24px; font-weight: bold; color: #f57c00;'>{average_utci:.1f}°C</p>
                                <p style='font-size: 14px; color: #666;'>UTCI across all points</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
            
            # Get current HTML content
            current_html = self.climate_results.toHtml()
            
            # Check if heatmap analysis already exists
            if "Heatmap Activity Analysis" not in current_html:
                print("   Adding new heatmap analysis...")
                # Add to existing results
                if current_html.strip():
                    new_html = current_html + heatmap_html
                else:
                    new_html = heatmap_html
                self.climate_results.setHtml(new_html)
            else:
                print("   Replacing existing heatmap analysis...")
                # Replace existing heatmap analysis
                lines = current_html.split('\n')
                new_lines = []
                skip_heatmap = False
                for line in lines:
                    if "Heatmap Activity Analysis" in line:
                        skip_heatmap = True
                    elif skip_heatmap and "</div>" in line and "background-color: #f8f9fa" in line:
                        skip_heatmap = False
                        continue
                    if not skip_heatmap:
                        new_lines.append(line)
                
                # Add new heatmap analysis
                new_html = '\n'.join(new_lines) + heatmap_html
                self.climate_results.setHtml(new_html)
            
            print("   ✅ Heatmap analysis displayed successfully!")
            
        except Exception as e:
            print(f"   ❌ Error displaying heatmap analysis: {str(e)}")
            error_html = f"""
                <div style='text-align: center; color: #c62828; padding: 20px;'>
                    <h3 style='font-size: 20px; margin-bottom: 15px;'>❌ Error displaying heatmap analysis</h3>
                    <p style='font-size: 16px; margin: 8px 0;'>Error: {str(e)}</p>
                </div>
            """
            
            # Add to existing results
            current_html = self.climate_results.toHtml()
            if current_html.strip():
                new_html = current_html + error_html
            else:
                new_html = error_html
            self.climate_results.setHtml(new_html)

    def send_concept_to_server(self):
        """Send the current concept to the server for heatmap analysis"""
        try:
            if hasattr(self, 'concept') and self.concept:
                headers = {'Content-Type': 'application/json'}
                response = requests.post(
                    "http://127.0.0.1:5000/concept",
                    json={"concept": self.concept},
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"✅ Concept sent to server: {self.concept[:50]}...")
                else:
                    print(f"❌ Failed to send concept to server: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Error sending concept to server: {e}")


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