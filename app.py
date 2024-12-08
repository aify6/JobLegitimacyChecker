import streamlit as st
import google.generativeai as genai
import re
from joblegitchecker2 import JobLegitimacyChecker

# Configure Generative AI
def setup_generative_ai(api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    return model 

# Configure page settings
st.set_page_config(
    page_title="Job Legitimacy Checker",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS styling
st.markdown("""
    <style>
        .banner-image { width: 100%; object-fit: cover; border-radius: 10px; margin-bottom: 20px; }
        .confidence-score { font-size: 1.2rem; font-weight: bold; color: #007BFF; }
        .section-header { font-size: 2.0rem; font-weight: bold; margin-top: 20px; color: #444444; }
        .risk-warning { background-color: #FF0000; color: #FFFFFF; border-radius: 5px; padding: 10px; margin: 10px 0; }
        footer { text-align: center; padding: 10px; font-size: 0.85rem; color: #555555; }
    </style>
    """, unsafe_allow_html=True)

# Main functionality
def main(): 
    st.title("🛡️ Job Legitimacy Checker")
    st.write("Analyze job postings for legitimacy using AI and data-driven techniques.")
    st.image(r"762887_Job1-01.jpg", caption="Ensure safe job applications!", use_container_width=True)

    with st.sidebar:
        st.header("🔍 Input Job Details")
        company_name = st.text_input("Company Name", placeholder="e.g., Acme Corporation")
        job_title = st.text_input("Job Title", placeholder="e.g., Software Engineer")
        job_description = st.text_area("Job Description", placeholder="Paste the job description here...")
        job_url = st.text_input("Job URL", placeholder="e.g., https://example.com/job123")
        company_profile = st.text_input("Company Profile", placeholder="Leading tech company")
        requirements = st.text_area("Job Requirements", placeholder="Enter the job requirements")
        benefits = st.text_area("Job Benefits", placeholder="Enter the job benefits")
        
        analyze_button = st.button("Analyze Job")

    # Main analysis logic
    if analyze_button:
        # Validate inputs
        if not all([company_name, job_title, job_description, job_url]):
            st.warning("Please fill in all required fields.")
            return

        try:
            # Initialize services
            job_verifier = JobLegitimacyChecker()
            
            # Setup Generative AI
            gemini_model = setup_generative_ai(st.secrets.get("GEMINI_API_KEY"))

            # Run checks
            validate_url = job_verifier.validate_url(job_url)
            desc_analysis = job_verifier.analyze_job_description(job_description)
            in_verified_job_board = job_verifier.verify_job_source(job_url)

            # Prepare ML prediction data
            ml_data = {
                "title": job_title,
                "company_profile": company_profile,
                "description": job_description,
                "requirements": requirements,
                "benefits": benefits,
            }
            ml_prediction = job_verifier.preprocess_and_predict(ml_data)

            # Comprehensive analysis prompt
            prompt = f"""Carefully analyze this job posting for legitimacy:

Job Details:
- Job Title: {job_title}
- Company: {company_name}
- Job URL: {job_url}

Technical Verification:
- URL Validation: {validate_url}
- Verified Job Board: {in_verified_job_board}

Risk Indicators:
- Red Flags Detected: {desc_analysis.get('red_flag_count', 0)}
- Suspicious Patterns: {desc_analysis.get('suspicious_pattern_count', 0)}
- Calculated Risk Score: {desc_analysis.get('risk_score', 0)}

Machine Learning Prediction: {'Legitimate' if ml_prediction == 1 else 'Suspicious'}

Comprehensive Analysis Request:
1. Provide a detailed assessment of the job posting's legitimacy.
2. Explain the reasoning behind your assessment.
3. Generate a confidence percentage (0-100%) based on the strength of evidence.
4. Highlight specific red flags or positive indicators.
5. Recommend actions for the job seeker.

Output Format:
Prediction: [Legitimate/Suspicious]
Confidence: [XX%]
Explanation: [Your detailed reasoning here]

Your response should be Accurate, Clear, Concise and straight to the point. 
Your tone should be friendly but professional.
""" 

            # Generate analysis
            response = gemini_model.generate_content(prompt)
            response_text = response.text
            
            # Extract prediction and confidence from the response
            prediction_match = re.search(r'Prediction:\s*(Legitimate|Suspicious)', response_text, re.IGNORECASE)
            confidence_match = re.search(r'Confidence:\s*(\d+)%', response_text, re.IGNORECASE)

            prediction = prediction_match.group(1) if prediction_match else "Unknown"
            confidence = int(confidence_match.group(1)) if confidence_match else 50

            # Display results
            st.subheader("Job Legitimacy Analysis")

            # Prediction visualization
            if prediction.lower() == "legitimate":
                st.success("✅ Job Appears Legitimate")
                st.markdown("#### **Prediction**: **Legitimate**")
                confidence_color = "green"
            elif prediction.lower() == "suspicious":
                st.warning("⚠️ Potential Job Scam Detected")
                st.markdown("#### **Prediction**: **Suspicious**")
                confidence_color = "red"
            else:
                st.error("⚠️ Unable to determine legitimacy.")
                confidence_color = "gray"

            # Confidence display
            st.markdown(f"#### **Confidence**: **{confidence}%**")

            # Explanation section
            st.markdown("#### **Thoughts**:")
            st.write(response_text)  # Display the explanation directly

        except Exception as e:
            st.error(f"An error occurred during analysis: {str(e)}")

if __name__ == "__main__":
    main()