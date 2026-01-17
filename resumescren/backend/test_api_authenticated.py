#!/usr/bin/env python3
"""
Test script for the resume screening API with authentication.
This script will test the API endpoint with proper authentication.
"""

import requests
import json
import os
import sys
from pathlib import Path

def test_api_with_auth():
    """Test the API with authentication"""
    
    # Base URL
    base_url = "http://localhost:5000"
    
    # Create a test session
    session = requests.Session()
    
    # First, let's try to register a test user
    print("Attempting to register test user...")
    register_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpassword123'
    }
    
    try:
        response = session.post(f"{base_url}/register", json=register_data)
        print(f"Registration response: {response.status_code}")
        if response.status_code == 200:
            print("Registration successful!")
        else:
            print(f"Registration response: {response.text}")
            # Try to login instead
            print("Attempting to login...")
            login_data = {
                'username': 'testuser',
                'password': 'testpassword123'
            }
            response = session.post(f"{base_url}/login", json=login_data)
            print(f"Login response: {response.status_code}")
            print(f"Login response text: {response.text}")
    except Exception as e:
        print(f"Registration/Login failed: {e}")
    
    # Test the API endpoint
    print("\n=== Testing /api/upload endpoint ===")
    
    # Prepare test data
    job_description = """
    We are looking for a Software Engineer with experience in:
    - Python programming
    - Web development (Flask/Django)
    - Database management (SQL)
    - Machine learning concepts
    - Team collaboration
    """
    
    # Create a simple test resume file
    test_resume_content = """
    John Doe
    Software Engineer
    Email: john.doe@email.com
    Phone: (555) 123-4567
    
    Experience:
    - Senior Python Developer at Tech Corp (2020-2023)
    - Flask and Django web application development
    - SQL database design and optimization
    - Machine learning model implementation
    - Team lead for 5 developers
    
    Skills:
    Python, Flask, Django, SQL, Machine Learning, Git, AWS
    """
    
    # Write test resume to file
    test_resume_path = "test_resume.txt"
    with open(test_resume_path, 'w') as f:
        f.write(test_resume_content)
    
    # Prepare files for upload
    files = {
        'resume': ('test_resume.txt', open(test_resume_path, 'rb'), 'text/plain')
    }
    
    data = {
        'job_description': job_description
    }
    
    try:
        print("Sending request to /api/upload...")
        response = session.post(f"{base_url}/api/upload", files=files, data=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content Type: {response.headers.get('content-type', 'Not specified')}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("=== API Response ===")
                print(json.dumps(result, indent=2))
                
                # Check the results
                if 'results' in result and result['results']:
                    first_result = result['results'][0]
                    if 'match_score' in first_result:
                        print(f"\n=== MATCH SCORE FOUND: {first_result['match_score']}% ===")
                        print(f"Details: {first_result.get('details', 'No details')}")
                    else:
                        print("\n=== NO MATCH_SCORE IN RESULT ===")
                        print(f"Available keys: {list(first_result.keys())}")
                else:
                    print("\n=== NO RESULTS FOUND ===")
                    
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON: {e}")
                print(f"Response text: {response.text[:500]}...")
        else:
            print(f"Request failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
    except Exception as e:
        print(f"Request failed: {e}")
    
    finally:
        # Clean up
        if os.path.exists(test_resume_path):
            os.remove(test_resume_path)
        print("\nTest completed!")

if __name__ == "__main__":
    test_api_with_auth()