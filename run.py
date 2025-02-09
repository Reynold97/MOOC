import os
from dotenv import load_dotenv
from src.processors.unstructured_processor import UnstructuredProcessor
from src.generators.presentation_generator import PresentationGenerator
from src.formatters.mooc_formatter import MOOCFormatter

load_dotenv()

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
    
    
    
    # Initialize generator
    generator = PresentationGenerator(output_dir="data/output")
    
    # Process input file
    input_file = "data/processed_input/chunking_big_cleaned.json"  # Replace with your input file path
    output_file = generator.run(input_file)
    print(f"Results saved to: {output_file}")
    
    
    
    # Initialize the formatter
    formatter = MOOCFormatter(output_dir="data/pdf_presentation")

    # Format the results
    pdf_path = formatter.format_results("data/output/chunking_big_cleaned_results.json")

if __name__ == "__main__":
    main()