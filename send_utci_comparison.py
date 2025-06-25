# requirements: requests

import requests
import json

def send_utci_to_ui(utci_values, utci_values_flat):
    """
    Send two sets of UTCI values to the server for comparison:
        1. utci_values: UTCI values with trees (better thermal comfort)
        2. utci_values_flat: UTCI values without trees (baseline)

    Returns:
        success: Boolean
        message: Status message
    """
    try:
        print(f"📤 Sending UTCI comparison data")
        print(f"   With trees: {utci_values}")
        print(f"   Without trees: {utci_values_flat}")
        
        # ✅ Correct data structure that matches server expectations
        data = {
            "utci_values": utci_values,  # Values with trees
            "utci_values_flat": utci_values_flat  # Values without trees
        }

        response = requests.post(
            "http://127.0.0.1:5000/utci_values",
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        print(f"   Response status: {response.status_code}")
        print(f"   Response content: {response.text}")

        if response.status_code == 200:
            result = response.json()
            print("✅ UTCI comparison data sent successfully!")
            return True, "UTCI comparison data sent successfully"
        else:
            print("❌ Server returned an error")
            return False, f"Server error: {response.status_code}"

    except Exception as e:
        print(f"❌ Error sending UTCI comparison data: {e}")
        return False, str(e)


def flatten(input_list):
    """Recursively flattens nested lists/tuples"""
    for item in input_list:
        if isinstance(item, (list, tuple)):
            yield from flatten(item)
        else:
            yield item


def process_utci_list(utci_input):
    """
    Clean and convert UTCI inputs to floats.
    Handles flat and nested lists.
    """
    print(f"🔍 Processing input of type {type(utci_input)}")
    clean_utci_values = []

    try:
        # Handle different input types
        if isinstance(utci_input, (list, tuple)):
            flattened = list(flatten(utci_input))
        elif isinstance(utci_input, str):
            # If it's a single string, try to convert it to float
            flattened = [utci_input]
        else:
            # Single value
            flattened = [utci_input]
    except Exception as e:
        print(f"❌ Error processing input: {e}")
        return []

    for i, val in enumerate(flattened):
        try:
            clean_val = float(val)
            clean_utci_values.append(clean_val)
            print(f"   ✓ Value {i+1}: {clean_val:.2f}°C")
        except (ValueError, TypeError) as e:
            print(f"   ⚠️ Skipping value {i+1}: '{val}' (error: {e})")

    return clean_utci_values


# --- Grasshopper inputs ---
# Replace these with actual GH inputs: utci_values and utci_values_flat
# Make sure you FLATTEN the second input (`utci_values_flat`) in GH if needed

print("🔄 Processing UTCI values for comparison...")

# Process both sets of UTCI values
all_utci_values_tree = process_utci_list(utci_values)  # With trees
all_utci_values_flat = process_utci_list(utci_values_flat)  # Without trees

if all_utci_values_tree or all_utci_values_flat:
    print(f"\n🚀 Ready to send comparison data:")
    print(f"   With trees: {len(all_utci_values_tree)} values")
    print(f"   Without trees: {len(all_utci_values_flat)} values")
    
    success, message = send_utci_to_ui(all_utci_values_tree, all_utci_values_flat)
else:
    success = False
    message = "No valid UTCI values to send"
    print("❌ No valid UTCI values found")

# Grasshopper outputs
a = success
b = message
c = len(all_utci_values_tree)
d = len(all_utci_values_flat)

print(f"\nFinal Status: {message}")
print(f"Values with trees: {c}")
print(f"Values without trees: {d}")

# Additional info for debugging
if success:
    print("✅ Data sent successfully! The UI will now show:")
    print("   - Comparison between tree and flat values")
    print("   - Average improvement from trees")
    print("   - Tips for further optimization")
else:
    print("❌ Failed to send data. Check the error message above.") 