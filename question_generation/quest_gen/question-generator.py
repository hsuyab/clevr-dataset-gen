import json
import itertools
import argparse


def load_data(templates_file, values_file):
    """Load templates and transformation values from the JSON files."""
    with open(templates_file, 'r') as f:
        templates_data = json.load(f)
    
    with open(values_file, 'r') as f:
        values_data = json.load(f)
    
    return templates_data["QUESTION_TEMPLATES"], values_data["TRANSFORM_PLACEHOLDER_VALUES"]


def all_placeholder_combinations(transformation_name, placeholder_values):
    """
    Returns a list of dictionaries, where each dict is one possible mapping
    of placeholders -> a chosen value from the placeholder values.
    """
    if transformation_name not in placeholder_values:
        # If no placeholders are defined for this transformation, return an empty list
        return [{}]

    placeholders_dict = placeholder_values[transformation_name]

    # Get a sorted list of placeholder names to ensure stable iteration
    placeholder_names = sorted(placeholders_dict.keys())
    # For each placeholder, get the list of possible values
    list_of_value_lists = [placeholders_dict[name] for name in placeholder_names]

    # Cartesian product of these value lists
    product_of_values = itertools.product(*list_of_value_lists)

    # Build a dictionary for each combination
    all_combos = []
    for combo in product_of_values:
        # combo is a tuple with len == len(placeholder_names)
        placeholders_map = {}
        for name, val in zip(placeholder_names, combo):
            placeholders_map[name] = val
        all_combos.append(placeholders_map)

    return all_combos


def generate_questions(question_templates, placeholder_values, max_questions=None, transformation_filter=None):
    """
    Generate questions from templates and placeholder values.
    
    Args:
        question_templates: Dictionary of templates from the JSON file
        placeholder_values: Dictionary of values from the JSON file
        max_questions: Optional limit on the number of questions to generate
        transformation_filter: Optional list of transformations to include
        
    Returns:
        List of question dictionaries
    """
    all_questions = []
    count = 0

    transformations = question_templates.keys()
    if transformation_filter:
        transformations = [t for t in transformations if t in transformation_filter]

    for transformation in transformations:
        transform_data = question_templates[transformation]
        question_types = transform_data["question_types"]

        # Get all possible placeholder combos for this transformation
        combos = all_placeholder_combinations(transformation, placeholder_values)

        for qtype, templates in question_types.items():
            # 'templates' is a list of template strings
            for template_str in templates:
                # For each combo, try to format the template
                for placeholders_map in combos:
                    try:
                        question_text