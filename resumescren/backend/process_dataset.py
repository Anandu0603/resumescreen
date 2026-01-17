import os
import json
import time
from pathlib import Path
import requests
from tqdm import tqdm

# Configuration
BASE_URL = "http://localhost:5000"
AUTH_TOKEN = "YOUR_AUTH_TOKEN"  # Replace with your actual token
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}

# Paths
DATASET_DIR = os.path.join(os.path.dirname(__file__), "..", "dataset", "data", "data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "dataset", "processed_results")

# Job Description (Customize this based on your requirements)
JOB_DESCRIPTION = """
We are looking for a skilled professional with the following qualifications:
- Strong programming skills in Python, Java, or JavaScript
- Experience with web development frameworks (Django, Flask, React, or Node.js)
- Knowledge of databases (SQL/NoSQL)
- Experience with version control (Git)
- Problem-solving and analytical skills
- Good communication and teamwork abilities
"""

def process_resume(file_path):
    """Process a single resume file and return the result"""
    try:
        with open(file_path, 'rb') as f:
            files = {
                'resume': (os.path.basename(file_path), f, 
                         'application/pdf' if file_path.lower().endswith('.pdf') 
                         else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            }
            data = {'job_description': JOB_DESCRIPTION}
            
            response = requests.post(
                f"{BASE_URL}/api/upload",
                headers=HEADERS,
                files=files,
                data=data,
                timeout=30  # 30 seconds timeout
            )
            return response.json()
    except Exception as e:
        return {"error": str(e), "file": file_path}

def process_dataset():
    """Process all resumes in the dataset directory"""
    # Create output directory if it doesn't exist
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Get list of all resume files
    resume_files = []
    for ext in ('*.pdf', '*.docx', '*.doc', '*.txt'):
        resume_files.extend(Path(DATASET_DIR).rglob(ext))
    
    print(f"Found {len(resume_files)} resume files to process")
    
    results = {}
    processed_count = 0
    error_count = 0
    
    # Process each resume with progress bar
    for file_path in tqdm(resume_files, desc="Processing Resumes"):
        try:
            # Skip if already processed
            result_file = os.path.join(OUTPUT_DIR, f"{file_path.stem}_result.json")
            if os.path.exists(result_file):
                with open(result_file, 'r') as f:
                    results[str(file_path)] = json.load(f)
                processed_count += 1
                continue
                
            # Process the resume
            result = process_resume(str(file_path))
            results[str(file_path)] = result
            
            # Save individual result
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2)
                
            processed_count += 1
            
            # Add a small delay to avoid overwhelming the server
            time.sleep(0.5)
            
        except Exception as e:
            error_count += 1
            print(f"\nError processing {file_path}: {str(e)}")
            continue
    
    # Save summary of all results
    summary = {
        "total_resumes": len(resume_files),
        "processed_count": processed_count,
        "error_count": error_count,
        "results": results
    }
    
    with open(os.path.join(OUTPUT_DIR, "processing_summary.json"), 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary

def get_top_matches(top_n=10, min_score=70):
    """Get top matching resumes from the processed results"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/rank-resumes",
            headers={"Content-Type": "application/json", **HEADERS},
            json={
                "job_description": JOB_DESCRIPTION,
                "top_n": top_n,
                "min_score": min_score
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting top matches: {response.text}")
            return None
    except Exception as e:
        print(f"Error in get_top_matches: {str(e)}")
        return None

def analyze_results():
    """Analyze and display the processing results"""
    # Load the processing summary
    summary_file = os.path.join(OUTPUT_DIR, "processing_summary.json")
    if not os.path.exists(summary_file):
        print("No processing summary found. Please run process_dataset() first.")
        return
    
    with open(summary_file, 'r') as f:
        summary = json.load(f)
    
    print("\n" + "="*50)
    print("PROCESSING SUMMARY")
    print("="*50)
    print(f"Total Resumes: {summary['total_resumes']}")
    print(f"Successfully Processed: {summary['processed_count']}")
    print(f"Errors: {summary['error_count']}")
    
    # Get top matches
    print("\n" + "="*50)
    print("TOP MATCHING RESUMES")
    print("="*50)
    
    top_matches = get_top_matches(top_n=10, min_score=70)
    if top_matches and 'top_resumes' in top_matches:
        for i, resume in enumerate(top_matches['top_resumes'], 1):
            print(f"\n{i}. {resume.get('filename', 'N/A')}")
            print(f"   Match Score: {resume.get('match_score', 0):.2f}%")
            
            details = resume.get('details', {})
            if 'matched_terms' in details and details['matched_terms']:
                print(f"   Matched Skills: {', '.join(details['matched_terms'][:5])}...")
            if 'missing_terms' in details and details['missing_terms']:
                print(f"   Missing Skills: {', '.join(details['missing_terms'][:3])}...")
    else:
        print("No matching resumes found or there was an error fetching results.")

if __name__ == "__main__":
    print("Starting resume dataset processing...")
    process_dataset()
    analyze_results()
