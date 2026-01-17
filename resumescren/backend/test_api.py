#!/usr/bin/env python3

import requests
import json

def test_api():
    """Test the API to see what data structure is being returned"""
    
    # Test data
    job_description = "We are looking for a skilled software engineer with Python and JavaScript experience."
    
    # Create a simple test resume content
    test_resume_content = """
    John Doe
    Software Engineer
    Email: john.doe@email.com
    Phone: (555) 123-4567
    
    EXPERIENCE:
    Senior Software Engineer at Tech Corp (2020-Present)
    - Developed Python applications and JavaScript web interfaces
    - Worked with React and Node.js frameworks
    - Database management with PostgreSQL and MongoDB
    
    SKILLS:
    Python, JavaScript, React, Node.js, PostgreSQL, MongoDB, Git, Docker
    
    EDUCATION:
    Bachelor of Science in Computer Science, University of Technology, 2019
    """
    
    # Create a simple test file (we'll simulate the file upload)
    files = {
        'resume': ('test_resume.txt', test_resume_content.encode(), 'text/plain')
    }
    
    data = {
        'job_description': job_description
    }
    
    try:
        response = requests.post('http://localhost:5000/api/upload', 
                               files=files, 
                               data=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content Type: {response.headers.get('content-type')}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response structure:")
            print(json.dumps(result, indent=2))
            
            if 'results' in result and result['results']:
                first_result = result['results'][0]
                print(f"\nFirst result structure:")
                print(json.dumps(first_result, indent=2))
                
                print(f"\nMatch score: {first_result.get('match_score', 'NOT FOUND')}")
                print(f"Resume data: {first_result.get('resume_data', 'NOT FOUND')}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Error testing API: {e}")

if __name__ == "__main__":
    test_api()