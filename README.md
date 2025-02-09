# AI MOOC Storyboard Generator

An AI-powered system that automatically generates MOOC (Massive Open Online Course) storyboards from PDF documents. The system processes educational content and creates structured slides with instructor dialogue, making it easier to develop online course materials.

## Features
- PDF document processing using Unstructured API
- Automatic slide generation with GPT-4
- Content validation for accuracy and groundedness
- PDF output generation with formatted storyboards
- Support for both chunked and non-chunked processing
- Automatic cleaning of processed data

## Prerequisites
- Python 3.10 or higher
- OpenAI API access
- Unstructured API access

## Installation

1. Clone the repository:
```bash
git clone [https://github.com/Reynold97/MOOC.git]
cd MOOC
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Environment Setup

Create a `.env` file in the root directory with the following variables:
```
OPENAI_API_KEY=your_openai_api_key
UNSTRUCTURED_API_KEY=your_unstructured_api_key
UNSTRUCTURED_API_URL=your_unstructured_api_url
```

## Project Structure

```
.
├── data/                      # Data directory for input/output files
│   ├── input/                 # Input PDF files
│   ├── output/                # Generated JSON results
│   ├── pdf_presentation/      # Final PDF presentations
│   └── processed_input/       # Processed JSON files
├── docs/                      # Useful documentation of the principal resources used
    ├── openai_api/
    ├── unstructured_docs/
    ├── unstructured_notebooks/
├── example_data/              # Example files and outputs
├── resorces/                  # Images for README                     
├── src/                       # Source code
│   ├── formatters/            # PDF formatting modules
│   ├── generators/            # Presentation generation modules
│   ├── processors/            # PDF processing modules
│   ├── prompts/               # GPT prompts
│   └── utils/                 # Utility functions
├── tests/                     # Test files
├── .env                       # Environment variables
├── requirements.txt           # Python dependencies
└── run.py                     # Main execution script
```

## Components Description

### UnstructuredProcessor (processors/unstructured_processor.py)
Handles PDF processing using the Unstructured API with the following capabilities:
- `process_pdf_no_chunking`: Processes PDF without content chunking
- `process_pdf_with_chunking`: Processes PDF with title-based chunking
- `clean_orig_elements`: Removes original elements from metadata
- `remove_base64_images`: Removes base64 encoded images from JSON

### PresentationGenerator (generators/presentation_generator.py)
Generates MOOC storyboards using OpenAI's GPT-4:
- `generate_slide`: Creates individual slides with title, content, and dialogue
- `validate_slide`: Validates content groundedness
- `run`: Processes entire document and generates full storyboard

### MOOCFormatter (formatters/mooc_formatter.py)
Converts JSON storyboards to formatted PDFs:
- `format_results`: Processes JSON results into PDF format
- `create_pdf`: Generates formatted PDF with proper layout
- `sanitize_content`: Cleans and formats content for PDF

### Prompts (prompts/)
- `gen_prompts.py`: Contains system and user prompts for storyboard generation
- `val_prompts.py`: Contains prompts for content validation

## Usage

1. Place your input PDF file in the `data/input/` directory

2. Put the name of the file in the input path in [run.py](run.py)

```python
pdf_file_path = "data/input/markdown_manual.pdf"
```

3. Run the main script:
```bash
python run.py
```

4. The script will:
   - Process the PDF and create JSON files in `data/processed_input/`
   - Generate storyboards in `data/output/`
   - Create final PDF presentation in `data/pdf_presentation/`

## Processing Pipeline

1. PDF Processing:
   ```python
   processor = UnstructuredProcessor(api_key, api_url)
   processor.process_pdf_with_chunking(pdf_file_path, chunking_output)
   processor.clean_orig_elements(chunking_output, cleaned_output)
   ```

2. Storyboard Generation:
   ```python
   generator = PresentationGenerator(output_dir="data/output")
   output_file = generator.run(input_file)
   ```

3. PDF Formation:
   ```python
   formatter = MOOCFormatter(output_dir="data/pdf_presentation")
   pdf_path = formatter.format_results(json_file)
   ```

## Example Data

The `example_data/` directory contains sample files generated during the experimentation phase:
- `input/`: The required document, Markdown Manual. 
- `processed_input/`: Processed JSON files showing different processing stages, explanation below.
- `output/`: Generated storyboard JSON files, explanation below.
- `pdf_presentation/`: Final PDF presentation

## Notes

- Ensure all API keys are properly configured in the `.env` file
- Large PDFs may require additional processing time
- Check example outputs for expected format

## Result

<p align="center">
  <img src="resources\Captura de pantalla 2025-02-09 193342.png" alt="Result Presentation" width="800"/>
</p>

## Reasoning and Experimentation:

**This section is a blog where I write my reasoning and chain of thought while confronting different parts of the project. Is not intended to be very professional, but could be useful to the reader.**

The core of the challenge is the data processing pipeline. If we need to support any type of unstructured data including PDF, XML, Markdown, code, text documents, and spreadsheets we need a robust tool that can scale. I propose 2 main tools:

- Unstructured
- Azure Vision OCR to process images and Azure Document Intelligence for text.

Both are robust tools, and they are even used to process data to train LLMs. 
Both are scalable, offering APIs and serverless solutions.

I will go this time with Unstructured because it is a framework built specifically for our type of use case (data for LLMs), all the tools for different data types are concentrated, the data is fully private and even if this raises concerns, Unstructured can be used on private Azure and AWS infrastructure through the marketplace. I also personally like to use open-source projects to explore innovation.

[https://unstructured.io/](https://unstructured.io/)

For the scope of this project, I will use simple requests to the Unstructured Serverless API, which is the simplest way to process a single file and later can be scalable with batch processing. If needed, Unstructured also provides a python SDK. 

### Summary of Experiment: Data Preprocessing for MOOC Storyboard Generation
This section details the data preprocessing journey I took using the Unstructured Serverless API.  The ultimate goal is to get the raw PDF into a structured JSON format that an LLM can easily use to create slide content and instructor dialogue.

**Initial Goal:**

I wanted to take the PDF and transform it into manageable chunks of text that could be used as context for an LLM.  Ideally, these chunks would correspond roughly to the content that would go on a single slide.

**Step 1: No Chunking (Just Partitioning) - Baseline and Inspection**

My first step was to see what Unstructured's partitioning would do *without* any chunking. This gives me a baseline and lets me inspect how Unstructured identifies different elements (titles, paragraphs, tables, etc.).  Here's what I used:

*   `strategy="hi_res"`: I chose "hi_res" because it's the best for PDFs with images and tables, and I wanted the best possible element detection.
*   `output_format="application/json"`:  JSON is nice and structured for further processing.
*    `"extract_image_block_types": '["Image", "Table"]'` and `"pdf_infer_table_structure": "true"`, so that the API would provide base64 of images and html version of tables.

This produced `no_chunking.json`.  When I looked at it, I saw *lots* of individual elements. Each short line, each list item, each title was its own element.  This was way too fragmented!  An LLM would struggle to make a coherent slide from a single sentence.

I also created a version of this output without the Base64 of the images [example_data\processed_input\no_chunking_no_base64.json](example_data\processed_input\no_chunking_no_base64.json), to eliminate the noise of the Image encription that is not necessary for the context, since Unstructured has a text field for each image where it extract the content, for example, this occur with code and markdown snippets.

**Step 2:  Trying "by_title" Chunking with a Smaller Combine Threshold**

My next idea was to use Unstructured's built-in chunking.  I chose the `by_title` strategy because it tries to group content based on headings, which seemed like a good way to create slide-sized chunks. I used these settings:

*   `chunking_strategy="by_title"`:  Use title-based chunking.
*   `max_characters=100000`: A *huge* maximum chunk size. My thinking was that I wanted entire sections, and I didn't want to accidentally split in the middle of a paragraph. Also, I was expecting that giving huge maximums the partition would rely solely on the titles.
*   `new_after_n_chars=90000`:  A large "soft" maximum.  This encourages chunks to get close to the `max_characters` limit before starting a new one.
*   `combine_under_n_chars=500`:  This was my attempt to fix the fragmentation problem from Step 1.  It tells Unstructured to combine small, consecutive elements (like titles followed by short paragraphs) into a single chunk, *up to* 500 characters. I choose this because is a recommended value in Unstructured documentation, but was still too small.

This was *better*, but still not great.  It created fewer chunks than Step 1, but many chunks were still too small. The `combine_under_n_chars` helped, but it wasn't enough because Unstructured was still treating many short lines (like list items, or even single lines after a heading) as "Titles," causing premature chunk breaks. Outputs is [example_data\processed_input\chunking_small.json](example_data\processed_input\chunking_small.json).

**Step 3: Chunking by Title (Aggressive Combining)**

I realized I needed to be *much* more aggressive with combining elements. I kept the `by_title` strategy, but I cranked up the combination parameters:

*   `max_characters=100000`:  Still a huge maximum.
*   `new_after_n_chars=90000`:  Still a huge soft maximum.
*   `combine_under_n_chars=10000`:  This is the key change.  I made this *very* large, essentially telling Unstructured to combine *everything* it could under a title, up to a massive 10,000-character limit.  I figured I'd rather have chunks that were too big and then manually split them later, than have tons of tiny chunks.

This produced [example_data\processed_input\chunking_big.json](example_data\processed_input\chunking_big.json).  This file, as expected, had *far* fewer chunks.  Each chunk now corresponded much more closely to a logical section of the document.  However, it also included the `orig_elements` field in the metadata of each chunk, that is a base64 encription of the original prepartitioned content.

**Step 4: Cleaning the Chunked Output**

The `orig_elements` field, while useful for debugging, is bulky and unnecessary for my LLM. I wrote a simple function, to load the JSON from Step 3, remove the `orig_elements` field, and save the result to a new file, `output_cleaned.json`. This is now my preferred output. It also helps the manual revision of the file.

The generated files are [example_data\processed_input\chunking_small_cleaned.json](example_data\processed_input\chunking_small_cleaned.json) and [example_data\processed_input\chunking_big_cleaned.json](example_data\processed_input\chunking_big_cleaned.json)

**Final Recommendation**

I'm going with [example_data\processed_input\chunking_big_cleaned.json](example_data\processed_input\chunking_big_cleaned.json) (chunked by title, large chunks, no `orig_elements`, and no `base64` images) as the input for my LLM. Here's why:

*   **Chunking is Essential:** The un-chunked data is too fragmented. The LLM needs larger, coherent units of text to work with.
*   **"by_title" is a Good Heuristic:**  While not perfect, chunking by title provides a reasonable starting point for grouping related content.  It roughly aligns with how a MOOC might be structured into sections.
*   **Aggressive Combining is Necessary:**  Because Unstructured's title detection isn't perfect (and because the document has many short headings), I need to aggressively combine elements to avoid tiny chunks.
*   **`orig_elements` is Unnecessary:**  I don't need the fine-grained original element boundaries for this task.  Removing it makes the JSON smaller and easier to work with.
*    **Images as base64 is Unnecessary:** I removed the base64 representation of images and if I wanted to use it in the future I could recover it with `output_no_chunking.json`

**Future Improvements**

This is a good starting point, but here are some ways I could improve it:

1.  **Better Title Detection:** I could add a post-processing step *before* chunking to refine the title detection.  I might use regular expressions or some custom logic to identify *true* section headings and adjust the `type` of those elements in the JSON.
2.  **More Sophisticated Chunking:** I could explore more advanced chunking techniques, perhaps incorporating semantic similarity.
3.  **Table Handling:** I might want to treat tables differently.  Perhaps convert them to a more concise textual representation for the LLM.
4.  **Image Handling:** I am doing this excercice asuming that I don't want to use images of the PDF for the slide, I took this decision for simplicity. If I want to incorporate images, I can keep the `image_base64` from the outputs, creating a separate file with `element_id` as a key.

This approach leverages Unstructured's strengths (partitioning, chunking, ocr) and provides a clear path for further refinement. It gives me a structured, reasonably chunked JSON representation of the document that I can then feed to an LLM for storyboard generation.

### Slides Generation.

To generate slides and dialogue content I will use OpenAI GPT-4o, mainly because I already have an API key. 

I want to ensure that I can generate the format requested in the challenge, including slide title and content and interlocutor content. For that, I will use OpenAI structured output and the following schema:

```python
class SlideResult(BaseModel):
    """Model for the final slide result including validation."""
    title: str
    content: str
    dialogue: str
```

Generation prompt: [src\prompts\gen_prompts.py](src\prompts\gen_prompts.py)

At this point, I consider the solution satisfactory but working with LLMs we need always some type of validation, that is why I propose a validation step to evaluate groundedness, or how correlated is the output to the input context. For that, I will use the same model. I want to have a score between 0 to 10 in which 10 is perfect correlation and no hallucinations, and feedback to improve the generation step to do that I will also use OpenAI structured output and I will add the fields to the schema:

```python
class SlideResult(BaseModel):
    """Model for the final slide result including validation."""
    title: str
    content: str
    dialogue: str
    groundedness_score: float
    feedback: str
```
Validation prompt: [src\prompts\val_prompts.py](src\prompts\val_prompts.py)

The idea for the feedback is to be able to improve the generation prompt in a loop. This concept can be applied to many posterior requisites and is in line with Graph-Based Agent Frameworks like LangGraph, which I pretend to use to manage these complex flows and loops in the future for this project. Although we have the feedback and score fields I considered not to use them for now, because it will be a lot of work to keep building these loops and I prefer to discuss that architecture later with the project responsible.  

Another idea for improvement I decided not to use, is batch processing for the generation, to process in parallel all the json elements. Again I decided against it for now because the future architecture will impact it, maybe we decide that processing each element independently is fine, but maybe we need to retain information on the first processed element for the current one, and that type of decision will impact on how to process the batches. 