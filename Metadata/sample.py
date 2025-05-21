import json
from pprint import pprint

# Path to the JSON file
json_file_path = "output_scenes/CLEVR_new_000000.json"

# Load the JSON file
with open(json_file_path, 'r') as f:
    data = json.load(f)

# Print the structure of the JSON
print("\nJSON Structure:")
print("=" * 50)
print(f"Top-level keys: {list(data.keys())}")
print("\nDetailed structure:")
print("=" * 50)

# Print basic info
print(f"\nSplit: {data['split']}")
print(f"Image index: {data['image_index']}")
print(f"Image filename: {data['image_filename']}")

# Print objects info
print("\nObjects:")
print("-" * 20)
for i, obj in enumerate(data['objects']):
    print(f"\nObject {i}:")
    for key, value in obj.items():
        print(f"  {key}: {value}")

# Print directions
print("\nDirections:")
print("-" * 20)
for direction, vector in data['directions'].items():
    print(f"  {direction}: {vector}")

# Print relationships
print("\nRelationships:")
print("-" * 20)
for relation, objects in data['relationships'].items():
    print(f"  {relation}: {objects}")
