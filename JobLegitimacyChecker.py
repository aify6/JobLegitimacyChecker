import requests
from bs4 import BeautifulSoup
import numpy as np
from sklearn.naive_bayes import GaussianNB
import pandas as pd
import time
import re
from urllib.parse import quote
import json

class JobLegitimacyChecker:
    def __init__(self):
        """Initialize the checker with a more robust ML model"""
        # Sample training data - expanded from original
        self.data = np.array([
            # [LinkedIn, Twitter, Glassdoor, GovReg, ValidEmail, PhysicalAddress]
            [1, 1, 1, 1, 1, 1],  # Legitimate company
            [1, 1, 1, 1, 1, 0],  # Legitimate company
            [1, 1, 0, 1, 1, 1],  # Legitimate company
            [1, 0, 1, 1, 1, 1],  # Legitimate company
            [0, 0, 0, 0, 0, 0],  # Fraudulent
            [0, 1, 0, 0, 0, 0],  # Fraudulent
            [0, 0, 0, 0, 1, 0],  # Fraudulent
            [1, 0, 0, 0, 0, 0],  # Fraudulent
            [0, 0, 0, 0, 0, 1],  # Fraudulent
        ])
        self.labels = np.array([1, 1, 1, 1, 0, 0, 0, 0, 0])  # 1 = Legitimate, 0 = Fraudulent

        # Initialize and train the model
        self.model = GaussianNB()
        self.model.fit(self.data, self.labels)

        # Initialize session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })

    def check_linkedin_presence(self, company_name):
        """Check company's LinkedIn presence using Google search"""
        try:
            search_query = f"{company_name} site:linkedin.com/company"
            response = self.session.get(
                f"https://www.google.com/search?q={quote(search_query)}",
                timeout=10
            )

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('div', class_='g')

                for result in results:
                    if result.find('a', href=re.compile(r'linkedin\.com/company')):
                        return True
            return False
        except Exception as e:
            print(f"LinkedIn check error: {e}")
            return False

    def check_X_presence(self, company_name):
        """Check company's Twitter/X presence using Google search"""
        try:
            search_query = f"{company_name} site:twitter.com"
            response = self.session.get(
                f"https://www.google.com/search?q={quote(search_query)}",
                timeout=10
            )

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('div', class_='g')

                for result in results:
                    if result.find('a', href=re.compile(r'twitter\.com/')):
                        return True
            return False
        except Exception as e:
            print(f"Twitter check error: {e}")
            return False

    def check_glassdoor_rating(self, company_name):
        """
        Check company's Glassdoor rating using a more robust approach
        Returns:
            float or None: Company rating if found, None otherwise
        """
        try:
            # Try multiple search patterns to increase chances of finding the rating
            search_queries = [
                f"{company_name} site:glassdoor.com reviews",
                f"{company_name} glassdoor rating reviews",
                f"{company_name} reviews glassdoor employees"
            ]

            for search_query in search_queries:
                response = self.session.get(
                    f"https://www.google.com/search?q={quote(search_query)}",
                    timeout=10
                )

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Try multiple patterns for finding ratings
                    patterns = [
                        r'(\d+(\.\d+)?)\s*out of\s*5',  # "4.2 out of 5"
                        r'Rating:\s*(\d+(\.\d+)?)',      # "Rating: 4.2"
                        r'(\d+(\.\d+)?)/5',              # "4.2/5"
                        r'(\d+(\.\d+)?)\s+stars?'        # "4.2 stars"
                    ]

                    # Look in different elements
                    for element in [soup.get_text(), str(soup)]:
                        text = element.lower()
                        for pattern in patterns:
                            rating_match = re.search(pattern, text)
                            if rating_match:
                                rating = float(rating_match.group(1))
                                # Validate rating is within expected range
                                if 0 <= rating <= 5:
                                    return rating

                    # Try finding rating in structured data
                    script_tags = soup.find_all('script', type='application/ld+json')
                    for script in script_tags:
                        try:
                            data = json.loads(script.string)
                            if isinstance(data, dict):
                                rating = data.get('aggregateRating', {}).get('ratingValue')
                                if rating is not None:
                                    rating = float(rating)
                                    if 0 <= rating <= 5:
                                        return rating
                        except (json.JSONDecodeError, AttributeError):
                            continue

                # Add delay between requests to avoid rate limiting
                time.sleep(1)

            return None

        except Exception as e:
            print(f"Glassdoor check error: {e}")
            return None

        finally:
            # Always ensure we have a small delay after completing checks
            time.sleep(0.5)

    def check_government_registration(self, company_name, country='US'):
        """
        Check company's government registration
        Note: This is a simplified version. For production use, you'd want to:
        1. Add specific APIs for different countries
        2. Include multiple database checks
        3. Add proper authentication
        """
        try:
            # List of legitimate business registries to check
            registries = {
                'US': [
                    'https://www.sec.gov/edgar/searchedgar/companysearch',
                    'https://www.sam.gov/SAM/pages/public/searchRecords/search.jsf'
                ],
                'UK': [
                    'https://find-and-update.company-information.service.gov.uk'
                ],
                # Add more countries as needed
            }

            if country not in registries:
                return "Unknown"

            # Search for company registration using Google
            search_query = f"{company_name} {country} business registration corporation LLC"
            response = self.session.get(
                f"https://www.google.com/search?q={quote(search_query)}",
                timeout=10
            )

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text().lower()

                # Look for registration indicators
                reg_indicators = [
                    'incorporated',
                    'llc',
                    'corporation',
                    'registered',
                    'business entity',
                    'ein:',
                    'registration number'
                ]

                if any(indicator in text for indicator in reg_indicators):
                    return "Registered"

            return "No Registration Found"

        except Exception as e:
            print(f"Government registration check error: {e}")
            return "Check Failed"

    def check_job_legitimacy(self, company_name, job_title, job_description):
        """Main method to check job legitimacy"""
        # Initialize results dictionary
        results = {
            'company_name': company_name,
            'job_title': job_title,
            'checks': {},
            'prediction': None,
            'confidence': None,
            'risk_factors': []
        }

        # Perform all checks
        print("Checking LinkedIn presence...")
        linkedin_present = self.check_linkedin_presence(company_name)

        print("Checking X presence...")
        X_present = self.check_X_presence(company_name)

        print("Checking Glassdoor rating...")
        glassdoor_rating = self.check_glassdoor_rating(company_name)

        print("Checking government registration...")
        gov_registration = self.check_government_registration(company_name)

        # Store check results
        results['checks'] = {
            'linkedin_presence': linkedin_present,
            'X_presence': X_present,
            'glassdoor_rating': glassdoor_rating,
            'government_registration': gov_registration
        }

        # Check for red flags in job description
        red_flags = [
            'upfront payment',
            'processing fee',
            'wire transfer',
            'bank details',
            'social security',
            'passport copy',
            'investment required'
        ]

        job_description_lower = job_description.lower()
        for flag in red_flags:
            if flag in job_description_lower:
                results['risk_factors'].append(f"Warning: Job posting mentions '{flag}'")

        # Prepare data for ML model
        has_glassdoor = 1 if glassdoor_rating is not None else 0
        has_gov_reg = 1 if gov_registration == "Registered" else 0

        # Create feature vector
        features = np.array([[
            int(linkedin_present),
            int(X_present),
            has_glassdoor,
            has_gov_reg,
            1 if '@' in job_description else 0,  # Check for contact email
            1 if any(word in job_description.lower() for word in ['address', 'location', 'office']) else 0
        ]])

        # Get prediction and probability
        prediction = self.model.predict(features)[0]
        probabilities = self.model.predict_proba(features)[0]

        # Store prediction results
        results['prediction'] = 'Legitimate' if prediction == 1 else 'Suspicious'
        results['confidence'] = float(max(probabilities))

        # Add additional risk factors based on checks
        if not linkedin_present and not X_present:
            results['risk_factors'].append("No social media presence detected")
        if not has_gov_reg:
            results['risk_factors'].append("No clear government registration found")
        if glassdoor_rating is not None and glassdoor_rating < 2.5:
            results['risk_factors'].append("Low Glassdoor rating")

        return results

def main():
    # Initialize the checker
    checker = JobLegitimacyChecker()

    # Get input from user
    print("\n=== Job Legitimacy Checker ===")
    company_name = input("Enter company name: ")
    job_title = input("Enter job title: ")
    job_description = input("Enter job description (or press Enter to use default): ")

    # Use default job description if none provided
    if not job_description:
        job_description = """
        We are seeking a talented professional to join our team.
        Requirements:
        - 3+ years of relevant experience
        - Bachelor's degree
        - Strong communication skills

        Benefits:
        - Competitive salary
        - Health insurance
        - Professional development
        """

    # Run the check
    print("\nAnalyzing... This may take a few moments...\n")
    results = checker.check_job_legitimacy(company_name, job_title, job_description)

    # Print results
    print("\n=== Results ===")
    print(f"Company: {results['company_name']}")
    print(f"Job Title: {results['job_title']}")
    print(f"Prediction: {results['prediction']}")
    print(f"Confidence: {results['confidence']:.2%}")

    print("\nChecks Performed:")
    for check, result in results['checks'].items():
        print(f"- {check}: {result}")

    if results['risk_factors']:
        print("\nRisk Factors:")
        for factor in results['risk_factors']:
            print(f"- {factor}")

    print("\nNote: This is a preliminary assessment. Always conduct thorough research before sharing sensitive information or making employment decisions.")

if __name__ == "__main__":
    main()