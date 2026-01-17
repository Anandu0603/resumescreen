# Resume Parser Module
import os
import re
from pdfminer.high_level import extract_text as pdf_extract
from docx import Document

def extract_text_from_pdf(path):
    try:
        return pdf_extract(path)
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        return ''

def extract_text_from_docx(path):
    try:
        doc = Document(path)
        return '\n'.join([p.text for p in doc.paragraphs])
    except Exception as e:
        print(f"Error extracting text from DOCX: {str(e)}")
        return ''

def extract_email(text):
    """Extract email address from text using regex"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return match.group(0) if match else None

def extract_phone(text):
    """Extract phone number from text using regex"""
    # Match various phone number formats
    phone_patterns = [
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # 123-456-7890 or 123.456.7890 or 123 456 7890
        r'\b\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b',  # (123) 456-7890
        r'\b\+?[\d\s-]{10,}\b'  # International numbers
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()
    return None

def extract_name(text):
    """Extract name from the beginning of the text (simplified)"""
    # This is a simple approach - in production, you might want to use a more sophisticated NER model
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line and any(c.isalpha() for c in line):
            # Basic check for name-like strings (contains letters and spaces, not too long)
            if 3 <= len(line.split()) <= 4 and all(any(c.isalpha() for c in word) for word in line.split()):
                return line
    return None

def parse_resume(filepath):
    """Parse resume and extract structured information"""
    try:
        # Check file exists
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return {'error': 'File not found'}
            
        # Extract text based on file type
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.pdf':
            text = extract_text_from_pdf(filepath)
        elif ext == '.docx':
            text = extract_text_from_docx(filepath)
        else:
            return {'error': 'Unsupported file format'}
            
        if not text.strip():
            return {'error': 'Could not extract text from file'}
            
        # Extract contact information
        email = extract_email(text)
        phone = extract_phone(text)
        name = extract_name(text)
        
        # Prepare result
        result = {
            'raw_text': text[:5000],  # Limit text length
            'contact': {
                'name': name,
                'email': email,
                'phone': phone
            },
            'filename': os.path.basename(filepath)
        }
        
        return result
        
    except Exception as e:
        print(f"Error parsing resume: {str(e)}")
        return {'error': str(e)}
