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

def generate_weights(message):
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": """
                        generate a matrix that assigns a value between **"1"** (not included) and **"20"** (dominant feature) for each provided area category. Use only the categories present in the input. These values should be scaled based on their relative size or importance in the design.

                        **Format your output exactly like this:**

                        1. The design paragraph.
                        2. A new line.
                        3. A JSON object like:
                        {
                        "matrix": {
                        "Category1": "X",
                        "Category2": "Y",
                        ...
                        }
                        }
                        Do **not** include any explanation, notes, or extra text — just the matrix.
                        """,
            },
            {
                "role": "user",
                "content": f"""
                        Initial information: {message}
                        """,
            },
        ],
    )
    return response.choices[0].message.content

def generate_locations(message):
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
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
                        "locations": {
                        "Function1": [X, Y],
                        "Function2": [X, Y],
                        ...
                        }
                        }
                        Only include the functions provided in the input. Each `[X, Y]` should be a pair of integers between 0 and 19. Do not include explanations or commentary. Only output the JSON object in the format shown above.
                        """
                                    },
                                    {
                                        "role": "user",
                                        "content": f"""
                        Based on this courtyard design: {message}
                        """
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


def extract_attributes(message):
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": """

                        You are a keyword and parameter extraction assistant.

                        Your task is to read a given concept description and extract specific attributes according to the categories below. Focus only on **vegetation and material-related elements**.

                        # Categories #
                        1. **Tree species**: List all mentioned species or write "None" if not specified.
                        2. **Tree number**: Extract as a string (e.g., "12").
                        3. **Flower types**: List the flower types mentioned or write "None".
                        4. **Materials**: List only physical materials used in the design (e.g., wood, steel, brick, glass). Use lowercase. Separate multiple materials with commas.

                        # Rules #
                        - If an attribute is not mentioned, write `"None"` for that field.
                        - Do not generate new values; only extract from the input.
                        - Only output the JSON — no explanations, extra text, or formatting characters.
                        - Begin your output with `{` and end with `}`.
                        - Use lowercase for all items in "materials" and "flower_types".
                        - Separate multiple items in lists with commas (no bullet points or line breaks).
                        - Always include all four fields in the output, even if some are "None".

                        # Example Output #
                        {
                        "tree_species": "oak,maple,cherry",
                        "tree_number": "12",
                        "flower_types": "lavender,daffodil",
                        "materials": "wood,concrete"
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
        response_format=
                {
                "type": "json_schema",
                "json_schema": {
                    "name": "attributes",
                    "description": "Extracted vegetation and material attributes from the text",
                    "strict": "true",
                    "schema": {
                    "type": "object",
                    "properties": {
                        "tree_species": {
                        "type": "array",
                        "items": { "type": "string" }
                        },
                        "tree_number": {
                        "type": "string"
                        },
                        "flower_types": {
                        "type": "array",
                        "items": { "type": "string" }
                        },
                        "materials": {
                        "type": "array",
                        "items": { "type": "string" }
                        }
                    },
                    "required": ["tree_species", "tree_number", "flower_types", "materials"]
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



