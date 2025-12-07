import json

INPUT_FILE = 'devices_110.json'
OUTPUT_FILE = 'devices_final.json'

# We are done trying to find a URL.
# A simple string is all you need for CW1.
PLACEHOLDER_STRING = "placeholder.png"

print(f"Loading '{INPUT_FILE}'...")

try:
    with open(INPUT_FILE, 'r') as f:
        devices = json.load(f)

    # Loop through every device and replace the URL
    for device in devices:
        device['image_url'] = PLACEHOLDER_STRING

    # Save the new file
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(devices, f, indent=2)

    print(f"Success! All {len(devices)} image URLs have been set to 'placeholder.png'.")
    print(f"Your new file is '{OUTPUT_FILE}'.")
    print("Use this new file to import into MongoDB. This problem is now solved.")

except Exception as e:
    print(f"An error occurred: {e}")