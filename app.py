import streamlit as st
import pandas as pd
from utils.data_processor import DataProcessor
from utils.gap_analyzer import GapAnalyzer
from utils.database import SkillsDatabase

# Configure page
st.set_page_config(
    page_title="Skills Audit Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'employee_data' not in st.session_state:
    st.session_state.employee_data = None
if 'manager_data' not in st.session_state:
    st.session_state.manager_data = None
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'gap_threshold' not in st.session_state:
    st.session_state.gap_threshold = 2.0
if 'skills_matrix' not in st.session_state:
    st.session_state.skills_matrix = None
if 'use_matrix_gaps' not in st.session_state:
    st.session_state.use_matrix_gaps = False

# Initialize database
try:
    db = SkillsDatabase()
    db_available = True
    
    # Auto-load data from database if session state is empty
    if (st.session_state.employee_data is None and 
        st.session_state.manager_data is None and 
        st.session_state.processed_data is None):
        
        employee_data = db.load_assessment_data('employee')
        manager_data = db.load_assessment_data('manager')
        skills_matrix = db.load_skills_matrix()
        processed_data = db.load_processed_data()
        
        if employee_data is not None:
            st.session_state.employee_data = employee_data
        if manager_data is not None:
            st.session_state.manager_data = manager_data
        if skills_matrix is not None:
            st.session_state.skills_matrix = skills_matrix
        if processed_data is not None:
            st.session_state.processed_data = processed_data
            
except Exception as e:
    db_available = False

def main():
    st.title("🎯 Skills Audit Tool")
    st.markdown("### Automated Skills Gap Analysis Dashboard")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Gap threshold setting
        gap_threshold = st.slider(
            "Skills Gap Threshold",
            min_value=0.5,
            max_value=4.0,
            value=st.session_state.gap_threshold,
            step=0.1,
            help="Define the minimum gap to identify skills deficiencies"
        )
        st.session_state.gap_threshold = gap_threshold
        
        # Skills matrix toggle
        if st.session_state.skills_matrix is not None:
            use_matrix = st.checkbox(
                "Use Skills Matrix for Gap Analysis",
                value=st.session_state.use_matrix_gaps,
                help="Compare against skills matrix standards instead of perception gaps"
            )
            st.session_state.use_matrix_gaps = use_matrix
        
        # Data status
        st.header("📊 Data Status")
        employee_status = "✅ Loaded" if st.session_state.employee_data is not None else "❌ Not Loaded"
        manager_status = "✅ Loaded" if st.session_state.manager_data is not None else "❌ Not Loaded"
        
        st.write(f"Employee Assessments: {employee_status}")
        st.write(f"Manager Assessments: {manager_status}")
        
        matrix_status = "✅ Loaded" if st.session_state.skills_matrix is not None else "❌ Not Loaded"
        st.write(f"Skills Matrix: {matrix_status}")
        
        if st.session_state.employee_data is not None:
            st.write(f"Employees: {len(st.session_state.employee_data)}")
        if st.session_state.manager_data is not None:
            st.write(f"Manager Reviews: {len(st.session_state.manager_data)}")
        if st.session_state.skills_matrix is not None:
            st.write(f"Skills Standards: {len(st.session_state.skills_matrix)}")
    
    # Main content area
    if st.session_state.employee_data is None and st.session_state.manager_data is None:
        st.info("👆 Please upload your assessment data using the 'Data Upload' page to get started.")
        
        # Quick start guide
        st.markdown("### 🚀 Quick Start Guide")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Step 1: Upload Data**
            - Navigate to the 'Data Upload' page
            - Upload Employee Self-Assessment CSV
            - Upload Manager Assessment CSV
            """)
            
        with col2:
            st.markdown("""
            **Step 2: Analyze Skills**
            - View employee dashboards
            - Analyze skills gaps
            - Generate reports
            """)
    
    else:
        # Process data if both datasets are available
        if st.session_state.employee_data is not None and st.session_state.manager_data is not None:
            if st.session_state.processed_data is None:
                processor = DataProcessor()
                try:
                    processed_data = processor.merge_assessments(
                        st.session_state.employee_data,
                        st.session_state.manager_data,
                        st.session_state.skills_matrix
                    )
                    st.session_state.processed_data = processed_data
                    st.success("✅ Data processed successfully!")
                except Exception as e:
                    st.error(f"Error processing data: {str(e)}")
                    return
        
        # Display overview metrics
        if st.session_state.processed_data is not None:
            analyzer = GapAnalyzer(st.session_state.gap_threshold)
            gaps = analyzer.calculate_gaps(
                st.session_state.processed_data, 
                st.session_state.use_matrix_gaps
            )
            
            # Save gap analysis to database
            if db_available:
                gap_type = "matrix" if st.session_state.use_matrix_gaps else "perception"
                db.save_gap_analysis(gaps, gap_type)
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_employees = len(st.session_state.processed_data['Employee'].unique())
                st.metric("Total Employees", total_employees)
            
            with col2:
                total_skills = len([col for col in st.session_state.processed_data.columns if col.endswith('_avg')])
                st.metric("Skills Assessed", total_skills)
            
            with col3:
                employees_with_gaps = len(gaps[gaps['has_gaps'] == True])
                st.metric("Employees with Gaps", employees_with_gaps)
            
            with col4:
                avg_gap_score = gaps['avg_gap_score'].mean() if not gaps.empty else 0
                st.metric("Average Gap Score", f"{avg_gap_score:.2f}")
            
            # Recent activity summary
            st.markdown("### 📈 Overview")
            if not gaps.empty:
                top_gaps = gaps.nlargest(5, 'avg_gap_score')
                st.markdown("**Top 5 Employees with Largest Skills Gaps:**")
                for _, row in top_gaps.iterrows():
                    st.write(f"• {row['Employee']}: {row['avg_gap_score']:.2f} average gap")

if __name__ == "__main__":
    main()
