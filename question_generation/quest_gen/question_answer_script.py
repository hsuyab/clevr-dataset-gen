# %% [markdown]
# ### Question 1:
# 
# - "Remove any object that has `{attribute}` = `{value}`. How many objects remain that have `{color}` and `{shape}`?"
# - Question Template: Delete,  Question Type: Existence

# %%
import json

# --- Load JSON from file ---
json_file_path = "/Users/ayush/Documents/GitHub/clevr-dataset-gen/Metadata/output_scenes/CLEVR_new_000000.json"  # Change path as needed

with open(json_file_path, "r") as f:
    scene_data = json.load(f)


def count_after_removal(data, remove_attribute, remove_value, target_color, target_shape):
    """
    Removes objects based on a condition and counts remaining objects matching color and shape.

    Args:
        data (dict): The dictionary loaded from the JSON scene file.
        remove_attribute (str): The attribute key to check for removal (e.g., "size").
        remove_value (str): The value of the attribute that triggers removal (e.g., "large").
        target_color (str): The color to count in the remaining objects.
        target_shape (str): The shape to count in the remaining objects.

    Returns:
        int: The count of remaining objects matching the target color and shape.
    """
    if 'objects' not in data:
        print("Error: 'objects' key not found in data.")
        return 0

    remaining_objects = []
    for obj in data['objects']:
        # Check if the object has the removal attribute and if its value matches the removal value
        if remove_attribute in obj and obj[remove_attribute] == remove_value:
            continue # Skip this object (simulate removal)
        remaining_objects.append(obj)

    count = 0
    for obj in remaining_objects:
        # Check if the remaining object has the target color and shape
        if obj.get('color') == target_color and obj.get('shape') == target_shape:
            count += 1

    print(f"Removed objects where {remove_attribute} = {remove_value}.")
    print(f"Found {count} remaining objects with color = {target_color} and shape = {target_shape}.")
    return count

# --- Example Usage for Question 1 ---
# Remove any object that has material = metal. How many objects remain that have color=blue and shape=cylinder?
remove_attr = "material"
remove_val = "metal"
target_col = "blue"
target_shp = "cylinder"

count1 = count_after_removal(scene_data, remove_attr, remove_val, target_col, target_shp)

print("-" * 20)

# Remove any object that has size = large. How many objects remain that have color=gray and shape=cube?
remove_attr = "size"
remove_val = "large"
target_col = "gray"
target_shp = "cube"

count2 = count_after_removal(scene_data, remove_attr, remove_val, target_col, target_shp)

# %% [markdown]
# ### Question 2:

# %%
import json
import copy  # Needed for deepcopy

# --- Load JSON from file ---
# json_file_path = "/content/output_scenes/CLEVR_new_000000.json"  # Change path as needed

# with open(json_file_path, "r") as f:
#     scene_data = json.load(f)
def load_scene(file_path):
    json_file_path = "/Users/ayush/Documents/GitHub/clevr-dataset-gen/Metadata/output_scenes/"+file_path
    with open(json_file_path, "r") as f:
        scene_data = json.load(f)
    return scene_data

def count_after_color_change(data, original_color, new_color):
    """
    Changes the color of objects and counts how many objects still have the original color.

    Args:
        data (dict): The dictionary loaded from the JSON scene file.
        original_color (str): The color of objects to change.
        new_color (str): The color to change the objects to.

    Returns:
        tuple: A tuple containing:
            - int: The count of objects that *still* have the original_color.
            - int: The count of objects that *now* have the new_color.
    """
    if 'objects' not in data:
        print("Error: 'objects' key not found in data.")
        return 0, 0

    # Create a deep copy to avoid modifying the original data
    modified_data = copy.deepcopy(data)
    objects_to_change = 0

    for obj in modified_data['objects']:
        if obj.get('color') == original_color:
            obj['color'] = new_color
            objects_to_change += 1

    print(f"Changed {objects_to_change} objects from {original_color} to {new_color}.")

    # Count how many objects *still* have the original color
    original_color_remaining_count = sum(1 for obj in modified_data['objects'] if obj.get('color') == original_color)

    # Count how many objects *now* have the new color
    new_color_count = sum(1 for obj in modified_data['objects'] if obj.get('color') == new_color)

    print(f"Found {original_color_remaining_count} objects remaining with color={original_color}.")
    print(f"Found {new_color_count} objects now with color={new_color}.")

    return original_color_remaining_count, new_color_count

# %%
scene_data = load_scene("CLEVR_new_000000.json")
# --- Example Usage ---
# scene_data = load_scene()
# Change all gray objects to yellow. How many gray objects remain?
orig_color = "gray"
new_col = "yellow"
remaining_count, new_count = count_after_color_change(scene_data, orig_color, new_col)

print("-" * 20)

# Change all purple objects to red. How many purple objects remain?
orig_color = "purple"
new_col = "red"
remaining_count2, new_count2 = count_after_color_change(scene_data, orig_color, new_col)


# %%
scene_data = load_scene("CLEVR_new_000001.json")
# --- Example Usage ---
# scene_data = load_scene()
# Change all gray objects to yellow. How many gray objects remain?
orig_color = "yellow"
new_col = "red"
remaining_count, new_count = count_after_color_change(scene_data, orig_color, new_col)

# %% [markdown]
# ### Questions 4

# %%
# Script using 3D coordinates for viewpoint change
import json
import math

# --- Vector Math Helpers ---
def subtract_vectors(v1, v2):
    """Subtracts v2 from v1."""
    if v1 is None or v2 is None or len(v1) != len(v2):
        return None
    return [a - b for a, b in zip(v1, v2)]

def dot_product(v1, v2):
    """Calculates the dot product of v1 and v2."""
    if v1 is None or v2 is None or len(v1) != len(v2):
        return 0 # Or raise an error? Returning 0 might hide issues. Let's check inputs later.
    return sum(a * b for a, b in zip(v1, v2))

def vector_magnitude(v):
    """Calculates the magnitude (length) of a vector."""
    if v is None: return 0
    return math.sqrt(sum(a * a for a in v))

def normalize_vector(v):
    """Normalizes a vector to unit length."""
    if v is None: return None
    mag = vector_magnitude(v)
    if mag == 0:
        return [0.0] * len(v) # Or handle as error?
    return [a / mag for a in v]

# --- Object Identification Helpers ---
def find_object_index_by_attrs(objects, attrs):
    """Finds the index of the first object matching all given attributes."""
    for i, obj in enumerate(objects):
        if not isinstance(obj, dict): continue # Skip if not a dictionary
        match = True
        for key, value in attrs.items():
            if obj.get(key) != value:
                match = False
                break
        if match:
            return i
    return -1 # Not found

def get_object_description(objects, index):
    """Generates a string description for an object at a given index."""
    if 0 <= index < len(objects) and isinstance(objects[index], dict):
        obj = objects[index]
        # Filter out None or empty values before joining
        parts = [
            obj.get('size'), obj.get('color'), obj.get('material'), obj.get('shape')
        ]
        desc = ' '.join(filter(None, parts))
        return f"the {desc}" if desc else "unknown object"
    return "unknown object"

# --- Main Logic ---
def find_objects_left_from_new_view(data, ref_object_attrs):
    """
    Finds objects to the 'left' of a reference object when viewing from the 'right',
    using 3D coordinate calculations.
    """
    if 'objects' not in data or 'directions' not in data:
        print("Error: 'objects' or 'directions' key not found in data.")
        return []
    
    objects = data['objects']
    directions = data['directions']

    # 1. Identify Reference Object
    ref_index = find_object_index_by_attrs(objects, ref_object_attrs)
    if ref_index == -1:
        print(f"Error: Reference object with attributes {ref_object_attrs} not found.")
        return []
    ref_obj = objects[ref_index]
    ref_coords = ref_obj.get('3d_coords')
    if ref_coords is None or len(ref_coords) != 3:
        print(f"Error: Missing or invalid 3D coordinates for reference object {ref_object_attrs}.")
        return []
    ref_desc = get_object_description(objects, ref_index)
    print(f"Reference object: {ref_desc} at {ref_coords}")

    # 2. Define New Coordinate System Vectors (Based on Original Directions)
    # New 'left' is original 'front'
    new_left_vec = directions.get('front')
    # New 'front' is original 'left'
    new_front_vec = directions.get('left')

    if new_left_vec is None or new_front_vec is None or len(new_left_vec)!=3 or len(new_front_vec)!=3:
        print("Error: Invalid 'front' or 'left' direction vectors in JSON.")
        return []
        
    # Normalization is good practice but might not be strictly necessary
    # if only comparing relative projections. Let's use original vectors for now.
    # new_left_unit_vec = normalize_vector(new_left_vec)
    # new_front_unit_vec = normalize_vector(new_front_vec)
    
    print(f"Using new 'left' direction vector: {new_left_vec} (original 'front')")
    print(f"Using new 'front' direction vector: {new_front_vec} (original 'left')")


    objects_to_left = []
    tolerance = 0.1 # Minimum projection value onto 'left' to be considered

    # 3. Iterate through Candidate Objects
    for i, cand_obj in enumerate(objects):
        if i == ref_index:
            continue # Skip self-comparison

        if not isinstance(cand_obj, dict): continue

        cand_coords = cand_obj.get('3d_coords')
        if cand_coords is None or len(cand_coords) != 3:
            continue # Skip objects without valid coordinates

        # 4. Calculate Relative Position Vector
        relative_vec = subtract_vectors(cand_coords, ref_coords)
        if relative_vec is None: continue

        # 5. Calculate Projections onto New Axes
        proj_left = dot_product(relative_vec, new_left_vec)
        proj_front = dot_product(relative_vec, new_front_vec)
        
        cand_desc = get_object_description(objects, i)
        # print(f"  Checking {cand_desc}: Proj_Left={proj_left:.2f}, Proj_Front={proj_front:.2f}")


        # 6. Apply Condition
        if proj_left > tolerance and proj_left > abs(proj_front):
            objects_to_left.append(cand_desc)
            # print(f"    -> Qualifies as 'left'")


    return objects_to_left

# --- Main Execution ---
if __name__ == "__main__":
    json_file_path ="/Users/ayush/Documents/GitHub/clevr-dataset-gen/Metadata/output_scenes/CLEVR_new_000000.json"
    try:
        with open(json_file_path, 'r') as f:
            scene_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at {json_file_path}")
        exit()
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_file_path}")
        exit()
    except Exception as e:
        print(f"An unexpected error occurred loading JSON: {e}")
        exit()


    print("\n--- Running Question with 3D Coords ---")
    print("Query: If looking from the right side, what object(s) are to the left of the purple cube?")

    # Attributes to uniquely identify the reference object
    ref_attrs = {"color": "purple", "shape": "cube"}

    left_objects = find_objects_left_from_new_view(scene_data, ref_attrs)

    print("\n--- Results ---")
    if left_objects:
        print(f"Objects found to the 'left' of the '{get_object_description(scene_data['objects'], find_object_index_by_attrs(scene_data['objects'], ref_attrs))}' from the new viewpoint:")
        for desc in left_objects:
            print(f"- {desc}")
    else:
        print(f"No objects found primarily to the 'left' of the reference object based on this calculation.")


# %%
# Script using 3D coordinates for viewpoint change (extended)
import json
import math

# --- Vector Math Helpers ---
def subtract_vectors(v1, v2):
    """Subtracts v2 from v1."""
    if v1 is None or v2 is None or len(v1) != 3 or len(v2) != 3: # Ensure 3D
        return None
    return [a - b for a, b in zip(v1, v2)]

def dot_product(v1, v2):
    """Calculates the dot product of v1 and v2."""
    if v1 is None or v2 is None or len(v1) != 3 or len(v2) != 3:
        # Return None or raise error to indicate problem more clearly
        return None 
    return sum(a * b for a, b in zip(v1, v2))

def vector_magnitude(v):
    """Calculates the magnitude (length) of a vector."""
    if v is None or len(v)!=3: return 0
    return math.sqrt(sum(a * a for a in v))

def normalize_vector(v):
    """Normalizes a vector to unit length."""
    if v is None or len(v)!=3: return None
    mag = vector_magnitude(v)
    if mag == 0:
        return [0.0] * 3
    return [a / mag for a in v]

# --- Object Identification Helpers ---
def find_object_index_by_attrs(objects, attrs):
    """Finds the index of the first object matching all given attributes."""
    for i, obj in enumerate(objects):
        if not isinstance(obj, dict): continue
        match = True
        for key, value in attrs.items():
            if obj.get(key) != value:
                match = False
                break
        if match:
            return i
    return -1

def get_object_description(objects, index):
    """Generates a string description for an object at a given index."""
    if 0 <= index < len(objects) and isinstance(objects[index], dict):
        obj = objects[index]
        parts = [
            obj.get('size'), obj.get('color'), obj.get('material'), obj.get('shape')
        ]
        desc = ' '.join(filter(None, parts))
        return f"the {desc}" if desc else "unknown object"
    return "unknown object"

# --- Core Logic for Relative Direction Calculation ---
def find_objects_relative_direction_from_new_view(
    data,
    ref_object_attrs,
    primary_direction_original_key, # e.g., 'front' if looking for new 'left'
    orthogonal_direction_original_key # e.g., 'left' if primary is new 'left'/'right'
    ):
    """
    General function to find objects in a specific relative direction
    from a reference object when viewing from the 'right', using 3D coordinates.

    Args:
        data (dict): The loaded scene data.
        ref_object_attrs (dict): Attributes to find the reference object.
        primary_direction_original_key (str): The key in `data['directions']`
            that corresponds to the *primary* direction vector in the *new* view.
        orthogonal_direction_original_key (str): The key in `data['directions']`
            that corresponds to an *orthogonal* direction vector in the *new* view,
            used for comparison.

    Returns:
        list: A list of descriptions of objects found in the specified direction.
    """
    if 'objects' not in data or 'directions' not in data:
        print("Error: 'objects' or 'directions' key not found in data.")
        return []

    objects = data['objects']
    directions = data['directions']

    # 1. Identify Reference Object
    ref_index = find_object_index_by_attrs(objects, ref_object_attrs)
    if ref_index == -1:
        print(f"Error: Reference object with attributes {ref_object_attrs} not found.")
        return []
    ref_obj = objects[ref_index]
    ref_coords = ref_obj.get('3d_coords')
    if ref_coords is None or len(ref_coords) != 3:
        print(f"Error: Missing or invalid 3D coordinates for reference object {ref_object_attrs}.")
        return []

    # 2. Define Primary and Orthogonal Direction Vectors (from Original JSON)
    primary_vec = directions.get(primary_direction_original_key)
    orthogonal_vec = directions.get(orthogonal_direction_original_key)

    if primary_vec is None or orthogonal_vec is None or len(primary_vec)!=3 or len(orthogonal_vec)!=3:
        print(f"Error: Invalid direction vectors for keys '{primary_direction_original_key}' or '{orthogonal_direction_original_key}'.")
        return []

    # --- Optional: Normalize direction vectors ---
    # primary_vec = normalize_vector(primary_vec)
    # orthogonal_vec = normalize_vector(orthogonal_vec)
    # if primary_vec is None or orthogonal_vec is None:
    #     print("Error normalizing direction vectors.")
    #     return []
    # ---------------------------------------------

    found_objects = []
    tolerance = 0.1 # Minimum projection value onto primary axis to be considered

    # 3. Iterate through Candidate Objects
    for i, cand_obj in enumerate(objects):
        if i == ref_index: continue
        if not isinstance(cand_obj, dict): continue

        cand_coords = cand_obj.get('3d_coords')
        if cand_coords is None or len(cand_coords) != 3: continue

        # 4. Calculate Relative Position Vector
        relative_vec = subtract_vectors(cand_coords, ref_coords)
        if relative_vec is None: continue

        # 5. Calculate Projections onto New Axes
        proj_primary = dot_product(relative_vec, primary_vec)
        proj_orthogonal = dot_product(relative_vec, orthogonal_vec)

        # Check if dot products are valid (vectors were valid)
        if proj_primary is None or proj_orthogonal is None:
             print(f"Warning: Could not calculate projection for object index {i}. Skipping.")
             continue


        # 6. Apply Condition: Primarily along primary axis
        if proj_primary > tolerance and proj_primary > abs(proj_orthogonal):
            found_objects.append(get_object_description(objects, i))

    return found_objects


# --- Specific Helper Functions for Each Direction ("View from Right") ---

def find_objects_left_from_new_view(data, ref_object_attrs):
    """Finds objects LEFT of ref_obj when viewing from RIGHT."""
    # New Left = Original Front | Orthogonal check: New Front = Original Left
    return find_objects_relative_direction_from_new_view(
        data, ref_object_attrs, 'front', 'left'
    )

def find_objects_right_from_new_view(data, ref_object_attrs):
    """Finds objects RIGHT of ref_obj when viewing from RIGHT."""
    # New Right = Original Behind | Orthogonal check: New Front = Original Left
    return find_objects_relative_direction_from_new_view(
        data, ref_object_attrs, 'behind', 'left'
    )

def find_objects_front_from_new_view(data, ref_object_attrs):
    """Finds objects FRONT of ref_obj when viewing from RIGHT."""
    # New Front = Original Left | Orthogonal check: New Left = Original Front
    return find_objects_relative_direction_from_new_view(
        data, ref_object_attrs, 'left', 'front'
    )

def find_objects_behind_from_new_view(data, ref_object_attrs):
    """Finds objects BEHIND ref_obj when viewing from RIGHT."""
    # New Behind = Original Right | Orthogonal check: New Left = Original Front
    return find_objects_relative_direction_from_new_view(
        data, ref_object_attrs, 'right', 'front'
    )


# --- Main Execution ---
if __name__ == "__main__":
    json_file_path ="/Users/ayush/Documents/GitHub/clevr-dataset-gen/Metadata/output_scenes/CLEVR_new_000000.json"
    try:
        with open(json_file_path, 'r') as f:
            scene_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at {json_file_path}")
        exit()
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_file_path}")
        exit()
    except Exception as e:
        print(f"An unexpected error occurred loading JSON: {e}")
        exit()

    # Define the reference object
    ref_attrs = {"color": "purple", "shape": "cube"}
    ref_desc_str = get_object_description(scene_data['objects'], find_object_index_by_attrs(scene_data['objects'], ref_attrs))

    print(f"\n--- Running Spatial Queries (View from Right) Relative to: {ref_desc_str} ---")

    # --- Test LEFT ---
    print("\nQuery: What is to the LEFT?")
    left_objects = find_objects_left_from_new_view(scene_data, ref_attrs)
    if left_objects:
        print("Objects found to the LEFT:")
        for desc in left_objects: print(f"- {desc}")
    else:
        print("No objects found primarily to the LEFT.")

    # --- Test RIGHT ---
    print("\nQuery: What is to the RIGHT?")
    right_objects = find_objects_right_from_new_view(scene_data, ref_attrs)
    if right_objects:
        print("Objects found to the RIGHT:")
        for desc in right_objects: print(f"- {desc}")
    else:
        print("No objects found primarily to the RIGHT.")

    # --- Test FRONT ---
    print("\nQuery: What is in FRONT?")
    front_objects = find_objects_front_from_new_view(scene_data, ref_attrs)
    if front_objects:
        print("Objects found in FRONT:")
        for desc in front_objects: print(f"- {desc}")
    else:
        print("No objects found primarily in FRONT.")

    # --- Test BEHIND ---
    print("\nQuery: What is BEHIND?")
    behind_objects = find_objects_behind_from_new_view(scene_data, ref_attrs)
    if behind_objects:
        print("Objects found BEHIND:")
        for desc in behind_objects: print(f"- {desc}")
    else:
        print("No objects found primarily BEHIND.")

# %%

# --- Main Execution ---
if __name__ == "__main__":
    json_file_path ="/Users/ayush/Documents/GitHub/clevr-dataset-gen/Metadata/output_scenes/CLEVR_new_000003.json"
    try:
        with open(json_file_path, 'r') as f:
            scene_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at {json_file_path}")
        exit()
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_file_path}")
        exit()
    except Exception as e:
        print(f"An unexpected error occurred loading JSON: {e}")
        exit()

    # Define the reference object
    ref_attrs = {"color": "yellow", "shape": "sphere"}
    ref_desc_str = get_object_description(scene_data['objects'], find_object_index_by_attrs(scene_data['objects'], ref_attrs))

    print(f"\n--- Running Spatial Queries (View from Right) Relative to: {ref_desc_str} ---")

    # --- Test LEFT ---
    print("\nQuery: What is to the LEFT?")
    left_objects = find_objects_left_from_new_view(scene_data, ref_attrs)
    if left_objects:
        print("Objects found to the LEFT:")
        for desc in left_objects: print(f"- {desc}")
    else:
        print("No objects found primarily to the LEFT.")

    # --- Test RIGHT ---
    print("\nQuery: What is to the RIGHT?")
    right_objects = find_objects_right_from_new_view(scene_data, ref_attrs)
    if right_objects:
        print("Objects found to the RIGHT:")
        for desc in right_objects: print(f"- {desc}")
    else:
        print("No objects found primarily to the RIGHT.")

    # --- Test FRONT ---
    print("\nQuery: What is in FRONT?")
    front_objects = find_objects_front_from_new_view(scene_data, ref_attrs)
    if front_objects:
        print("Objects found in FRONT:")
        for desc in front_objects: print(f"- {desc}")
    else:
        print("No objects found primarily in FRONT.")

    # --- Test BEHIND ---
    print("\nQuery: What is BEHIND?")
    behind_objects = find_objects_behind_from_new_view(scene_data, ref_attrs)
    if behind_objects:
        print("Objects found BEHIND:")
        for desc in behind_objects: print(f"- {desc}")
    else:
        print("No objects found primarily BEHIND.")

# %% [markdown]
# - Distribution of Answers are not skewed
# - Negative Samples: Model should output 0
# - 

# %%



