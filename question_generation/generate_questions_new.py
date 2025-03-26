import itertools

# -------------------------------------------------------------------
# 1) QUESTION_TEMPLATES:
#    A dictionary mapping each transformation to its relevant question types and templates.
# -------------------------------------------------------------------
QUESTION_TEMPLATES = {
    "Rotate": {
        "question_types": {
            "spatial_relational": [
                "Rotate the scene by {angle} degrees {direction}. Which object is to the {spatial_term} of {reference_object}?",
                "Rotate the scene by {angle} degrees {direction}. Which object is between {object1} and {object2} after rotation?",
                "Rotate the scene by {angle} degrees {direction}. Which object is nearest to {reference_object} after rotation?"
            ],
            "ordering": [
                "Rotate the scene by {angle} degrees {direction}. From left to right, which one is the {extreme_side} by their {attribute}?"
            ]
        }
    },

    "Change Viewpoint": {
        "question_types": {
            "spatial_relational": [
                "Change the viewpoint to {view_direction}. Which object is to the {spatial_term} of {reference_object}?",
                "Change the viewpoint to {view_direction}. Which object is between {object1} and {object2}?",
                "Change the viewpoint to {view_direction}. Which object is nearest to {reference_object}?"
            ],
            "ordering": [
                "Change the viewpoint to {view_direction}. From left to right, which one is the {extreme_side} by their {attribute}?"
            ]
        }
    },

    "Swap_Attributes": {
        "question_types": {
            "counting": [
                "Swap the {attribute} of the most frequent objects with the least frequent objects. How many objects have {color} and {shape}?",
                "Swap the {attribute} of the most frequent objects with the least frequent objects. How many objects are {relation} {reference_object}?"
            ],
            "existence": [
                "Swap the {attribute} of the most frequent objects with the least frequent objects. Is there any object with {attribute} = {value}?"
            ],
            "attribute_identification": [
                "Swap the {attribute} of the most frequent objects with the least frequent objects. Which {attribute} does the object {relation} {reference_object} have now?",
                "Swap the {attribute} of the most frequent objects with the least frequent objects. What is the {attribute} of {unique_descriptor}?"
            ],
            "conditional": [
                "Swap the {attribute} of the most frequent objects with the least frequent objects. If we delete all {color} objects now, will there be any {shape} left?"
            ]
        }
    },

    "Swap_Positions": {
        "question_types": {
            "spatial_relational": [
                "Swap positions of all {color} objects with all {shape} objects. Which object is to the {spatial_term} of {reference_object} now?",
                "Swap positions of all {color} objects with all {shape} objects. Which object is nearest to {reference_object} now?"
            ],
            "ordering": [
                "Swap positions of all {color} objects with all {shape} objects. From left to right, which is the {extreme_side} by their {attribute}?"
            ],
            "counting": [
                "Swap positions of all {color} objects with all {shape} objects. How many objects are {relation} {reference_object} now?"
            ]
        }
    },

    "Delete": {
        "question_types": {
            "counting": [
                "Remove any object that has {attribute} = {value}. How many objects remain that have {color} and {shape}?",
                "Delete all objects that are {relation} {reference_object}. How many objects have {color} and {shape}?"
            ],
            "existence": [
                "Remove any object that has {attribute} = {value}. Are there any {shape} objects left?",
                "Delete all objects that are {relation} {reference_object}. Is there any object with {attribute} = {value}?"
            ],
            "attribute_identification": [
                "Delete all {color} objects. Which {color/shape/size} does the object {relation} {reference_object} have (if it still exists)?"
            ],
            "spatial_relational": [
                "Delete all objects that have {attribute} = {value}. Which object is to the {spatial_term} of {reference_object} now?",
                "Delete all objects that are {relation} {reference_object}. Which object is between {object1} and {object2} now?"
            ],
            "ordering": [
                "Delete all objects with {attribute} = {value}. From left to right, which one is the {extreme_side} by {attribute}?"
            ],
            "conditional": [
                "If we delete all {color} objects, how many {attribute} objects remain?",
                "If we delete all objects that are {relation} {reference_object}, do we still have any {color} objects left?"
            ]
        }
    },

    "Change_Attribute": {
        "question_types": {
            "counting": [
                "Change all {color} objects to {new_color}. How many {color} objects remain?",
                "Change the {shape} of any {size} object to {new_shape}. How many objects have {color} and {shape}?"
            ],
            "existence": [
                "Change all {color} objects to {new_color}. Are there any objects left with {attribute} = {value}?"
            ],
            "attribute_identification": [
                "Change all {color} objects to {new_color}. What is the {attribute} of {unique_descriptor} now?"
            ]
        }
    },

    "Move": {
        "question_types": {
            "spatial_relational": [
                "Move the {shape} object(s) {distance} units to the {direction}. Which object is to the {spatial_term} of {reference_object} now?",
                "Shift all {color} objects by {x_shift} along x and {y_shift} along y. Which object is nearest to {reference_object} now?"
            ],
            "ordering": [
                "Move the {shape} object(s) {distance} units {direction}. From left to right, which one is the {extreme_side} by {attribute}?"
            ],
            "counting": [
                "Shift all {color} objects by {x_shift} along x and {y_shift} along y. How many objects are now {relation} {reference_object}?"
            ]
        }
    },

    "Mirror_Reflect": {
        "question_types": {
            "spatial_relational": [
                "Reflect the scene across the {mirror_axis} axis. Which object is to the {spatial_term} of {reference_object} now?",
                "Mirror the positions of all objects about the center. Which object is between {object1} and {object2}?"
            ],
            "ordering": [
                "Reflect the scene across the {mirror_axis} axis. From left to right, which one is the {extreme_side} by {attribute}?"
            ]
        }
    },

    "Scale": {
        "question_types": {
            "counting": [
                "Scale the scene by a factor of {scale_factor}. How many large objects do we have now?",
                "Enlarge any {color} objects to {size_large}. How many objects have {color} and {shape} left?"
            ],
            "existence": [
                "Enlarge any {color} objects to {size_large}. Are there any small {color} objects left?"
            ],
            "attribute_identification": [
                "Scale the scene by {scale_factor}. What is the size of {unique_descriptor} now?"
            ]
        }
    }
}


# -------------------------------------------------------------------
# 2) For each transformation, define the *complete sets of possible values*
#    for each placeholder that might appear in the templates.
# -------------------------------------------------------------------
TRANSFORM_PLACEHOLDER_VALUES = {

    "Rotate": {
        "angle":       [90, 180, 270],
        "direction":   ["clockwise", "counterclockwise"],
        "spatial_term":["left", "right", "above", "below"],
        "reference_object": ["the red cube", "the blue sphere", "the green cylinder"],
        "object1":     ["the green cube", "the blue sphere"],
        "object2":     ["the yellow cylinder", "the red sphere"],
        "extreme_side":["leftmost", "rightmost"],
        "attribute":   ["color", "size", "shape"]
    },

    "Change Viewpoint": {
        "view_direction": ["front", "back", "left_side", "right_side"],
        "spatial_term":   ["left", "right", "above", "below"],
        "reference_object": ["the red cube", "the blue sphere"],
        "object1":         ["the green cube", "the blue sphere"],
        "object2":         ["the yellow cylinder", "the red sphere"],
        "extreme_side":    ["leftmost", "rightmost"],
        "attribute":       ["color", "size", "shape"]
    },

    "Swap_Attributes": {
        "attribute":       ["color", "size", "shape"],
        "color":           ["red", "blue", "green", "yellow"],
        "shape":           ["cube", "sphere", "cylinder"],
        "relation":        ["to the left of", "behind", "in front of"],
        "reference_object":["the red cube", "the blue sphere", "the green cylinder"],
        "value":           ["red", "blue", "green", "small", "large", "cube"],
        "unique_descriptor":["the large red sphere", "the small blue cube"]
    },

    "Swap_Positions": {
        "color":           ["red", "blue", "green", "yellow"],
        "shape":           ["cube", "sphere", "cylinder"],
        "spatial_term":    ["left", "right", "above", "below"],
        "reference_object":["the red cube", "the blue sphere", "the green cylinder"],
        "attribute":       ["color", "size", "shape"],
        "extreme_side":    ["leftmost", "rightmost"],
        "relation":        ["to the left of", "behind", "in front of"]
    },

    "Delete": {
        "attribute":       ["color", "size", "shape"],
        "value":           ["red", "blue", "green", "small", "large", "cube"],
        "color":           ["red", "blue", "green", "yellow"],
        "shape":           ["cube", "sphere", "cylinder"],
        "reference_object":["the red cube", "the blue sphere", "the green cylinder"],
        "relation":        ["to the left of", "behind", "in front of"],
        "spatial_term":    ["left", "right", "above", "below"],
        "object1":         ["the green cube", "the blue sphere"],
        "object2":         ["the yellow cylinder", "the red sphere"],
        "extreme_side":    ["leftmost", "rightmost"]
    },

    "Change_Attribute": {
        "color":           ["red", "blue", "green", "yellow"],
        "new_color":       ["red", "blue", "green", "yellow", "purple"],
        "shape":           ["cube", "sphere", "cylinder"],
        "new_shape":       ["cube", "sphere", "cylinder", "pyramid"],
        "size":            ["small", "medium", "large"],
        "attribute":       ["color", "size", "shape"],
        "value":           ["red", "blue", "green", "small", "large", "cube"],
        "unique_descriptor": ["the small blue cube", "the large red sphere"]
    },

    "Move": {
        "shape":           ["cube", "sphere", "cylinder"],
        "distance":        [1, 2, 3],
        "direction":       ["up", "down", "left", "right"],
        "x_shift":         [1, -1, 2, -2],
        "y_shift":         [1, -1, 2, -2],
        "color":           ["red", "blue", "green"],
        "reference_object":["the red cube", "the blue sphere"],
        "relation":        ["to the left of", "behind", "in front of"],
        "spatial_term":    ["left", "right", "above", "below"],
        "attribute":       ["color", "size", "shape"],
        "extreme_side":    ["leftmost", "rightmost"]
    },

    "Mirror_Reflect": {
        "mirror_axis":     ["x", "y"],
        "reference_object":["the red cube", "the blue sphere"],
        "spatial_term":    ["left", "right", "above", "below"],
        "object1":         ["the green cube", "the blue sphere"],
        "object2":         ["the yellow cylinder", "the red sphere"],
        "attribute":       ["color", "size", "shape"],
        "extreme_side":    ["leftmost", "rightmost"]
    },

    "Scale": {
        "scale_factor":    [0.5, 2, 3],
        "color":           ["red", "blue", "green"],
        "size_large":      ["large", "very large"],
        "shape":           ["cube", "sphere", "cylinder"],
        "attribute":       ["color", "size", "shape"],
        "unique_descriptor": ["the small green cube", "the medium blue sphere"]
    }
}


# -------------------------------------------------------------------
# 3) A helper function to get all possible combinations (cartesian product)
#    of placeholder values for a given transformation.
# -------------------------------------------------------------------
def all_placeholder_combinations(transformation_name):
    """
    Returns a list of dictionaries, where each dict is one possible mapping
    of placeholders -> a chosen value from TRANSFORM_PLACEHOLDER_VALUES[transformation_name].
    """
    if transformation_name not in TRANSFORM_PLACEHOLDER_VALUES:
        # If no placeholders are defined for this transformation, return an empty list
        return [{}]

    placeholders_dict = TRANSFORM_PLACEHOLDER_VALUES[transformation_name]

    # placeholders_dict might look like:
    # {
    #   "angle": [90,180,270],
    #   "direction": ["clockwise","counterclockwise"],
    #   ...
    # }
    # We want the cartesian product of all these lists.

    # We'll get a sorted list of placeholder names to ensure stable iteration:
    placeholder_names = sorted(placeholders_dict.keys())
    # For each placeholder, get the list of possible values:
    list_of_value_lists = [placeholders_dict[name] for name in placeholder_names]

    # cartesian product of these value lists:
    product_of_values = itertools.product(*list_of_value_lists)

    # Now build a dictionary for each combination
    all_combos = []
    for combo in product_of_values:
        # combo is a tuple with len == len(placeholder_names)
        # e.g., (90, "clockwise", "left", "the red cube", ...)
        placeholders_map = {}
        for name, val in zip(placeholder_names, combo):
            placeholders_map[name] = val
        all_combos.append(placeholders_map)

    return all_combos


# -------------------------------------------------------------------
# 4) Generate *all* possible questions (no randomness).
#    For each transform, each question type, each template, and each
#    placeholder combination => format and produce the question.
# -------------------------------------------------------------------
def generate_all_possible_questions():
    """
    Returns a list of all possible (transformation, question_type, template, placeholders, question_text).
    You could also just return question_text or store them differently as needed.
    """
    all_questions = []

    for transformation, transform_data in QUESTION_TEMPLATES.items():
        # transform_data has {"question_types": { ... }}
        question_types = transform_data["question_types"]

        # 1) Get all possible placeholder combos for this transformation
        combos = all_placeholder_combinations(transformation)

        for qtype, templates in question_types.items():
            # 'templates' is a list of template strings
            for template_str in templates:

                # 2) For each combo, try to format the template
                for placeholders_map in combos:
                    try:
                        question_text = template_str.format(**placeholders_map)
                    except KeyError:
                        # If the template references a placeholder not in placeholders_map,
                        # you could skip it or handle it differently.
                        # We'll skip that combination:
                        continue

                    # Save a record of the question
                    record = {
                        "transformation": transformation,
                        "question_type": qtype,
                        "template": template_str,
                        "placeholders": placeholders_map,
                        "question": question_text
                    }
                    all_questions.append(record)

    return all_questions

def main():
    # Generate the entire set of questions
    questions_dataset = generate_all_possible_questions()

    # Print out how many we got
    print(f"Generated {len(questions_dataset)} total questions.\n")

    # Print a small sample (e.g. first 20) to avoid overwhelming the console:
    for i, qinfo in enumerate(questions_dataset[:20], start=1):
        print(f"{i}. [{qinfo['transformation']}, {qinfo['question_type']}] => {qinfo['question']}")


if __name__ == "__main__":
    main()
