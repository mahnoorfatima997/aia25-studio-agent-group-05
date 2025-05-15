import gradio as gr
from llm_calls import generate_concept, extract_attributes
import json

# --- Speckle Setup ---
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_default_account
from specklepy.objects.base import Base

# --- Setup Speckle client and project/model ---
account = get_default_account()
client = SpeckleClient(host=account.serverInfo.url)
client.authenticate_with_account(account)

# Use your own project ID and model name or create them manually beforehand
PROJECT_ID = "2d3cf081b5"
MODEL_NAME = "data"
VERSION_ID = "fe82df895d"

def send_to_speckle(attributes_dict):
    if not isinstance(attributes_dict, dict):
        print("Error: attributes_dict is not a dictionary")
        raise ValueError("attributes_dict must be a dictionary")

    base = Base()
    for key, value in attributes_dict.items():
        if isinstance(value, dict):  # Handle nested dictionaries
            nested_base = Base()
            for nested_key, nested_value in value.items():
                nested_base[nested_key] = nested_value
            base[key] = nested_base
        else:
            base[key] = value

    print("Populated Base object:", base)  # Debug print

    # Use the new Project/Model/Version API
    try:
        version_id = client.version.create(
            project_id=PROJECT_ID,  # Use the project ID
            model_name=MODEL_NAME,  # Name of the model
            object=base,  # Base object to send
            message="what kind of courtyard would be suitable for cold weather?",
            source_application="Gradio"
        )
        print("✅ Sent to Speckle with version ID:", version_id)
        return version_id

    except Exception as e:
        print("❌ Failed to send to Speckle:", e)
        raise e


# --- AI + Speckle Processing ---
def process_input(user_input):
    concept = generate_concept(user_input)
    attributes = extract_attributes(concept)

    # Parse attributes into a dictionary if it's a JSON string
    try:
        attributes = json.loads(attributes)  # Convert JSON string to dictionary
        print("Extracted attributes:", attributes)  # Debug print
    except json.JSONDecodeError as e:
        print("Error parsing attributes JSON:", e)
        return concept, "Error: Failed to parse attributes JSON."

    # Send to Speckle
    try:
        version_id = send_to_speckle(attributes)
        attributes["speckle_version"] = version_id
    except Exception as e:
        attributes["speckle_error"] = str(e)

    return concept, str(attributes)

# --- Gradio Interface ---
with gr.Blocks() as demo:
    gr.Markdown("""# Courtyard Design Assistant  
    Enter details about your courtyard design, and the system will generate a concept and calculate parameters for you. This tool uses AI and sends results to Speckle for downstream use in Grasshopper.
    """)

    with gr.Row():
        user_input = gr.Textbox(label="Enter courtyard details", placeholder="E.g., courtyard size, climate, etc.")

    with gr.Row():
        concept_output = gr.Textbox(label="Generated Concept", lines=5, interactive=False)
        attributes_output = gr.Textbox(label="Extracted Attributes", lines=10, interactive=False)

    submit_button = gr.Button("Generate")

    submit_button.click(
        process_input,
        inputs=[user_input],
        outputs=[concept_output, attributes_output]
    )

demo.launch()
