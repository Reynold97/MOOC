from typing import Dict, List, Any, Optional
import json
import os
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI
from pydantic import BaseModel, Field
import jsonlines
from ..prompts.gen_prompts import (
    STORYBOARD_SYSTEM_PROMPT,
    STORYBOARD_USER_PROMPT_TEMPLATE,
)
from ..prompts.val_prompts import (
    VALIDATION_SYSTEM_PROMPT,
    VALIDATION_USER_PROMPT_TEMPLATE
)

load_dotenv()

class SlideResult(BaseModel):
    """Model for the final slide result including validation."""
    content: str
    dialogue: str
    groundedness_score: float
    feedback: str

class PresentationGenerator:
    """
    Class to generate MOOC storyboards using OpenAI API.
    
    This class handles the entire pipeline of:
    1. Generating slides from source content
    2. Validating the generated content for groundedness
    3. Saving the results with validation scores
    """
    
    def __init__(self, output_dir: str = "outputs"):
        """
        Initialize the PresentationGenerator.
        
        Args:
            output_dir (str): Directory where output files will be saved
        """
        self.client = OpenAI()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_slide(self, text: str) -> Dict[str, str]:
        """
        Generate a single slide with content and dialogue using GPT-4.
        
        Args:
            text (str): Source text to create slide from
            
        Returns:
            Dict[str, str]: Dictionary containing slide content and dialogue
        """
        # Format the user prompt with the provided text
        user_prompt = STORYBOARD_USER_PROMPT_TEMPLATE.format(text=text)
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": STORYBOARD_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "slide_content",  # Added required name parameter
                    "schema": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "The content that will appear on the slide"
                            },
                            "dialogue": {
                                "type": "string",
                                "description": "The instructor's dialogue for this slide"
                            }
                        },
                        "required": ["content", "dialogue"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        )
        
        return json.loads(response.choices[0].message.content)

    def validate_slide(self, text: str, slide_content: str, slide_dialogue: str) -> Dict[str, Any]:
        """
        Validate the groundedness of generated content against source material.
        
        Args:
            text (str): Original source text
            slide_content (str): Generated slide content
            slide_dialogue (str): Generated instructor dialogue
            
        Returns:
            Dict[str, Any]: Validation results including score and feedback
        """
        # Format the user prompt with all required content
        user_prompt = VALIDATION_USER_PROMPT_TEMPLATE.format(
            text=text,
            slide_content=slide_content,
            slide_dialogue=slide_dialogue
        )
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": VALIDATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "slide_validation",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "score": {
                                "type": "number",
                                "description": "Groundedness score from 0 to 10"
                            },
                            "feedback": {
                                "type": "string",
                                "description": "Explanation of the score and any issues found"
                            }
                        },
                        "required": ["score", "feedback"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        )
        
        return json.loads(response.choices[0].message.content)

    def run(self, input_file: str) -> str:
        """
        Process a JSON input file and generate slides for each text element.
        
        The input JSON should contain a list of elements, each with:
        - element_id: Unique identifier
        - text: Source content to create slide from
        
        Args:
            input_file (str): Path to input JSON file
            
        Returns:
            str: Path to the output results file
            
        Raises:
            Exception: If there's an error processing the document
        """
        try:
            # Load input JSON
            with open(input_file, 'r', encoding='utf-8') as f:
                elements = json.load(f)

            # Process each element
            results = []
            for element in elements:
                # Generate slide
                print(f"Generating slide for element {element['element_id']}...")
                slide = self.generate_slide(element['text'])
                
                # Validate slide
                print(f"Validating slide for element {element['element_id']}...")
                validation = self.validate_slide(
                    element['text'],
                    slide['content'],
                    slide['dialogue']
                )
                
                # Store results using Pydantic model for validation
                result = SlideResult(
                    content=slide['content'],
                    dialogue=slide['dialogue'],
                    groundedness_score=validation['score'],
                    feedback=validation['feedback']
                )
                
                results.append({
                    "element_id": element['element_id'],
                    "result": result.model_dump()
                })

            # Save results to JSON file
            output_path = self.output_dir / f"{Path(input_file).stem}_results.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            return str(output_path)

        except Exception as e:
            print(f"Error processing document: {e}")
            raise

# Example usage:
'''
def main():
    generator = PresentationGenerator()
    
    input_file = "input/document.json"
    output_file = generator.process_document(input_file)
    print(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()
'''