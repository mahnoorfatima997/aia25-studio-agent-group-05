#!/usr/bin/env python3
"""
Fallback utilities for LLM function calls
Provides default values when LLM responses are incomplete or fail
"""

import json
import random

# Default fallback values for different data types
DEFAULT_SPACES = {
    "spaces": {
        "play": 1,
        "rest": 3,
        "pond": 5,
        "flower": 7,
        "tree": 9
    }
}

DEFAULT_LINKS = {
    "links": {
        "play": "rest",
        "rest": "tree",
        "tree": "flower",
        "flower": "pond",
        "pond": "play"
    }
}

DEFAULT_POSITIONS = {
    "positions": [
        "play: center",
        "rest: north",
        "pond: east",
        "flower: south",
        "tree: west"
    ]
}

DEFAULT_CARDINAL_DIRECTIONS = {
    "cardinal_directions": [
        "play: center",
        "rest: N",
        "pond: E",
        "flower: S",
        "tree: W"
    ]
}

DEFAULT_WEIGHTS = {
    "weights": {
        "play": 5,
        "rest": 5,
        "pond": 5,
        "flower": 5,
        "tree": 5
    }
}

DEFAULT_ANCHORS = {
    "anchors": {
        "play": False,
        "rest": False,
        "pond": False,
        "flower": False,
        "tree": False
    }
}

DEFAULT_POS = {
    "pos": {
        "play": [0.5, 0.5],
        "rest": [0.5, 0.8],
        "pond": [0.8, 0.5],
        "flower": [0.5, 0.2],
        "tree": [0.2, 0.5]
    }
}

DEFAULT_TREE_PLACEMENT = {
    "tree_placement": {
        "shade_trees": "north_west",
        "ornamental_trees": "center",
        "fruit_trees": "south_east"
    }
}

DEFAULT_PWR = {
    "pwr": {
        "shade_trees": "medium",
        "ornamental_trees": "low",
        "fruit_trees": "high"
    }
}

DEFAULT_ATTRIBUTES = {
    "materials": "natural stone and wood",
    "style": "modern minimalist",
    "lighting": "ambient",
    "seating": "wooden benches",
    "pathways": "stone pavers"
}

def safe_extract_json(llm_response, fallback_data, data_type="unknown"):
    """
    Safely extract JSON from LLM response with fallback values
    
    Args:
        llm_response: The raw LLM response string
        fallback_data: Default data to use if extraction fails
        data_type: Type of data for logging purposes
    
    Returns:
        dict: Extracted JSON data or fallback data
    """
    try:
        # Try to parse the LLM response as JSON
        if isinstance(llm_response, str):
            extracted_data = json.loads(llm_response)
        elif isinstance(llm_response, dict):
            extracted_data = llm_response
        else:
            print(f"⚠️ Invalid LLM response format for {data_type}, using fallback")
            return fallback_data
        
        # Validate that the extracted data has the expected structure
        if _validate_data_structure(extracted_data, fallback_data, data_type):
            print(f"✅ Successfully extracted {data_type} from LLM response")
            return extracted_data
        else:
            print(f"⚠️ LLM response for {data_type} has invalid structure, using fallback")
            return fallback_data
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error for {data_type}: {e}")
        print(f"   Raw response: {llm_response}")
        return fallback_data
    except Exception as e:
        print(f"❌ Unexpected error extracting {data_type}: {e}")
        return fallback_data

def _validate_data_structure(extracted_data, fallback_data, data_type):
    """
    Validate that extracted data has the expected structure
    
    Args:
        extracted_data: Data extracted from LLM
        fallback_data: Reference structure to validate against
        data_type: Type of data being validated
    
    Returns:
        bool: True if structure is valid, False otherwise
    """
    try:
        # Check if the top-level keys match
        if set(extracted_data.keys()) != set(fallback_data.keys()):
            print(f"   Structure mismatch: expected {list(fallback_data.keys())}, got {list(extracted_data.keys())}")
            return False
        
        # For nested structures, check if required keys exist
        for key in fallback_data.keys():
            if key not in extracted_data:
                print(f"   Missing required key: {key}")
                return False
            
            # For spaces, weights, anchors - check if all required space types exist
            if key in ["spaces", "weights", "anchors"]:
                required_spaces = ["play", "rest", "pond", "flower", "tree"]
                if not all(space in extracted_data[key] for space in required_spaces):
                    print(f"   Missing required space types in {key}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"   Validation error: {e}")
        return False

def get_fallback_spaces():
    """Get fallback spaces data"""
    return DEFAULT_SPACES.copy()

def get_fallback_links():
    """Get fallback links data"""
    return DEFAULT_LINKS.copy()

def get_fallback_positions():
    """Get fallback positions data"""
    return DEFAULT_POSITIONS.copy()

def get_fallback_cardinal_directions():
    """Get fallback cardinal directions data"""
    return DEFAULT_CARDINAL_DIRECTIONS.copy()

def get_fallback_weights():
    """Get fallback weights data"""
    return DEFAULT_WEIGHTS.copy()

def get_fallback_anchors():
    """Get fallback anchors data"""
    return DEFAULT_ANCHORS.copy()

def get_fallback_pos():
    """Get fallback position coordinates data"""
    return DEFAULT_POS.copy()

def get_fallback_tree_placement():
    """Get fallback tree placement data"""
    return DEFAULT_TREE_PLACEMENT.copy()

def get_fallback_pwr():
    """Get fallback plant water requirement data"""
    return DEFAULT_PWR.copy()

def get_fallback_attributes():
    """Get fallback attributes data"""
    return DEFAULT_ATTRIBUTES.copy()

def enhance_fallback_with_context(fallback_data, concept, external_functions, attributes):
    """
    Enhance fallback data with context from concept and other data
    
    Args:
        fallback_data: Base fallback data
        concept: Design concept
        external_functions: External functions dict
        attributes: Design attributes
    
    Returns:
        dict: Enhanced fallback data
    """
    enhanced_data = fallback_data.copy()
    
    # Enhance spaces based on concept keywords
    if "spaces" in enhanced_data:
        spaces = enhanced_data["spaces"]
        
        # Adjust based on concept keywords
        concept_lower = concept.lower()
        
        if "play" in concept_lower or "social" in concept_lower:
            spaces["play"] = 2  # More prominent position
        if "quiet" in concept_lower or "meditation" in concept_lower:
            spaces["rest"] = 4  # More prominent position
        if "water" in concept_lower or "pond" in concept_lower:
            spaces["pond"] = 6  # More prominent position
        if "garden" in concept_lower or "flower" in concept_lower:
            spaces["flower"] = 8  # More prominent position
        if "tree" in concept_lower or "shade" in concept_lower:
            spaces["tree"] = 10  # More prominent position
    
    # Enhance links based on external functions
    if "links" in enhanced_data and external_functions:
        links = enhanced_data["links"]
        
        # Add connections to external functions
        for func_name in external_functions.keys():
            if func_name not in links:
                # Connect to most appropriate space based on function name
                if "cafe" in func_name.lower() or "restaurant" in func_name.lower():
                    links[func_name] = "play"
                elif "library" in func_name.lower() or "study" in func_name.lower():
                    links[func_name] = "rest"
                elif "garden" in func_name.lower():
                    links[func_name] = "flower"
                else:
                    links[func_name] = "play"  # Default connection
    
    # Enhance positions based on external functions
    if "positions" in enhanced_data and external_functions:
        positions = enhanced_data["positions"]
        
        for func_name, direction in external_functions.items():
            if direction:
                positions.append(f"{func_name}: {direction}")
    
    return enhanced_data

def create_robust_geometry_data(concept, external_functions, attributes):
    """
    Create a complete geometry data structure with fallbacks
    
    Args:
        concept: Design concept
        external_functions: External functions dict
        attributes: Design attributes
    
    Returns:
        dict: Complete geometry data with fallbacks
    """
    # Create enhanced fallback data
    enhanced_spaces = enhance_fallback_with_context(
        get_fallback_spaces(), concept, external_functions, attributes
    )
    enhanced_links = enhance_fallback_with_context(
        get_fallback_links(), concept, external_functions, attributes
    )
    enhanced_positions = enhance_fallback_with_context(
        get_fallback_positions(), concept, external_functions, attributes
    )
    enhanced_cardinal_directions = enhance_fallback_with_context(
        get_fallback_cardinal_directions(), concept, external_functions, attributes
    )
    enhanced_weights = enhance_fallback_with_context(
        get_fallback_weights(), concept, external_functions, attributes
    )
    enhanced_anchors = enhance_fallback_with_context(
        get_fallback_anchors(), concept, external_functions, attributes
    )
    enhanced_pos = enhance_fallback_with_context(
        get_fallback_pos(), concept, external_functions, attributes
    )
    
    # Create complete geometry data structure
    geometry_data = {
        "spaces": enhanced_spaces["spaces"],
        "links": enhanced_links["links"],
        "positions": enhanced_positions["positions"],
        "cardinal_directions": enhanced_cardinal_directions["cardinal_directions"],
        "weights": enhanced_weights["weights"],
        "anchors": enhanced_anchors["anchors"],
        "external_functions": external_functions or {},
        "pos": enhanced_pos["pos"],
        "boundary_box": {},
        "external_anchors": {}
    }
    
    return geometry_data

def create_robust_tree_data(concept, attributes):
    """
    Create a complete tree data structure with fallbacks
    
    Args:
        concept: Design concept
        attributes: Design attributes
    
    Returns:
        dict: Complete tree data with fallbacks
    """
    enhanced_tree_placement = enhance_fallback_with_context(
        get_fallback_tree_placement(), concept, {}, attributes
    )
    enhanced_pwr = enhance_fallback_with_context(
        get_fallback_pwr(), concept, {}, attributes
    )
    
    tree_data = {
        "tree_placement": enhanced_tree_placement["tree_placement"],
        "PWR": enhanced_pwr["pwr"]
    }
    
    return tree_data 