import os
import xml.etree.ElementTree as ET
from pdf2image import convert_from_path
import pytesseract #Requires Tesseract-OCR to be installed. Installed with Homebrew with `brew install tesseract`
from PIL import Image
import sys

# Path to the directory containing the publication issues
pub_path = "downloads/The Rugbeian and District Reporter (Rugby, Tenn.) 1882 to 1883 (25)"

# Obtain OCR data for a pdf file
def process_pdf(pdf_path, alto_path):
    # Convert PDF to image (assuming only one image)
    image = convert_from_path(pdf_path)[0]
    
    # Parse ALTO XML
    tree = ET.parse(alto_path)
    root = tree.getroot()
    
    # Get measurement unit and image dimensions
    measurement_unit = root.find(".//{http://www.loc.gov/standards/alto/ns-v2#}MeasurementUnit").text
    width = int(root.find(".//{http://www.loc.gov/standards/alto/ns-v2#}Page").get('WIDTH'))
    height = int(root.find(".//{http://www.loc.gov/standards/alto/ns-v2#}Page").get('HEIGHT'))
    
    # Calculate scaling factor (assuming 300 DPI)
    scale_factor = image.width / width
    
    # Extract text content using ALTO XML structure
    refined_text = extract_text_from_alto(root, scale_factor)
    
    # Save refined text to file
    with open(pdf_path.replace(".pdf", "_ocr.txt"), "w", encoding="utf-8") as f:
        f.write(refined_text)

# Extract text content from ALTO XML structure
def extract_text_from_alto(root, scale_factor):
    namespace = {'alto': 'http://www.loc.gov/standards/alto/ns-v2#'}
    refined_text = ""
    
    for text_block in root.findall(".//alto:TextBlock", namespace):
        block_text = ""
        for text_line in text_block.findall(".//alto:TextLine", namespace):
            line_text = ""
            for string in text_line.findall(".//alto:String", namespace):
                content = string.get('CONTENT')
                style = string.get('STYLEREFS')
                # Apply style formatting if needed
                if style and 'I' in style:
                    content = f"*{content}*"  # Italics
                elif style and 'M' in style:
                    content = content.upper()  # Small caps
                line_text += content + " "
            block_text += line_text.strip() + "\n"
        refined_text += block_text + "\n"
    
    return refined_text

# Run transcription for all PDF files in a directory
def extract_all_text_from_alto(publication_path):

    if not os.path.isdir(publication_path):
        print(f"Error: {publication_path} is not a valid directory.")
        sys.exit(1)

    print(f"Processing {publication_path}")

    for issue_folder in os.listdir(publication_path):
        issue_path = os.path.join(publication_path, issue_folder)

        print(f"Processing {issue_folder}")

        if os.path.isdir(issue_path):
            for filename in os.listdir(issue_path):
                if filename.endswith(".pdf"):
                    pdf_path = os.path.join(issue_path, filename)
                    alto_path = os.path.join(issue_path, filename.replace(".pdf", ".xml"))

                    if os.path.exists(alto_path):
                        print(f"Processing {filename} in {issue_folder}")
                        process_pdf(pdf_path, alto_path)
                    else:
                        print(f"ALTO XML not found for {filename} in {issue_folder}")


extract_all_text_from_alto(pub_path)