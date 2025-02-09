import os
from dotenv import load_dotenv
from src.generators.presentation_generator import PresentationGenerator
from src.formatters.mooc_formatter import MOOCFormatter

load_dotenv()

def main():
    '''
    # Initialize generator
    generator = PresentationGenerator(output_dir="data/output")
    
    # Process input file
    input_file = "data/processed_input/chunking_big_cleaned.json"  # Replace with your input file path
    output_file = generator.run(input_file)
    print(f"Results saved to: {output_file}")
    '''
    
    # Initialize the formatter
    formatter = MOOCFormatter(output_dir="data/pdf_presentation")

    # Format the results
    pdf_path = formatter.format_results("data/output/chunking_big_cleaned_results.json")

if __name__ == "__main__":
    main()