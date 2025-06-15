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


def generate_concept_with_conversation(conversation_messages):
    chat_messages = [
            {
                "role": "system",
                "content": """
                        You are a leading landscape architect and designer.

                        Your task is to generate a **short**, **clear**, and **practical** concept for a courtyard design based on the user's input and the provided attributes.

                        Limit your response to **a single paragraph**, **no more than 3 sentences** total. Use concise language. Make sure the areas add up to the total courtyard area. Keep one part of the courtyard open and accessible, with no proper function.

                        Mention:
                        - Key spatial strategies
                        - Suggested materials
                        - General use of areas

                        Then, include all relevant spatial areas and performance scores in the following format:

                        "We envision an outdoor space with a total courtyard area of {plot_area} sqm. The design includes {area_descriptions}. The site supports {tree_count} trees across {tree_species_count} different species. The advantages and disadvantages of the design are as follows: {advantages} and {disadvantages}."

                        Where:
                        - `{area_descriptions}` is a list of all area types (e.g., social, calm, permeable, garden) and their sizes (e.g., "20 sqm of social zones, 15 sqm of calm spaces").

                        Also develop a spatial matrix in the form of numbered relationships between the various areas and functions, assigning a grid point to each area based on its proximity to other areas. Be sure to include tree, play, rest, pond and flower as zones defining the courtyard division.

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


def extract_spaces(concept, external_functions, attributes):
    chat_messages = [
            {
                "role": "system",
                "content": """
                        You are a spatial functions extraction assistant.

                        Your task is to read the concept and attributes.

                        You must then identify the locations of these spaces and estimate the grid points where they are located based on the description.

                        # Space Type Mapping Rules:
                        - Map any garden spaces to either "flower" or "tree" based on their function
                        - Map any social/gathering spaces to "play"
                        - Map any quiet/contemplative spaces to "rest"
                        - Map any water features to "pond"
                        - Only use these exact space types: play, rest, pond, flower, tree

                        # Output Format:
                        Return a JSON object with a "spaces" key containing a mapping of space types to their grid points:
                        {
                            "spaces": {
                                "play": 1,    // integer grid point
                                "rest": 3,    // integer grid point
                                "pond": 5,    // integer grid point
                                "flower": 7,  // integer grid point
                                "tree": 9     // integer grid point
                            }
                        }

                        # Instructions:
                        - Each key must be one of: play, rest, pond, flower, tree
                        - Each value must be an integer grid point (1-10)
                        - You must include all 5 spaces
                        - If a space's location is not specified, assign it a grid point based on its function
                        - Do not include any explanations or extra text
                        - Only output the JSON object
                        """
            },
        ]
    chat_messages.append({
    "role": "user",
    "content": """
        Concept: {concept}
        Extracted Functions: {external_functions}
        Attributes: {attributes}
    """.format(
        concept=concept,
        external_functions=external_functions,
        attributes=attributes
    )
    })
    print("Extracting spaces...")
    print("Conversation messages:", chat_messages)
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "spaces",
                "description": "Extracted spaces and features from the design description",
                "schema": {
                    "type": "object",
                    "properties": {
                        "spaces": {
                            "type": "object",
                            "properties": {
                                "play": {"type": "integer"},
                                "rest": {"type": "integer"},
                                "pond": {"type": "integer"},
                                "flower": {"type": "integer"},
                                "tree": {"type": "integer"},
                            },
                            "required": ["play", "rest", "pond", "flower", "tree"],
                            "additionalProperties": False,
                        }
                    },
                    "required": ["spaces"],
                    "additionalProperties": False,
                }
            }
        }
    )
    print("Response from LLM for spaces:", response.choices[0].message.content)
    return response.choices[0].message.content

def extract_links(concept, external_functions=None):
    # Ensure external_functions is properly formatted
    if isinstance(external_functions, str):
        try:
            external_functions = json.loads(external_functions)
        except json.JSONDecodeError:
            print("Error: external_functions is not valid JSON")
            external_functions = {}
    
    # Extract the external_functions dictionary if it's nested
    if isinstance(external_functions, dict) and "external_functions" in external_functions:
        external_functions = external_functions["external_functions"]
    
    # Convert external_functions dict to list of names for the LLM
    external_function_names = list(external_functions.keys()) if external_functions else []
    
    # Define allowed courtyard zones
    ALLOWED_COURTYARD_ZONES = ["play", "rest", "pond", "flower", "tree"]
    
    chat_messages = [
        {
            "role": "system",
            "content": """
                You are assisting in the spatial design of a courtyard.

                Build relationships between these functional zones:

                Courtyard zones (ONLY use these exact names, no variations):
                - play (for any social or active spaces)
                - rest (for any quiet or contemplative spaces)
                - pond (for any water features)
                - flower (for any garden or planting areas)
                - tree (for any tree or shade areas)

                External functions:
                {external_functions}

                Determine which zones should be connected or adjacent, based on:

                1. Design intent (from the concept)
                2. Functional needs or compatibility (from the attributes)
                3. General principles of spatial planning (e.g., active zones near active zones, quiet areas near quiet areas)
                4. Logical relationships between external functions and courtyard zones (e.g., library might connect to rest areas, cafe might connect to play areas)

                You are not placing zones spatially. You are only identifying logical adjacency relationships.

                Output Instructions:
                Output a JSON object with a "links" key containing an object of relationships.
                Each relationship should be a pair of zone names that should be connected.
                Include both courtyard-to-courtyard and external-function-to-courtyard relationships.

                **Example Output:**
                {
                "links": {
                    "tree": "pond",
                    "tree": "flower",
                    "play": "rest",
                    "cafe": "play"
                }
                }

                Important Rules:
                1. ONLY use the exact courtyard zone names: play, rest, pond, flower, tree
                2. Map any social/gathering spaces to "play"
                3. Map any quiet/contemplative spaces to "rest"
                4. Map any water features to "pond"
                5. Map any garden/planting areas to "flower"
                6. Map any tree/shade areas to "tree"
                7. Include at least one connection for each external function
                8. Maintain existing courtyard zone relationships

                Do not use any other names or variations for the courtyard zones.
                """
            },
        ]
    chat_messages.append({
    "role": "user",
    "content": """
        Concept: {concept}
        External Functions: {external_functions}
    """.format(
        concept=concept,
        external_functions=json.dumps(external_function_names)
    )
    })
    print("Extracting links ...")
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "links",
                "description": "Extracted links from the design description",
                "schema": {
                    "type": "object",
                    "properties": {
                        "links": {
                            "type": "object",
                            "description": "Mapping of source nodes to their target nodes",
                            "additionalProperties": {
                                "type": "string",
                                "enum": ALLOWED_COURTYARD_ZONES + external_function_names
                            }
                        }
                    },
                    "required": ["links"],
                    "additionalProperties": False
                }
            }
        }
    )

    print("Response from LLM:", response.choices[0].message.content)
    return response.choices[0].message.content


def extract_positions(concept, external_functions):
    chat_messages = [
        {
            "role": "system",
            "content": """

                You are assisting in the spatial design of a courtyard.

                The user has already provided a design concept, {external_functions}, a list of inferred adjacency relationships, and the courtyard zones: tree, pond, play, rest, flower. 

                From this information, your task is to:

                Assign relationships between the functional zones in the courtyard and the external functions based on their inferred location in the courtyard grid. This will help determine the orientation of each zone for optimal sunlight, wind, and environmental conditions.
                You must determine which zones should be connected or adjacent, based on:
                1. Design intent (from the concept)
                2. Functional needs or compatibility (from the attributes)
                3. General principles of spatial planning (e.g., gathering zones may connect to social zones, calm areas may avoid noisy zones)
                You are not placing zones spatially. You are only identifying logical adjacency relationships.
:
                
                **Example Output:**
                {"positions": {"cafe": "tree", "library": "flower"}
                }


                Do not use any other punctuation such as hyphens. Only use colons to denote these relationships. Only use the zones in the extracted_functions list and attach them to our courtyard ones.
                """,
            },
        ]
    chat_messages.append({
    "role": "user",
    "content": """
        Concept: {concept}
        Extracted Functions: {external_functions}
    """.format(
        concept=concept,
        external_functions=external_functions,
    )
    })
    print("Extracting positions ...")
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
        response_format=
                {
                "type": "json_schema",
                    "json_schema":{
                        "name": "positions",
                        "schema": {
                            "type": "object",
                            "properties": {
                            "positions": {
                                "type": "array",
                                "description": "Relationships between external functions and courtyard zones.",
                                "items": {
                                    "type": "string", "type": "string",
                                    "description": "Relationsips between external functions and courtyard zones."
                                    }
                                }
                            },
                            "required": [
                            "positions"
                            ],
                            "additionalProperties": False
                        },
                        "strict": True
                    }
                }
    )

    print("Response from LLM:", response.choices[0].message.content)
    return response.choices[0].message.content

def extract_external_functions(conversation_messages):
    chat_messages = [
        {
            "role": "system",
            "content": """
                You are assisting in the spatial design of a courtyard.

                The user will provide a set of functions that are external to the courtyard design. Your task is to identify the external functions explicitly mentioned by the user and their associated cardinal directions (N, E, S, W) if specified.

                For example, if the user says "cafe on the north side" or "library facing east", you should include both the function and its cardinal direction.

                Do NOT include any courtyard functions or zones in this list. Do NOT add any default or assumed functions. Do NOT include explanations or extra information.

                # Output Instructions:
                Output a JSON object with a single key "external_functions", whose value is an object mapping function names to their cardinal directions.
                Each function name should map to either a cardinal direction (N, E, S, W) or null if no direction is specified.

                # Example Output:
                {
                "external_functions": {
                    "cafe": "N",
                    "library": "E",
                    "yoga": null
                }
                }

                Only include functions that are explicitly mentioned by the user.
                Only use N, E, S, W as cardinal directions.
                If no direction is specified for a function, use null for its direction.
                """
            },
        
    ]
    chat_messages.extend(conversation_messages)
    print("Extracting functions with conversation history...", chat_messages)
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "external_functions",
                "description": "External functions and their cardinal directions",
                "schema": {
                    "type": "object",
                    "properties": {
                        "external_functions": {
                            "type": "object",
                            "additionalProperties": {
                                "oneOf": [
                                    {"type": "string", "enum": ["N", "E", "S", "W"]},
                                    {"type": "null"}
                                ]
                            }
                        }
                    },
                    "required": ["external_functions"]
                }
            }
        }
    )

    print("Response from LLM:", response.choices[0].message.content)
    return response.choices[0].message.content


def extract_attributes_with_conversation(conversation_messages, concept):
    print("EXTRACTING ATTRIBUTES FROM CONCEPT", concept)
    chat_messages = [
            {
                "role": "system",
                "content": """

                        You are a keyword and parameter extraction assistant.

                        Your task is to read a given design concept description and extract all specific design-related attributes as key–value pairs.

                        # Instructions:
                        - Each key must be a **concise, lowercase design parameter** (e.g., "tree species", "bench count", "materials", "path width").
                        - Each value must be **directly lifted or inferred verbatim** from the input (no assumptions or guesses).
                        - Use lowercase for keys and string values unless the original text uses capitalized proper nouns (e.g., "Japanese maple").
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
                        """
            },
        ]
    chat_messages.append({
    "role": "user",
    "content": """
        Here is the concept: {concept}
    """.format(
        concept=concept,
    )
    })
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
                        "description": "Extracted design attributes from the concept description",
                        "schema": {
                            "type": "object",
                            "properties": {},
                            "description": "Attributes extracted from the courtyard design concept",
                            "additionalProperties": {
                                "type": "string"
                            }
                        },
                    }
                }  
        )
    print("Response from LLM for attributes:", response.choices[0].message.content)
    return response.choices[0].message.content

def extract_cardinal_directions(concept, external_functions, attributes):
    chat_messages = [
        {
            "role": "system",
            "content": """

                You are assisting in the spatial design of a courtyard.

                The user has already provided a design concept, extracted spatial attributes, a list of functional zones with inferred adjacency relationships, and external functions earlier in this conversation. 

                From this information, your task is to:

                Assign to the functional zones a N, S, E, or W cardinal direction based on their inferred location in the courtyard grid. This will help determine the orientation of each zone for optimal sunlight, wind, and environmental conditions.
                Not all the functions need cardinal directions, only some need to be oriented and anchored to a specific direction based on their function and the design intent.
:
                
                **Example Output:**
                {"directions": {
                "tree": "N", "play": "S"}
                }
                
                Do not assign the same cardinal direction to more than one zone. If there is no previous information provided, you must assign at least two directions to any of the zones.
                """,
            },
        ]
    chat_messages.append({
    "role": "user",
    "content": """
        Concept: {concept}
        Extracted Functions: {external_functions}
        Attributes: {attributes}
    """.format(
        concept=concept,
        external_functions=external_functions,
        attributes=attributes
    )
    })
    print("Extracting cardinal directions...")
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
        response_format=
        {
                "type": "json_schema",
                    "json_schema":{
                        "name": "cardinal_directions",
                        "schema": {
                            "type": "object",
                            "properties": {
                            "cardinal_directions": {
                                "type": "array",
                                "description": "List of cardinal directions attached to their functional zones.",
                                "items": {
                                    "type": "string", "type": "string",
                                    "description": "Cardinal directions for spaces mentioned."
                                    }
                                }
                            },
                            "required": [
                            "cardinal_directions"
                            ],
                            "additionalProperties": False
                        },
                        "strict": True
                    }
                }
    )

    print("Response from LLM:", response.choices[0].message.content)
    return response.choices[0].message.content


def extract_weights(concept, external_functions, attributes):
    chat_messages = [
        {
            "role": "system",
            "content": """

                You are assisting in the spatial design of a courtyard.

                The user has already provided a design concept, extracted spatial attributes, and a list of functional zones with inferred adjacency relationships earlier in this conversation. The courtyard is divided into discrete numbered cells.

                From this information, your task is to:

                Assign each functional zone and spatial attribute from the extracted attributes a specific weight in the courtyard based on how important it is to the overall design and functionality of the space. The weights should reflect the priority or significance of each zone in relation to the others.
                The weights should be integers between 1 and 10, where the importance of the zone can be inferred from:

                1. Spatial logic from the adjacency relationships (e.g., adjacent zones should be placed in neighboring or strategically close cells)
                2. Design intent (from the concept)
                3. Environmental considerations (e.g., calm zones oriented to shaded or enclosed areas; active zones to open or sunny areas)
                4. General spatial planning principles (e.g., entries near entrances, buffers between conflicting functions)

                Important Notes:

                1. You are not generating geometry or visual layout.
                2. You are assigning weights to each functional zone based on its significance in the courtyard design.
                3. The weights must lie between 1 and 10, with higher weights indicating greater importance.
                4. DO NOT output null values. Always assign a number.

                Output Instructions:
                Output only a JSON array of index-cell pairs, where each pair [a, b] means the zone at index a should have a weight placed at b.
                Your array should match the functions and zones inferred from the previous steps.
                Do not include any explanation, text, or metadata — just the final result in the format below:
                
                **Example Output:**
                {"weights": { "tree": 2, "pond": 4, "kindergarden": 8, "yoga": 3} }


                DO NOT use any other punctuation to denote relationships, only use the colon to show that.
                """,
            },
        ]
    chat_messages.append({
    "role": "user",
    "content": """
        Concept: {concept}
        Extracted Functions: {external_functions}
        Attributes: {attributes}
    """.format(
        concept=concept,
        external_functions=external_functions,
        attributes=attributes
    )
    })
    print("Extracting weights with conversation history...")
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
        response_format=
                {
                    "type": "json_schema",
                "json_schema": {
                    "name": "weights",
                    "description": "Extracted weights for functional zones in courtyard design",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "weights": {
                                "type": "object",
                                "properties": {
                                        "play": {
                                            "type": "integer",
                                            "description": "Grid point for play in courtyard space"},
                                        "rest": {"type": "integer",
                                                 "description": "Grid point for rest in courtyard space"},
                                        "pond": {"type": "integer",
                                                 "description": "Grid point for pond in courtyard space"},
                                        "flower": {"type": "integer",
                                                   "description": "Grid point for flower in courtyard space"},
                                        "tree": {"type": "integer",
                                                 "description": "Grid point for tree in courtyard space"},
                                    },
                                    "required": ["play", "rest", "pond", "flower", "tree"],
                                    "additionalProperties": False,
                                }
                            },
                            "required": ["weights"],
                            "additionalProperties": False,
                        },
                        
                    }
                }
    )

    print("Response from LLM:", response.choices[0].message.content)
    return response.choices[0].message.content

def extract_anchors(concept, external_functions, attributes):
    chat_messages = [
        {
            "role": "system",
            "content": """
                You are assisting in the spatial design of a courtyard.

                The user has already provided a design concept, extracted spatial attributes, and a list of functional zones with inferred adjacency relationships earlier in this conversation. The courtyard is divided into discrete numbered cells.

                From this information, your task is to:

                Make a list of the {external_functions} provided by the user and the existing spaces (i.e tree, pond, flower, rest, play) generated for the courtyard.

                IMPORTANT: You MUST select AT LEAST 4 spaces/functions to be anchors. These should be the most strategically important locations in the courtyard design.
                Consider:
                1. Entry points and main circulation paths
                2. Key functional spaces that define the courtyard's character
                3. Spaces that need to be fixed in place for optimal design
                4. Spaces that serve as focal points or landmarks
                5. Additional spaces that would benefit from being anchored for design stability

                Provide your output in the form of true/false, with AT LEAST 4 spaces marked as "true".
                
                **Example Output:**
                {"anchors": {"tree": "true", "pond": "true", "kindergarden": "true", "yoga": "true", "play": "true", "rest": "false"}}

                DO NOT use any other spaces apart from the external_functions and the courtyard zones.
                You MUST select AT LEAST 4 anchors, but you can select more if it would improve the design stability.
                """,
            },
        ]
    chat_messages.append({
    "role": "user",
    "content": """
        Concept: {concept}
        Extracted Functions: {external_functions}
        Attributes: {attributes}
    """.format(
        concept=concept,
        external_functions=external_functions,
        attributes=attributes
    )
    })
    print("Extracting anchors...")
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
        response_format=
                {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "anchors",
                        "description": "Boolean values showing which spaces/functions are anchors. Must have at least 4 true values.",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "anchors": {
                                    "type": "object",
                                    "description": "Mapping of space/function names to boolean anchor status",
                                    "additionalProperties": {
                                        "type": "string",
                                        "enum": ["true", "false"]
                                    },
                                    "custom_validator": {
                                        "validate_anchor_count": {
                                            "description": "Must have at least 4 true values",
                                            "validate": "function(obj) { return Object.values(obj).filter(v => v === 'true').length >= 4; }"
                                        }
                                    }
                                }
                            },
                            "required": ["anchors"],
                            "additionalProperties": False
                        }
                    }
                }  
        )

    print("Response from LLM:", response.choices[0].message.content)
    return response.choices[0].message.content

def extract_pos(concept, external_functions):
    chat_messages = [
        {
            "role": "system",
            "content": """
                You are assisting in the spatial design of a courtyard.

                The user has already provided enough information for you to extract.

                Your task now is to make a list of the areas (pond, tree, flower, play, rest) and functions {external_functions} we are working with, and add to it a position on a 2D grid. You must consider all other information before deciding on the placement of each.

                IMPORTANT: The grid coordinates must follow these ranges:
                - x coordinates range from -34 to -4
                - y coordinates range from 30 to 60
                - Use the full range to distribute spaces effectively
                - Consider the relationships between spaces when assigning coordinates
                - Place related spaces closer together
                - Use the grid space efficiently

                DO NOT output any extra information or text, only the JSON with the data. Make sure you add the external_functions as well as the courtyard areas.

                #EXAMPLE OUTPUT
                {"pos": {"tree": [-20, 45], "yoga": [-15, 35], "open": [-25, 50]}}

                Make sure you ALWAYS output positions. DO NOT include any extra data. ONLY output X and Y coordinates of functional zones and external functions.
                DO NOT give null values. Always use numbers within the specified ranges.
                """,
            },
        ]
    chat_messages.append({
    "role": "user",
    "content": """
        Concept: {concept}
        Extracted Functions: {external_functions}
    """.format(
        concept=concept,
        external_functions=external_functions,
    )
    })
    print("Extracting pos...")
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
        response_format=
                {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "position_schema",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "pos": {
                                    "type": "object",
                                    "description": "Mapping of zone/function names to [x, y] coordinates. x must be between -34 and -4, y must be between 30 and 60.",
                                    "additionalProperties": {
                                        "type": "array",
                                        "description": "Array of two numbers [x, y] where -34 <= x <= -4 and 30 <= y <= 60",
                                        "items": {
                                            "type": "number",
                                            "minimum": -34,
                                            "maximum": -4
                                        },
                                        "minItems": 2,
                                        "maxItems": 2
                                    }
                                }
                            },
                            "required": ["pos"],
                            "additionalProperties": False
                        }
                    },
                })
    print("Response from LLM:", response.choices[0].message.content)
    return response.choices[0].message.content

def assemble_courtyard_graph(spaces, external_functions, weights, anchors, positions, links, cardinal_directions, pos):
    print("Assembling courtyard graph....")
    # Ensure spaces is a dictionary
    if isinstance(spaces, str):
        try:
            spaces = json.loads(spaces)
        except json.JSONDecodeError:
            print("Error: spaces is not valid JSON")
            return None
    
    # Extract the spaces dictionary if it's nested
    if isinstance(spaces, dict) and "spaces" in spaces:
        spaces = spaces["spaces"]
    
    # Ensure pos is a dictionary
    if isinstance(pos, str):
        try:
            pos = json.loads(pos)
        except json.JSONDecodeError:
            print("Error: pos is not valid JSON")
            return None
    
    # Extract the pos dictionary if it's nested
    if isinstance(pos, dict) and "pos" in pos:
        pos = pos["pos"]
    
    chat_messages = [
        {
            "role": "system",
            "content": """
                You are a spatial graph assembly assistant for courtyard design.

                Given:
                - A dictionary of internal spaces and their grid points: {spaces}
                - A dictionary of external functions with their cardinal directions: {external_functions}
                - A dictionary of weights for each node: {weights}
                - A dictionary of anchor node names: {anchors}
                - A dictionary of positions for each node: {positions}
                - A dictionary of X and Y coordinates for each node: {pos}
                - A dictionary of links (edges): {links}
                - A dictionary of cardinal directions for each node: {cardinal_directions}

                Your task is to output a single JSON object with the following structure:

                {
                "directed": false,
                "multigraph": false,
                "graph": {},
                "nodes": [
                    {
                    "id": "node_name",
                    "pos": {"x": number, "y": number, "z": 0},  // x must be between -34 and -4, y must be between 30 and 60
                    "weight": number,  // must be a number between 1 and 10
                    "anchor": true/false
                    },
                    ...
                ],
                "links": [
                    {"source": "node_name", "target": "node_name"},
                    ...
                ]
                }

                Important Rules:
                1. NEVER use null/None for x, y coordinates or weights
                2. For any missing coordinates, use default values:
                   - For courtyard spaces (play, rest, pond, flower, tree): use values from pos dictionary
                   - For external functions: 
                     * If a cardinal direction is specified, place the function at the appropriate edge:
                       - N: y = 60, x = -19 (middle of x range)
                       - E: x = -34, y = 45 (middle of y range)
                       - S: y = 30, x = -19 (middle of x range)
                       - W: x = -4, y = 45 (middle of y range)
                     * If no direction is specified, assign coordinates within the valid ranges
                3. For any missing weights:
                   - For courtyard spaces: use values from weights dictionary
                   - For external functions: assign a default weight of 5
                   - For the "open" node: assign a default weight of 1
                4. All coordinates MUST be within the specified ranges:
                   - x coordinates must be between -34 and -4
                   - y coordinates must be between 30 and 60
                5. All weights must be numbers between 1 and 10
                6. Include the "open" node if it exists in the pos dictionary, with its specified coordinates
                7. If any coordinates from pos dictionary are outside the valid ranges, scale them proportionally to fit within the ranges

                Only use the provided data. Do not invent or assume any values except for the defaults specified above.
                Output only the JSON object, nothing else.
                """
        },
    ]
    chat_messages.append({
    "role": "user",
    "content": """
        spaces: {spaces}
        external_functions: {external_functions}
        weights: {weights}
        anchors: {anchors}
        positions: {positions}
        links: {links}
        cardinal_directions: {cardinal_directions}
        pos: {pos}
    """.format(
        spaces=json.dumps(spaces),
        external_functions=json.dumps(external_functions),
        weights=json.dumps(weights),
        anchors=json.dumps(anchors),
        positions=json.dumps(positions),
        links=json.dumps(links),
        cardinal_directions=json.dumps(cardinal_directions),
        pos=json.dumps(pos)
    )
    })
    print("Assembling courtyard graph with conversation history...", chat_messages)
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "courtyard_graph",
                "description": "Graph representation of courtyard spaces and their relationships",
                "schema": {
                    "type": "object",
                    "properties": {
                        "directed": {"type": "boolean"},
                        "multigraph": {"type": "boolean"},
                        "graph": {"type": "object"},
                        "nodes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "pos": {
                                        "type": "object",
                                        "properties": {
                                            "x": {
                                                "type": "number",
                                                "minimum": -34,
                                                "maximum": -4
                                            },
                                            "y": {
                                                "type": "number",
                                                "minimum": 30,
                                                "maximum": 60
                                            },
                                            "z": {"type": "number"}
                                        },
                                        "required": ["x", "y", "z"]
                                    },
                                    "weight": {
                                        "type": "number",
                                        "minimum": 1,
                                        "maximum": 10
                                    },
                                    "anchor": {"type": "boolean"}
                                },
                                "required": ["id", "pos", "weight", "anchor"]
                            }
                        },
                        "links": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "source": {"type": "string"},
                                    "target": {"type": "string"}
                                },
                                "required": ["source", "target"]
                            }
                        }
                    },
                    "required": ["directed", "multigraph", "graph", "nodes", "links"]
                }
            }
        }
    )

    print("Response from LLM for assemble_courtyard_graph:", response.choices[0].message.content)
    return response.choices[0].message.content


def criticize_courtyard_graph(graph):
    print("Assembling courtyard graph....")
    chat_messages = [
        {
            "role": "system",
            "content": """
                You are a landscape architect and graph specialist.

                Your job is to criticize the graph created and to point out things that could be made better for it. 

                You should talk about what spaces could be relocated and why. You mention how environmental and spatial problems could be better solved with another layout. 
                You should also appreciate the current layout and list out the advantages. List them out in bullet points.

                Ask the user if they want to go back and redo their concept.
                """
        },
    ]
    print("Criticizing courtyard graph with conversation history...", chat_messages)
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages
    )

    print("Response from LLM for criticize_courtyard_graph:", response.choices[0].message.content)
    return response.choices[0].message.content

def extract_tree_placement(concept, attributes):
    chat_messages = [
        {
            "role": "system",
            "content": """
                        You are a tree placement assistant and a tree species assistant.
                        Your task is to read a given design concept description and extract:
                        1. ONLY the tree species that are explicitly mentioned or can be reasonably inferred from the concept
                        2. The tree placement as a list of grid cell number pairs, based on adjacency and tree radius.

                        # Instructions:
                        - ONLY include tree species that are explicitly mentioned in the concept or attributes
                        - If a tree species is mentioned but not in our list, map it to the most similar type from: acer, aesculus, eucalyptus, fagus, jacaranda, pinus, platanus, quercus, tilia
                        - If no trees are mentioned, use "acer" as a single default tree
                        - Each placement must be a range of two numbers separated by "to" (e.g., "2 to 4")
                        - Numbers must be positive integers
                        - Each range must be unique and not overlap with other ranges
                        - Do not include any explanation or extra text
                        - IMPORTANT: Do NOT include all tree types - only include the ones mentioned or inferred

                        # Example Output (when only maple and pine are mentioned):
                        {
                        "tree_placement": {
                            "acer": "2 to 4",    # maple mapped to acer
                            "pinus": "5 to 7"    # pine mapped to pinus
                        }
                        }

                        # Example Output (when no trees mentioned):
                        {
                        "tree_placement": {
                            "acer": "2 to 4"     # default tree
                        }
                        }
                        """,
        },
    ]
    chat_messages.append({
    "role": "user",
    "content": """
        Concept: {concept}
        Attributes: {attributes}
    """.format(
        concept=concept,
        attributes=attributes
    )
    })
    print("Extracting tree placement...")
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "tree_placement",
                "description": "Tree species and their placement ranges in the courtyard",
                "schema": {
                    "type": "object",
                    "properties": {
                        "tree_placement": {
                            "type": "object",
                            "properties": {
                                "acer": {"type": "string", "pattern": "^\\d+ to \\d+$"},
                                "aesculus": {"type": "string", "pattern": "^\\d+ to \\d+$"},
                                "eucalyptus": {"type": "string", "pattern": "^\\d+ to \\d+$"},
                                "fagus": {"type": "string", "pattern": "^\\d+ to \\d+$"},
                                "jacaranda": {"type": "string", "pattern": "^\\d+ to \\d+$"},
                                "pinus": {"type": "string", "pattern": "^\\d+ to \\d+$"},
                                "platanus": {"type": "string", "pattern": "^\\d+ to \\d+$"},
                                "quercus": {"type": "string", "pattern": "^\\d+ to \\d+$"},
                                "tilia": {"type": "string", "pattern": "^\\d+ to \\d+$"}
                            },
                            "minProperties": 1,
                            "maxProperties": 3,  # Limit to maximum 3 different tree types
                            "additionalProperties": False
                        }
                    },
                    "required": ["tree_placement"],
                    "additionalProperties": False
                }
            }
        }
    )
    
    print("Response from LLM for tree placement:", response.choices[0].message.content)
    return response.choices[0].message.content

def extract_plant_water_requirement(concept, attributes, tree_placement):
    # First validate tree placement data
    if not tree_placement or "tree_placement" not in tree_placement:
        print("Warning: Invalid tree placement data")
        return '{"pwr": {"acer": "0.5"}}'  # Default fallback
        
    chat_messages = [
        {
            "role": "system",
            "content": """
                        You are a plant water requirement extraction assistant.
                        Your task is to assign water requirements to each tree species in the tree placement data.
                        
                        # Instructions:
                        - For each tree species in the tree_placement, assign a water requirement between 0 and 1
                        - 0 means no water required, 1 means high water requirement
                        - Use these standard values:
                          * acer: 0.3 (moderate water)
                          * aesculus: 0.4 (moderate-high water)
                          * eucalyptus: 0.2 (low water)
                          * fagus: 0.3 (moderate water)
                          * jacaranda: 0.4 (moderate-high water)
                          * pinus: 0.2 (low water)
                          * platanus: 0.3 (moderate water)
                          * quercus: 0.3 (moderate water)
                          * tilia: 0.4 (moderate-high water)
                        - If a species is not in the list above, use 0.3 as default
                        - Do not include any explanation or extra text
                        
                        # Example Output:
                        {
                        "pwr": {
                            "acer": "0.3",
                            "pinus": "0.2",
                            "quercus": "0.3"
                        }
                        }
                        """,
        },
    ]
    chat_messages.append({
    "role": "user",
    "content": """
        Concept: {concept}
        Attributes: {attributes}
        Tree Placement: {tree_placement}
    """.format(
        concept=concept,
        attributes=attributes,
        tree_placement=json.dumps(tree_placement)
    )
    })
    print("Extracting plant water requirements...")
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "pwr",
                "description": "Water requirements for each tree species",
                "schema": {
                    "type": "object",
                    "properties": {
                        "pwr": {
                            "type": "object",
                            "properties": {
                                "acer": {"type": "string", "pattern": "^0\\.[0-9]$"},
                                "aesculus": {"type": "string", "pattern": "^0\\.[0-9]$"},
                                "eucalyptus": {"type": "string", "pattern": "^0\\.[0-9]$"},
                                "fagus": {"type": "string", "pattern": "^0\\.[0-9]$"},
                                "jacaranda": {"type": "string", "pattern": "^0\\.[0-9]$"},
                                "pinus": {"type": "string", "pattern": "^0\\.[0-9]$"},
                                "platanus": {"type": "string", "pattern": "^0\\.[0-9]$"},
                                "quercus": {"type": "string", "pattern": "^0\\.[0-9]$"},
                                "tilia": {"type": "string", "pattern": "^0\\.[0-9]$"}
                            },
                            "minProperties": 1,
                            "additionalProperties": False
                        }
                    },
                    "required": ["pwr"],
                    "additionalProperties": False
                }
            }
        }
    )

    print("Response from LLM for PWR:", response.choices[0].message.content)
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

def generate_image_prompt(concept, attributes, connections, targets, spaces, pwr, tree_placement):
    """
    Generates a detailed prompt for an image generation model, using all relevant design data and spatial logic.
    Args:
        concept (str): The design concept text.
        attributes (dict or str): Extracted attributes (JSON or string).
        connections (dict or str): Zone connections (JSON or string).
        targets (dict or str): Zone-to-grid assignments (JSON or string).
        spaces (dict or str): Extracted spaces (JSON or string).
        pwr (str): Plant water requirements.
        tree_placement (str): Tree placement info.
    Returns:
        str: A prompt for an image generation model.
    """
    # Convert all inputs to string for LLM context
    def to_str(val):
        if isinstance(val, dict):
            return json.dumps(val, indent=2)
        return str(val)

    context = f"""
# Courtyard Design Context #
Concept:
{to_str(concept)}

Attributes:
{to_str(attributes)}

Functional Zones and Connections:
{to_str(connections)}

Zone-to-Grid Assignments:
{to_str(targets)}

Spaces:
{to_str(spaces)}

Plant Water Requirements:
{to_str(pwr)}

Tree Placement:
{to_str(tree_placement)}
"""

    system_prompt = """
You are an expert landscape architect and visual storyteller.
Your task is to generate a detailed, vivid, and spatially accurate prompt for an image generation model (such as Stable Diffusion or DALL-E) to visualize a courtyard design.

# Instructions:
- Use the provided context (concept, attributes, connections, grid assignments, spaces, tree types, water requirements, and tree placement).
- Clearly describe the spatial arrangement: where each functional zone, tree, and feature is located on the grid.
- Mention the number, type, and placement of trees, flower beds, and other key elements.
- Describe the materials, colors, and atmosphere as inferred from the attributes.
- Use concise, visual language. Do not include any explanation or extra text—just the prompt.
- The prompt should be a single paragraph, max 120 words.

DO NOT add any additional information or context outside the provided data.

# Example Output:
A sunlit courtyard with a central calm area (grid 10,10), social zones to the south (grids 5,5 to 5,10), permeable garden beds along the east edge where the area is colored pink, and a cluster of oak and maple trees (grids 12,12 and 13,13). Flower beds with lavender and daffodil line the paths, which are a grey. Benches and permeable paving are colored brown and create a welcoming, sustainable space. The design integrates biodiversity, health, and social interaction, with a mix of brick, wood, and green foliage.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context}
    ]
    response = client.chat.completions.create(
        model=completion_model,
        messages=messages
    )
    return response.choices[0].message.content


