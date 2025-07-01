import json
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import copy

@dataclass
class Object3D:
    shape: str
    size: str
    material: str
    color: str
    coords: List[float]
    rotation: float
    pixel_coords: List[float]
    visible: bool

@dataclass
class Scene:
    objects: List[Object3D]
    directions: Dict[str, List[float]]
    relationships: Dict[str, List[List[int]]]
    split: str
    image_index: int
    image_filename: str

    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> 'Scene':
        objects = []
        for obj in json_data['objects']:
            objects.append(Object3D(
                shape=obj['shape'],
                size=obj['size'],
                material=obj['material'],
                color=obj['color'],
                coords=obj['3d_coords'],
                rotation=obj['rotation'],
                pixel_coords=obj['pixel_coords'],
                visible=obj['visible']
            ))
        
        return cls(
            objects=objects,
            directions=json_data['directions'],
            relationships=json_data['relationships'],
            split=json_data['split'],
            image_index=json_data['image_index'],
            image_filename=json_data['image_filename']
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            'objects': [
                {
                    'shape': obj.shape,
                    'size': obj.size,
                    'material': obj.material,
                    'color': obj.color,
                    '3d_coords': obj.coords,
                    'rotation': obj.rotation,
                    'pixel_coords': obj.pixel_coords,
                    'visible': obj.visible
                }
                for obj in self.objects
            ],
            'directions': self.directions,
            'relationships': self.relationships,
            'split': self.split,
            'image_index': self.image_index,
            'image_filename': self.image_filename
        }

class SceneOperations:
    @staticmethod
    def load_scene(file_path: str) -> Scene:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return Scene.from_json(data)

    @staticmethod
    def save_scene(scene: Scene, file_path: str):
        with open(file_path, 'w') as f:
            json.dump(scene.to_json(), f, indent=2)

    @staticmethod
    def remove_objects_by_attribute(scene: Scene, attribute: str, value: Any) -> Scene:
        """Remove objects that have the specified attribute value."""
        new_scene = copy.deepcopy(scene)
        new_scene.objects = [
            obj for obj in new_scene.objects 
            if getattr(obj, attribute) != value
        ]
        return new_scene

    @staticmethod
    def change_viewpoint(scene: Scene, new_viewpoint: str) -> Scene:
        """Change the viewpoint of the scene."""
        new_scene = copy.deepcopy(scene)
        
        # Define viewpoint transformations
        viewpoint_transforms = {
            'front': {'left': 'left', 'right': 'right', 'front': 'front', 'behind': 'behind'},
            'back': {'left': 'right', 'right': 'left', 'front': 'behind', 'behind': 'front'},
            'left_side': {'left': 'behind', 'right': 'front', 'front': 'left', 'behind': 'right'},
            'right_side': {'left': 'front', 'right': 'behind', 'front': 'right', 'behind': 'left'}
        }
        
        if new_viewpoint not in viewpoint_transforms:
            raise ValueError(f"Invalid viewpoint: {new_viewpoint}")
            
        transform = viewpoint_transforms[new_viewpoint]
        
        # Update relationships based on new viewpoint
        new_relationships = {}
        for old_dir, new_dir in transform.items():
            if old_dir in scene.relationships:
                new_relationships[new_dir] = scene.relationships[old_dir]
        
        new_scene.relationships = new_relationships
        return new_scene

    @staticmethod
    def change_attribute(scene: Scene, target_attribute: str, target_value: Any, 
                        new_attribute: str, new_value: Any) -> Scene:
        """Change attribute of objects matching target criteria."""
        new_scene = copy.deepcopy(scene)
        for obj in new_scene.objects:
            if getattr(obj, target_attribute) == target_value:
                setattr(obj, new_attribute, new_value)
        return new_scene

    @staticmethod
    def count_objects_by_attributes(scene: Scene, attributes: Dict[str, Any]) -> int:
        """Count objects matching all specified attributes."""
        count = 0
        for obj in scene.objects:
            if all(getattr(obj, attr) == value for attr, value in attributes.items()):
                count += 1
        return count

    @staticmethod
    def find_objects_by_attributes(scene: Scene, attributes: Dict[str, Any]) -> List[Object3D]:
        """Find objects matching all specified attributes."""
        return [
            obj for obj in scene.objects
            if all(getattr(obj, attr) == value for attr, value in attributes.items())
        ]

    @staticmethod
    def get_spatial_relationship(obj1: Object3D, obj2: Object3D, 
                               direction: str, scene: Scene) -> bool:
        """Determine if obj1 is in the specified direction relative to obj2."""
        if direction not in scene.relationships:
            return False
            
        # Get indices of objects
        obj1_idx = scene.objects.index(obj1)
        obj2_idx = scene.objects.index(obj2)
        
        # Check if obj1 is in the specified direction relative to obj2
        return obj1_idx in scene.relationships[direction][obj2_idx]

    @staticmethod
    def find_objects_in_direction(scene: Scene, reference_obj: Object3D, 
                                direction: str) -> List[Object3D]:
        """Find all objects in the specified direction relative to reference object."""
        ref_idx = scene.objects.index(reference_obj)
        if direction not in scene.relationships or ref_idx >= len(scene.relationships[direction]):
            return []
            
        return [scene.objects[idx] for idx in scene.relationships[direction][ref_idx]]

    @staticmethod
    def extract_scene_vocab(scene: 'Scene') -> Dict[str, set]:
        vocab = {
            'color': set(),
            'shape': set(),
            'size': set(),
            'material': set()
        }
        for obj in scene.objects:
            vocab['color'].add(obj.color)
            vocab['shape'].add(obj.shape)
            vocab['size'].add(obj.size)
            vocab['material'].add(obj.material)
        return vocab 