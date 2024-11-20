import streamlit as st
from JobLegitimacyChecker import JobLegitimacyChecker  # Ensure this file exists or replace with the actual implementation

# Initialize the checker
checker = JobLegitimacyChecker()

# Configure page settings
st.set_page_config(
    page_title="Job Legitimacy Checker",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS styling
st.markdown(
    """
    <style>
        .banner-image {
            width: 100%;
            height: 20px;
            object-fit: cover;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .confidence-score {
            font-size: 1.2rem;
            font-weight: bold;
            color: #007BFF;
        }
        .section-header {
            font-size: 2.0rem;
            font-weight: bold;
            margin-top: 20px;
            color: #444444;
        }
        .risk-warning {
            background-color: #FF0000;
            border: 1px solid #FFA07A;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
        }
        footer {
            text-align: center;
            padding: 10px;
            font-size: 0.85rem;
            color: #555555;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Main Banner Section
st.title("🛡️ Job Legitimacy Checker")
st.write("Analyze job postings for legitimacy using data-driven techniques.")
st.image(r"762887_Job1-01.jpg", caption="Ensure safe job applications!", use_container_width=True)

# Sidebar for inputs
with st.sidebar:
    st.header("🔍 Input Job Details")
    company_name = st.text_input("Company Name", placeholder="e.g., Acme Corporation")
    job_title = st.text_input("Job Title", placeholder="e.g., Software Engineer")
    job_description = st.text_area("Job Description", placeholder="Paste the job description here...")
    analyze_button = st.button("Analyze")

# Main logic
if analyze_button:
    if not company_name or not job_title or not job_description:
        st.warning("Please fill in all the fields to proceed.")
    else:
        st.info("Analyzing the job posting... This may take a few moments.")
        with st.spinner("Running legitimacy checks..."):
            results = checker.check_job_legitimacy(company_name, job_title, job_description)

        # Display results
        st.markdown("<div class='section-header'>Prediction Results</div>", unsafe_allow_html=True)
        prediction = "✅ Legitimate" if results['prediction'] == "Legitimate" else "⚠️ Suspicious"
        st.write(f"### **Prediction:** {prediction}")

        confidence = int(results['confidence'] * 100)
        st.markdown(
            f"<div class='confidence-score'>Confidence: {confidence}%</div>", unsafe_allow_html=True
        )
        st.progress(confidence)

        # Detailed Checks
        st.markdown("<div class='section-header'>Detailed Checks</div>", unsafe_allow_html=True)
        for check, result in results['checks'].items():
            if isinstance(result, (bool, str)):
                formatted_result = "✅ Passed" if result in [True, "Registered"] else "❌ Failed"
            elif isinstance(result, (int, float)):
                formatted_result = f"📊 {result}"
            else:
                formatted_result = "❓ Unknown"

            st.write(f"- **{check.replace('_', ' ').capitalize()}:** {formatted_result}")

        # Risk Factors
        st.markdown("<div class='section-header'>⚠️ Risk Factors</div>", unsafe_allow_html=True)
        if results['risk_factors']:
            for risk in results['risk_factors']:
                st.markdown(f"<div class='risk-warning'>{risk}</div>", unsafe_allow_html=True)
        else:
            st.success("No major risk factors detected.")

        # Footer
        st.markdown(
            """
            ---
            <footer>
                Made with ❤️ using Streamlit | <a href="#">GitHub Repository</a>
            </footer>
            """,
            unsafe_allow_html=True,
        )
