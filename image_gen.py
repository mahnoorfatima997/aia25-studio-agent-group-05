import requests
import os
from datetime import datetime

def generate_ai_enhanced_image(image_path, prompt, output_filename=None):
    """
    Generate an AI-enhanced image using the provided screenshot and prompt.
    
    Args:
        image_path: Path to the input image
        prompt: Text prompt for AI enhancement
        output_filename: Optional custom filename (if None, generates timestamped name)
    
    Returns:
        tuple: (success: bool, output_path: str, message: str)
    """
    # Generate output filename if not provided
    if output_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"ai_enhanced_courtyard_{timestamp}.png"
    
    # Ensure output directory exists
    output_dir = os.path.expanduser("~/Downloads/ai_enhanced_images")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)
    
    # Server configuration
    SERVER_URL = "https://e746-34-125-179-186.ngrok-free.app/generate"
    SEND_DATA = {
        "prompt": prompt,
        "seed": 123456,
        "steps": 40,
        "scale": 0.7
    }

    try:
        # Load image
        with open(image_path, "rb") as image_file:
            files = {"image": image_file}
            response = requests.post(SERVER_URL, data=SEND_DATA, files=files, timeout=60)

        # Save output
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"✅ AI-enhanced image saved to {output_path}")
            return True, output_path, f"🎨 AI-enhanced visualization complete! Saved to: {output_path}"
        else:
            error_msg = f"⚠️ Image generation service returned error {response.status_code}. Please try again."
            print(f"❌ Error {response.status_code}: {response.text}")
            return False, "", error_msg
            
    except requests.exceptions.Timeout:
        error_msg = "⚠️ Image generation service timed out. Please try again."
        print("❌ Request timed out")
        return False, "", error_msg
    except requests.exceptions.ConnectionError:
        error_msg = "⚠️ Could not connect to image generation service. Please check your internet connection."
        print("❌ Connection error")
        return False, "", error_msg
    except Exception as e:
        error_msg = f"⚠️ Unexpected error during image generation: {str(e)}"
        print(f"❌ Unexpected error: {e}")
        return False, "", error_msg

# Original code for direct execution
if __name__ == "__main__":
    # Replace as needed.
    # Default values will be taken if not included in SEND_DATA

    IMAGE_PATH = "input.jpg"
    SERVER_URL = "https://e746-34-125-179-186.ngrok-free.app"
    SEND_DATA = {
        "prompt": "futuristic public bathhouse by the ocean",
        "seed": 123456,
        "steps": 40,
        "scale": 0.7
    }

    # Load image
    SERVER_URL += "/generate"
    with open(IMAGE_PATH, "rb") as image_file:
        files = {"image": image_file}
        response = requests.post(SERVER_URL, data=SEND_DATA, files=files)

    # Save output.png
    if response.status_code == 200:
        with open("output.png", "wb") as f:
            f.write(response.content)
        print("✅ Image saved to output.png")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")