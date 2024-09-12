import os
import xml.etree.ElementTree as ET
from pdf2image import convert_from_path
import pytesseract #Requires Tesseract-OCR to be installed. Installed with Homebrew with `brew install tesseract`
from PIL import Image

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

def main():
    page_folder = "downloads/The Rugbeian and District Reporter (Rugby, Tenn.) 1882 to 1883 (25)/1882-10-07"
    
    for filename in os.listdir(page_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(page_folder, filename)
            alto_path = os.path.join(page_folder, filename.replace(".pdf", ".xml"))
            
            if os.path.exists(alto_path):
                print(f"Processing {filename}")
                process_pdf(pdf_path, alto_path)
            else:
                print(f"ALTO XML not found for {filename}")

if __name__ == "__main__":
    main()