#!/usr/bin/env python3
"""
Test script using the user's actual resume content.
"""

import requests
import json
import os
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def create_resume_pdf():
    """Create a PDF with the user's actual resume content"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    
    doc = SimpleDocTemplate(temp_file.name, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # User's actual resume content
    resume_content = """
John Doe
Software Engineer
Email: john.doe@email.com | Phone: (555) 123-4567

PROFESSIONAL SUMMARY
Results-driven Software Engineer with 3+ years of experience in full-stack development, specializing in Python, JavaScript, and cloud technologies. Proven track record of delivering scalable web applications and implementing machine learning solutions. Passionate about clean code, agile methodologies, and continuous learning.

TECHNICAL SKILLS
Programming Languages: Python, JavaScript, TypeScript, Java, C++
Web Technologies: React, Node.js, Express.js, Flask, Django, HTML5, CSS3, RESTful APIs
Databases: MongoDB, PostgreSQL, MySQL, Redis
Cloud & DevOps: AWS (EC2, S3, Lambda), Docker, Kubernetes, Jenkins, Git, CI/CD
Tools & Frameworks: Git, VS Code, PyCharm, Jira, Agile/Scrum

PROFESSIONAL EXPERIENCE

Senior Software Engineer | TechCorp Solutions | Jan 2022 - Present
• Developed and maintained 5+ web applications using React and Node.js, serving 100K+ users
• Implemented RESTful APIs and integrated third-party services, improving system performance by 40%
• Led a team of 4 developers in agile development, delivering projects 20% faster
• Deployed applications on AWS cloud using Docker and Kubernetes

Software Engineer | InnovateTech | Jun 2020 - Dec 2021
• Built machine learning models using Python and scikit-learn for predictive analytics
• Designed and optimized SQL databases, reducing query response time by 30%
• Collaborated with cross-functional teams to deliver software solutions
• Participated in code reviews and implemented best practices

Junior Developer | StartupXYZ | May 2019 - May 2020
• Assisted in development of web applications using Python Flask framework
• Wrote unit tests and documentation for software modules
• Fixed bugs and implemented feature requests from clients

EDUCATION
Bachelor of Technology in Computer Science | University of Technology | 2019
GPA: 8.5/10 | Relevant Coursework: Data Structures, Algorithms, Machine Learning, Database Systems

CERTIFICATIONS
• AWS Certified Solutions Architect - Associate
• Python for Data Science - IBM
• Full Stack Web Development - Coursera

PROJECTS
E-Commerce Platform: Built a full-stack e-commerce application using MERN stack with payment integration and admin dashboard.
Weather Prediction App: Developed a machine learning model to predict weather patterns using historical data and Python.
Task Management System: Created a collaborative task management tool with real-time updates using React and Socket.io.
"""
    
    # Add content to PDF
    lines = resume_content.strip().split('\n')
    for line in lines:
        if line.strip():
            if line.isupper() and len(line) < 50:
                story.append(Paragraph(f"<b>{line}</b>", styles['Heading2']))
            elif line.startswith('•'):
                story.append(Paragraph(line, styles['Normal']))
            elif ':' in line and len(line) < 100:
                parts = line.split(':', 1)
                story.append(Paragraph(f"<b>{parts[0]}:</b>{parts[1]}", styles['Normal']))
            else:
                story.append(Paragraph(line, styles['Normal']))
            
            if line.strip() == '':
                story.append(Spacer(1, 6))
    
    doc.build(story)
    return temp_file.name

def test_with_real_resume():
    """Test the API with the user's actual resume content"""
    
    # Base URL
    base_url = "http://localhost:5000"
    
    # Create a test session
    session = requests.Session()
    
    # Login with existing credentials
    print("Logging in...")
    login_data = {
        'username': 'testuser',
        'password': 'testpassword123'
    }
    
    try:
        response = session.post(f"{base_url}/login", json=login_data)
        if response.status_code == 200:
            print("Login successful!")
        else:
            print(f"Login failed: {response.text}")
            return
    except Exception as e:
        print(f"Login failed: {e}")
        return
    
    # Test the API endpoint with real resume
    print("\n=== Testing with Real Resume Content ===")
    
    # Job description from the user's previous input
    job_description = """
    We are looking for a Software Engineer with experience in:
    - Python programming and web development
    - Machine learning and data science
    - Database management and SQL
    - Cloud technologies (AWS, Docker)
    - Team collaboration and agile methodologies
    - Full-stack development (React, Node.js)
    """
    
    temp_pdf_path = None
    try:
        # Create resume PDF
        print("Creating resume PDF...")
        temp_pdf_path = create_resume_pdf()
        print(f"Resume PDF created at: {temp_pdf_path}")
        
        # Prepare files for upload
        with open(temp_pdf_path, 'rb') as f:
            files = {
                'resume': ('john_doe_resume.pdf', f, 'application/pdf')
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
                            score = first_result['match_score']
                            print(f"\n=== 🎯 ATS MATCH SCORE: {score}% ===")
                            
                            if score == 0:
                                print("\n⚠️  WARNING: MATCH SCORE IS 0%")
                                print("Possible causes:")
                                print("1. Resume text extraction failed")
                                print("2. No relevant keywords found")
                                print("3. Job description too generic")
                                print("4. Resume format issues")
                            elif score < 30:
                                print("\n📊 Low match score - consider improving resume keywords")
                            elif score < 60:
                                print("\n📊 Moderate match - some alignment with job requirements")
                            else:
                                print("\n🎉 High match score - good alignment with job requirements!")
                                
                            # Show details
                            details = first_result.get('details', {})
                            print(f"\n📋 Match Details:")
                            print(f"Matched Terms: {', '.join(details.get('matched_terms', []))}")
                            print(f"Missing Terms: {', '.join(details.get('missing_terms', []))}")
                        else:
                            print("\n❌ NO MATCH_SCORE IN RESULT")
                            print(f"Available keys: {list(first_result.keys())}")
                    else:
                        print("\n❌ NO RESULTS FOUND")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON: {e}")
                    print(f"Response text: {response.text[:500]}...")
            else:
                print(f"❌ Request failed with status {response.status_code}")
                print(f"Response: {response.text[:500]}...")
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
                print(f"✅ Cleaned up test PDF: {temp_pdf_path}")
            except:
                pass
        print("\n🎯 Test completed!")

if __name__ == "__main__":
    test_with_real_resume()