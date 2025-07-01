import csv
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re

@dataclass
class QuestionTemplate:
    transformation_type: str
    question_category: str
    template_id: str
    original_template: str
    updated_template: str

class QuestionParser:
    # Directions, shapes, and viewpoints can be manually input
    MANUAL_DIRECTIONS = ['left', 'right', 'above', 'below']
    MANUAL_SHAPES = ['cube', 'sphere', 'cylinder']
    MANUAL_VIEWPOINTS = ['front', 'back', 'left_side', 'right_side']

    def __init__(self, template_file: str, scene_vocab: Dict[str, set]):
        self.templates = self._load_templates(template_file)
        self.scene_vocab = scene_vocab
        
    def _load_templates(self, template_file: str) -> List[QuestionTemplate]:
        """Load question templates from CSV file."""
        templates = []
        with open(template_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                templates.append(QuestionTemplate(
                    transformation_type=row['Transformation_Type'],
                    question_category=row['Question_Category'],
                    template_id=row['Template_ID'],
                    original_template=row['Original_Question_Template'],
                    updated_template=row['Updated_Question_Template']
                ))
        return templates

    def parse_question(self, question: str) -> Optional[Dict[str, Any]]:
        """Parse a question string into its template and parameters."""
        template = self._find_matching_template(question)
        if not template:
            return None
        parameters = self._extract_parameters(question, template)
        if not parameters:
            return None
        return {
            'template': template,
            'parameters': parameters
        }

    def _find_matching_template(self, question: str) -> Optional[QuestionTemplate]:
        for template in self.templates:
            pattern = self._template_to_regex(template.updated_template)
            if re.match(pattern, question, re.IGNORECASE):
                return template
        return None

    def _template_to_regex(self, template: str) -> str:
        pattern = template
        # Replace placeholders with scene-based vocab
        pattern = pattern.replace('{color/size/shape}', self._regex_union(self.scene_vocab['color'], self.scene_vocab['size'], self.MANUAL_SHAPES))
        pattern = pattern.replace('{red/blue/green/small/large/cube}', self._regex_union(self.scene_vocab['color'], self.scene_vocab['size'], self.MANUAL_SHAPES))
        pattern = pattern.replace('{red/blue/green/yellow}', self._regex_union(self.scene_vocab['color']))
        pattern = pattern.replace('{cube/sphere/cylinder}', self._regex_union(self.MANUAL_SHAPES))
        pattern = pattern.replace('{front/back/left_side/right_side}', self._regex_union(self.MANUAL_VIEWPOINTS))
        pattern = pattern.replace('{left/right/above/below}', self._regex_union(self.MANUAL_DIRECTIONS))
        pattern = pattern.replace('{the red cube/the blue sphere}', r'(the [a-z]+ (cube|sphere|cylinder))')
        pattern = pattern.replace('{red/blue/green/yellow/purple}', self._regex_union(self.scene_vocab['color'], {'purple'}))
        # Escape remaining special characters
        pattern = re.escape(pattern)
        # Replace escaped placeholders with capture groups
        pattern = pattern.replace(r'\{.*?\}', r'([^\.\?]+)')
        return f"^{pattern}$"

    def _regex_union(self, *args) -> str:
        # Accepts multiple sets/lists and unions them for regex
        values = set()
        for arg in args:
            values.update(arg)
        # Remove empty strings
        values = {v for v in values if v}
        return '(' + '|'.join(re.escape(str(v)) for v in values) + ')'

    def _extract_parameters(self, question: str, template: QuestionTemplate) -> Optional[Dict[str, Any]]:
        pattern = self._template_to_regex(template.updated_template)
        match = re.match(pattern, question, re.IGNORECASE)
        if not match:
            return None
        placeholders = re.findall(r'\{([^}]+)\}', template.updated_template)
        parameters = {}
        for placeholder, value in zip(placeholders, match.groups()):
            if '/' in placeholder:
                options = placeholder.split('/')
                if value in options:
                    parameters[options[0]] = value
                else:
                    parameters[placeholder] = value
            else:
                parameters[placeholder] = value
        return parameters

    def get_template_by_id(self, template_id: str) -> Optional[QuestionTemplate]:
        for template in self.templates:
            if template.template_id == template_id:
                return template
        return None

    def get_templates_by_type(self, transformation_type: str) -> List[QuestionTemplate]:
        return [template for template in self.templates if template.transformation_type == transformation_type]

    def get_templates_by_category(self, category: str) -> List[QuestionTemplate]:
        return [template for template in self.templates if template.question_category == category] 