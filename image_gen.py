import requests
import base64
import io
from PIL import Image
import os
from datetime import datetime
import random

def generate_ai_enhanced_image(image_path, prompt, output_filename=None, design_data=None):
    """
    Generate AI-enhanced image using text-to-image generation with detailed architectural description
    """
    try:
        # Updated ngrok URL with the new server - using text-to-image endpoint
        SERVER_URL = "https://838e-34-126-162-220.ngrok-free.app/generate"
        
        # Generate detailed architectural description from design data
        detailed_prompt = generate_detailed_courtyard_prompt(prompt, design_data)
        
        # Enhanced prompt for architectural images - focus on top-down view
        enhanced_prompt = f"{detailed_prompt}, architectural top-down visualization, professional rendering, high quality, detailed, photorealistic, enhanced lighting, improved materials, refined textures, aerial perspective"
        
        # Use random seed for variety
        random_seed = random.randint(1, 9999999999)
        
        data = {
            "prompt": enhanced_prompt,
            "seed": random_seed,
            "steps": 35,  # Good balance for architectural images
            "scale": 8.0  # Strong guidance for architectural adherence
        }
        
        print(f"Sending request to {SERVER_URL}")
        print(f"Detailed Prompt: {enhanced_prompt}")
        print(f"Using seed: {random_seed}")
        
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
    # Start with the base architectural structure with random variation
    architectural_styles = [
        "A 4-sided rectangular courtyard surrounded by buildings, viewed from above in a top-down aerial perspective",
        "A modern rectangular courtyard enclosed by building walls, captured in an aerial top-down view",
        "A contemporary courtyard space bounded by four building sides, shown from above in architectural perspective",
        "A traditional rectangular courtyard with building perimeter, viewed from directly overhead"
    ]
    detailed_description = f"{random.choice(architectural_styles)}. "
    
    # Add the base prompt
    detailed_description += f"{base_prompt}. "
    
    # Add architectural context with variation
    context_options = [
        "The courtyard is enclosed by building walls on all four sides, creating a private outdoor space",
        "Building walls form a protective perimeter around the courtyard, defining the outdoor living area",
        "The courtyard is bounded by architectural walls, creating an intimate outdoor environment",
        "Four building sides create a sheltered courtyard space for outdoor activities"
    ]
    detailed_description += f"{random.choice(context_options)}. "
    
    # If we have design data, add specific details
    if design_data and isinstance(design_data, dict):
        # Add spaces and their descriptions
        spaces = design_data.get('spaces', {})
        if spaces:
            detailed_description += "The courtyard contains several functional areas: "
            space_descriptions = []
            for space_name, space_type in spaces.items():
                if space_type == 'play':
                    play_descriptions = [
                        f"a {space_name} area for active recreation",
                        f"a {space_name} zone designed for play and activities",
                        f"a {space_name} space for outdoor games and recreation"
                    ]
                    space_descriptions.append(random.choice(play_descriptions))
                elif space_type == 'rest':
                    rest_descriptions = [
                        f"a {space_name} zone for quiet contemplation",
                        f"a {space_name} area for relaxation and meditation",
                        f"a {space_name} space for peaceful reflection"
                    ]
                    space_descriptions.append(random.choice(rest_descriptions))
                elif space_type == 'pond':
                    pond_descriptions = [
                        f"a {space_name} water feature",
                        f"a {space_name} reflecting pool",
                        f"a {space_name} water element for tranquility"
                    ]
                    space_descriptions.append(random.choice(pond_descriptions))
                elif space_type == 'flower':
                    flower_descriptions = [
                        f"a {space_name} garden area",
                        f"a {space_name} planting zone",
                        f"a {space_name} floral landscape"
                    ]
                    space_descriptions.append(random.choice(flower_descriptions))
                elif space_type == 'tree':
                    tree_descriptions = [
                        f"a {space_name} tree and shade area",
                        f"a {space_name} canopy zone",
                        f"a {space_name} wooded space"
                    ]
                    space_descriptions.append(random.choice(tree_descriptions))
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
    
    # Add material and visual specifications with variation
    material_options = [
        "The courtyard features a mix of hardscape and softscape elements with natural materials",
        "Natural materials and sustainable elements define the courtyard's character",
        "The design incorporates a blend of hard and soft landscaping with eco-friendly materials",
        "Sustainable materials and natural elements create the courtyard's aesthetic"
    ]
    detailed_description += f"{random.choice(material_options)}. "
    
    detailed_description += "The design emphasizes sustainability and environmental harmony. "
    
    # Add visual style specifications with variation
    style_options = [
        "Professional architectural visualization with accurate spatial relationships, proper proportions, and realistic materials",
        "High-quality architectural rendering showing precise spatial layout, correct proportions, and authentic materials",
        "Detailed architectural documentation with accurate measurements, proper scale, and realistic material representation",
        "Professional design visualization with exact spatial relationships, appropriate proportions, and true-to-life materials"
    ]
    detailed_description += f"{random.choice(style_options)}. "
    
    detailed_description += "The top-down view clearly shows the layout, circulation patterns, and functional zoning of the courtyard design."
    
    return detailed_description.strip()

def generate_concept_view_from_text(prompt, output_filename=None):
    """
    Generate concept view using text-to-image generation with LoRA weights
    Uses the /generate endpoint for inspirational concept images
    """
    try:
        # Use the /generate endpoint for concept images (text-to-image with LoRA)
        SERVER_URL = "https://838e-34-126-162-220.ngrok-free.app/generate"
        
        # Enhanced prompt for concept visualization with LoRA
        enhanced_prompt = f"{prompt}, architectural concept visualization, inspirational design, artistic rendering, high quality, detailed, photorealistic, enhanced lighting, improved materials, refined textures, creative courtyard environment, brown square building surrounding the courtyard, courtyard space inside the building perimeter"
        
        # Use random seed for variety
        random_seed = random.randint(1, 9999999999)
        
        data = {
            "prompt": enhanced_prompt,
            "seed": random_seed,
            "steps": 35,  # Good balance for concept images
            "scale": 8.0  # Strong guidance for concept adherence
        }
        
        print(f"Sending concept generation request to {SERVER_URL}")
        print(f"Prompt: {enhanced_prompt}")
        print(f"Using seed: {random_seed}")
        
        response = requests.post(SERVER_URL, data=data, timeout=120)
        
        if response.status_code == 200:
            # Save the generated image
            if output_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"concept_{timestamp}.png"
            
            output_dir = os.path.expanduser("~/Downloads/ai_generated_images")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Concept view generated and saved to: {output_path}")
            return True, output_path, "Concept view generated successfully!"
        else:
            error_msg = f"Server error: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            return False, None, error_msg
            
    except Exception as e:
        error_msg = f"Error generating concept view: {str(e)}"
        print(f"❌ {error_msg}")
        return False, None, error_msg

def generate_plan_view_from_text(prompt, output_filename=None):
    """
    Generate plan view using image-to-image generation with Grasshopper screenshot
    Uses the /generate-img2img endpoint for precise plan layouts
    """
    try:
        # Use the /generate-img2img endpoint for plan views (image-to-image with regular SDXL)
        SERVER_URL = "https://838e-34-126-162-220.ngrok-free.app/generate-img2img"
        
        # Enhanced prompt for plan visualization with coordinates and architectural precision
        enhanced_prompt = f"{prompt}, architectural plan view, technical drawing style, clean lines, professional layout, top-down perspective, precise measurements, clear zone boundaries, elegant spatial composition, coordinate system, realistic materials, professional architectural documentation, brown square building surrounding the courtyard, courtyard space inside the building perimeter"
        
        # Look for the most recent Grasshopper screenshot to use as base image
        screenshot_path = None
        gh_screenshots_dir = os.path.expanduser("~/Downloads/gh_screenshots")
        if os.path.exists(gh_screenshots_dir):
            screenshot_files = [f for f in os.listdir(gh_screenshots_dir) if f.endswith('.png')]
            if screenshot_files:
                # Use the most recent screenshot
                latest_screenshot = max(screenshot_files, key=lambda x: os.path.getctime(os.path.join(gh_screenshots_dir, x)))
                screenshot_path = os.path.join(gh_screenshots_dir, latest_screenshot)
                print(f"📸 Using Grasshopper screenshot: {latest_screenshot}")
            else:
                print("⚠️ No Grasshopper screenshots found, creating generic base image")
                # Fallback to creating a generic base image if no screenshot exists
                from PIL import Image, ImageDraw
                base_image = Image.new('RGB', (1024, 1024), color='white')
                draw = ImageDraw.Draw(base_image)
                grid_spacing = random.choice([48, 56, 64, 72])
                for i in range(0, 1024, grid_spacing):
                    draw.line([(i, 0), (i, 1024)], fill='lightgray', width=1)
                    draw.line([(0, i), (1024, i)], fill='lightgray', width=1)
                temp_image_path = "/tmp/base_plan_image.png"
                base_image.save(temp_image_path)
                screenshot_path = temp_image_path
        else:
            print("⚠️ No Grasshopper screenshots directory found, creating generic base image")
            # Fallback to creating a generic base image
            from PIL import Image, ImageDraw
            base_image = Image.new('RGB', (1024, 1024), color='white')
            draw = ImageDraw.Draw(base_image)
            grid_spacing = random.choice([48, 56, 64, 72])
            for i in range(0, 1024, grid_spacing):
                draw.line([(i, 0), (i, 1024)], fill='lightgray', width=1)
                draw.line([(0, i), (1024, i)], fill='lightgray', width=1)
            temp_image_path = "/tmp/base_plan_image.png"
            base_image.save(temp_image_path)
            screenshot_path = temp_image_path
        
        # Use random seed for variety
        random_seed = random.randint(1, 9999999999)
        
        # Prepare the request with both prompt and image
        data = {
            "prompt": enhanced_prompt,
            "seed": random_seed,
            "steps": 35,  # Good balance for plan images
            "scale": 8.0  # Strong guidance for plan adherence
        }
        
        # Prepare the image file
        with open(screenshot_path, 'rb') as img_file:
            files = {'image': img_file}
            
            print(f"Sending plan generation request to {SERVER_URL}")
            print(f"Prompt: {enhanced_prompt}")
            print(f"Using seed: {random_seed}")
            print(f"Using base image: {screenshot_path}")
            
            response = requests.post(SERVER_URL, data=data, files=files, timeout=120)
        
        # Clean up temporary file if we created one
        if screenshot_path == "/tmp/base_plan_image.png" and os.path.exists(screenshot_path):
            os.remove(screenshot_path)
        
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

def generate_plan_view_from_screenshot(screenshot_path, prompt, output_filename=None):
    """
    Generate enhanced plan view using image-to-image generation with Grasshopper screenshot
    Uses the /generate-img2img endpoint for precise plan layouts
    """
    try:
        # Use the /generate-img2img endpoint for plan views (image-to-image with regular SDXL)
        SERVER_URL = "https://838e-34-126-162-220.ngrok-free.app/generate-img2img"
        
        # Enhanced prompt for plan visualization with coordinates and architectural precision
        enhanced_prompt = f"{prompt}, architectural plan view, technical drawing style, clean lines, professional layout, top-down perspective, precise measurements, clear zone boundaries, elegant spatial composition, coordinate system, realistic materials, professional architectural documentation, brown square building surrounding the courtyard, courtyard space inside the building perimeter"
        
        # Check if screenshot exists
        if not os.path.exists(screenshot_path):
            return False, None, f"Screenshot file not found: {screenshot_path}"
        
        # Use random seed for variety
        random_seed = random.randint(1, 9999999999)
        
        # Prepare the request with both prompt and image
        data = {
            "prompt": enhanced_prompt,
            "seed": random_seed,
            "steps": 35,  # Good balance for plan images
            "scale": 8.0  # Strong guidance for plan adherence
        }
        
        # Prepare the image file
        with open(screenshot_path, 'rb') as img_file:
            files = {'image': img_file}
            
            print(f"Sending plan generation request to {SERVER_URL}")
            print(f"Prompt: {enhanced_prompt}")
            print(f"Using seed: {random_seed}")
            print(f"Using screenshot: {screenshot_path}")
            
            response = requests.post(SERVER_URL, data=data, files=files, timeout=120)
        
        if response.status_code == 200:
            # Save the generated image
            if output_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"enhanced_plan_{timestamp}.png"
            
            output_dir = os.path.expanduser("~/Downloads/ai_generated_images")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Enhanced plan view generated and saved to: {output_path}")
            return True, output_path, "Enhanced plan view generated successfully!"
        else:
            error_msg = f"Server error: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            return False, None, error_msg
            
    except Exception as e:
        error_msg = f"Error generating enhanced plan view: {str(e)}"
        print(f"❌ {error_msg}")
        return False, None, error_msg

def generate_detailed_plan_courtyard_prompt(concept, design_data, tree_data, attributes):
    """
    Generate a detailed plan view architectural description with coordinates and precise layout
    """
    # Start with the base architectural structure
    detailed_description = "A precise architectural plan view of a courtyard, viewed from directly above showing exact spatial relationships and coordinates. "
    
    # Add the base concept
    detailed_description += f"The courtyard plan reflects the concept: {concept}. "
    
    # Add architectural context
    detailed_description += "The courtyard is enclosed by building walls on all four sides, creating a rectangular outdoor space with clear boundaries. The brown square represents the building perimeter, and the courtyard space is inside this building. "
    
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
    detailed_description += "All elements are shown in their exact spatial relationships with accurate dimensions and material specifications. The brown square building perimeter clearly defines the courtyard space within."
    
    return detailed_description.strip()

# Test function
if __name__ == "__main__":
    # Test text-to-image generation with detailed architectural description
    SERVER_URL = "https://838e-34-126-162-220.ngrok-free.app"
    
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