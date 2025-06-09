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

                        # Output Format:
                        Return a JSON object, whose value is an object with the following keys:
                        - play: grid point based on proximity matrix developed in concept description (integer)
                        - rest: grid point based on proximity matrix developed in concept description (integer)
                        - pond: grid point based on proximity matrix developed in concept description (integer)
                        - flower: grid point based on proximity matrix developed in concept description (integer)
                        - tree: grid point based on proximity matrix developed in concept description (integer)

                        # Instructions:
                        - Each key must be a **concise, lowercase space type** (e.g., "play", "rest", "pond", "flower", "tree").
                        - Do NOT include textual descriptions.
                        - Use whole numbers (no decimals).
                        - If no information is available, omit assigning a number to that category.

                        # Example Output:
                        {
                        "spaces": {
                            "play": 1,
                            "rest": 3,
                            "pond": 5,
                            "flower": 7,
                            "tree": 9
                        }
                        }

                        You must include all 5 areas in every answer. If one of the areas does not have a number, you will enter a 0 next to it.
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
    print("Extracting spaces...")
    print("Conversation messages:", chat_messages)
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
        response_format = {
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
                        },
                        
                    }
                }
    )
    print("Response from LLM for spaces:", response.choices[0].message.content)
    return response.choices[0].message.content

def extract_links(concept):
    chat_messages = [
        {
            "role": "system",
            "content": """

                You are assisting in the spatial design of a courtyard.

                Build relationships between these functional zones:

                - play
                - rest
                - pond
                - flower
                - tree

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
                {"links": {
                "tree": "pond", "tree": "flower", "play": "rest"}
                }

                ONLY make links between these areas. Do not make links with other attributes/zones.
                        """,
            },
        ]
    chat_messages.append({
    "role": "user",
    "content": """
        Concept: {concept}
    """.format(
        concept=concept,
    )
    })
    print("Extracting links ...")
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
        response_format=
                {
                "type": "json_schema",
                "json_schema": {
                    "name": "links",
                    "description": "Extracted links from the design description",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "links": {
                                "type": "object",
                                "properties": {
                                        "tree": {
                                            "type": "string",
                                            "description": "Relates to a concept of tree, e.g., pond, flower."
                                        },
                                        "play": {
                                            "type": "string",
                                            "description": "Relates to the concept of play, e.g., rest."
                                        },
                                        "pond": {
                                            "type": "string",
                                            "description": "Relates to a concept of pond, e.g., tree, flower."
                                        },
                                        "flower": {
                                            "type": "string",
                                            "description": "Relates to a concept of flower, e.g., tree, rest."
                                        },
                                        "rest": {
                                            "type": "string",
                                            "description": "Relates to a concept of rest, e.g., flower, pond."
                                        }
                                        },
                                    "required": ["play", "rest", "pond", "flower", "tree"],
                                    "additionalProperties": False,
                                }
                            },
                            "required": ["links"],
                            "additionalProperties": False,
                        },
                        
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

                The user will provide a set of functions that are external to the courtyard design. Your task is to identify ONLY the external functions explicitly mentioned by the user and arrange them in a JSON.

                Do NOT include any courtyard functions or zones in this list. Do NOT add any default or assumed functions. Do NOT include explanations or extra information.

                # Output Instructions:
                Output only a JSON object with a single key "external_functions", whose value is a list.

                # Example Output:
                {
                "external_functions": [
                    "yoga", "school"
                ]
                }
                """
            },
        ]
    chat_messages.extend(conversation_messages)
    print("Extracting functions with conversation history...", chat_messages)
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
        response_format=
                {
                    "type": "json_schema",
                    "json_schema":{
                        "name": "external_functions",
                        "schema": {
                            "type": "object",
                            "properties": {
                            "external_functions": {
                                "type": "array",
                                "description": "List of external functions.",
                                "items": {
                                    "type": "string",
                                    "description": "The function name."
                                    }
                                }
                            },
                            "required": [
                            "external_functions"
                            ],
                            "additionalProperties": False
                        },
                        "strict": True
                    }
                }
    )

    print("Response from LLM for external_functions:", response.choices[0].message.content)
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

                Assign which function zones should be anchored and which should not be. Provide your output in the form of true/false.
                
                **Example Output:**
                {"anchors": {"tree":, "true", "pond": "true", "kindergarden": "false", "yoga": "false"}}

                DO NOT use any other spaces apart from the external_functions and the courtyard zones.
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
                        "description": "Boolean values showing which spaces/functions are anchors.",
                        "schema": {
                            "type": "object",
                            "properties": {},
                            "description": "Boolean values showing which spaces/functions are anchors.",
                            "additionalProperties": {
                                "type": "string"
                            }
                        },
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

                DO NOT output any extra information or text, only the JSON with the data. Make sure you add the external_functions as well as the courtyard areas.

                #EXAMPLE OUTPUT

                {"pos": {"tree": [1, 2], "yoga": [4, 9], "open": [2, 6]}}

                Make sure you ALWAYS output positions. DO NOT include any extra data. ONLY output X and Y coordinates of functional zones and external functions.
                DO NOT give null values. Always numbers.
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
                                    "description": "Mapping of zone/function names to [x, y] coordinates.",
                                    "additionalProperties": {
                                        "type": "array",
                                        "description": "Array of two numbers [x, y]",
                                        "items": {"type": "number"},
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
    chat_messages = [
        {
            "role": "system",
            "content": """
                You are a spatial graph assembly assistant for courtyard design.

                Given:
                - A list of internal spaces: {spaces}
                - A list of external functions: {external_functions}
                - A dictionary of weights for each node: {weights}
                - A list of anchor node names: {anchors}
                - A dictionary of positions for each node: {positions}
                - A dictionary of X and Y coordinates for each node: {pos}
                - A list of links (edges) as [source, target] pairs: {links}
                - A list of cardinal directions for each node: {cardinal_directions}

                Your task is to output a single JSON object with the following structure:

                {
                "directed": false,
                "multigraph": false,
                "graph": {},
                "nodes": [
                    {
                    "id": "node_name",
                    "pos": {"x": ..., "y": ..., "z": ...},
                    "weight": ...,
                    "anchor": true/false
                    },
                    ...
                ],
                "links": [
                    {"source": "node_name", "target": "node_name"},
                    ...
                ]
                }

                Only use the provided data. Do not invent or assume any values. Output only the JSON object, nothing else.
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
        spaces=spaces,
        external_functions=external_functions,
        weights=weights,
        anchors=anchors,
        positions=positions,
        links=links,
        cardinal_directions=cardinal_directions,
        pos=pos
    )
    })
    print("Assembling courtyard graph with conversation history...", chat_messages)
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages
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



# def extract_tree_types(conversation_messages):
#     chat_messages = [
#             {
#                 "role": "system",
#                 "content": """

#                         You are a tree species extraction assistant.
#                         Your task is to read a given design concept description and extract all specific tree species mentioned as a list.

#                         The tree species should be categorized on the basis of their geometric similarity to the following types:
#                         acer, aesculus, eucalyptus, fagus, jacaranda, pinus, platanus, quercus, tilia

#                         You will then output the tree species in the following format:
#                         {acer, eucalyptus, acer, fagus}

#                         # Instructions:
#                         - Each word must be from the list of tree species provided above
#                         - Each tree species from the input must be compared geometrically to the list of tree species provided above for most similar geometric shape
#                         - If a tree species is not found to match any in the list, any other is to be used as a placeholder

#                         # Output Format:
#                         {acer, eucalyptus, acer, fagus}
#                         """,
#             },
#         ]
#     chat_messages.extend(conversation_messages)
#     print("Extracting attributes with conversation history...")
#     print("Conversation messages:", chat_messages)
#     response = client.chat.completions.create(
#         model=completion_model,
#         messages=chat_messages,
#     )
#     return response.choices[0].message.content

def extract_plant_water_requirement(conversation_messages):
    chat_messages = [
            {
                "role": "system",
                "content": """

                        You are a plant water requirement extraction assistant.
                        Your task is to analyze the tree species mentioned in the design concept description and extract their water requirements as a list.
                        The water requirements should be listed out as a decimal number between 0 and 1, where 0 means no water is required and 1 means the plant requires a lot of water.
                        The item number should match the order of the trees mentioned before.
                        
                        You will then output the water requirements in the following format:
                        {0.1, 0.2, 0.3, 0.4}

                        Do not include any explanation, extra text, or formatting characters—just the final result in the format below.

                        # Instructions:
                        - Each number must be a decimal between 0 and 1
                        """,
            },
        ]
    chat_messages.extend(conversation_messages)
    print("Extracting attributes with conversation history...")
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
    )
    return response.choices[0].message.content

def extract_tree_placement(conversation_messages):
    chat_messages = [
        {
            "role": "system",
            "content": """
                        You are a tree placement assistant and a tree species assistant.
                        Your task is to read a given design concept description and extract:
                        1. All specific tree species mentioned as a list, categorized by geometric similarity to the following types: acer, aesculus, eucalyptus, fagus, jacaranda, pinus, platanus, quercus, tilia.
                        2. The tree placement as a list of grid cell number pairs, based on adjacency and tree radius.

                        # Output Format:
                        Return a single JSON object with two keys:
                        - "tree_species": a list of tree species (e.g., ["acer", "eucalyptus", "acer", "fagus"])
                        - "tree_placement": a list of string ranges (e.g., ["2 to 4", "5 to 7", "8 to 10"])

                        # Example Output:
                        {
                        "tree_species": ["acer", "eucalyptus", "acer", "fagus"],
                        "tree_placement": ["2 to 4", "5 to 7", "8 to 10"]
                        }

                        # Instructions:
                        - Each word in "tree_species" must be from the list above.
                        - Each tree species from the input must be compared geometrically to the list for the most similar shape.
                        - If a tree species is not found to match any in the list, use any other as a placeholder.
                        - Each number in "tree_placement" must be a unique grid cell number or range.
                        - Do not include any explanation, extra text, or formatting—just the JSON object as shown above.
                        """,
        },
    ]
    chat_messages.extend(conversation_messages)
    print("Extracting tree placement and species with conversation history...")
    print("Conversation messages:", chat_messages)
    response = client.chat.completions.create(
        model=completion_model,
        messages=chat_messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "tree_placement_and_species",
                "description": "Extracted tree species and their placement as a JSON object.",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "tree_species": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "tree_placement": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["tree_species", "tree_placement"]
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


# def route_query_to_function(phase: str, conversation_history=None):
#     """
#     Routes a user message to the appropriate LLM function based on intent.
#     Optionally takes conversation_history for context.
#     """

#     # Example routing logic (customize as needed)
#     if phase == "concept":
#         # Generate a concept
#         return generate_concept_with_conversation(conversation_history)
    
#     elif phase == "functions":
#         return extract_external_functions(conversation_history)
    
#     elif phase == "attributes":
#         return extract_attributes_with_conversation(conversation_history)

#     elif phase == "graph":
#         return assemble_courtyard_graph(
#             spaces=conversation_history['spaces'],
#             external_functions=conversation_history['external_functions'],
#             weights=conversation_history['weights'],
#             anchors=conversation_history['anchors'],
#             positions=conversation_history['positions'],
#             links=conversation_history['links']
#         )
    
#     elif phase == "criticism":
#         return criticize_courtyard_graph(
#             graph=conversation_history['graph']
#         )
      
#     else:
#         print(f"Unknown phase: {phase}")


    # else:
    #     # Default: classify if it's architectural
    #     classification = classify_input(message)
    #     if "refuse" in classification.lower():
    #         return "Sorry, I can only answer questions about architecture."
    #     else:
    #         # Fallback: try to generate a concept
    #         return generate_concept_with_conversation([{"role": "user", "content": message}])
