#!/usr/bin/env python3
"""
Test script for the resume screening API with authentication.
This script will test the API endpoint with proper authentication using a PDF file.
"""

import requests
import json
import os
import sys
from pathlib import Path
import tempfile

def create_test_pdf():
    """Create a simple test PDF file"""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    
    # Create a temporary PDF file
    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    
    doc = SimpleDocTemplate(temp_file.name, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Add content to PDF
    story.append(Paragraph("John Doe", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Software Engineer", styles['Heading2']))
    story.append(Paragraph("john.doe@email.com | (555) 123-4567", styles['Normal']))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Professional Experience", styles['Heading2']))
    story.append(Paragraph("<b>Senior Python Developer</b> - Tech Corp (2020-2023)", styles['Normal']))
    story.append(Paragraph("• Flask and Django web application development", styles['Normal']))
    story.append(Paragraph("• SQL database design and optimization", styles['Normal']))
    story.append(Paragraph("• Machine learning model implementation", styles['Normal']))
    story.append(Paragraph("• Team lead for 5 developers", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Skills", styles['Heading2']))
    story.append(Paragraph("Python, Flask, Django, SQL, Machine Learning, Git, AWS", styles['Normal']))
    
    doc.build(story)
    return temp_file.name

def test_api_with_auth():
    """Test the API with authentication"""
    
    # Base URL
    base_url = "http://localhost:5000"
    
    # Create a test session
    session = requests.Session()
    
    # First, let's try to register a test user
    print("Attempting to register test user...")
    register_data = {
        'username': 'testuser2',
        'email': 'test2@example.com',
        'password': 'testpassword123'
    }
    
    try:
        response = session.post(f"{base_url}/register", json=register_data)
        print(f"Registration response: {response.status_code}")
        if response.status_code == 200:
            print("Registration successful!")
        else:
            print(f"Registration response: {response.text}")
    except Exception as e:
        print(f"Registration failed: {e}")
    
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
    
    try:
        # Create test PDF
        print("Creating test PDF...")
        test_pdf_path = create_test_pdf()
        print(f"Test PDF created at: {test_pdf_path}")
        
        # Prepare files for upload
        files = {
            'resume': ('test_resume.pdf', open(test_pdf_path, 'rb'), 'application/pdf')
        }
        
        data = {
            'job_description': job_description
        }
        
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
                        print(f"Details: {json.dumps(first_result.get('details', {}), indent=2)}")
                        
                        # Check if score is 0
                        if first_result['match_score'] == 0:
                            print("\n=== WARNING: MATCH SCORE IS 0% ===")
                            print("This could indicate:")
                            print("1. Empty resume text after parsing")
                            print("2. Empty job description")
                            print("3. No matching keywords")
                            print("4. Error in score calculation")
                    else:
                        print("\n=== NO MATCH_SCORE IN RESULT ===")
                        print(f"Available keys: {list(first_result.keys())}")
                        print(f"Full result: {first_result}")
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
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        if 'test_pdf_path' in locals() and os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)
            print(f"Cleaned up test PDF: {test_pdf_path}")
        print("\nTest completed!")

if __name__ == "__main__":
    test_api_with_auth()