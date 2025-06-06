import sys
import requests
from llm_calls import *
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QTextBrowser, QHBoxLayout
)
import re


class FlaskClientChatUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Assistant")
        self.setGeometry(200, 200, 800, 800)
        self.phases = {
            "concept": [],
            "functions": [],
            "attributes": [],
        }
        self.current_phase = "concept"

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
        input_layout.addWidget(self.input_field)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        # Continue button (hidden by default)
        self.continue_button = QPushButton("Continue")
        self.continue_button.clicked.connect(self.handle_continue)
        self.continue_button.hide()  # Hide initially
        layout.addWidget(self.continue_button)

        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.handle_back)
        self.back_button.hide()  # Hide initially
        layout.addWidget(self.back_button)


        # Set central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.update_phase_buttons()

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
            llm_response = route_query_to_function(self.current_phase, self.phases[self.current_phase])
            self.phases[self.current_phase].append({'role': 'assistant', 'content': llm_response})

            if (self.current_phase == "functions"):
                json_llm_response = extract_json(llm_response)
                self.extracted_functions = json_llm_response["external_functions"]
                self.set_extracted_functions()
            
            # Display the user's message in the chat window
            self.chat_display.append(f"<b>You:</b> {message}")

            # Display the server's response in the chat window
            self.chat_display.append(f"<b>Assistant:</b> {llm_response}")
            self.continue_button.show()  # Show continue button for next phase
            self.update_phase_buttons()
    
            # func_response = requests.post(
            #     "http://127.0.0.1:5000/llm_call/extract_external_functions",
            #     json={"functions": external_functions}
            # )
            # func_data = func_response.json()
            # external_functions = func_data.get("external_functions", [])
           

            
            # Send the concept text to Grasshopper
            # response = requests.post(
            #     "http://127.0.0.1:5000/send_to_grasshopper",
            #     json={"functions": external_functions}
            # )
            # response_data = response.json()
            # print(f"Response from Grasshopper: {response_data}")
            # if response.status_code == 200:
            #     self.chat_display.append("<i>Sent external functions to Grasshopper.</i>")
            # else:
            #     self.chat_display.append("<span style='color: red;'>Failed to send to Grasshopper.</span>")


        except Exception as e:
            self.chat_display.append("<span style='color: red;'>Error connecting to the server.</span>")
            print(f"Error: {e}")
        

    def handle_continue(self):
        phases = list(self.phases.keys())
        current_index = list(phases).index(self.current_phase)
        if current_index < len(phases) - 1:
            self.current_phase = phases[current_index + 1]
            self.chat_display.append(f"<b>Phase changed to:</b> {self.current_phase}")
            self.continue_button.hide()
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
        self.update_phase_buttons()

    def get_plot_area(self):
        plot_area = None
        try:
            plot_area_response = requests.get("http://127.0.0.1:5000/plot_area")
            print(f"Plot area response status: {plot_area_response.status_code}")
            plot_area = plot_area_response.json()
            print("plot_area", plot_area)
        except Exception as e:
            self.chat_display.append("<span style='color: red;'>Error fetching plot area from Grasshopper.</span>")
            print(f"Error fetching plot area: {e}")
        return plot_area
    
    def set_extracted_functions(self):
        try:
            response = requests.post(
                "http://localhost:5000/external_functions",
                json={"functions": self.extracted_functions}),
        except Exception as e:
            self.chat_display.append("<span style='color: red;'>Error extracting functions.</span>")
            print(f"Error setting functions: {e}")
            return
        
def extract_json(body):
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
