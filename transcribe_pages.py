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
    #print(tree)

    # Get root element
    root = tree.getroot()
    #print(root)
    
    #All text blocks from alto file
    alto_blocks = root.findall(".//{http://www.loc.gov/standards/alto/ns-v2#}TextBlock")

    # Initialize list to store text blocks
    text_blocks = []
    
    # Extract text blocks from ALTO XML
    for text_block in alto_blocks:
        text_blocks.append({
            'id': text_block.get('ID'),
            'hpos': int(text_block.get('HPOS')),
            'vpos': int(text_block.get('VPOS')),
            'width': int(text_block.get('WIDTH')),
            'height': int(text_block.get('HEIGHT'))
        })
        #print(text_blocks)
    
    # Perform OCR on the entire image
    print("Performing OCR on the entire image")
    ocr_text = pytesseract.image_to_string(image)
    
    # Refine OCR results using ALTO XML information
    print("Refining OCR results using ALTO XML information")
    refined_text = refine_ocr(image, text_blocks, ocr_text)
    
    # Save refined text to file
    with open(pdf_path.replace(".pdf", "_ocr.txt"), "w", encoding="utf-8") as f:
        f.write(refined_text)

def refine_ocr(image, text_blocks, ocr_text):
    refined_text = ""
    
    for block in text_blocks:
        # Crop image to text block coordinates
        cropped = image.crop((block['hpos'], block['vpos'], 
                              block['hpos'] + block['width'], 
                              block['vpos'] + block['height']))
        
        # Perform OCR on cropped image
        block_text = pytesseract.image_to_string(cropped)
        
        # Add block text to refined text
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