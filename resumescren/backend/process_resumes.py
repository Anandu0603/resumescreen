import os
import json
import requests
from pathlib import Path
from tqdm import tqdm

# Configuration
DATASET_DIR = '../dataset/data/data'  # Update this path if needed
OUTPUT_FILE = 'resume_matches.csv'
JOB_DESCRIPTION = """
We are looking for a skilled Python developer with experience in Flask and machine learning.
Requirements:
- 3+ years of Python experience
- Experience with Flask or Django
- Knowledge of machine learning concepts
- Strong problem-solving skills
- Experience with data analysis
- Familiarity with databases (SQL/NoSQL)
- Version control with Git
"""

def get_resume_files(directory):
    """Get all PDF and DOCX files from the directory"""
    files = []
    for ext in ['*.pdf', '*.docx']:
        files.extend(Path(directory).rglob(ext))
    return files

def process_resume(file_path, job_description):
    """Process a single resume file"""
    url = 'http://localhost:5000/api/upload'
    try:
        with open(file_path, 'rb') as f:
            files = {'resume': f}
            data = {'job_description': job_description}
            response = requests.post(url, files=files, data=data)
            return response.json()
    except Exception as e:
        return {'error': str(e), 'file': str(file_path)}

def save_results(results, output_file):
    """Save results to CSV file"""
    import csv
    
    if not results:
        print("No results to save.")
        return
    
    # Get all possible fieldnames from all results
    fieldnames = set()
    for result in results:
        if 'resume_data' in result and isinstance(result['resume_data'], dict):
            for key in result['resume_data']:
                fieldnames.add(f'resume_{key}')
        fieldnames.update(key for key in result.keys() if key != 'resume_data')
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
        writer.writeheader()
        
        for result in results:
            row = {}
            for key, value in result.items():
                if key == 'resume_data' and isinstance(value, dict):
                    for k, v in value.items():
                        if isinstance(v, (list, dict)):
                            row[f'resume_{k}'] = json.dumps(v)
                        else:
                            row[f'resume_{k}'] = v
                else:
                    if isinstance(value, (list, dict)):
                        row[key] = json.dumps(value)
                    else:
                        row[key] = value
            writer.writerow(row)

def main():
    # Ensure the Flask server is running
    print("Make sure the Flask server is running at http://localhost:5000")
    
    # Get all resume files
    print("\nScanning for resume files...")
    resume_files = get_resume_files(DATASET_DIR)
    
    if not resume_files:
        print(f"No PDF or DOCX files found in {DATASET_DIR}")
        return
    
    print(f"Found {len(resume_files)} resume files. Starting processing...")
    
    # Process each resume
    results = []
    for resume_file in tqdm(resume_files, desc="Processing Resumes"):
        try:
            result = process_resume(resume_file, JOB_DESCRIPTION)
            result['filename'] = str(resume_file.name)
            results.append(result)
            
            # Print basic info for each processed resume
            if 'resume_data' in result and 'name' in result['resume_data']:
                name = result['resume_data']['name']
                score = result.get('match_score', 'N/A')
                print(f"\nProcessed: {name} - Score: {score}")
            
        except Exception as e:
            print(f"\nError processing {resume_file.name}: {str(e)}")
    
    # Save results
    save_results(results, OUTPUT_FILE)
    print(f"\nProcessing complete! Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
