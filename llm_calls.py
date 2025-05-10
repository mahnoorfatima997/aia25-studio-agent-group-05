import json
from server.config import *

with open("knowledge/merged.json", "r") as file:
    json_data = json.load(file)

# Convert the JSON data to a string
json_data_str = json.dumps(json_data)

def classify_input(message):
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": """
                        Your task is to classify if the user message is related to buildings and architecture or not.
                        Output only the classification string.
                        If it is related, output "Related", if not, output "Refuse to answer".

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
                        You are a visionary intern at a leading architecture firm.
                        Your task is to craft a short, poetic, and highly imaginative concept for a building design.
                        Weave the initial information naturally into your idea, letting it inspire creative associations and unexpected imagery.
                        Your concept should feel bold, evocative, and memorable — like the opening lines of a story.
                        Keep your response to a maximum of one paragraph.
                        Avoid generic descriptions; instead, focus on mood, atmosphere, and emotional resonance. Be a little critical and snarky when you talk.

                        Use the following JSON data as a reference for calculations:
                        {json_data_str}

                        Based on the user's input and the JSON data, calculate the values for the following parameters:
                        - Social area
                        - Permeable area
                        - Calm area
                        - Flower area
                        - Tree number and species
                        - Scores for health, biodiversity, open space quality, and design integration.

                        Use the following format for your output:
                        "We envision an outdoor space with a total plot area of {'plot_area'} sqm, 
                        centered around a courtyard of {'courtyard_area'} sqm. The design includes 
                        {'calm_area'} sqm of calm areas for relaxation and {row['out:social_area']} sqm 
                        of social zones for gathering. To enhance environmental quality, the site features 
                        {'permeable_area'} sqm of permeable ground and supports {'tree_number'} trees 
                        across {'tree_species'} different species. Additionally, {'flower_area'} sqm 
                        is allocated for flower beds to boost biodiversity. This design approach scores {'score_health'} 
                        for health benefits, {'score_biodiversity'} for biodiversity value, 
                        {'score_open_space'} for open space quality, and {'score_design_integration'} 
                        for design integration."

                        Ensure that all numerical values are calculated based on the JSON data and user input.
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
                        Use the following JSON data as a reference for calculations:
                        {json_data_str}
                        Based on the user's input and the JSON data, calculate the values for the following parameters:
                        - Social area
                        - Permeable area
                        - Calm area
                        - Flower area

                        Use the following JSON format for your output:
                        {
                            "shape": "keyword1, keyword2",
                            "theme": "keyword3, keyword4",
                            "materials": "keyword5, keyword6"
                            "parameters":{
                            "courtyard_area": "value1",
                            "social_area": "value2",
                            "permeable_area": "value3",
                            "calm_area": "value4",
                            "flower_area": "value5"}
                        }

                        # Rules #
                        If a category has no relevant keywords, write "None" for that field. 
                        For parameters, extract numerical values and include the unit of measurement (e.g., m², m³, kg).
                        Separate multiple keywords in the same field by commas without any additional text.
                        Do not include explanations, introductions, or any extra information—only output the JSON.
                        Focus on concise, meaningful keywords and numerical values directly related to the given categories.
                        Do not try to format the json output with characters like ```json

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
                        Your question should invite an answer that points to references to specific brutalist buildings or notable examples.
                        Imagine the question will be answered using a detailed text about courtyard design and related elements and scores.
                        The question should feel exploratory and intellectually curious.
                        Output only the question, without any extra text.

                        # Examples #
                        - How would I design a 30 sqm courtyard for a hot arid climate while incorporating playful elements for children?
                        - What’s the best way to design a courtyard that acts as a seasonal gathering space in a high-humidity climate?
                        - How would I integrate edible landscaping in a courtyard without compromising on formal aesthetics?
                        - Can I design a courtyard that doubles as a thermal buffer and a public amenity?
                        - What are passive strategies to cool a courtyard in a subtropical high-density site without relying on trees?
                        - How do I incorporate shadow play in a courtyard for sensory engagement?

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
