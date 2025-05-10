import gradio as gr
from llm_calls import generate_concept, extract_attributes

def process_input(user_input):
    # Generate the concept using the user input
    concept = generate_concept(user_input)
    
    # Extract attributes from the generated concept
    attributes = extract_attributes(concept)

    return concept, attributes

# Define the Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("""# Courtyard Design Assistant
    Enter details about your courtyard design, and the system will generate a concept and calculate parameters for you. This tool uses advanced AI to assist in creating sustainable and functional courtyard designs.
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

# Launch the Gradio app
demo.launch()
