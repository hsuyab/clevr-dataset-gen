import json
from pprint import pprint
import numpy as np

# Load the base scene information
with open("/Users/ayush/Documents/GitHub/clevr-dataset-gen/Metadata/base_scene_scene_info.json", 'r') as f:
    base_scene_data = json.load(f)

# Load the scene data with directions
with open("output_scenes/CLEVR_new_000000.json", 'r') as f:
    scene_data = json.load(f)

# Get camera location
camera_location = np.array(base_scene_data['cameras'][0]['location'])

# Get direction vectors
directions = scene_data['directions']

print("\nCamera-Direction Analysis:")
print("=" * 50)
print(f"Camera Location: {camera_location}")

# Function to calculate angle between two vectors
def calculate_angle(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    dot_product = np.dot(v1, v2)
    norms = np.linalg.norm(v1) * np.linalg.norm(v2)
    cos_angle = dot_product / norms
    angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
    return np.degrees(angle)

print("\nDirection Vectors and their relationship to camera:")
print("-" * 50)
for direction_name, direction_vector in directions.items():
    # Convert direction vector to numpy array
    dir_vector = np.array(direction_vector)
    
    # Calculate angle between camera position and direction vector
    angle = calculate_angle(camera_location, dir_vector)
    
    # Calculate dot product to determine if vectors are pointing in similar direction
    dot_product = np.dot(camera_location, dir_vector)
    
    print(f"\nDirection: {direction_name}")
    print(f"Vector: {direction_vector}")
    print(f"Angle with camera position: {angle:.2f}°")
    print(f"Dot product: {dot_product:.2f}")
    
    # Determine if vectors are pointing in similar direction
    if abs(dot_product) > 0.5:
        if dot_product > 0:
            print("Status: Vectors are pointing in similar direction")
        else:
            print("Status: Vectors are pointing in opposite direction")
    else:
        print("Status: Vectors are roughly perpendicular")

# Calculate camera's view direction (assuming camera is looking at origin)
origin = np.array([0, 0, 0])
camera_direction = origin - camera_location
camera_direction = camera_direction / np.linalg.norm(camera_direction)

print("\nCamera View Direction Analysis:")
print("-" * 50)
print(f"Camera View Direction (normalized): {camera_direction}")

for direction_name, direction_vector in directions.items():
    dir_vector = np.array(direction_vector)
    angle = calculate_angle(camera_direction, dir_vector)
    print(f"\n{direction_name} vs Camera View:")
    print(f"Angle: {angle:.2f}°")
    
    # Determine if direction is in front of or behind camera
    dot_product = np.dot(camera_direction, dir_vector)
    if dot_product > 0:
        print("Status: Direction is in front of camera")
    else:
        print("Status: Direction is behind camera")
