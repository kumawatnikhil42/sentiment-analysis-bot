from flask import Flask, render_template, request
from PyPDF2 import PdfReader
from docx import Document
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import re
import numpy as np

nltk.download('punkt')
nltk.download('vader_lexicon')

app = Flask(__name__)

def extract_text_from_pdf(file):
    text = ''
    pdf_reader = PdfReader(file)
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text

def extract_text_from_docx(file):
    doc = Document(file)
    text = ''
    for paragraph in doc.paragraphs:
        text += paragraph.text + '\n'  # Ensure each paragraph is separated by newline
    return text

def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()
    # Remove special characters and numbers
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return text



def analyze_sentiment_for_paragraphs(text):
    paragraphs = text.split('\n\n')
    sid = SentimentIntensityAnalyzer()
    positive_scores = []
    negative_scores = []
    for paragraph in paragraphs:
        if paragraph.strip():
            scores = sid.polarity_scores(paragraph)
            if scores['compound'] > 0:
                positive_scores.append(scores['compound'])
            elif scores['compound'] < 0:
                negative_scores.append(scores['compound'])
    overall=sum(positive_scores)-sum(negative_scores)
    print(overall)
    positive_confidence = sum(positive_scores)/overall
    print(positive_confidence)
    negative_confidence = (sum(negative_scores)/overall)
    print(negative_confidence)
    return positive_confidence * 100, -(negative_confidence * 100)

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files['file']
    if file.filename.endswith('.pdf'):
        text = extract_text_from_pdf(file)
    elif file.filename.endswith('.docx'):
        text = extract_text_from_docx(file)
    else:
        return "Unsupported file format. Please upload a PDF or DOCX file."
    
    preprocessed_text = preprocess_text(text)
    paragraphs = preprocessed_text.split('\n\n')
    
    positive_clauses = []
    negative_clauses = []
    
    sid = SentimentIntensityAnalyzer()
    for paragraph in paragraphs:
        sentiment_score = sid.polarity_scores(paragraph)['compound']
        if sentiment_score > 0:
            positive_clauses.append(paragraph)
        elif sentiment_score < 0:
            negative_clauses.append(paragraph)
    
    positive_confidence, negative_confidence = analyze_sentiment_for_paragraphs(preprocessed_text)
    
    result = {
        "positive_confidence": positive_confidence,
        "negative_confidence": negative_confidence,
        "positive_clauses": positive_clauses,
        "negative_clauses": negative_clauses
    }
    
    return render_template('results.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
