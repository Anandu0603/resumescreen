import re
import os
import PyPDF2
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file with improved error handling"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            try:
                reader = PyPDF2.PdfReader(file)
                if not reader.pages:
                    print(f"Warning: No pages found in PDF: {pdf_path}")
                    return ""
                
                for page in reader.pages:
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                        else:
                            print(f"Warning: No text extracted from a page in {pdf_path}")
                    except Exception as page_error:
                        print(f"Error extracting text from a page in {pdf_path}: {str(page_error)}")
                        continue
                        
            except PyPDF2.errors.PdfReadError as pdf_error:
                print(f"Error reading PDF {pdf_path}: {str(pdf_error)}"
                      " - The PDF might be corrupted or encrypted.")
                return ""
                
    except Exception as e:
        print(f"Error opening/reading file {pdf_path}: {str(e)}")
        return ""
        
    if not text.strip():
        print(f"Warning: No text could be extracted from {pdf_path}")
        
    return text

def extract_text_from_docx(docx_path):
    """Extract text from DOCX file"""
    try:
        doc = Document(docx_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        print(f"Error reading DOCX file {docx_path}: {str(e)}")
        return ""

def parse_resume(filepath):
    """
    Parse resume file and extract text content with validation
    
    Args:
        filepath (str): Path to the resume file
        
    Returns:
        str: Extracted text from the resume
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is empty, corrupted, or in an unsupported format
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    if os.path.getsize(filepath) == 0:
        raise ValueError(f"File is empty: {filepath}")
    
    _, ext = os.path.splitext(filepath.lower())
    ext = ext.lower()
    
    try:
        if ext == '.pdf':
            text = extract_text_from_pdf(filepath)
        elif ext in ['.docx', '.doc']:
            text = extract_text_from_docx(filepath)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
            
        if not text or not text.strip():
            raise ValueError(f"No text could be extracted from the file: {filepath}")
            
        return text
        
    except Exception as e:
        # Log the full error for debugging
        print(f"Error parsing resume {filepath}: {str(e)}")
        raise ValueError(f"Failed to parse resume: {str(e)}")

def preprocess_text(text):
    """Preprocess text by converting to lowercase and removing special characters"""
    if not text:
        return ""
    # Convert to lowercase and remove special characters
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

def calculate_match_score(resume_text, job_description):
    """Calculate match score between resume and job description using TF-IDF and cosine similarity"""
    # Preprocess texts
    resume_processed = preprocess_text(resume_text)
    job_desc_processed = preprocess_text(job_description)
    
    if not resume_processed or not job_desc_processed:
        return 0.0, {}
    
    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = vectorizer.fit_transform([resume_processed, job_desc_processed])
    except ValueError:
        return 0.0, {}
    
    # Calculate cosine similarity
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    match_score = float(similarity[0][0]) * 100  # Convert to percentage
    
    # Get feature importance (top matching terms)
    feature_names = vectorizer.get_feature_names_out()
    tfidf_scores = tfidf_matrix.toarray()
    
    # Get top 10 important terms from job description
    top_terms_indices = np.argsort(tfidf_scores[1])[-10:][::-1]
    important_terms = [feature_names[i] for i in top_terms_indices if tfidf_scores[1][i] > 0]
    
    # Check for presence of important terms in resume
    present_terms = [term for term in important_terms if term in resume_processed]
    
    # Prepare match details
    match_details = {
        'important_terms': important_terms,
        'matched_terms': present_terms,
        'match_percentage': min(round(match_score, 2), 100.0),  # Cap at 100%
        'missing_terms': [term for term in important_terms if term not in present_terms]
    }
    
    return match_score, match_details

def rank_resumes(resumes, job_description, top_n=5):
    """
    Rank resumes based on their match with the job description
    
    Args:
        resumes: List of dictionaries with 'id' and 'text' keys
        job_description: Job description text
        top_n: Number of top resumes to return
        
    Returns:
        List of dictionaries with 'id', 'score', and 'details' keys, sorted by score
    """
    if not resumes or not job_description:
        return []
    
    scored_resumes = []
    for resume in resumes:
        score, details = calculate_match_score(resume.get('text', ''), job_description)
        scored_resumes.append({
            'id': resume.get('id'),
            'filename': resume.get('filename', ''),
            'score': score,
            'details': details
        })
    
    # Sort by score in descending order
    scored_resumes.sort(key=lambda x: x['score'], reverse=True)
    
    # Return top N resumes
    return scored_resumes[:top_n]
