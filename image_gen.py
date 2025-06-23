import requests
import base64
import io
from PIL import Image
import os
from datetime import datetime

def generate_ai_enhanced_image(image_path, prompt, output_filename=None, design_data=None):
    """
    Generate AI-enhanced image using text-to-image generation with detailed architectural description
    """
    try:
        # Updated ngrok URL with the new server - using text-to-image endpoint
        SERVER_URL = "https://c005-34-23-75-86.ngrok-free.app/generate"
        
        # Generate detailed architectural description from design data
        detailed_prompt = generate_detailed_courtyard_prompt(prompt, design_data)
        
        # Enhanced prompt for architectural images - focus on top-down view
        enhanced_prompt = f"{detailed_prompt}, architectural top-down visualization, professional rendering, high quality, detailed, photorealistic, enhanced lighting, improved materials, refined textures, aerial perspective"
        
        data = {
            "prompt": enhanced_prompt,
            "seed": 7797676568,
            "steps": 35,  # Good balance for architectural images
            "scale": 8.0  # Strong guidance for architectural adherence
        }
        
        print(f"Sending request to {SERVER_URL}")
        print(f"Detailed Prompt: {enhanced_prompt}")
        
        response = requests.post(SERVER_URL, data=data, timeout=120)
        
        if response.status_code == 200:
            # Save the generated image
            if output_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"ai_enhanced_{timestamp}.png"
            
            output_dir = os.path.expanduser("~/Downloads/ai_generated_images")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ AI-enhanced image saved to: {output_path}")
            return True, output_path, "Image generated successfully!"
        else:
            error_msg = f"Server error: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            return False, None, error_msg
                
    except Exception as e:
        error_msg = f"Error generating AI-enhanced image: {str(e)}"
        print(f"❌ {error_msg}")
        return False, None, error_msg

def generate_detailed_courtyard_prompt(base_prompt, design_data=None):
    """
    Generate a detailed architectural description for the courtyard based on design data
    """
    # Start with the base architectural structure
    detailed_description = "A 4-sided rectangular courtyard surrounded by buildings, viewed from above in a top-down aerial perspective. "
    
    # Add the base prompt
    detailed_description += f"{base_prompt}. "
    
    # Add architectural context
    detailed_description += "The courtyard is enclosed by building walls on all four sides, creating a private outdoor space. "
    
    # If we have design data, add specific details
    if design_data and isinstance(design_data, dict):
        # Add spaces and their descriptions
        spaces = design_data.get('spaces', {})
        if spaces:
            detailed_description += "The courtyard contains several functional areas: "
            space_descriptions = []
            for space_name, space_type in spaces.items():
                if space_type == 'play':
                    space_descriptions.append(f"a {space_name} area for active recreation")
                elif space_type == 'rest':
                    space_descriptions.append(f"a {space_name} zone for quiet contemplation")
                elif space_type == 'pond':
                    space_descriptions.append(f"a {space_name} water feature")
                elif space_type == 'flower':
                    space_descriptions.append(f"a {space_name} garden area")
                elif space_type == 'tree':
                    space_descriptions.append(f"a {space_name} tree and shade area")
                else:
                    space_descriptions.append(f"a {space_name} {space_type} area")
            
            if space_descriptions:
                detailed_description += ", ".join(space_descriptions) + ". "
        
        # Add external functions as anchor points
        external_functions = design_data.get('external_functions', {})
        if external_functions:
            detailed_description += "External functions are positioned at the corners: "
            external_list = []
            for func_name, direction in external_functions.items():
                external_list.append(f"{func_name} facing {direction}")
            detailed_description += ", ".join(external_list) + ". "
        
        # Add boundary information
        boundary_box = design_data.get('boundary_box', {})
        if boundary_box:
            width = boundary_box.get('width', 0)
            height = boundary_box.get('height', 0)
            if width and height:
                detailed_description += f"The courtyard measures approximately {width:.1f} by {height:.1f} units. "
    
    # Add material and visual specifications
    detailed_description += "The courtyard features a mix of hardscape and softscape elements with natural materials. "
    detailed_description += "The design emphasizes sustainability and environmental harmony. "
    
    # Add visual style specifications
    detailed_description += "Professional architectural visualization with accurate spatial relationships, proper proportions, and realistic materials. "
    detailed_description += "The top-down view clearly shows the layout, circulation patterns, and functional zoning of the courtyard design."
    
    return detailed_description.strip()

def generate_concept_view_from_text(prompt, output_filename=None):
    """
    Generate concept view using text-to-image generation with architectural focus
    """
    # This function is deprecated - concept view has been removed
    pass

def generate_3d_view_from_text(prompt, output_filename=None):
    """
    Generate 3D view using text-to-image generation with detailed courtyard features
    """
    try:
        # Updated ngrok URL for text-to-image generation - using the new server
        SERVER_URL = "https://c005-34-23-75-86.ngrok-free.app/generate"
        
        # Enhanced prompt for 3D visualization with detailed courtyard features
        enhanced_prompt = f"{prompt}, architectural 3D visualization, photorealistic rendering, high quality, detailed textures, natural materials, immersive atmosphere, professional architectural photography, dramatic lighting, depth of field, atmospheric perspective, realistic courtyard environment"
        
        data = {
            "prompt": enhanced_prompt,
            "seed": 7797676568,
            "steps": 35,  # Good balance for 3D images
            "scale": 8.0  # Strong guidance for 3D adherence
        }
        
        print(f"Sending 3D generation request to {SERVER_URL}")
        print(f"Prompt: {enhanced_prompt}")
        
        response = requests.post(SERVER_URL, data=data, timeout=120)
        
        if response.status_code == 200:
            # Save the generated image
            if output_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"3d_view_{timestamp}.png"
            
            output_dir = os.path.expanduser("~/Downloads/ai_generated_images")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ 3D view generated and saved to: {output_path}")
            return True, output_path, "3D view generated successfully!"
        else:
            error_msg = f"Server error: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            return False, None, error_msg
            
    except Exception as e:
        error_msg = f"Error generating 3D view: {str(e)}"
        print(f"❌ {error_msg}")
        return False, None, error_msg

def generate_plan_view_from_text(prompt, output_filename=None):
    """
    Generate plan view using text-to-image generation with coordinates and realistic details
    """
    try:
        # Updated ngrok URL for text-to-image generation - using the new server
        SERVER_URL = "https://c005-34-23-75-86.ngrok-free.app/generate"
        
        # Enhanced prompt for plan visualization with coordinates and architectural precision
        enhanced_prompt = f"{prompt}, architectural plan view, technical drawing style, clean lines, professional layout, top-down perspective, precise measurements, clear zone boundaries, elegant spatial composition, coordinate system, realistic materials, professional architectural documentation"
        
        data = {
            "prompt": enhanced_prompt,
            "seed": 7797676568,
            "steps": 35,  # Good balance for plan images
            "scale": 8.0  # Strong guidance for plan adherence
        }
        
        print(f"Sending plan generation request to {SERVER_URL}")
        print(f"Prompt: {enhanced_prompt}")
        
        response = requests.post(SERVER_URL, data=data, timeout=120)
        
        if response.status_code == 200:
            # Save the generated image
            if output_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"plan_view_{timestamp}.png"
            
            output_dir = os.path.expanduser("~/Downloads/ai_generated_images")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Plan view generated and saved to: {output_path}")
            return True, output_path, "Plan view generated successfully!"
        else:
            error_msg = f"Server error: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            return False, None, error_msg
            
    except Exception as e:
        error_msg = f"Error generating plan view: {str(e)}"
        print(f"❌ {error_msg}")
        return False, None, error_msg

def generate_detailed_3d_courtyard_prompt(concept, design_data, tree_data, attributes):
    """
    Generate a detailed 3D architectural description for the courtyard based on design data
    """
    # Start with the base architectural structure
    detailed_description = "A 3D architectural visualization of a courtyard surrounded by buildings, viewed from an elevated perspective showing depth and spatial relationships. "
    
    # Add the base concept
    detailed_description += f"The courtyard embodies the concept: {concept}. "
    
    # Add architectural context
    detailed_description += "The courtyard is enclosed by building walls on all four sides, creating a private outdoor space with natural light and ventilation. "
    
    # If we have design data, add specific details
    if design_data and isinstance(design_data, dict):
        # Add spaces and their descriptions with 3D elements
        spaces = design_data.get('spaces', {})
        if spaces:
            detailed_description += "The courtyard contains several functional areas in 3D space: "
            space_descriptions = []
            for space_name, space_type in spaces.items():
                if space_type == 'play':
                    space_descriptions.append(f"a {space_name} area with elevated platforms and interactive elements for active recreation")
                elif space_type == 'rest':
                    space_descriptions.append(f"a {space_name} zone with comfortable seating, shade structures, and quiet contemplation spaces")
                elif space_type == 'pond':
                    space_descriptions.append(f"a {space_name} water feature with flowing water, stone edges, and aquatic plants")
                elif space_type == 'flower':
                    space_descriptions.append(f"a {space_name} garden area with raised beds, colorful flowers, and seasonal blooms")
                elif space_type == 'tree':
                    space_descriptions.append(f"a {space_name} tree and shade area with mature trees, canopy coverage, and natural shade")
                else:
                    space_descriptions.append(f"a {space_name} {space_type} area with appropriate 3D elements")
            
            if space_descriptions:
                detailed_description += ", ".join(space_descriptions) + ". "
        
        # Add external functions as anchor points
        external_functions = design_data.get('external_functions', {})
        if external_functions:
            detailed_description += "External functions are positioned at the corners with architectural elements: "
            external_list = []
            for func_name, direction in external_functions.items():
                external_list.append(f"{func_name} building facing {direction} with appropriate architectural details")
            detailed_description += ", ".join(external_list) + ". "
        
        # Add positions for spatial accuracy
        positions = design_data.get('pos', {})
        if positions:
            detailed_description += "The spatial layout includes: "
            pos_list = []
            for space_name, coords in positions.items():
                if isinstance(coords, list) and len(coords) >= 2:
                    pos_list.append(f"{space_name} at coordinates ({coords[0]:.1f}, {coords[1]:.1f})")
            if pos_list:
                detailed_description += ", ".join(pos_list) + ". "
    
    # Add tree details for 3D visualization
    if tree_data and isinstance(tree_data, dict):
        tree_placement = tree_data.get('tree_placement', {})
        if tree_placement:
            detailed_description += "The landscape includes: "
            tree_list = []
            for tree_type, placement in tree_placement.items():
                tree_list.append(f"{tree_type} trees positioned according to {placement}")
            if tree_list:
                detailed_description += ", ".join(tree_list) + ". "
    
    # Add material specifications for 3D realism
    if attributes and isinstance(attributes, dict):
        material_list = []
        for key, value in attributes.items():
            if 'material' in key.lower() or 'stone' in key.lower() or 'wood' in key.lower() or 'brick' in key.lower():
                material_list.append(f"{value} materials")
        if material_list:
            detailed_description += f"The courtyard features {', '.join(material_list)} for authentic texture and appearance. "
    
    # Add 3D visual style specifications
    detailed_description += "The 3D visualization shows realistic lighting with natural shadows, detailed textures on all surfaces, proper depth and perspective, and atmospheric effects. "
    detailed_description += "The view captures the full spatial experience of the courtyard with all architectural and landscape elements in their proper 3D relationships."
    
    return detailed_description.strip()

def generate_detailed_plan_courtyard_prompt(concept, design_data, tree_data, attributes):
    """
    Generate a detailed plan view architectural description with coordinates and precise layout
    """
    # Start with the base architectural structure
    detailed_description = "A precise architectural plan view of a courtyard, viewed from directly above showing exact spatial relationships and coordinates. "
    
    # Add the base concept
    detailed_description += f"The courtyard plan reflects the concept: {concept}. "
    
    # Add architectural context
    detailed_description += "The courtyard is enclosed by building walls on all four sides, creating a rectangular outdoor space with clear boundaries. "
    
    # If we have design data, add specific details with coordinates
    if design_data and isinstance(design_data, dict):
        # Add spaces and their descriptions with precise coordinates
        spaces = design_data.get('spaces', {})
        positions = design_data.get('pos', {})
        if spaces and positions:
            detailed_description += "The courtyard contains functional areas at specific coordinates: "
            space_descriptions = []
            for space_name, space_type in spaces.items():
                if space_name in positions and isinstance(positions[space_name], list):
                    coords = positions[space_name]
                    if space_type == 'play':
                        space_descriptions.append(f"{space_name} play area at coordinates ({coords[0]:.1f}, {coords[1]:.1f}) with defined boundaries")
                    elif space_type == 'rest':
                        space_descriptions.append(f"{space_name} rest zone at coordinates ({coords[0]:.1f}, {coords[1]:.1f}) with seating areas")
                    elif space_type == 'pond':
                        space_descriptions.append(f"{space_name} water feature at coordinates ({coords[0]:.1f}, {coords[1]:.1f}) with stone edges")
                    elif space_type == 'flower':
                        space_descriptions.append(f"{space_name} garden at coordinates ({coords[0]:.1f}, {coords[1]:.1f}) with planting beds")
                    elif space_type == 'tree':
                        space_descriptions.append(f"{space_name} tree area at coordinates ({coords[0]:.1f}, {coords[1]:.1f}) with canopy coverage")
                    else:
                        space_descriptions.append(f"{space_name} {space_type} area at coordinates ({coords[0]:.1f}, {coords[1]:.1f})")
            
            if space_descriptions:
                detailed_description += ", ".join(space_descriptions) + ". "
        
        # Add external functions as anchor points with coordinates
        external_functions = design_data.get('external_functions', {})
        if external_functions and positions:
            detailed_description += "External functions are positioned at corner coordinates: "
            external_list = []
            for func_name, direction in external_functions.items():
                if func_name in positions and isinstance(positions[func_name], list):
                    coords = positions[func_name]
                    external_list.append(f"{func_name} building at coordinates ({coords[0]:.1f}, {coords[1]:.1f}) facing {direction}")
            if external_list:
                detailed_description += ", ".join(external_list) + ". "
        
        # Add connections and circulation paths
        links = design_data.get('links', [])
        if links:
            detailed_description += "Circulation paths connect: "
            connection_list = []
            for link in links:
                if isinstance(link, dict):
                    source = link.get('source', '')
                    target = link.get('target', '')
                    if source and target:
                        connection_list.append(f"{source} to {target}")
            if connection_list:
                detailed_description += ", ".join(connection_list) + ". "
    
    # Add tree details with placement ranges
    if tree_data and isinstance(tree_data, dict):
        tree_placement = tree_data.get('tree_placement', {})
        if tree_placement:
            detailed_description += "Tree placement follows: "
            tree_list = []
            for tree_type, placement in tree_placement.items():
                tree_list.append(f"{tree_type} trees in range {placement}")
            if tree_list:
                detailed_description += ", ".join(tree_list) + ". "
    
    # Add material specifications for plan accuracy
    if attributes and isinstance(attributes, dict):
        material_list = []
        for key, value in attributes.items():
            if 'material' in key.lower() or 'stone' in key.lower() or 'wood' in key.lower() or 'brick' in key.lower():
                material_list.append(f"{value} materials")
        if material_list:
            detailed_description += f"The plan shows {', '.join(material_list)} with precise material boundaries. "
    
    # Add plan view specifications
    detailed_description += "The plan view is drawn to scale with precise measurements, clear zone boundaries, coordinate grid system, and professional architectural drafting standards. "
    detailed_description += "All elements are shown in their exact spatial relationships with accurate dimensions and material specifications."
    
    return detailed_description.strip()

# Test function
if __name__ == "__main__":
    # Test text-to-image generation with detailed architectural description
    SERVER_URL = "https://c005-34-23-75-86.ngrok-free.app"
    
    # Sample design data for testing
    sample_design_data = {
        'spaces': {
            'playground': 'play',
            'meditation': 'rest',
            'fountain': 'pond',
            'garden': 'flower',
            'shade': 'tree'
        },
        'external_functions': {
            'entrance': 'north',
            'kitchen': 'east',
            'storage': 'south',
            'workshop': 'west'
        },
        'boundary_box': {
            'width': 25.0,
            'height': 20.0
        }
    }
    
    success, path, message = generate_ai_enhanced_image(
        None,  # No image path needed for text-to-image
        "modern courtyard design with sustainable landscaping and natural materials",
        design_data=sample_design_data
    )
    print(f"Result: {success}, Path: {path}, Message: {message}")