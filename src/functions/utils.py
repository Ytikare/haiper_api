# This file will contain common utility functions
def format_response(data, status="success", message=None):
    return {
        "status": status,
        "message": message,
        "data": data
    }


def assign_new_values(workflow:any, workflow_data: dict):
    # Update the workflow attributes
    for key, value in workflow_data.items():
        # Convert camelCase to snake_case for database columns
        if key == "apiConfig":
            setattr(workflow, "api_config", value)
        elif key == "isPublished":
            setattr(workflow, "is_published", value)
        elif key == "createdAt":
            setattr(workflow, "created_at", value)
        elif key == "updatedAt":
            setattr(workflow, "updated_at", value)
        elif key == "id":
            continue
        elif key == "createdBy":
            setattr(workflow, "created_by", value)
        else:
            setattr(workflow, key, value)



import PyPDF2
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import io
import numpy as np
from openai import AzureOpenAI
import httpx
import json
import time
import calendar
import re
import cv2
import os
from dotenv import load_dotenv


# Get configuration from environment variables
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
HTTPS_PROXY = os.getenv('HTTPS_PROXY')

# Set Tesseract path from environment variable
tesseract_path = os.getenv('TESSERACT_PATH')
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def is_valid_egn(egn):
    """
    Check if a Bulgarian EGN (Unified Civil Number) is valid
    """
    # Weights used for checksum calculation
    EGN_WEIGHTS = [2, 4, 8, 5, 10, 9, 7, 3, 6]
    
    # Check if EGN is exactly 10 digits
    if len(egn) != 10 or not egn.isdigit():
        return False
        
    year = int(egn[0:2])
    month = int(egn[2:4])
    day = int(egn[4:6])
    
    # Adjust for different centuries based on month codes
    if month > 40:  # 2000+
        if not is_valid_date(day, month - 40, year + 2000):
            return False
    elif month > 20:  # 1800+
        if not is_valid_date(day, month - 20, year + 1800):
            return False
    else:  # 1900+
        if not is_valid_date(day, month, year + 1900):
            return False
            
    # Calculate and validate checksum
    checksum = int(egn[9])
    egn_sum = 0
    for i in range(9):
        egn_sum += int(egn[i]) * EGN_WEIGHTS[i]
    valid_checksum = egn_sum % 11
    if valid_checksum == 10:
        valid_checksum = 0
        
    return checksum == valid_checksum

def is_valid_date(day, month, year):
    """
    Helper function to check if a date is valid
    """
    try:
        if month < 1 or month > 12:
            return False
        # Get the last day of the month
        last_day = calendar.monthrange(year, month)[1]
        return 1 <= day <= last_day
    except ValueError:
        return False

def validate_bulgarian_eik(eik):
    """ 
    Validates a Bulgarian EIK/BULSTAT number.
    """
    # Check if EIK is a string and only contains digits
    if not isinstance(eik, str) or not eik.isdigit():
        return False
        
    # EIK can be either 9 or 13 digits
    if len(eik) == 9:
        return validate_eik_9_digits(eik)
    elif len(eik) == 13:
        return validate_eik_13_digits(eik)
    else:
        return False
        
def validate_eik_9_digits(eik):
    """Validates a 9-digit EIK number."""
    # First check digit (position 8) weights
    weights_1 = [1, 2, 3, 4, 5, 6, 7, 8]
    sum_1 = 0
    
    for i in range(8):
        sum_1 += int(eik[i]) * weights_1[i]
        
    remainder_1 = sum_1 % 11
    
    if remainder_1 == 10:
        # Recalculate with different weights
        weights_alt = [3, 4, 5, 6, 7, 8, 9, 10]
        sum_alt = 0
        
        for i in range(8):
            sum_alt += int(eik[i]) * weights_alt[i]
            
        remainder_1 = sum_alt % 11
        if remainder_1 == 10:
            remainder_1 = 0
            
    # Verify the check digit
    return remainder_1 == int(eik[8])
    
def validate_eik_13_digits(eik):
    """Validates a 13-digit EIK number."""
    # First check if the first 9 digits are valid
    if not validate_eik_9_digits(eik[:9]):
        return False
        
    # Check the additional 4 digits
    weights_2 = [2, 7, 3, 5]
    sum_2 = 0
    
    for i in range(4):
        sum_2 += int(eik[i+9]) * weights_2[i]
        
    remainder_2 = sum_2 % 11
    
    if remainder_2 == 10:
        # Recalculate with different weights
        weights_alt = [4, 9, 5, 7]
        sum_alt = 0
        
        for i in range(4):
            sum_alt += int(eik[i+9]) * weights_alt[i]
            
        remainder_2 = sum_alt % 11
        if remainder_2 == 10:
            remainder_2 = 0
            
    # Verify the check digit for the extension
    return remainder_2 == int(eik[12])

def save_extracted_text(text, output_path=None, filename=None):
    """
    Save extracted text to a file for review
    """
    if not text:
        return None
        
    # Set default output path if not provided
    if not output_path:
        output_path = os.getcwd()
        
    # Create the directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    # Set default filename if not provided
    if not filename:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"extracted_text_{timestamp}.txt"
        
    # Full path to the output file
    file_path = os.path.join(output_path, filename)
    
    # Save the file
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(text)
        return file_path
    except Exception:
        return None

def extract_text_from_pdf_with_tesseract(pdf_path, language='bul+eng', display_pages=False, auto_rotate=True, mixed_language_approach="primary"):
    """
    Extract text directly from a PDF file using Tesseract OCR with automatic orientation correction
    """
    try:
        # Import required libraries

        
        # Open the PDF
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
        
        # Convert PDF pages to images
        images = convert_from_path(pdf_path, dpi=200)  # Higher DPI for better OCR
        all_text = ""
        
        # Process each page
        for page_num, img in enumerate(images):
            try:
                # Convert PIL image to OpenCV format for better rotation handling
                img_cv = np.array(img)
                img_cv = img_cv[:, :, :3]  # Remove alpha channel if present
                
                rotation_angle = 0
                
                # Auto-rotate image if enabled
                if auto_rotate:
                    try:
                        # First try with Tesseract's orientation detection
                        osd = pytesseract.image_to_osd(img)
                        rotation_angle = int(re.search(r'Rotate: (\d+)', osd).group(1))
                        
                        if rotation_angle == 0:
                            # If Tesseract says no rotation needed, check with advanced method as backup
                            img_cv_gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
                            non_zero_pixels = cv2.findNonZero(cv2.threshold(img_cv_gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1])
                            if non_zero_pixels is not None:
                                rect = cv2.minAreaRect(non_zero_pixels)
                                angle = rect[2]
                                if abs(angle) > 5:  # Only apply if significant angle detected
                                    rotation_angle = 90 if (angle < -45) else 0
                        
                    except Exception:
                        # Fall back to trying all orientations
                        best_conf = 0
                        best_angle = 0
                        
                        for angle in [0, 90, 180, 270]:
                            # Rotate image for testing
                            if angle == 0:
                                test_img = img
                            else:
                                test_img = img.rotate(angle, expand=True)
                            
                            # Get confidence at this orientation
                            try:
                                data = pytesseract.image_to_data(test_img, lang=language, 
                                                             output_type=pytesseract.Output.DICT)
                                confidences = [conf for conf in data['conf'] if conf != -1]
                                
                                if confidences:
                                    avg_conf = sum(confidences) / len(confidences)
                                    if avg_conf > best_conf:
                                        best_conf = avg_conf
                                        best_angle = angle
                            except:
                                pass  # Skip errors in test orientations
                        
                        rotation_angle = best_angle
                
                # Apply rotation if needed
                if rotation_angle != 0:
                    # Rotate using OpenCV for better quality
                    if rotation_angle == 90:
                        img_cv = cv2.rotate(img_cv, cv2.ROTATE_90_CLOCKWISE)
                    elif rotation_angle == 180:
                        img_cv = cv2.rotate(img_cv, cv2.ROTATE_180)
                    elif rotation_angle == 270:
                        img_cv = cv2.rotate(img_cv, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    
                    # Convert back to PIL
                    img = Image.fromarray(img_cv)
                
                # Use Tesseract for OCR with the selected approach
                if mixed_language_approach == "primary":
                    # Standard approach using the specified language(s)
                    page_text = pytesseract.image_to_string(img, lang=language)
                    
                elif mixed_language_approach == "two_pass":
                    # First pass with Bulgarian
                    bul_text = pytesseract.image_to_string(img, lang='bul')
                    
                    # Second pass with English
                    eng_text = pytesseract.image_to_string(img, lang='eng')
                    
                    # Merge the results using a custom merging strategy
                    page_text = bul_text
                    
                    # Add English words that were likely missed in Bulgarian pass
                    known_english_terms = ["MoneyGram", "Western Union", "PayPal", "Money Transfer"]
                    for term in known_english_terms:
                        if term in eng_text and term not in bul_text:
                            page_text = page_text.replace(term.lower(), term)
                            if term not in page_text:
                                page_text += f"\nDetected English term: {term}\n"
                    
                elif mixed_language_approach == "whitelist":
                    # Define a custom configuration with whitelist
                    custom_config = f'-l {language} --psm 6 -c tessedit_char_whitelist="АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЬЮЯабвгдежзийклмнопрстуфхцчшщъьюя0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"'
                    page_text = pytesseract.image_to_string(img, config=custom_config)
                    
                else:
                    # Default to standard approach
                    page_text = pytesseract.image_to_string(img, lang=language)
                
                # Add page text to all text
                all_text += f"\n\n--- PAGE {page_num+1} ---\n\n" + page_text
                
            except Exception:
                continue
            
        return all_text
        
    except Exception:
        return None

def extract_entities_from_text(text, max_retries=3, retry_delay=60):
    """
    Extract structured information from text using Azure OpenAI
    """
    try:
        # Create HTTP client with proxy
        http_client = None
        if HTTPS_PROXY:
            http_client = httpx.Client(
                transport=httpx.HTTPTransport(
                    proxy=httpx.Proxy(url=HTTPS_PROXY)
                ),
                verify=False
            )
        
        # Initialize OpenAI client
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            http_client=http_client
        )
        
        # Using exponential backoff for retries
        for attempt in range(max_retries):
            try:
                system_prompt = """You are a data extraction assistant. Extract all people and companies mentioned in the document, along with their identification numbers (EGN for individuals, EIK for companies). 

                For each extraction, include a confidence score from 0.0 to 1.0 that represents how confident you are in the accuracy of the extraction. Consider the following when determining confidence:
                - For names: Is the full name clearly visible and properly formatted?
                - For identification numbers: Are all digits clearly visible and does the format match expected patterns?
                - For entity type: Is it clear whether this is a person or a company?
                
                Use these confidence levels:
                - 1.0: Perfect clarity with no ambiguity
                - 0.8-0.9: Very clear with minimal ambiguity
                - 0.6-0.7: Mostly clear but with some uncertainty
                - 0.4-0.5: Significant uncertainty but probably correct
                - 0.1-0.3: Highly uncertain, likely contains errors
                - 0.0: Cannot determine at all

                Return the results in JSON format with the following structure:
                {
                    "entities": [
                        {
                            "name": "Full Name",
                            "type": "person/company",
                            "identification_number": "number",
                            "identification_type": "EGN/EIK",
                            "confidence": 0.8,
                            "ValidIdentificator": "Valid/Invalid"
                        }
                    ],
                    "overall_extraction_quality": 0.7
                }
                
                Also include an overall_extraction_quality score from 0.0 to 1.0 that represents the general quality of the text extraction and your confidence in the overall data extraction process.
                
                Only include entities where both name and identification number are mentioned.
                The document is in Bulgarian language.
                """
                
                response = client.chat.completions.create(
                    model=AZURE_OPENAI_DEPLOYMENT_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ],
                    temperature=0,
                    response_format={"type": "json_object"}
                )
                
                # Parse the response
                result = json.loads(response.choices[0].message.content)
                
                # Validate identifiers for each entity
                if "entities" in result and len(result["entities"]) > 0:
                    for entity in result["entities"]:
                        if entity["type"].lower() == "person" and entity["identification_type"] == "EGN":
                            # Validate person's EGN
                            entity["ValidIdentificator"] = "Valid" if is_valid_egn(entity["identification_number"]) else "Invalid"
                        elif entity["type"].lower() == "company" and entity["identification_type"] == "EIK":
                            # Validate company's EIK
                            entity["ValidIdentificator"] = "Valid" if validate_bulgarian_eik(entity["identification_number"]) else "Invalid"
                        else:
                            # For other types or identification types, mark as Valid
                            entity["ValidIdentificator"] = "Valid"
                
                return result
                
            except Exception:
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                
        return None
        
    except Exception:
        return None

def process_pdf_end_to_end(pdf_path, ocr_language='bul+eng', mixed_language_approach="primary", save_text=False, output_dir=None):
    """
    Process a PDF file from start to finish:
    1. Extract text with Tesseract OCR
    2. Extract entities with Azure OpenAI
    
    Parameters:
    pdf_path (str): Path to the PDF file
    ocr_language (str): Language code for Tesseract OCR
    mixed_language_approach (str): Approach for handling mixed languages
    save_text (bool): Whether to save the extracted text to a file
    output_dir (str): Directory to save the extracted text (default: same directory as PDF)
    
    Returns:
    dict: Extracted entities in JSON format
    """
    # Step 1: Extract text from PDF using Tesseract
    extracted_text = extract_text_from_pdf_with_tesseract(
        pdf_path, 
        language=ocr_language,
        mixed_language_approach=mixed_language_approach
    )
    
    if not extracted_text or len(extracted_text.strip()) == 0:
        return {"error": "No text was extracted from the PDF"}
    
    # Save the extracted text to a file if requested
    if save_text:
        if not output_dir:
            # Default to the same directory as the PDF
            output_dir = os.path.dirname(pdf_path)
            
        # Generate filename based on the PDF name
        pdf_filename = os.path.basename(pdf_path)
        pdf_name = os.path.splitext(pdf_filename)[0]
        text_filename = f"{pdf_name}_extracted_text.txt"
        
        # Save the text
        save_extracted_text(extracted_text, output_dir, text_filename)
    
    # Step 2: Extract entities from the text using Azure OpenAI
    entities = extract_entities_from_text(extracted_text)
    
    if not entities:
        return {"error": "Failed to extract entities"}
    
    return entities
