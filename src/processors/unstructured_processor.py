import requests
import os
import json
import base64
from typing import List, Dict, Any
from unstructured_ingest.v2.interfaces import ProcessorConfig

class UnstructuredProcessor:
    """A class to handle PDF processing using the Unstructured API."""
    
    def __init__(self, api_key: str, api_url: str):
        """
        Initialize the UnstructuredProcessor.
        
        Args:
            api_key (str): The API key for Unstructured API
            api_url (str): The URL endpoint for Unstructured API
        """
        self.api_key = api_key
        self.api_url = api_url
        self.headers = {
            "unstructured-api-key": api_key,
        }

    def process_pdf_no_chunking(self, pdf_path: str, output_path: str) -> None:
        """
        Processes a PDF using Unstructured API, *without* chunking, and saves the JSON.
        
        Args:
            pdf_path (str): Path to the input PDF file
            output_path (str): Path where the output JSON will be saved
        """
        data = {
            "strategy": "hi_res",  # Use hi_res for tables and images
            "output_format": "application/json",
            "extract_image_block_types": '["Image", "Table"]', # Extract image and table
            "pdf_infer_table_structure": "true",  # For HTML table output
        }

        with open(pdf_path, "rb") as f:
            files = {"files": (os.path.basename(pdf_path), f, "application/pdf")}

            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    data=data,
                    files=files,
                )
                response.raise_for_status()
                json_data = response.json()

                with open(output_path, 'w', encoding='utf-8') as json_file:
                    json.dump(json_data, json_file, ensure_ascii=False, indent=4)

                print(f"No-chunking processing successful. Output saved to: {output_path}")

            except requests.exceptions.RequestException as e:
                print(f"Error processing PDF: {e}")

    def process_pdf_with_chunking(self, pdf_path: str, output_path: str) -> None:
        """
        Processes a PDF with title-based chunking (large chunks) and saves JSON.
        
        Args:
            pdf_path (str): Path to the input PDF file
            output_path (str): Path where the output JSON will be saved
        """
        data = {
            "strategy": "hi_res",
            "output_format": "application/json",
            "chunking_strategy": "by_title",
            "max_characters": 120000,  # Very large chunk size
            "new_after_n_chars": 100000,  # Slightly less, soft limit
            "combine_under_n_chars": 500, # Combine small titles/paragraphs
            "extract_image_block_types": '["Image", "Table"]',
            "pdf_infer_table_structure": "true",
        }

        with open(pdf_path, "rb") as f:
            files = {"files": (os.path.basename(pdf_path), f, "application/pdf")}

            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    data=data,
                    files=files,
                )
                response.raise_for_status()
                json_data = response.json()

                with open(output_path, 'w', encoding='utf-8') as json_file:
                    json.dump(json_data, json_file, ensure_ascii=False, indent=4)
                print(f"Chunking processing successful. Output saved to: {output_path}")

            except requests.exceptions.RequestException as e:
                print(f"Error processing PDF: {e}")

    def clean_orig_elements(self, input_path: str, output_path: str) -> None:
        """
        Loads a JSON file, removes the 'orig_elements' field from metadata,
        and saves the cleaned JSON to a new file.
        
        Args:
            input_path (str): Path to the input JSON file
            output_path (str): Path where the cleaned JSON will be saved
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as infile:
                data = json.load(infile)

            for element in data:
                if "metadata" in element and "orig_elements" in element["metadata"]:
                    del element["metadata"]["orig_elements"]

            with open(output_path, 'w', encoding='utf-8') as outfile:
                json.dump(data, outfile, ensure_ascii=False, indent=4)

            print(f"Cleaned JSON saved to: {output_path}")

        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error processing JSON: {e}")

    def remove_base64_images(self, input_path: str, output_path: str) -> None:
        """
        Loads JSON, removes 'image_base64' from 'metadata', saves cleaned JSON.
        
        Args:
            input_path (str): Path to the input JSON file
            output_path (str): Path where the cleaned JSON will be saved
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as infile:
                data = json.load(infile)

            for element in data:
                if "metadata" in element and "image_base64" in element["metadata"]:
                    del element["metadata"]["image_base64"]

            with open(output_path, 'w', encoding='utf-8') as outfile:
                json.dump(data, outfile, ensure_ascii=False, indent=4)
            print(f"JSON with base64 images removed saved to: {output_path}")

        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error processing JSON: {e}")


# Example Usage

def main():
    # Initialize processor
    api_key = os.getenv("UNSTRUCTURED_API_KEY")
    api_url = os.getenv("UNSTRUCTURED_API_URL")
    processor = UnstructuredProcessor(api_key, api_url)
    
    # File paths
    pdf_file_path = "data/input/markdown_manual.pdf"
    no_chunking_output = "data/processed_input/no_chunking.json"
    chunking_output = "data/processed_input/chunking_big.json"
    cleaned_output = "data/processed_input/chunking_big_cleaned.json"
    no_base64_output = "data/processed_input/no_chunking_no_base64.json"

    # Process without chunking
    processor.process_pdf_no_chunking(pdf_file_path, no_chunking_output)

    # Process with chunking
    processor.process_pdf_with_chunking(pdf_file_path, chunking_output)

    # Clean orig_elements
    processor.clean_orig_elements(chunking_output, cleaned_output)
    
    # Remove base64 images
    processor.remove_base64_images(no_chunking_output, no_base64_output)

if __name__ == "__main__":
    main()
