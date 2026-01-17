# AI-Powered Resume Screening Tool Project Report

## 1. Objective
To automate and enhance the resume screening process using AI, providing recruiters with a fast, accurate, and data-driven method for shortlisting candidates based on job requirements.

## 2. Introduction
Recruitment is a critical function in organizations, but manual resume screening is time-consuming and prone to bias. Traditional keyword-based systems often miss context and relevant skills. This project leverages NLP and ML to intelligently analyze and rank resumes, improving both efficiency and fairness in hiring.

## 3. Problem Definition
Manual screening is repetitive, slow, and inconsistent. Existing automated tools are limited to keyword matching, which fails to capture the full scope of candidate capabilities. There is a need for a smarter, scalable solution that accurately matches resumes to job descriptions.

## 4. Proposed System
- Recruiters upload resumes (PDF/DOCX) and job descriptions.
- Backend extracts relevant information (skills, experience, education) using NLP.
- ML techniques compare extracted features with job requirements, generating a match score.
- Results and analytics are displayed in an interactive frontend.

## 5. System Architecture
- **Frontend:** React app for uploading resumes, entering job descriptions, and viewing results.
- **Backend:** Python Flask server for file handling, text extraction, and ML-based scoring.
- **Resume Parsing:** Uses PDF/DOCX parsers and simple entity recognition.
- **Matching:** TF-IDF vectorization and cosine similarity for scoring.

### Architecture Diagram

```
Recruiter (Web UI)
     |
     v
[React Frontend] <----> [Flask Backend] ----> [NLP/ML Modules]
     |                                 |
     |                                 +--> [PDF/DOCX Parser]
     |                                 +--> [Similarity Scorer]
     v
Results/Analytics
```

## 6. Conclusion
The AI-Powered Resume Screening Tool reduces human effort, increases accuracy, and brings transparency to the hiring process. By automating resume analysis and ranking, it enables recruiters to focus on high-value tasks and make data-driven decisions.

## 7. References
- scikit-learn documentation: https://scikit-learn.org/
- Flask documentation: https://flask.palletsprojects.com/
- pdfminer.six: https://github.com/pdfminer/pdfminer.six
- python-docx: https://python-docx.readthedocs.io/
- React: https://react.dev/

---
This report and the accompanying codebase are suitable for college submission and demonstration purposes.
