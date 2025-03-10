# This file will contain common utility functions
import PyPDF2
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
import logging
import fitz  # PyMuPDF
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get configuration from environment variables
load_dotenv()
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
HTTPS_PROXY = os.getenv('HTTPS_PROXY')

# Set Tesseract path from environment variable
tesseract_path = os.getenv('TESSERACT_PATH')
logger.info(f"Tesseract path from env: {tesseract_path}")

if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    logger.info(f"Tesseract path set to: {pytesseract.pytesseract.tesseract_cmd}")
else:
    logger.warning("TESSERACT_PATH environment variable not set")

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
        logger.warning("No text to save")
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
        logger.info(f"Text saved to: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving text file: {str(e)}")
        return None

def extract_text_from_pdf_with_fitz(pdf_path, language='bul+eng', display_pages=False, auto_rotate=True):
    """
    Extract text from PDF using PyMuPDF (fitz) and Tesseract OCR
    """
    try:
        logger.info(f"Opening PDF with PyMuPDF: {pdf_path}")
        
        # Open the PDF
        doc = fitz.open(pdf_path)
        logger.info(f"PDF opened successfully with {doc.page_count} pages")
        
        all_text = ""
        
        # Process each page
        for page_num in range(len(doc)):
            try:
                logger.info(f"Processing page {page_num+1} of {len(doc)}")
                
                # Get the page
                page = doc.load_page(page_num)
                
                # Convert to pixmap (image)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Higher resolution for better OCR
                
                # Convert pixmap to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
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
                        logger.info(f"Detected page rotation: {rotation_angle} degrees")
                        
                        if rotation_angle == 0:
                            # If Tesseract says no rotation needed, check with advanced method as backup
                            img_cv_gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
                            non_zero_pixels = cv2.findNonZero(cv2.threshold(img_cv_gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1])
                            if non_zero_pixels is not None:
                                rect = cv2.minAreaRect(non_zero_pixels)
                                angle = rect[2]
                                if abs(angle) > 5:  # Only apply if significant angle detected
                                    rotation_angle = 90 if (angle < -45) else 0
                        
                    except Exception as e:
                        logger.warning(f"Error in orientation detection: {str(e)}")
                        logger.info("Trying alternative orientation detection...")
                        
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
                                    logger.info(f"Angle {angle} - Average confidence: {avg_conf}")
                                    if avg_conf > best_conf:
                                        best_conf = avg_conf
                                        best_angle = angle
                            except Exception as conf_error:
                                logger.warning(f"Error testing angle {angle}: {str(conf_error)}")
                        
                        rotation_angle = best_angle
                        logger.info(f"Selected best rotation angle: {rotation_angle}")
                
                # Apply rotation if needed
                if rotation_angle != 0:
                    logger.info(f"Rotating image by {rotation_angle} degrees")
                    # Rotate using OpenCV for better quality
                    if rotation_angle == 90:
                        img_cv = cv2.rotate(img_cv, cv2.ROTATE_90_CLOCKWISE)
                    elif rotation_angle == 180:
                        img_cv = cv2.rotate(img_cv, cv2.ROTATE_180)
                    elif rotation_angle == 270:
                        img_cv = cv2.rotate(img_cv, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    
                    # Convert back to PIL
                    img = Image.fromarray(img_cv)
                
                # Use Tesseract for OCR
                logger.info(f"Running OCR with language: {language}")
                try:
                    # Standard approach using the specified language(s)
                    page_text = pytesseract.image_to_string(img, lang=language)
                    
                    # Get Tesseract data including confidence
                    data = pytesseract.image_to_data(img, lang=language, output_type=pytesseract.Output.DICT)
                    
                    # Calculate average confidence for the page
                    confidences = [conf for conf in data['conf'] if conf != -1]  # Filter out -1 values
                    if confidences:
                        avg_confidence = sum(confidences) / len(confidences)
                        logger.info(f"Page {page_num+1} OCR confidence: {avg_confidence:.2f}%")
                        
                        # Add a warning if OCR confidence is low
                        if avg_confidence < 70:  # 70% threshold
                            logger.warning(f"OCR confidence is low for page {page_num+1}. Text extraction may be unreliable.")
                    
                    logger.info(f"OCR completed for page {page_num+1}")
                    if not page_text.strip():
                        logger.warning(f"No text extracted from page {page_num+1}")
                    else:
                        logger.info(f"Extracted {len(page_text)} characters from page {page_num+1}")
                        # Log a preview of the text (first 100 chars)
                        preview = page_text[:100].replace('\n', ' ')
                        logger.info(f"Text preview: {preview}...")
                except Exception as ocr_error:
                    logger.error(f"OCR error on page {page_num+1}: {str(ocr_error)}")
                    continue
                
                # Add page text to all text
                all_text += f"\n\n--- PAGE {page_num+1} ---\n\n" + page_text
                
            except Exception as page_error:
                logger.error(f"Error processing page {page_num+1}: {str(page_error)}")
                continue
        
        if not all_text.strip():
            logger.warning("No text was extracted from any page of the PDF with Tesseract")
        else:
            logger.info(f"Successfully extracted {len(all_text)} characters of text")
            
        return all_text
        
    except Exception as e:
        logger.error(f"General error in text extraction: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def extract_entities_from_text(text, max_retries=3, retry_delay=60):
    """
    Extract structured information from text using Azure OpenAI
    """
    try:
        logger.info("Starting entity extraction from text")
        # Check if we have text to process
        if not text or not text.strip():
            logger.error("No text provided for entity extraction")
            return None
            
        # Log text length
        logger.info(f"Text length: {len(text)} characters")
        
        # Create HTTP client with proxy
        http_client = None
        if HTTPS_PROXY:
            logger.info(f"Using proxy: {HTTPS_PROXY}")
            http_client = httpx.Client(
                transport=httpx.HTTPTransport(
                    proxy=httpx.Proxy(url=HTTPS_PROXY)
                ),
                verify=False
            )
        
        # Check for Azure OpenAI credentials
        if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME]):
            logger.error("Missing Azure OpenAI credentials - check environment variables")
            return {"error": "Azure OpenAI credentials not configured"}
        
        # Initialize OpenAI client
        logger.info(f"Initializing Azure OpenAI client with endpoint: {AZURE_OPENAI_ENDPOINT}")
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            http_client=http_client
        )
        
        # Using exponential backoff for retries
        for attempt in range(max_retries):
            try:
                logger.info(f"Entity extraction attempt {attempt+1}/{max_retries}")
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
                
                logger.info(f"Sending request to Azure OpenAI model: {AZURE_OPENAI_DEPLOYMENT_NAME}")
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
                logger.info("Parsing Azure OpenAI response")
                result = json.loads(response.choices[0].message.content)
                
                # Validate identifiers for each entity
                if "entities" in result and len(result["entities"]) > 0:
                    entity_count = len(result["entities"])
                    logger.info(f"Found {entity_count} entities, validating identifiers")
                    
                    for i, entity in enumerate(result["entities"]):
                        logger.info(f"Validating entity {i+1}/{entity_count}: {entity.get('name', 'Unknown')} - {entity.get('identification_number', 'No ID')}")
                        
                        if entity["type"].lower() == "person" and entity["identification_type"] == "EGN":
                            # Validate person's EGN
                            is_valid = is_valid_egn(entity["identification_number"])
                            entity["ValidIdentificator"] = "Valid" if is_valid else "Invalid"
                            logger.info(f"EGN validation result: {entity['ValidIdentificator']}")
                            
                        elif entity["type"].lower() == "company" and entity["identification_type"] == "EIK":
                            # Validate company's EIK
                            is_valid = validate_bulgarian_eik(entity["identification_number"])
                            entity["ValidIdentificator"] = "Valid" if is_valid else "Invalid"
                            logger.info(f"EIK validation result: {entity['ValidIdentificator']}")
                            
                        else:
                            # For other types or identification types, mark as Valid
                            entity["ValidIdentificator"] = "Valid"
                            logger.info(f"Other ID type, marking as: {entity['ValidIdentificator']}")
                
                logger.info("Entity extraction completed successfully")
                return result
                
            except Exception as api_error:
                logger.error(f"Error in API call (attempt {attempt+1}): {str(api_error)}")
                if attempt < max_retries - 1:
                    backoff_time = retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {backoff_time} seconds...")
                    time.sleep(backoff_time)  # Exponential backoff
                
        logger.error(f"All {max_retries} extraction attempts failed")
        return {"error": "Failed to extract entities after multiple attempts"}
        
    except Exception as e:
        logger.error(f"General error in entity extraction: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": "Unexpected error during entity extraction"}

def process_pdf_end_to_end(pdf_path, ocr_language='bul+eng', save_text=False, output_dir=None):
    """
    Process a PDF file from start to finish:
    1. Extract text with PyMuPDF and Tesseract OCR
    2. Extract entities with Azure OpenAI
    
    Parameters:
    pdf_path (str): Path to the PDF file
    ocr_language (str): Language code for Tesseract OCR
    save_text (bool): Whether to save the extracted text to a file
    output_dir (str): Directory to save the extracted text (default: same directory as PDF)
    
    Returns:
    dict: Extracted entities in JSON format
    """
    start_time = time.time()
    logger.info(f"Starting end-to-end PDF processing for {pdf_path}")
    logger.info(f"Parameters: ocr_language={ocr_language}")
    
    # Check if the PDF file exists
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return {"error": f"PDF file not found: {pdf_path}"}
    
    # Check file size
    try:
        file_size = os.path.getsize(pdf_path)
        logger.info(f"PDF file size: {file_size} bytes")
        if file_size == 0:
            logger.error("PDF file is empty (zero bytes)")
            return {"error": "PDF file is empty"}
    except Exception as e:
        logger.error(f"Error checking PDF file size: {str(e)}")
    
    # Step 1: Extract text from PDF using PyMuPDF and Tesseract OCR
    extracted_text = extract_text_from_pdf_with_fitz(
        pdf_path, 
        language=ocr_language
    )
    
    # Save the extracted text to a file if requested and if we have text
    if extracted_text and save_text:
        logger.info("Saving extracted text to file")
        if not output_dir:
            # Default to the same directory as the PDF
            output_dir = os.path.dirname(pdf_path)
            
        # Generate filename based on the PDF name
        pdf_filename = os.path.basename(pdf_path)
        pdf_name = os.path.splitext(pdf_filename)[0]
        text_filename = f"{pdf_name}_extracted_text.txt"
        
        # Save the text
        text_path = save_extracted_text(extracted_text, output_dir, text_filename)
        logger.info(f"Extracted text saved to: {text_path}")
    
    # Check if we got any text
    if not extracted_text or len(extracted_text.strip()) == 0:
        logger.error("No text was extracted from the PDF using any method")
        
        # For debugging: save a small sample of the PDF info
        try:
            logger.info("Logging PDF metadata for debugging")
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            logger.info(f"PDF metadata: {metadata}")
            doc.close()
        except Exception as md_error:
            logger.error(f"Could not get PDF metadata: {str(md_error)}")
        
        # Development mode option
        if os.getenv('HAIPER_DEV_MODE') == 'true':
            logger.info("DEV MODE: Creating mock extraction result for testing purposes")
            return {
                "entities": [],
                "overall_extraction_quality": 0.0,
                "warning": "No text was extracted from the PDF",
                "process_status": "completed_with_warnings"
            }
        else:
            # In production, return the error
            return {"error": "No text was extracted from the PDF"}
    
    # Log text extraction success
    logger.info(f"Successfully extracted {len(extracted_text)} characters from PDF")
    text_preview = extracted_text[:200].replace('\n', ' ')
    logger.info(f"Text preview: {text_preview}...")
    
    # Step 2: Extract entities from the text using Azure OpenAI
    # Only proceed if we have Azure OpenAI configured
    if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME]):
        logger.warning("Azure OpenAI not configured, skipping entity extraction")
        return {
            "text_extraction": "success",
            "entity_extraction": "skipped",
            "text_length": len(extracted_text),
            "text_preview": text_preview
        }
    
    logger.info("Starting entity extraction from extracted text")
    try:
        entities = extract_entities_from_text(extracted_text)
        
        if not entities:
            logger.error("Failed to extract entities")
            return {
                "error": "Failed to extract entities",
                "text_extraction": "success",
                "text_length": len(extracted_text)
            }
            
        logger.info("Entity extraction completed successfully")
        # Add extra information to the response
        entities["text_extraction"] = "success"
        entities["text_length"] = len(extracted_text)
        
        # Calculate and log processing time
        end_time = time.time()
        processing_time = end_time - start_time
        logger.info(f"Processing completed in {processing_time:.2f} seconds")
        entities["processing_time"] = f"{processing_time:.2f} seconds"
        
        return entities
        
    except Exception as entity_error:
        logger.error(f"Error during entity extraction: {str(entity_error)}")
        import traceback
        logger.error(f"Entity extraction error trace: {traceback.format_exc()}")
        
        return {
            "error": "Error extracting entities",
            "text_extraction": "success", 
            "text_length": len(extracted_text),
            "text_preview": text_preview
        }