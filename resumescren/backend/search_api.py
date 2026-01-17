import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from resume_parser import parse_resume

app = Flask(__name__)
CORS(app)

DATASET_DIR = r'c:/Users/arjun/OneDrive/Desktop/resumescren/dataset/dataset/data/data'

@app.route('/api/search', methods=['GET'])
def search_resumes():
    keyword = request.args.get('keyword', '').lower()
    results = []
    for root, _, files in os.walk(DATASET_DIR):
        for file in files:
            if file.lower().endswith('.pdf'):
                path = os.path.join(root, file)
                parsed = parse_resume(path)
                text = parsed.get('raw_text', '').lower()
                if keyword in text:
                    results.append({'filename': file, 'path': path, 'extract': text[:500]})
    return jsonify({'matches': results})

if __name__ == '__main__':
    app.run(debug=True)
