import re
import pickle
from typing import List, Dict
import urllib.parse
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
nltk.download('stopwords', quiet=True)
from nltk.corpus import stopwords
import numpy as np

class JobLegitimacyChecker:
    RED_FLAGS = [
        'no experience needed', 'guaranteed income', 'pay upfront',
        'wire transfer', 'too good to be true', 'urgent hiring',
        'no interview required', 'work from home, earn instantly',
        'easy money', 'no skills required'
    ]
    
    SUSPICIOUS_PATTERNS = [
        r'\$\d+k.*per.*week',  # Unrealistic salary claims
        r'earn.*\$\d+.*hour',  # Suspicious hourly rate promises
        r'(western\s*union|money\s*gram)',  # Suspicious payment methods
        r'need.*bank.*details',  # Requests for sensitive financial info
        r'instant.*payment',
        r'no.*investment'
    ]
    
    VERIFIED_JOB_BOARDS = [
        'linkedin.com/jobs', 'indeed.com', 'glassdoor.com', 'monster.com',
        'ziprecruiter.com', 'dice.com', 'careerbuilder.com', 'google.com/jobs',
        'hired.com', 'angel.co', 'simplyhired.com'
    ]

    def __init__(self, tfidf_path="tfidf_vectorizer.pkl", model_path="model.pkl"):
        try:
            with open(tfidf_path, "rb") as vec_file:
                self.tfidf_vectorizer = pickle.load(vec_file)
            with open(model_path, "rb") as model_file:
                self.model = pickle.load(model_file)
        except FileNotFoundError:
            # Fallback: Create a new vectorizer and train a dummy model if files not found
            self.tfidf_vectorizer = TfidfVectorizer(stop_words='english')
            from sklearn.linear_model import LogisticRegression
            self.model = LogisticRegression()

    def validate_url(self, url: str) -> bool:
        try:
            result = urllib.parse.urlparse(url)
            return all([result.scheme, result.netloc]) and len(result.netloc) > 3
        except Exception:
            return False

    def analyze_job_description(self, description: str) -> dict:
        description_lower = description.lower()
        analysis = {
            "red_flag_count": 0, 
            "suspicious_pattern_count": 0,
            "risk_score": 0
        }
        
        # Check for red flags
        red_flag_matches = [flag for flag in self.RED_FLAGS if flag in description_lower]
        analysis["red_flag_count"] = len(red_flag_matches)
        
        # Check for suspicious patterns
        suspicious_matches = [
            pattern for pattern in self.SUSPICIOUS_PATTERNS 
            if re.search(pattern, description_lower)
        ]
        analysis["suspicious_pattern_count"] = len(suspicious_matches)
        
        # Calculate risk score
        analysis["risk_score"] = min((analysis["red_flag_count"] * 20 + 
                                      analysis["suspicious_pattern_count"] * 15), 90)
        
        return analysis

    def verify_job_source(self, job_url: str) -> bool:
        try:
            parsed_url = urllib.parse.urlparse(job_url)
            domain = parsed_url.netloc.lower().replace('www.', '')
            return any(board in domain for board in self.VERIFIED_JOB_BOARDS)
        except Exception:
            return False

    def preprocess_and_predict(self, data: Dict[str, str]) -> int:
        def preprocess_text(text: str) -> str:
            if not text:
                return ""
            text = text.lower()
            text = re.sub(r'\d+', '', text)
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s]', '', text)
            text = [word for word in text.split() if word not in stopwords.words('english')]
            return ' '.join(text)

        # Preprocess and combine text
        preprocessed_data = {key: preprocess_text(value) for key, value in data.items()}
        combined_text = ' '.join(preprocessed_data.values())
        
        # Predict using the ML model
        try:
            tfidf_features = self.tfidf_vectorizer.transform([combined_text])
            prediction = self.model.predict(tfidf_features)
            return prediction[0]
        except Exception:
            # Fallback prediction if model fails
            return 0  # Suspicious