from server.config import *
from llm_calls import *
from utils.rag_utils import rag_call
import json
import requests

user_message = "How would I design a 100 sqm courtyard in a cold climate?"

# URL of the Flask server
url = 'http://localhost:5000/llm_call'

# Send the user message to the server
payload = {'input': user_message}
response = requests.post(url, json=payload)

if response.status_code == 200:
    data = response.json()
    print("✅ Response from server:")
    print(json.dumps(data, indent=4))
else:
    print("❌ Failed to connect or server error:", response.status_code)

### EXAMPLE 1: Router ###
# Classify the user message to see if we should answer or not
router_output = classify_input(user_message)
if router_output == "Refuse to answer":
    llm_answer = "Sorry, I can only answer questions about architecture."

else:
    print(router_output)
    ### EXAMPLE 2: Simple call ###
    # simple call to LLM, try different sys prompt flavours
    brainstorm = generate_concept(user_message)
    print(brainstorm)

    casestudies = generate_casestudies(user_message)
    print(casestudies)

    imageprompt = generate_prompt(user_message)
    print(imageprompt)

    ### EXAMPLE 4: Structured Output ###
    # extract the architecture attributes from the user
    # parse a structured output with regex
    attributes = extract_attributes(brainstorm)
    print(attributes)

        # Send to the server via test request
    payload = {'input': attributes}

    # The URL of the Flask server endpoint
    url = 'http://localhost:5000/llm_call'  

    # Send the request to your local server
    response = requests.post(url, json=payload)

    # Check if the server responded successfully
    if response.status_code == 200:
        data = response.json()
        attributes_from_server = data['attributes']
        print("Attributes from server:", attributes_from_server)

        # Proceed with your next steps (parsing, using the attributes, etc.)
        try:
            shape, theme, materials, parameters = (
                attributes_from_server[k] for k in ("shape", "theme", "materials", "parameters")
            )
        except KeyError as e:
            print(f"Error: Missing attribute - {e}")
            exit(1)

    attributes = attributes.strip()
    # Load the JSON file
    with open("knowledge/merged.json", "r") as file:
        json_data = json.load(file)

# Convert the JSON data to a string
    json_data_str = json.dumps(json_data)

# Extract attributes
    attributes = extract_attributes(brainstorm)
    # print("Raw attributes:", attributes)

# Parse the JSON
    try:
        attributes = json.loads(attributes)
    except json.JSONDecodeError as e:
        print("JSON decoding error:", e)
        print("Invalid JSON:", attributes)
        exit(1)

    # print("Parsed attributes:", attributes)
    
# Extract the first JSON object if there is extra data
#     import re
#     match = re.search(r'\{.*\}', attributes, re.DOTALL)
#     if match:
#         attributes = match.group(0)
#     else:
#         print("No valid JSON object found in attributes.")
#         exit(1)

# # Parse the JSON
#     attributes = attributes.strip()
#     try:
#         attributes = json.loads(attributes)
#     except json.JSONDecodeError as e:
#         print("JSON decoding error:", e)
#         print("Invalid JSON:", attributes)
#         exit(1)

    shape, theme, materials, parameters = (attributes[k] for k in ("shape", "theme", "materials", "parameters"))

    ### EXAMPLE 3: Chaining ###
    courtyard_question = create_question(theme)
    print(courtyard_question)
    # call llm with the output of a previous call

    ### EXAMPLE 5: RAG ####
    # Get a response based on the knowledge found
    rag_result= rag_call(courtyard_question, embeddings = "knowledge/merged.json", n_results = 10)
    print(rag_result)

    #hi!