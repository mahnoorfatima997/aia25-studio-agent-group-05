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


def generate_concept(message):
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": """
                        You are a leading landscape architect and designer.
                        Your task is to generate a concept for a courtyard design based on the user's input.
                        Your task is to craft a short, very practical, and highly imaginative concept for a building design.
                        Expand on where the user can place design objects, how to use the space, and what materials to consider. 
                        Help the user visualize the design. 
                        Keep your response to a maximum of one paragraph.

                        Based on the user's input, calculate the values for the following parameters:
                        - Social area
                        - Permeable area
                        - Calm area
                        - Flower area
                        - Tree number and species
                        - Scores for health, biodiversity, open space quality, and design integration.

                        Use the following format for your output:
                        "We envision an outdoor space with a total plot area of {'plot_area'} sqm, 
                        centered around a courtyard of {'courtyard_area'} sqm. The design includes 
                        {'calm_area'} sqm of calm areas for relaxation and {row['social_area']} sqm 
                        of social zones for gathering. To enhance environmental quality, the site features 
                        {'permeable_area'} sqm of permeable ground and supports {'tree_number'} trees 
                        across {'tree_species'} different species. Additionally, {'flower_area'} sqm 
                        is allocated for flower beds to boost biodiversity. This design approach scores {'score_health'} 
                        for health benefits, {'score_biodiversity'} for biodiversity value, 
                        {'score_open_space'} for open space quality, and {'score_design_integration'} 
                        for design integration."

                        Ensure that all numerical values are calculated based on the JSON data and user input. Do not exceed this one paragraph.
                        Do not include explanations, introductions, or any extra information.
                        """,
            },
            {
                "role": "user",
                "content": f"""
                        What are the concepts and parameters behind this courtyard design? 
                        Initial information: {message}
                        """,
            },
        ],
    )
    return response.choices[0].message.content


def generate_casestudies(message):
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": """
                        Give me a list of 5 case studies related to the following courtyard design.
                        The case studies should be related to the following topics:
                        - courtyard design
                        - courtyard design for children
                        - courtyard design for elderly
                        - courtyard design for social interaction
                        - courtyard design for biodiversity
                        - courtyard design for health
                        - courtyard design for open space quality
                        - courtyard design for design integration
                        - courtyard design for permeable area
                        - courtyard design for calm area
                        - courtyard design for flower area
                        - courtyard design for tree number and species
                        - courtyard design for social area
                        Make sure you give me the case studies in a list format.
                        Explain only the courtyard design of the case studies in one short paragraph.
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


def extract_attributes(message):
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": """

                        # Instructions #
                        You are a keyword and parameter extraction assistant.
                        Your task is to read a given text and extract relevant keywords and numerical values according to four categories: shape, theme, materials, parameters.
                        Based on the user's input, calculate the values for the following parameters:
                        - Social area (should always be in square meters)
                        - Courtyard area (should always be in square meters)
                        - Tree number and species 
                        - Scores for health, biodiversity, open space quality, and design integration.
                        - Permeable area (should always be in square meters)
                        - Calm area (should always be in square meters)
                        - Flower area (should always be in square meters)


                        # Rules #
                        If a category has no relevant keywords, write "None" for that field.
                        For parameters, extract numerical values and include the unit of measurement (e.g., m², m³, kg). For numerical values, always extract as a string.
                        Separate multiple keywords in the same field by commas without any additional text.
                        Do not include explanations, introductions, or any extra information. You should only output the JSON.
                        Focus on concise, meaningful keywords and numerical values directly related to the given categories.
                        Do not try to format the json output with characters like ```json
                        Begin your output with '{' and end with '}' — no extra text or explanations.

                        # Category guidelines #
                        Shape: Words that describe form, geometry, structure (e.g., circle, rectangular, twisting, modular).
                        Theme: Words related to the overall idea, feeling, or concept (e.g., minimalism, nature, industrial, cozy).
                        Materials: Specific physical materials mentioned (e.g., wood, concrete, glass, steel).
                        Parameters: Specific numerical values with units related to the building's design such as:
                        - courtyard_area: area of the courtyard in square meters (m²)
                        - social_area: area of the social spaces in square meters (m²)
                        - permeable_area: area of the permeable surfaces in square meters (m²)
                        - calm_area: area of the calm spaces in square meters (m²)
                        - flower_area: area of the flower spaces in square meters (m²)
                        - tree_number: number of trees
                        - tree_species: number of different species of trees
                        - score_health: score for health benefits
                        - score_biodiversity: score for biodiversity value
                        - score_open_space: score for open space quality
                        - score_design_integration: score for design integration

                        # Example #
                        Input:
                        We envision an outdoor space with a total plot area of 1,200 sqm, centered around a courtyard of 400 sqm. The design includes 120 sqm of calm areas for relaxation and 180 sqm of social zones for gathering. To enhance environmental quality, the site features 300 sqm of permeable ground and supports 12 trees across three different species (oak, maple, and cherry). Additionally, 80 sqm is allocated for flower beds to boost biodiversity. This design approach scores 8/10 for health benefits, 9/10 for biodiversity value, 7/10 for open space quality, and 8.5/10 for design integration.

The courtyard's focal point is a tranquil water feature, surrounded by lush greenery and comfortable seating areas. The social zones are designed to accommodate various activities, such as outdoor yoga or book clubs, with modular furniture and flexible lighting. Permeable ground and rain gardens help to reduce stormwater runoff and create a natural habitat for local wildlife. The courtyard's perimeter features a living wall, incorporating native plants and vines to provide shade and visual interest.

The design emphasizes the emotional impact of the space by incorporating elements that promote relaxation, socialization, and connection with nature. By balancing functionality with aesthetics, this courtyard becomes an inviting oasis in the heart of the city, perfect for both personal reflection and community engagement.

                        Output:
                        {
                        "shape": "circular",
                        "theme": ["nature", "health"],
                        "materials": "wood",
                        "parameters": {
                            "courtyard_area": "400 sqm",
                            "social_area": "180 sqm",
                            "permeable_area": "300 sqm",
                            "calm_area": "120 sqm",
                            "flower_area": "80 sqm",
                            "tree_number": "12",
                            "tree_species": "3",
                            "score_health": "8/10",
                            "score_biodiversity": "9/10",
                            "score_open_space": "7/10",
                            "score_design_integration": "8.5/10"
                        }
                        }
                        """,
            },
            {
                "role": "user",
                "content": f"""
                        # GIVEN TEXT # 
                        {message}
                        """,
            },
        ],
        response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "attributes",
                    "description": "Extracted attributes from the text",
                    "strict": "true",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "shape": {"type": "array", "items": {"type": "string"}},
                            "theme": {"type": "array", "items": {"type": "string"}},
                            "materials": {"type": "array", "items": {"type": "string"}},
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "courtyard_area": {"type": "string"},
                                    "social_area": {"type": "string"},
                                    "permeable_area": {"type": "string"},
                                    "calm_area": {"type": "string"},
                                    "flower_area": {"type": "string"},
                                    "tree_number": {"type": "string"},
                                    "tree_species": {"type": "string"},
                                    "score_health": {"type": "number"},
                                    "score_biodiversity": {"type": "number"},
                                    "score_open_space": {"type": "number"},
                                    "score_design_integration": {"type": "number"}
                                },
                                "required": [
                                    "courtyard_area", "social_area", "permeable_area",
                                    "calm_area", "flower_area", "tree_number",
                                    "tree_species", "score_health", "score_biodiversity",
                                    "score_open_space", "score_design_integration"
                                ]
                            },
                            },
                            "required": ["shape", "theme", "materials", "parameters"]
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
                        Your task is to create an open-ended question based on the given text.
                        Imagine the question will be answered using a detailed text about courtyard design and related elements and scores.
                        The question should feel exploratory and intellectually curious.
                        Output only the question, without any extra text.

                        # Examples #
                        - Is this courtyard design suitable for children, and how does it promote their well-being?
                        - How does the design of this courtyard contribute to biodiversity and environmental sustainability?
                        - What are the key elements of this courtyard design that enhance social interaction and community engagement?
                        - How could the design of this courtyard be improved to better integrate with the surrounding environment?
                        - What are some critical aspects of this courtyard design that one should be aware of when considering its impact on health and well-being?

                        # Important #
                        Keep the question open-ended, inviting multiple references or examples.
                        The question must be naturally connected to the themes present in the input text.
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



