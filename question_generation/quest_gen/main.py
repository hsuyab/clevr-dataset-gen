import json
from typing import List, Dict, Any
from question_generation.quest_gen.scene_operations import Scene, SceneOperations
from question_generation.quest_gen.question_parser import QuestionParser
from question_generation.quest_gen.question_evaluator import QuestionEvaluator

def load_scene(file_path: str) -> Scene:
    """Load a scene from a JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return Scene.from_json(data)

def evaluate_question(scene: Scene, question: str, 
                     template_file: str, scene_vocab: Dict[str, set]) -> Dict[str, Any]:
    """Evaluate a question on a scene."""
    # Initialize parser and evaluator
    parser = QuestionParser(template_file, scene_vocab)
    evaluator = QuestionEvaluator(scene)
    
    # Parse the question
    parsed = parser.parse_question(question)
    if not parsed:
        return {
            'success': False,
            'error': 'Could not parse question'
        }
        
    # Evaluate the question
    try:
        result = evaluator.evaluate_question(
            parsed['template'],
            parsed['parameters']
        )
        return {
            'success': True,
            'result': result,
            'template': parsed['template'],
            'parameters': parsed['parameters']
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    # Example usage
    scene_file = "Metadata/output_scenes/CLEVR_new_000000.json"
    template_file = "question_generation/quest_gen/questions.csv"
    
    # Load scene
    scene = load_scene(scene_file)
    # Extract vocab from scene
    scene_vocab = SceneOperations.extract_scene_vocab(scene)
    
    # Example questions
    questions = [
        # Question 1: Remove objects with attribute
        "Remove any object that has color = red. How many objects remain that have blue and cylinder?",
        
        # Question 2: Change viewpoint
        "Change the viewpoint to right_side. Which object is to the left of the red cube?",
        
        # Question 3: Change attributes
        "Change all red objects to blue. How many red objects remain?"
    ]
    
    # Evaluate each question
    for question in questions:
        print(f"\nQuestion: {question}")
        result = evaluate_question(scene, question, template_file, scene_vocab)
        
        if result['success']:
            print(f"Result: {result['result']}")
            print(f"Template: {result['template'].template_id}")
            print(f"Parameters: {result['parameters']}")
        else:
            print(f"Error: {result['error']}")

if __name__ == "__main__":
    main() 