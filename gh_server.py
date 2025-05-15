from flask import Flask, request, jsonify
from server.config import *
from llm_calls import *
import json
import re

app = Flask(__name__)


@app.route('/llm_call', methods=['POST'])
def llm_call():
    data = request.get_json()
    input_string = data.get('input', '')

    classification = classify_input(input_string)
    print('Classification:', classification)

    concept = generate_concept(classification)
    print('Concept: ', concept)
    imageprompt = generate_prompt(concept)
    print('Image Prompt:', imageprompt)
    # Extract the attributes from the generated concept
    attributes = extract_attributes(concept)
    print('Attributes:', attributes)
    match = re.search(r'\{.*\}', attributes, re.DOTALL)
    if match:
        json_string = match.group(0)  # Extract the JSON part
        try:
            # Parse the JSON string
            parsed_json = json.loads(json_string)
            # print("Parsed JSON:", parsed_json)
        except json.JSONDecodeError as e:
            print("JSON decoding error:", e)
    else:
        print("No valid JSON found in the string.")

    # Update the return statement to include the JSON object
    return jsonify({'classification': classification, 'attributes': parsed_json, 'imageprompt': imageprompt})

if __name__ == '__main__':
    app.run(debug=True)