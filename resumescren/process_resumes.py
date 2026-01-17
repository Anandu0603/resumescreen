import os
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import re
from tqdm import tqdm

def extract_text_from_file(file_path):
    """Extract text from file (PDF or TXT)."""
    try:
        if file_path.lower().endswith('.pdf'):
            text = ""
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() or ""
            return text
        elif file_path.lower().endswith(('.txt', '.text')):
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        else:
            print(f"Unsupported file format: {file_path}")
            return ""
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return ""

def preprocess_text(text):
    """Basic text preprocessing."""
    # Convert to lowercase and remove special characters
    text = text.lower()
    text = re.sub(r'\W', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def calculate_similarity(job_desc, resume_text):
    """Calculate cosine similarity between job description and resume."""
    vectorizer = TfidfVectorizer(stop_words='english')
    try:
        # Combine job description and resume for vectorization
        texts = [job_desc, resume_text]
        tfidf_matrix = vectorizer.fit_transform(texts)
        # Calculate cosine similarity between the job description (first text) and resume (second text)
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return round(similarity * 100, 2)  # Convert to percentage
    except Exception as e:
        print(f"Error calculating similarity: {str(e)}")
        return 0.0

def process_resumes(job_desc, dataset_path):
    """Process all resumes in the dataset directory."""
    results = []
    
    # Walk through all directories in the dataset
    for root, _, files in os.walk(dataset_path):
        for file in tqdm(files, desc="Processing resumes"):
            if file.lower().endswith('.pdf'):
                file_path = os.path.join(root, file)
                category = os.path.basename(os.path.dirname(file_path))
                
                # Extract and preprocess text
                resume_text = extract_text_from_pdf(file_path)
                if not resume_text:
                    print(f"Could not extract text from {file}")
                    continue
                    
                # Calculate similarity score
                score = calculate_similarity(job_desc, resume_text)
                
                # Add to results
                results.append({
                    'filename': file,
                    'category': category,
                    'score': score,
                    'path': file_path
                })
    
    return results

def main():
    # Senior Software Engineer Job Description
    job_description = """
    Job Title: Senior Software Engineer
    Location: San Francisco, CA (Remote Available)
    Type: Full-time

    Key Responsibilities:
    - Design, develop, and maintain scalable web applications
    - Collaborate with cross-functional teams to implement new features
    - Write clean, maintainable, and efficient code
    - Optimize applications for maximum speed and scalability

    Requirements:
    - 5+ years of professional software development experience
    - Strong proficiency in Python and JavaScript/TypeScript
    - Experience with React.js and Node.js
    - Knowledge of cloud platforms (AWS, GCP, or Azure)
    - Experience with SQL and NoSQL databases
    - Bachelor's degree in Computer Science or related field

    Preferred Skills:
    - Experience with Docker and Kubernetes
    - Familiarity with CI/CD pipelines
    - Strong problem-solving and communication skills
    """
    
    # Path to John Doe's resume in the root directory
    resume_path = os.path.join(os.path.dirname(__file__), 'john_doe_resume.txt')
    
    if not os.path.exists(resume_path):
        print(f"Error: Could not find John Doe's resume at {resume_path}")
        print("Please make sure 'john_doe_resume.txt' exists in the same directory as this script.")
        return
    
    print(f"Analyzing {os.path.basename(resume_path)} against Senior Software Engineer position...")
    
    # Extract text from resume
    resume_text = extract_text_from_file(resume_path)
    if not resume_text:
        print("Error: Could not extract text from the resume")
        return
    
    # Calculate similarity score
    score = calculate_similarity(job_description, resume_text)
    
    # Print detailed analysis
    print("\n=== Resume Analysis Report ===")
    print(f"\nMatch Score: {score}%")
    
    # Check for key requirements
    requirements = {
        "5+ years of experience": bool(re.search(r'5\+?\s*years', resume_text, re.IGNORECASE)),
        "Python": bool(re.search(r'python', resume_text, re.IGNORECASE)),
        "JavaScript/TypeScript": bool(re.search(r'javascript|typescript', resume_text, re.IGNORECASE)),
        "React.js": bool(re.search(r'react\.?js', resume_text, re.IGNORECASE)),
        "Node.js": bool(re.search(r'node\.?js', resume_text, re.IGNORECASE)),
        "Cloud (AWS/GCP/Azure)": bool(re.search(r'aws|gcp|azure|cloud', resume_text, re.IGNORECASE)),
        "SQL/NoSQL": bool(re.search(r'sql|nosql|postgres|mysql|mongodb', resume_text, re.IGNORECASE))
    }
    
    print("\n=== Key Requirements Matched ===")
    for req, matched in requirements.items():
        status = "✓" if matched else "✗"
        print(f"{status} {req}")
    
    # Additional skills found
    additional_skills = []
    skills_to_check = [
        'docker', 'kubernetes', 'ci/cd', 'jenkins', 'git',
        'rest api', 'microservices', 'agile', 'scrum', 'tdd',
        'aws', 'azure', 'gcp', 'postgresql', 'mongodb', 'redis'
    ]
    
    for skill in skills_to_check:
        if re.search(rf'\b{re.escape(skill)}\b', resume_text, re.IGNORECASE):
            additional_skills.append(skill.title())
    
    if additional_skills:
        print("\n=== Additional Skills Found ===")
        print(", ".join(additional_skills))
    
    # Overall assessment
    print("\n=== Overall Assessment ===")
    if score >= 70:
        print("Excellent match! This candidate meets most of the job requirements.")
    elif score >= 50:
        print("Good match. The candidate has many of the required skills but may need some training.")
    else:
        print("Moderate match. Consider additional screening for this candidate.")
    
    print("\n=== Recommendation ===")
    if score >= 60:
        print("✅ STRONGLY RECOMMEND for interview")
    elif score >= 40:
        print("👍 CONSIDER for interview")
    else:
        print("❌ MAY NOT BE A GOOD FIT based on resume screening")
    
    # Save detailed report to file
    output_file = 'john_doe_analysis.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== Resume Analysis Report ===\n\n")
        f.write(f"Candidate: John Doe\n")
        f.write(f"Position: Senior Software Engineer\n")
        f.write(f"Match Score: {score}%\n\n")
        
        f.write("=== Key Requirements Matched ===\n")
        for req, matched in requirements.items():
            status = "✓" if matched else "✗"
            f.write(f"{status} {req}\n")
        
        if additional_skills:
            f.write("\n=== Additional Skills Found ===\n")
            f.write(", ".join(additional_skills) + "\n")
        
        f.write("\n=== Overall Assessment ===\n")
        if score >= 70:
            f.write("Excellent match! This candidate meets most of the job requirements.\n")
        elif score >= 50:
            f.write("Good match. The candidate has many of the required skills but may need some training.\n")
        else:
            f.write("Moderate match. Consider additional screening for this candidate.\n")
        
        f.write("\n=== Recommendation ===\n")
        if score >= 60:
            f.write("✅ STRONGLY RECOMMEND for interview")
        elif score >= 40:
            f.write("👍 CONSIDER for interview")
        else:
            f.write("❌ MAY NOT BE A GOOD FIT based on resume screening")
    
    print(f"\nDetailed analysis saved to {output_file}")

if __name__ == "__main__":
    main()
