#!/usr/bin/env python3
"""
Test script with multiple resumes to demonstrate the comparison feature.
"""

import requests
import json
import os
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def create_resume_pdf(content, filename):
    """Create a PDF with resume content"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    
    doc = SimpleDocTemplate(temp_file.name, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Add content to PDF
    lines = content.strip().split('\n')
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

def test_multiple_resumes():
    """Test the API with multiple resumes to show comparison"""
    
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
    
    # Test the API endpoint with multiple resumes
    print("\n=== Testing with Multiple Resumes ===")
    
    # Job description
    job_description = """
    We are looking for a Software Engineer with experience in:
    - Python programming and web development
    - Machine learning and data science
    - Database management and SQL
    - Cloud technologies (AWS, Docker)
    - Team collaboration and agile methodologies
    - Full-stack development (React, Node.js)
    """
    
    # Multiple resume contents with different match levels
    resumes = [
        {
            "name": "High Match Resume",
            "content": """
JOHN SMITH
Software Engineer
Email: john.smith@email.com | Phone: (555) 123-4567

PROFESSIONAL SUMMARY
Experienced Software Engineer with 5+ years in Python, React, and AWS cloud development. Strong background in machine learning, SQL databases, and agile team collaboration.

TECHNICAL SKILLS
Programming Languages: Python, JavaScript, TypeScript, React, Node.js
Cloud & DevOps: AWS (EC2, S3, Lambda), Docker, Kubernetes, CI/CD
Databases: PostgreSQL, MySQL, MongoDB, Redis
Machine Learning: scikit-learn, TensorFlow, pandas, numpy

PROFESSIONAL EXPERIENCE
Senior Software Engineer | TechCorp | 2021-Present
• Developed Python web applications using Flask and Django frameworks
• Built React frontend applications with RESTful API integration
• Implemented machine learning models for data analysis and prediction
• Managed SQL databases and optimized query performance
• Led agile development teams and collaborated on software projects
• Deployed applications on AWS cloud using Docker containers

Software Engineer | DataTech Solutions | 2019-2021
• Developed full-stack web applications using Python and React
• Implemented database solutions with PostgreSQL and MongoDB
• Collaborated with cross-functional teams in agile environment
• Built machine learning pipelines for data processing

EDUCATION
Bachelor of Science in Computer Science | University of Technology | 2019
"""
        },
        {
            "name": "Medium Match Resume", 
            "content": """
JANE DOE
Web Developer
Email: jane.doe@email.com | Phone: (555) 987-6543

PROFESSIONAL SUMMARY
Web Developer with 3 years of experience in frontend development using HTML, CSS, and JavaScript. Experience with React and some backend development.

TECHNICAL SKILLS
Programming Languages: JavaScript, HTML, CSS, React, Node.js
Databases: MySQL, basic SQL knowledge
Tools: Git, VS Code, Agile methodologies

PROFESSIONAL EXPERIENCE
Frontend Developer | WebSolutions Inc | 2021-Present
• Developed responsive web applications using React and JavaScript
• Collaborated with design teams to implement user interfaces
• Used Git for version control and team collaboration

Junior Developer | StartupXYZ | 2020-2021
• Assisted in web development projects using HTML, CSS, and JavaScript
• Basic database management with MySQL
• Participated in agile team meetings

EDUCATION
Associate Degree in Web Development | Community College | 2020
"""
        },
        {
            "name": "Low Match Resume",
            "content": """
ROBERT JOHNSON
Marketing Manager
Email: robert.johnson@email.com | Phone: (555) 456-7890

PROFESSIONAL SUMMARY
Experienced Marketing Manager with 7 years in digital marketing, brand management, and customer engagement. Proven track record in social media marketing and campaign management.

TECHNICAL SKILLS
Marketing Tools: Google Analytics, Facebook Ads Manager, MailChimp
Analytics: Data analysis, market research, customer insights
Communication: Public speaking, team leadership, project management

PROFESSIONAL EXPERIENCE
Senior Marketing Manager | BrandCorp | 2018-Present
• Managed digital marketing campaigns across multiple platforms
• Analyzed customer data and market trends
• Led marketing teams and coordinated with sales departments
• Developed brand strategies and customer engagement initiatives

Marketing Coordinator | RetailSolutions | 2015-2018
• Assisted in marketing campaign development
• Managed social media accounts and content creation
• Conducted market research and competitor analysis
• Coordinated with external vendors and agencies

EDUCATION
Bachelor of Business Administration | Marketing University | 2015
"""
        }
    ]
    
    temp_files = []
    try:
        # Create PDFs for all resumes
        print("Creating resume PDFs...")
        files_data = []
        for resume in resumes:
            temp_path = create_resume_pdf(resume["content"], resume["name"])
            temp_files.append(temp_path)
            files_data.append((resume["name"], temp_path))
            print(f"Created: {resume['name']}")
        
        # Prepare files for upload
        files = []
        for name, temp_path in files_data:
            files.append(('resume', (f'{name.lower().replace(" ", "_")}.pdf', open(temp_path, 'rb'), 'application/pdf')))
        
        data = {
            'job_description': job_description
        }
        
        print(f"\nSending {len(files)} resumes to /api/upload...")
        response = session.post(f"{base_url}/api/upload", files=files, data=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content Type: {response.headers.get('content-type', 'Not specified')}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("\n=== 🎯 MULTIPLE RESUME RESULTS ===")
                print(json.dumps(result, indent=2))
                
                # Analyze results
                if 'results' in result and result['results']:
                    results = result['results']
                    print(f"\n📊 PROCESSED {len(results)} RESUMES:")
                    
                    # Sort by match score (descending)
                    sorted_results = sorted(results, key=lambda x: x.get('match_score', 0), reverse=True)
                    
                    for i, res in enumerate(sorted_results, 1):
                        if res.get('success'):
                            score = res.get('match_score', 0)
                            filename = res.get('filename', 'Unknown')
                            print(f"\n{i}. {filename}")
                            print(f"   🎯 Match Score: {score}%")
                            
                            if score >= 40:
                                print("   ✅ HIGH MATCH")
                            elif score >= 20:
                                print("   ⚠️  MEDIUM MATCH") 
                            else:
                                print("   ❌ LOW MATCH")
                                
                            # Show details
                            details = res.get('details', {})
                            matched_terms = details.get('matched_terms', [])
                            if matched_terms:
                                print(f"   📋 Matched: {', '.join(matched_terms[:5])}")
                        else:
                            print(f"\n❌ Failed: {res.get('filename', 'Unknown')}")
                            print(f"   Error: {res.get('error', 'Unknown error')}")
                    
                    # Show best match
                    if sorted_results and sorted_results[0].get('success'):
                        best_score = sorted_results[0].get('match_score', 0)
                        best_filename = sorted_results[0].get('filename', 'Unknown')
                        print(f"\n🏆 BEST MATCH: {best_filename} with {best_score}%")
                        
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
        for temp_path in temp_files:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    print(f"✅ Cleaned up: {temp_path}")
                except:
                    pass
        print("\n🎯 Multi-resume test completed!")

if __name__ == "__main__":
    test_multiple_resumes()