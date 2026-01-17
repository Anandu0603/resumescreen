import os
import json
import time
import hashlib
import concurrent.futures
import argparse
from pathlib import Path
from tqdm import tqdm
import requests

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

# Global cache for scores
_score_cache = {}

def get_file_hash(file_path):
    """Generate a hash for file content to check for changes"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def process_resume(file_path, use_cache=True):
    """Process a single resume file with caching"""
    file_path = Path(file_path)
    result_file = os.path.join(OUTPUT_DIR, f"{file_path.stem}_result.json")
    
    # Check cache first
    if use_cache and os.path.exists(result_file):
        with open(result_file, 'r') as f:
            try:
                cached_result = json.load(f)
                # Check if file has been modified since last processing
                if 'file_hash' in cached_result and cached_result['file_hash'] == get_file_hash(file_path):
                    return cached_result
            except json.JSONDecodeError:
                pass  # If cache is corrupted, reprocess the file
    
    try:
        with open(file_path, 'rb') as f:
            files = {
                'resume': (file_path.name, f, 
                         'application/pdf' if str(file_path).lower().endswith('.pdf') 
                         else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            }
            data = {'job_description': JOB_DESCRIPTION}
            
            response = requests.post(
                f"{BASE_URL}/api/upload",
                headers=HEADERS,
                files=files,
                data=data,
                timeout=30
            )
            result = response.json()
            
            # Add file hash to result for caching
            if isinstance(result, dict):
                result['file_hash'] = get_file_hash(file_path)
            
            return result
    except Exception as e:
        return {"error": str(e), "file": str(file_path), "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}

def process_batch(batch_files, progress_bar=None):
    """Process a batch of files"""
    results = {}
    for file_path in batch_files:
        try:
            result = process_resume(file_path)
            results[str(file_path)] = result
            
            # Save individual result
            result_file = os.path.join(OUTPUT_DIR, f"{Path(file_path).stem}_result.json")
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2)
                
            if progress_bar:
                progress_bar.update(1)
                
        except Exception as e:
            print(f"\nError processing {file_path}: {str(e)}")
            continue
            
    return results

def process_dataset(batch_size=50, max_workers=4):
    """Process all resumes in the dataset directory with parallel processing"""
    # Create output directory if it doesn't exist
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Get list of all resume files
    resume_files = []
    for ext in ('*.pdf', '*.docx', '*.doc', '*.txt'):
        resume_files.extend(Path(DATASET_DIR).rglob(ext))
    
    print(f"Found {len(resume_files)} resume files to process")
    
    # Filter out already processed files
    files_to_process = [
        f for f in resume_files 
        if not os.path.exists(os.path.join(OUTPUT_DIR, f"{f.stem}_result.json"))
    ]
    
    if not files_to_process:
        print("All files have already been processed.")
        return {}
        
    print(f"Processing {len(files_to_process)} new files...")
    
    results = {}
    total_files = len(files_to_process)
    
    # Create progress bar
    with tqdm(total=total_files, desc="Processing Resumes", unit="file") as pbar:
        # Process in batches
        for i in range(0, len(files_to_process), batch_size):
            batch = files_to_process[i:i + batch_size]
            batch_results = process_batch(batch, progress_bar=pbar)
            results.update(batch_results)
            
            # Small delay between batches to prevent overwhelming the system
            time.sleep(1)
    
    return results

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
    # Get all result files
    result_files = list(Path(OUTPUT_DIR).glob("*_result.json"))
    
    if not result_files:
        print("No results found. Please run the processor first.")
        return
    
    # Load all results
    results = {}
    for result_file in result_files:
        try:
            with open(result_file, 'r') as f:
                result = json.load(f)
                if 'filename' in result:
                    results[result['filename']] = result
        except Exception as e:
            print(f"Error reading {result_file}: {str(e)}")
    
    # Calculate statistics
    total = len(results)
    successful = sum(1 for r in results.values() if 'match_score' in r)
    errors = total - successful
    
    print("\n" + "="*50)
    print("PROCESSING SUMMARY")
    print("="*50)
    print(f"Total Resumes Processed: {total}")
    print(f"Successfully Processed: {successful}")
    print(f"Errors: {errors}")
    
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
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Process resumes with ATS')
    parser.add_argument('--batch-size', type=int, default=50, help='Number of files to process in each batch')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    parser.add_argument('--min-score', type=float, default=70.0, help='Minimum match score to consider')
    parser.add_argument('--top-n', type=int, default=10, help='Number of top matches to show')
    
    args = parser.parse_args()
    
    print("Starting optimized resume processing...")
    print(f"Configuration: {args.workers} workers, batch size {args.batch_size}")
    
    # Process the dataset
    process_dataset(batch_size=args.batch_size, max_workers=args.workers)
    
    # Analyze and show results
    analyze_results()
