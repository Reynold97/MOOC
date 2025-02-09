# MOOC

This project aims to build an AI agent that generates a MOOC storyboard from the "Markdown Guide" manual (a PDF). 


## Reasoning:

The core of the challenge is the data processing pipeline. If we need to support any type of unstructured data including PDF, XML, Markdown, code, text documents, and spreadsheets we need a robust tool that can scale. I propose 2 main tools:

- Unstructured
- Azure Vision OCR to process images and Azure Document Intelligence for text.

Both are robust tools, and they are even used to process data to train LLMs. 
Both are scalable, offering APIs and serverless solutions.

I will go this time with Unstructured because it is a framework built specifically for our type of use case, all the tools for different data types are concentrated, the data is fully private and even if this raises concerns, Unstructured can be used on private Azure and AWS infrastructure through the marketplace. I also personally like to use open-source projects to explore innovation.

[https://unstructured.io/](https://unstructured.io/)

For the scope of this project I will use simple requests to the Unstructured Serverless API, is the simplest way to process a single file and later can be scalable with batch procesing. If needed, Unstructured also provide a python SDK. 

## Summary of Experiment: Data Preprocessing for MOOC Storyboard Generation
This section details the data preprocessing journey I took using the Unstructured Serverless API.  The ultimate goal is to get the raw PDF into a structured JSON format that an LLM can easily use to create slide content and instructor dialogue.

**Initial Goal:**

I wanted to take the PDF and transform it into manageable chunks of text that could be used as context for an LLM.  Ideally, these chunks would correspond roughly to the content that would go on a single slide.

**Step 1: No Chunking (Just Partitioning) - Baseline and Inspection**

My first step was to see what Unstructured's partitioning would do *without* any chunking. This gives me a baseline and lets me inspect how Unstructured identifies different elements (titles, paragraphs, tables, etc.).  Here's what I used:

*   `strategy="hi_res"`: I chose "hi_res" because it's the best for PDFs with images and tables, and I wanted the best possible element detection.
*   `output_format="application/json"`:  JSON is nice and structured for further processing.
*    `"extract_image_block_types": '["Image", "Table"]'` and `"pdf_infer_table_structure": "true"`, so that the API would provide base64 of images and html version of tables.

This produced `no_chunking.json`.  When I looked at it, I saw *lots* of individual elements. Each short line, each list item, each title was its own element.  This was way too fragmented!  An LLM would struggle to make a coherent slide from a single sentence.

I also created a version of this output without the Base64 of the images `no_chunking_no_base64.json`, to eliminate the noise of the Image encription that is not necessary for the context, since Unstructured has a text field for each image where it extract the content, for example, this occur with code and markdown snippets.

**Step 2:  Trying "by_title" Chunking with a Smaller Combine Threshold**

My next idea was to use Unstructured's built-in chunking.  I chose the `by_title` strategy because it tries to group content based on headings, which seemed like a good way to create slide-sized chunks. I used these settings:

*   `chunking_strategy="by_title"`:  Use title-based chunking.
*   `max_characters=100000`: A *huge* maximum chunk size. My thinking was that I wanted entire sections, and I didn't want to accidentally split in the middle of a paragraph. Also, I was expecting that giving huge maximums the partition would rely solely on the titles.
*   `new_after_n_chars=90000`:  A large "soft" maximum.  This encourages chunks to get close to the `max_characters` limit before starting a new one.
*   `combine_under_n_chars=500`:  This was my attempt to fix the fragmentation problem from Step 1.  It tells Unstructured to combine small, consecutive elements (like titles followed by short paragraphs) into a single chunk, *up to* 500 characters. I choose this because is a recommended value in Unstructured documentation, but was still too small.

This was *better*, but still not great.  It created fewer chunks than Step 1, but many chunks were still too small. The `combine_under_n_chars` helped, but it wasn't enough because Unstructured was still treating many short lines (like list items, or even single lines after a heading) as "Titles," causing premature chunk breaks. Outputs is `chunking_small.json`.

**Step 3: Chunking by Title (Aggressive Combining)**

I realized I needed to be *much* more aggressive with combining elements. I kept the `by_title` strategy, but I cranked up the combination parameters:

*   `max_characters=100000`:  Still a huge maximum.
*   `new_after_n_chars=90000`:  Still a huge soft maximum.
*   `combine_under_n_chars=10000`:  This is the key change.  I made this *very* large, essentially telling Unstructured to combine *everything* it could under a title, up to a massive 10,000-character limit.  I figured I'd rather have chunks that were too big and then manually split them later, than have tons of tiny chunks.

This produced `chunking_big.json`.  This file, as expected, had *far* fewer chunks.  Each chunk now corresponded much more closely to a logical section of the document.  However, it also included the `orig_elements` field in the metadata of each chunk, that is a base64 encription of the original prepartitioned content.

**Step 4: Cleaning the Chunked Output**

The `orig_elements` field, while useful for debugging, is bulky and unnecessary for my LLM. I wrote a simple function, to load the JSON from Step 3, remove the `orig_elements` field, and save the result to a new file, `output_cleaned.json`. This is now my preferred output. It also helps the manual revision of the file.

The generated files are `chunking_small_cleaned.json` and `chunking_big_cleaned.json`

**Final Recommendation and Reasoning**

I'm going with `chunking_big_clea.json` (chunked by title, large chunks, no `orig_elements`, and no `base64` images) as the input for my LLM. Here's why:

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

