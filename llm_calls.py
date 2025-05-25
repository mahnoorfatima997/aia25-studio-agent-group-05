import json
from server.config import *

with open("knowledge/merged.json", "r") as file:
    json_data = json.load(file)

# # Convert the JSON data to a string
json_data_str = json.dumps(json_data)

def classify_input(message):
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": """
                        Your task is to classify if the user message is related to buildings and architecture or not.
                        You should NOT try to answer the user message. Your only job is to classify the message
                        If it is related to architecture, you should output "Related", and if not, output "Refuse to answer".

                        # Example #
                        User message: "How do I bake cookies?"
                        Output: "Refuse to answer"

                        User message: "What is the tallest skyscrapper in the world?"
                        Output: "Related"
                        """,
            },
            {
                "role": "user",
                "content": f"""
                        {message}
                        """,
            },
        ],
    )
    return response.choices[0].message.content


# def generate_concept(message):
#     response = client.chat.completions.create(
#         model=completion_model,
#         messages=[
#             {
#                 "role": "system",
#                 "content": """
#                         You are a leading landscape architect and designer.

#                         Your task is to generate a **short**, **clear**, and **practical** concept for a courtyard design based on the user's input and the provided attributes.

#                         Limit your response to **a single paragraph**, **no more than 3 sentences** total. Use concise language.

#                         Mention:
#                         - Key spatial strategies
#                         - Suggested materials
#                         - General use of areas

#                         Then, include all relevant spatial areas and performance scores in the following format:

#                         "We envision an outdoor space with a total plot area of {plot_area} sqm, centered around a courtyard of {courtyard_area} sqm. The design includes {area_descriptions}. The site supports {tree_count} trees across {tree_species_count} different species. This design approach scores {score_list}."

#                         Where:
#                         - `{area_descriptions}` is a list of all area types (e.g., social, calm, permeable, garden) and their sizes (e.g., "20 sqm of social zones, 15 sqm of calm spaces").
#                         - `{score_list}` includes values for performance metrics such as health, biodiversity, open space quality, and integration (e.g., "8.5 for health benefits, 7.2 for biodiversity").

#                         Only use the attributes provided in the JSON. Do not assume or fabricate additional ones. Do not include explanations or extra information.
#                         """,
#             },
#             {
#                 "role": "user",
#                 "content": f"""
#                         What are the concepts and parameters behind this courtyard design? 
#                         Initial information: {message}
#                         """,
#             },
#         ],
#     )
#     return response.choices[0].message.content

def generate_concept_with_conversation(conversation_messages):
    chat_messages = [
            {
                "role": "system",
                "content": """
                        You are a leading landscape architect and designer.

                        Your task is to generate a **short**, **clear**, and **practical** concept for a courtyard design based on the user's input and the provided attributes.

                        Limit your response to **a single paragraph**, **no more than 3 sentences** total. Use concise language.

                        Mention:
                        - Key spatial strategies
                        - Suggested materials
                        - General use of areas

                        Then, include all relevant spatial areas and performance scores in the following format:

                        "We envision an outdoor space with a total plot area of {plot_area} sqm, centered around a courtyard of {courtyard_area} sqm. The design includes {area_descriptions}. The site supports {tree_count} trees across {tree_species_count} different species. This design approach scores {score_list}."

                        Where:
                        - `{area_descriptions}` is a list of all area types (e.g., social, calm, permeable, garden) and their sizes (e.g., "20 sqm of social zones, 15 sqm of calm spaces").
                        - `{score_list}` includes values for performance metrics such as health, biodiversity, open space quality, and integration (e.g., "8.5 for health benefits, 7.2 for biodiversity").

                        Only use the attributes provided in the JSON. Do not assume or fabricate additional ones. Do not include explanations or extra information.
                        """,
            },
        ]
    chat_messages.extend(conversation_messages)
    
    print(type(chat_messages)) # Debugging line')
    print("Generating concept with conversation history...")
    print("Conversation messages:", chat_messages)
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages
    )
    return response.choices[0].message.content


def extract_weights_with_conversation(conversation_messages):
    chat_messages = [
            {
                "role": "system",
                "content": """

                        Your task is to examine the user prompt, attributes and the previous conversation history to generate a list of area categories with their relative weights. Assign a value between **"1"** (not included) and **"20"** (dominant feature) for each provided area category. Use only the categories based on the text. These values should be scaled based on their relative size or importance in the design.

                        **Format your output exactly like this:**

                        # Example Output:
                        {
                        "calm area": "5",
                        "playground": "12",
                        "social area": "8",
                        "permeable ground": "15",
                        }
                        
                        Do **not** include any explanation, notes, or extra text — just the json.

                        """,
            },
        ]
    chat_messages.extend(conversation_messages)
    print("Extracting weights with conversation history...")
    print("Conversation messages:", chat_messages)
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
        response_format=
                {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "attributes",
                        "description": "Extracted design-related attributes from the text",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "additionalProperties": {
                                "type": "string"
                            }
                        }
                    }
                }
    )
    return response.choices[0].message.content


def extract_locations_with_conversation(conversation_messages):
    chat_messages = [
            {
                "role": "system",
                "content": """

                        Your task is to determine the placement of each functional zone on a 20 by 20 grid courtyard, based on the user's design intent and the relative importance (weights) of each zone.

                        The grid is defined with X and Y axes:
                        - X ranges from 0 to 19 (left to right)
                        - Y ranges from 0 to 19 (bottom to top)

                        You will be given a list of functional zones, along with their relative weights. Use these to decide appropriate placements. Zones with higher weights should be placed in more central, accessible, or prominent positions as inferred from the prompt.

                        Your output must use this **exact format**:
                        {
                        "Function1": [X, Y],
                        "Function2": [X, Y],
                        ...
                        }
                        Only include the functions provided in the input. Each `[X, Y]` should be a pair of integers between 0 and 19. 
                        
                        Do **not** include any explanation, notes, or extra text — just the json.

                        """,
            },
        ]
    chat_messages.extend(conversation_messages)
    print("Extracting locations with conversation history...")
    print("Conversation messages:", chat_messages)
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
    )
    return response.choices[0].message.content


def extract_connections_with_conversation(conversation_messages):
    chat_messages = [
            {
                "role": "system",
                "content": """

                You are assisting in the spatial design of a courtyard.

                The user has already provided a design concept and a set of extracted spatial attributes earlier in this conversation. From those inputs, your task is to:

                Identify the relevant functional zones mentioned in the concept and attributes.

                Build a list of these functional zones in the order they are inferred from the inputs.

                Determine which zones should be connected or adjacent, based on:

                1. Design intent (from the concept)
                2. Functional needs or compatibility (from the attributes)
                3. General principles of spatial planning (e.g., gathering zones may connect to social zones, calm areas may avoid noisy zones)

                You are not placing zones spatially. You are only identifying logical adjacency relationships.

                Output Instructions:
                Output only a JSON array of index pairs, where each pair [a, b] means the zone at index a should connect to the zone at index b.

                The order of the list should match the inferred zone list from step 1.

                Do not include any explanation, text, or metadata — just the final result in the format below:

                **Example Output:**
                {
                "connections": [[0, 2], [1, 3], [4, 5]]
                }
                        """,
            },
        ]
    chat_messages.extend(conversation_messages)
    print("Extracting locations with conversation history...")
    print("Conversation messages:", chat_messages)
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
    )
    return response.choices[0].message.content

def extract_targets_with_conversation(conversation_messages):
    chat_messages = [
            {
                "role": "system",
                "content": """

                You are assisting in the spatial design of a courtyard.

                The user has already provided a design concept, extracted spatial attributes, and a list of functional zones with inferred adjacency relationships earlier in this conversation. The courtyard is divided into discrete numbered cells.

                From this information, your task is to:

                Assign each functional zone from the list to a specific cell number in the courtyard based on:

                1. Spatial logic from the adjacency relationships (e.g., adjacent zones should be placed in neighboring or strategically close cells)
                2. Design intent (from the concept)
                3. Environmental considerations (e.g., calm zones oriented to shaded or enclosed areas; active zones to open or sunny areas)
                4. General spatial planning principles (e.g., entries near entrances, buffers between conflicting functions)

                Important Notes:

                1. You are not generating geometry or visual layout.
                2. You are assigning zone indices to cell numbers based on the best spatial fit inferred from context and adjacency.
                3. You may assume the courtyard cell numbers are provided in a numbered grid and you have freedom to assign any zone to any cell.
                4. Each zone index should be mapped to a single unique cell number.

                Output Instructions:
                Output only a JSON array of index-cell pairs, where each pair [a, b] means the zone at index a should be placed at cell b in the courtyard.

                Do not include any explanation, text, or metadata — just the final result in the format below:

                **Example Output:**
                {
                "targets": [[0, 2], [1, 3], [4, 5]]
                }
                        """,
            },
        ]
    chat_messages.extend(conversation_messages)
    print("Extracting locations with conversation history...")
    print("Conversation messages:", chat_messages)
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
    )
    return response.choices[0].message.content


def generate_casestudies(message):
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": """
                        Based on the user's courtyard design intent, identify one or two case studies that are most relevant.

                        The case studies must relate specifically to the courtyard’s key goals and features, such as:
                        - Social interaction
                        - Child-friendly design
                        - Elderly comfort
                        - Biodiversity
                        - Health and well-being
                        - Calm or quiet zones
                        - Flower planting
                        - Tree placement and species diversity
                        - Open space quality
                        - Permeability
                        - Design integration

                        Only select case studies that closely match the user’s priorities and spatial strategies.

                        For each case study, provide:
                        - The name and location
                        - A **short paragraph** describing the courtyard design and why it is relevant

                        Respond with no more than two case studies. Do not include explanations or general commentary outside the case study descriptions.

                        """,
            },
            {
                "role": "user",
                "content": f"""
                        {message}
                        """,
            },
        ],
    )
    return response.choices[0].message.content


def generate_prompt(message):
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": """
                        Depending on the user's input and the results of the previous steps, generate a prompt for an image generation model.
                        The prompt should be a detailed description of the courtyard design, but limit it to one paragraph. It should not exceed 150 words.
                        Do not add any extra information or explanations.
                        Example:
                        
                        Input:
                        We envision an outdoor space with a total plot area of 1,200 sqm, centered around a courtyard of 400 sqm. The design includes 120 sqm of calm areas for relaxation and 180 sqm of social zones for gathering. To enhance environmental quality, the site features 300 sqm of permeable ground and supports 12 trees across three different species (oak, maple, and cherry). Additionally, 80 sqm is allocated for flower beds to boost biodiversity. This design approach scores 8/10 for health benefits, 9/10 for biodiversity value, 7/10 for open space quality, and 8.5/10 for design integration.

                        Output:
                        A serene courtyard design featuring a 400 sqm central area surrounded by 120 sqm of calm spaces and 180 sqm of social zones. The design incorporates 300 sqm of permeable surfaces, enhancing environmental quality. Twelve trees from three species (oak, maple, cherry) provide shade and biodiversity, while 80 sqm of flower beds add color and attract pollinators. The layout promotes relaxation and social interaction, with modular furniture and flexible lighting. The design scores 8/10 for health benefits, 9/10 for biodiversity value, 7/10 for open space quality, and 8.5/10 for design integration.
                        """,
            },
            {
                "role": "user",
                "content": f"""
                        {message}
                        """,
            },
        ],
    )
    return response.choices[0].message.content


# def extract_attributes(message):
#     response = client.chat.completions.create(
#         model=completion_model,
#         messages=[
#             {
#                 "role": "system",
#                 "content": """

#                         You are a keyword and parameter extraction assistant.

#                         Your task is to read a given concept description and extract specific attributes according to the categories below. Focus only on **vegetation and material-related elements**.

#                         # Categories #
#                         1. **Tree species**: List all mentioned species or write "None" if not specified.
#                         2. **Tree number**: Extract as a string (e.g., "12").
#                         3. **Flower types**: List the flower types mentioned or write "None".
#                         4. **Materials**: List only physical materials used in the design (e.g., wood, steel, brick, glass). Use lowercase. Separate multiple materials with commas.

#                         # Rules #
#                         - If an attribute is not mentioned, write `"None"` for that field.
#                         - Do not generate new values; only extract from the input.
#                         - Only output the JSON — no explanations, extra text, or formatting characters.
#                         - Begin your output with `{` and end with `}`.
#                         - Use lowercase for all items in "materials" and "flower_types".
#                         - Separate multiple items in lists with commas (no bullet points or line breaks).
#                         - Always include all four fields in the output, even if some are "None".

#                         # Example Output #
#                         {
#                         "tree_species": "oak,maple,cherry",
#                         "tree_number": "12",
#                         "flower_types": "lavender,daffodil",
#                         "materials": "wood,concrete"
#                         }
#                         """,
#             },
#             {
#                 "role": "user",
#                 "content": f"""
#                         # GIVEN TEXT # 
#                         {message}
#                         """,
#             },
#         ],
#         response_format=
#                 {
#                 "type": "json_schema",
#                 "json_schema": {
#                     "name": "attributes",
#                     "description": "Extracted vegetation and material attributes from the text",
#                     "strict": "true",
#                     "schema": {
#                     "type": "object",
#                     "properties": {
#                         "tree_species": {
#                         "type": "array",
#                         "items": { "type": "string" }
#                         },
#                         "tree_number": {
#                         "type": "string"
#                         },
#                         "flower_types": {
#                         "type": "array",
#                         "items": { "type": "string" }
#                         },
#                         "materials": {
#                         "type": "array",
#                         "items": { "type": "string" }
#                         }
#                     },
#                     "required": ["tree_species", "tree_number", "flower_types", "materials"]
#                     }
#                 }
#                 }

#     )
#     return response.choices[0].message.content

def extract_attributes_with_conversation(conversation_messages):
    chat_messages = [
            {
                "role": "system",
                "content": """

                        You are a keyword and parameter extraction assistant.

                        Your task is to read a given design concept description and extract all specific design-related attributes as key–value pairs.

                        # Instructions:
                        - Each key must be a **concise, lowercase design parameter** (e.g., "tree species", "bench count", "materials", "path width").
                        - Each value must be **directly lifted or inferred verbatim** from the input (no assumptions or guesses).
                        - Use lowercase for keys and string values unless the original text uses capitalized proper nouns (e.g., “Japanese maple”).
                        - Output in a single flat JSON object.
                        - Include all **quantities, types, dimensions, uses, species, materials, and named spaces** mentioned in the description.
                        - If multiple values are present, separate them with commas as a single string (e.g., "lavender,daffodil").

                        # Output Format:
                        - Only output the JSON — no explanations, extra text, or formatting characters.
                        - Begin your output with `{` and end with `}`.

                        # Example Output:
                        {
                        "tree species": "oak,maple",
                        "tree count": "12",
                        "flower types": "lavender,daffodil",
                        "materials": "brick,wood",
                        "bench count": "4",
                        "path width": "2 meters",
                        "courtyard area": "35 sqm"
                        }

                        """,
            },
        ]
    chat_messages.extend(conversation_messages)
    print("Extracting attributes with conversation history...")
    print("Conversation messages:", chat_messages)
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
        response_format=
                {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "attributes",
                        "description": "Extracted design-related attributes from the text",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "additionalProperties": {
                                "type": "string"
                            }
                        }
                    }
                }
    )
    return response.choices[0].message.content

def extract_spaces_with_conversation(conversation_messages):
    chat_messages = [
            {
                "role": "system",
                "content": """

                        You are a spatial functions extraction assistant.

                        Your task is to read a given design concept description and extract all specific possible spaces as key–value pairs.

                        # Instructions:
                        - Each key must be a **concise, lowercase design parameter** (e.g., "tree species", "bench count", "materials", "path width").
                        - Each value must be **directly lifted or inferred verbatim** from the input (no assumptions or guesses).
                        - Use lowercase for keys and string values unless the original text uses capitalized proper nouns (e.g., “Japanese maple”).
                        - Output in a single flat JSON object.
                        - Include all **quantities, types, dimensions, uses, species, materials, and named spaces** mentioned in the description.
                        - If multiple values are present, separate them with commas as a single string (e.g., "lavender,daffodil").

                        # Output Format:
                        - Only output the JSON — no explanations, extra text, or formatting characters.
                        - Begin your output with `{` and end with `}`.

                        # Example Output:
                        {
                        "tree species": "oak,maple",
                        "tree count": "12",
                        "flower types": "lavender,daffodil",
                        "materials": "brick,wood",
                        "bench count": "4",
                        "path width": "2 meters",
                        "courtyard area": "35 sqm"
                        }

                        """,
            },
        ]
    chat_messages.extend(conversation_messages)
    print("Extracting attributes with conversation history...")
    print("Conversation messages:", chat_messages)
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
        response_format=
                {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "attributes",
                        "description": "Extracted design-related attributes from the text",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "additionalProperties": {
                                "type": "string"
                            }
                        }
                    }
                }
    )
    return response.choices[0].message.content


def create_question(message):
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": """
                        # Instruction #
                        You are a thoughtful research assistant specializing in architecture.
                        Your task is to create a targeted question based on the text to facilitate courtyard design.
                        Imagine the question will be answered using a detailed text about courtyard design and related elements and scores.
                        Output only the question, without any extra text.

                        # Examples #
                        - What layout principles can help organize a courtyard with distinct zones for trees, social areas, flowers, and quiet relaxation?
                        - How does the design of this courtyard contribute to biodiversity and environmental sustainability?
                        - What are the key elements of this courtyard design that enhance social interaction and community engagement?
                        - How could the design of this courtyard be improved to better integrate with the surrounding environment?
                        - What are some critical aspects of this courtyard design that one should be aware of when considering its impact on health and well-being?

                        # Important #
                        Keep the questions targeted and relevant to the courtyard design. Avoid vague or overly broad questions. The goal is to elicit specific information that can guide the design process.
                        """,
            },
            {
                "role": "user",
                "content": f"""
                        {message}
                        """,
            },
        ],
    )
    return response.choices[0].message.content



