# Job Matcher Module
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import time
from functools import lru_cache

# Pre-compile regex patterns for text cleaning
CLEAN_PATTERN = re.compile(r'[^a-zA-Z\s]')

@lru_cache(maxsize=100)  # Cache vectorizer results for common job descriptions
def get_vectorizer():
    return TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2),  # Consider both unigrams and bigrams
        max_features=5000,    # Limit number of features
        min_df=2,            # Ignore terms that appear in only 1 document
        max_df=0.8,          # Ignore terms that appear in more than 80% of documents
        use_idf=True,
        smooth_idf=True
    )

def clean_text(text):
    """Basic text cleaning"""
    if not text:
        return ""
    # Convert to lowercase and remove special characters
    text = text.lower()
    text = CLEAN_PATTERN.sub(' ', text)
    # Remove extra whitespace
    return ' '.join(text.split())

def match_resume_to_job(resume_data, job_description):
    start_time = time.time()
    
    # Clean and preprocess text
    resume_text = clean_text(resume_data.get('raw_text', ''))
    job_desc = clean_text(job_description)
    
    if not resume_text or not job_desc:
        return 0.0, {'error': 'Missing resume text or job description'}
    
    try:
        # Initialize vectorizer with optimized parameters
        vectorizer = get_vectorizer()
        
        # Transform the texts
        texts = [resume_text, job_desc]
        tfidf = vectorizer.fit_transform(texts)
        
        # Calculate similarity
        score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Prepare result
        details = {
            'similarity': float(score),
            'processing_time_seconds': round(processing_time, 3),
            'resume_length': len(resume_text.split()),
            'job_desc_length': len(job_desc.split())
        }
        
        return float(np.round(score * 100, 2)), details
        
    except Exception as e:
        return 0.0, {'error': str(e), 'processing_time_seconds': round(time.time() - start_time, 3)}
