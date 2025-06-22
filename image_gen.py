import requests

def generate_ai_enhanced_image(image_path, prompt, output_filename="ai_enhanced_courtyard.png"):
    """
    Generate an AI-enhanced image using the provided screenshot and prompt.
    """
    # Server configuration
    SERVER_URL = "https://e746-34-125-179-186.ngrok-free.app/generate"
    SEND_DATA = {
        "prompt": prompt,
        "seed": 123456,
        "steps": 40,
        "scale": 0.7
    }

    # Load image
    with open(image_path, "rb") as image_file:
        files = {"image": image_file}
        response = requests.post(SERVER_URL, data=SEND_DATA, files=files)

    # Save output
    if response.status_code == 200:
        with open(output_filename, "wb") as f:
            f.write(response.content)
        print(f"✅ AI-enhanced image saved to {output_filename}")
        return True, output_filename, "🎨 AI-enhanced visualization complete! Your courtyard has been reimagined with artistic flair."
    else:
        error_msg = f"⚠️ Image generation service returned error {response.status_code}. Please try again."
        print(f"❌ Error {response.status_code}: {response.text}")
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