# requirements: requests
"""
Minimal script for Grasshopper to send heatmap data to the server.
Grasshopper only needs this function - the analysis and recommendations are handled by the server/UI.
"""

import requests
import json

def send_heatmap_data_to_server(heatmap_data):
    """
    Send heatmap data from Grasshopper to the server for analysis.
    
    Args:
        heatmap_data (list): List of ({x, y, z}, utci_value) tuples
            Example: [({x1, y1, z1}, utci1), ({x2, y2, z2}, utci2), ...]
            Note: z-coordinate will be ignored for 2D analysis
    
    Returns:
        dict: Server response with analysis results
    """
    try:
        # Convert 3D coordinates to 2D for analysis (ignore z-coordinate)
        heatmap_2d = []
        for point in heatmap_data:
            # Handle set format ({x, y, z}, utci)
            if isinstance(point, tuple) and len(point) == 2:
                coord, utci_value = point
                if isinstance(coord, set) and len(coord) >= 2:
                    # Convert set to list and take only x, y coordinates, ignore z
                    coord_list = list(coord)
                    coord_2d = [float(coord_list[0]), float(coord_list[1])]
                    heatmap_2d.append([coord_2d, float(utci_value)])
                elif isinstance(coord, (list, tuple)) and len(coord) >= 2:
                    # Handle list/tuple format as well
                    coord_2d = [float(coord[0]), float(coord[1])]
                    heatmap_2d.append([coord_2d, float(utci_value)])
        
        # Prepare the request data
        request_data = {
            "heatmap_data": heatmap_2d
        }
        
        headers = {'Content-Type': 'application/json'}
        
        print(f"Original data points: {len(heatmap_data)}")
        print(f"Converted to 2D: {len(heatmap_2d)} points")
        print(f"Sample point: {heatmap_2d[0] if heatmap_2d else 'No data'}")
        print(f"Sending request to: http://127.0.0.1:5000/heatmap_analysis")
        
        response = requests.post(
            "http://127.0.0.1:5000/heatmap_analysis",
            json=request_data,
            headers=headers,
            timeout=60  # Longer timeout for analysis
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Heatmap analysis completed successfully!")
            print(f"Analysis result: {result}")
            return result
        else:
            print(f"❌ Server error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error sending heatmap data: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return None

# Test function to verify the connection
def test_connection():
    """Test if the server is running and accessible"""
    try:
        response = requests.get("http://127.0.0.1:5000/", timeout=5)
        print(f"✅ Server is running! Status: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the Flask server is running on port 5000")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

# Example usage in Grasshopper:
# 1. Extract mesh coordinates and UTCI values from your analysis
# 2. Format as: [({x, y, z}, utci_value), ({x, y, z}, utci_value), ...]
# 3. Call: send_heatmap_data_to_server(your_heatmap_data)
# 4. Check the UI for activity recommendations and analysis results

# To test the connection first:
# test_connection() 