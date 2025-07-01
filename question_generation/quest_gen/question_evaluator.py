from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from .scene_operations import Scene, SceneOperations, Object3D

@dataclass
class QuestionTemplate:
    transformation_type: str
    question_category: str
    template_id: str
    original_template: str
    updated_template: str

class QuestionEvaluator:
    def __init__(self, scene: Scene):
        self.scene = scene
        self.operations = SceneOperations()

    def evaluate_question(self, question_template: QuestionTemplate, 
                         parameters: Dict[str, Any]) -> Any:
        """Evaluate a question based on its template and parameters."""
        
        # Apply transformation based on question type
        transformed_scene = self._apply_transformation(
            question_template.transformation_type, 
            parameters
        )
        
        # Evaluate the question based on its category
        return self._evaluate_by_category(
            question_template.question_category,
            transformed_scene,
            parameters
        )

    def _apply_transformation(self, transformation_type: str, 
                            parameters: Dict[str, Any]) -> Scene:
        """Apply the appropriate transformation to the scene."""
        
        if transformation_type == "Delete":
            return self.operations.remove_objects_by_attribute(
                self.scene,
                parameters['attribute'],
                parameters['value']
            )
            
        elif transformation_type == "Change Viewpoint":
            return self.operations.change_viewpoint(
                self.scene,
                parameters['view_direction']
            )
            
        elif transformation_type == "Change_Attribute":
            return self.operations.change_attribute(
                self.scene,
                parameters['target_attribute'],
                parameters['target_value'],
                parameters['new_attribute'],
                parameters['new_value']
            )
            
        # Add other transformations as needed
        return self.scene

    def _evaluate_by_category(self, category: str, scene: Scene, 
                            parameters: Dict[str, Any]) -> Any:
        """Evaluate the question based on its category."""
        
        if category == "counting":
            return self._evaluate_counting(scene, parameters)
            
        elif category == "existence":
            return self._evaluate_existence(scene, parameters)
            
        elif category == "spatial_relational":
            return self._evaluate_spatial_relational(scene, parameters)
            
        elif category == "attribute_identification":
            return self._evaluate_attribute_identification(scene, parameters)
            
        elif category == "conditional":
            return self._evaluate_conditional(scene, parameters)
            
        return None

    def _evaluate_counting(self, scene: Scene, parameters: Dict[str, Any]) -> int:
        """Evaluate counting questions."""
        attributes = {}
        if 'color' in parameters:
            attributes['color'] = parameters['color']
        if 'shape' in parameters:
            attributes['shape'] = parameters['shape']
            
        return self.operations.count_objects_by_attributes(scene, attributes)

    def _evaluate_existence(self, scene: Scene, parameters: Dict[str, Any]) -> bool:
        """Evaluate existence questions."""
        attributes = {}
        if 'attribute' in parameters and 'value' in parameters:
            attributes[parameters['attribute']] = parameters['value']
            
        return self.operations.count_objects_by_attributes(scene, attributes) > 0

    def _evaluate_spatial_relational(self, scene: Scene, 
                                   parameters: Dict[str, Any]) -> List[Object3D]:
        """Evaluate spatial relational questions."""
        # Find reference object
        ref_obj = self.operations.find_objects_by_attributes(
            scene,
            self._parse_object_description(parameters['reference_object'])
        )[0]
        
        # Find objects in specified direction
        return self.operations.find_objects_in_direction(
            scene,
            ref_obj,
            parameters['spatial_term']
        )

    def _evaluate_attribute_identification(self, scene: Scene, 
                                         parameters: Dict[str, Any]) -> Any:
        """Evaluate attribute identification questions."""
        # Find target object
        target_obj = self.operations.find_objects_by_attributes(
            scene,
            self._parse_object_description(parameters['unique_descriptor'])
        )[0]
        
        # Return requested attribute
        return getattr(target_obj, parameters['attribute'])

    def _evaluate_conditional(self, scene: Scene, 
                            parameters: Dict[str, Any]) -> Any:
        """Evaluate conditional questions."""
        # Apply first condition
        if 'delete_color' in parameters:
            scene = self.operations.remove_objects_by_attribute(
                scene,
                'color',
                parameters['delete_color']
            )
            
        # Check second condition
        if 'check_attribute' in parameters:
            return self.operations.count_objects_by_attributes(
                scene,
                {parameters['check_attribute']: parameters['check_value']}
            )
            
        return None

    def _parse_object_description(self, description: str) -> Dict[str, str]:
        """Parse an object description into attributes."""
        # Example: "the red cube" -> {'color': 'red', 'shape': 'cube'}
        parts = description.lower().replace('the ', '').split()
        attributes = {}
        
        # Map common color words
        colors = {'red', 'blue', 'green', 'yellow', 'purple', 'gray', 'cyan'}
        shapes = {'cube', 'sphere', 'cylinder'}
        sizes = {'small', 'large'}
        
        for part in parts:
            if part in colors:
                attributes['color'] = part
            elif part in shapes:
                attributes['shape'] = part
            elif part in sizes:
                attributes['size'] = part
                
        return attributes 