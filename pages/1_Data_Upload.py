import streamlit as st
import pandas as pd
from utils.data_processor import DataProcessor
from utils.database import SkillsDatabase
import io

st.set_page_config(
    page_title="Data Upload - Skills Audit Tool",
    page_icon="📊",
    layout="wide"
)

st.title("📁 Data Upload")
st.markdown("Upload your MS Forms assessment data to begin the skills analysis.")

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

# Initialize data processor and database
processor = DataProcessor()
try:
    db = SkillsDatabase()
    db_available = True
except Exception as e:
    st.warning(f"Database connection failed: {str(e)}")
    db_available = False

# Database session management in sidebar
if db_available:
    with st.sidebar:
        st.header("💾 Database Sessions")
        
        # Current session info
        try:
            current_session = db.get_session_id()
            st.info(f"Current Session: {current_session}")
            
            # Load existing sessions
            sessions = db.get_saved_sessions()
            if sessions:
                st.subheader("Load Previous Session")
                session_options = [f"{s['session_id']} ({s['employee_count']} employees)" for s in sessions]
                selected_session = st.selectbox("Select session:", [""] + session_options)
                
                if selected_session and st.button("Load Session"):
                    session_id = selected_session.split(" ")[0]
                    if db.load_session(session_id):
                        st.success("Session loaded successfully!")
                        st.rerun()
            
            # Delete session option
            if sessions and st.checkbox("Show delete options"):
                session_to_delete = st.selectbox("Select session to delete:", [""] + [s['session_id'] for s in sessions])
                if session_to_delete and st.button("Delete Session", type="secondary"):
                    if db.delete_session(session_to_delete):
                        st.success("Session deleted!")
                        st.rerun()
        except Exception as e:
            st.error(f"Database error: {str(e)}")

# Create tabs for different upload types
tab1, tab2, tab3 = st.tabs(["Employee Self-Assessments", "Manager Assessments", "Skills Matrix"])

with tab1:
    st.header("📝 Employee Self-Assessment Data")
    st.markdown("Upload the CSV file containing employee self-assessment responses from MS Forms.")
    
    # File uploader for employee data
    employee_file = st.file_uploader(
        "Choose Employee Assessment CSV file",
        type=['csv'],
        key="employee_upload",
        help="Upload the CSV file exported from MS Forms containing employee self-assessments"
    )
    
    if employee_file is not None:
        try:
            # Read the CSV file
            employee_df = pd.read_csv(employee_file)
            
            # Validate the CSV structure
            is_valid, error_message = processor.validate_csv_structure(employee_df, 'employee')
            
            if is_valid:
                st.success("✅ Employee assessment file validated successfully!")
                
                # Clean and standardize the data
                cleaned_df = processor.clean_and_standardize(employee_df, 'employee')
                
                # Store in session state
                st.session_state.employee_data = cleaned_df
                
                # Save to database if available
                if db_available:
                    if db.save_assessment_data(cleaned_df, 'employee'):
                        st.success("Data saved to database!")
                
                # Display data preview
                st.subheader("📊 Data Preview")
                st.write(f"**Records:** {len(cleaned_df)}")
                st.write(f"**Columns:** {len(cleaned_df.columns)}")
                
                # Show skill columns identified
                skill_columns = processor._identify_skill_columns(cleaned_df)
                st.write(f"**Skills Identified:** {len(skill_columns)}")
                
                if skill_columns:
                    with st.expander("View Identified Skills"):
                        for skill in skill_columns:
                            st.write(f"• {skill}")
                
                # Show data sample
                with st.expander("View Data Sample"):
                    st.dataframe(cleaned_df.head())
                
                # Show data statistics
                with st.expander("View Data Statistics"):
                    # Employee count
                    unique_employees = cleaned_df['Employee'].nunique()
                    st.metric("Unique Employees", unique_employees)
                    
                    # Skill completion rates
                    if skill_columns:
                        completion_rates = {}
                        for skill in skill_columns:
                            completed = (cleaned_df[skill] > 0).sum()
                            rate = (completed / len(cleaned_df)) * 100
                            completion_rates[skill] = rate
                        
                        st.subheader("Skill Completion Rates")
                        completion_df = pd.DataFrame(
                            list(completion_rates.items()),
                            columns=['Skill', 'Completion Rate (%)']
                        ).sort_values('Completion Rate (%)', ascending=False)
                        st.dataframe(completion_df)
            
            else:
                st.error(f"❌ Validation Error: {error_message}")
                st.info("Please check your CSV file format and try again.")
                
                # Show expected format
                with st.expander("Expected CSV Format"):
                    st.markdown("""
                    Your CSV file should contain:
                    - **Employee**: Employee name
                    - **Email**: Employee email address
                    - **Skill columns**: Columns with numerical ratings (1-5 scale)
                    
                    Example:
                    ```
                    Employee,Email,Communication,Leadership,Technical Skills
                    John Doe,john@company.com,4,3,5
                    Jane Smith,jane@company.com,5,4,3
                    ```
                    """)
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            st.info("Please ensure your file is a valid CSV file.")

with tab2:
    st.header("👥 Manager Assessment Data")
    st.markdown("Upload the CSV file containing manager assessments of their subordinates from MS Forms.")
    
    # File uploader for manager data
    manager_file = st.file_uploader(
        "Choose Manager Assessment CSV file",
        type=['csv'],
        key="manager_upload",
        help="Upload the CSV file exported from MS Forms containing manager assessments"
    )
    
    if manager_file is not None:
        try:
            # Read the CSV file
            manager_df = pd.read_csv(manager_file)
            
            # Validate the CSV structure
            is_valid, error_message = processor.validate_csv_structure(manager_df, 'manager')
            
            if is_valid:
                st.success("✅ Manager assessment file validated successfully!")
                
                # Clean and standardize the data
                cleaned_df = processor.clean_and_standardize(manager_df, 'manager')
                
                # Store in session state
                st.session_state.manager_data = cleaned_df
                
                # Save to database if available
                if db_available:
                    if db.save_assessment_data(cleaned_df, 'manager'):
                        st.success("Data saved to database!")
                
                # Display data preview
                st.subheader("📊 Data Preview")
                st.write(f"**Records:** {len(cleaned_df)}")
                st.write(f"**Columns:** {len(cleaned_df.columns)}")
                
                # Show skill columns identified
                skill_columns = processor._identify_skill_columns(cleaned_df)
                st.write(f"**Skills Identified:** {len(skill_columns)}")
                
                if skill_columns:
                    with st.expander("View Identified Skills"):
                        for skill in skill_columns:
                            st.write(f"• {skill}")
                
                # Show data sample
                with st.expander("View Data Sample"):
                    st.dataframe(cleaned_df.head())
                
                # Show data statistics
                with st.expander("View Data Statistics"):
                    # Employee count
                    unique_employees = cleaned_df['Employee'].nunique()
                    st.metric("Unique Employees Assessed", unique_employees)
                    
                    # Skill completion rates
                    if skill_columns:
                        completion_rates = {}
                        for skill in skill_columns:
                            completed = (cleaned_df[skill] > 0).sum()
                            rate = (completed / len(cleaned_df)) * 100
                            completion_rates[skill] = rate
                        
                        st.subheader("Skill Assessment Completion Rates")
                        completion_df = pd.DataFrame(
                            list(completion_rates.items()),
                            columns=['Skill', 'Completion Rate (%)']
                        ).sort_values('Completion Rate (%)', ascending=False)
                        st.dataframe(completion_df)
            
            else:
                st.error(f"❌ Validation Error: {error_message}")
                st.info("Please check your CSV file format and try again.")
                
                # Show expected format
                with st.expander("Expected CSV Format"):
                    st.markdown("""
                    Your CSV file should contain:
                    - **Employee**: Employee name being assessed
                    - **Email**: Employee email address
                    - **Skill columns**: Columns with numerical ratings (1-5 scale)
                    
                    Example:
                    ```
                    Employee,Email,Communication,Leadership,Technical Skills
                    John Doe,john@company.com,4,3,5
                    Jane Smith,jane@company.com,5,4,3
                    ```
                    """)
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            st.info("Please ensure your file is a valid CSV file.")

# Data processing status
st.divider()
st.header("🔄 Data Processing Status")

col1, col2 = st.columns(2)

with col1:
    if st.session_state.employee_data is not None:
        st.success("✅ Employee assessments loaded")
        st.write(f"Records: {len(st.session_state.employee_data)}")
    else:
        st.warning("⏳ Employee assessments not loaded")

with col2:
    if st.session_state.manager_data is not None:
        st.success("✅ Manager assessments loaded")
        st.write(f"Records: {len(st.session_state.manager_data)}")
    else:
        st.warning("⏳ Manager assessments not loaded")

# Process data if both are available
if st.session_state.employee_data is not None and st.session_state.manager_data is not None:
    if st.button("🔄 Process Data", type="primary"):
        try:
            with st.spinner("Processing assessment data..."):
                processed_data = processor.merge_assessments(
                    st.session_state.employee_data,
                    st.session_state.manager_data,
                    st.session_state.skills_matrix
                )
                st.session_state.processed_data = processed_data
                
                # Save processed data to database
                if db_available:
                    if db.save_processed_data(processed_data):
                        st.success("Processed data saved to database!")
            
            st.success("✅ Data processed successfully!")
            st.balloons()
            
            # Show processing results
            st.subheader("📈 Processing Results")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Employees Processed", len(processed_data))
            
            with col2:
                skill_count = len([col for col in processed_data.columns if col.endswith('_avg')])
                st.metric("Skills Analyzed", skill_count)
            
            with col3:
                gap_count = len([col for col in processed_data.columns if col.endswith('_gap')])
                matrix_gap_count = len([col for col in processed_data.columns if col.endswith('_matrix_gap')])
                st.metric("Gap Metrics", gap_count + matrix_gap_count)
            
            st.info("🎉 You can now proceed to the Employee Dashboard to view individual profiles and Skills Analysis for organization insights!")
            
        except Exception as e:
            st.error(f"❌ Error processing data: {str(e)}")
            st.info("Please check that both assessment files have matching employee names and skill columns.")

# Clear data option
st.divider()
st.subheader("🗑️ Clear Data")
st.markdown("Use this option to clear uploaded data and start over.")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Clear Employee Data", type="secondary"):
        st.session_state.employee_data = None
        st.session_state.processed_data = None
        st.success("Employee data cleared!")
        st.rerun()

with col2:
    if st.button("Clear Manager Data", type="secondary"):
        st.session_state.manager_data = None
        st.session_state.processed_data = None
        st.success("Manager data cleared!")
        st.rerun()

with col3:
    if st.button("Clear All Data", type="secondary"):
        st.session_state.employee_data = None
        st.session_state.manager_data = None
        st.session_state.processed_data = None
        st.session_state.skills_matrix = None
        st.success("All data cleared!")
        st.rerun()

with tab3:
    st.header("📊 Skills Matrix")
    st.markdown("Upload your skills matrix to define skill level standards for gap analysis.")
    
    # File uploader for skills matrix
    matrix_file = st.file_uploader(
        "Choose Skills Matrix CSV file",
        type=['csv'],
        key="matrix_upload",
        help="Upload CSV file containing skill standards and level definitions"
    )
    
    if matrix_file is not None:
        try:
            # Read the skills matrix file
            matrix_df = pd.read_csv(matrix_file)
            
            # Validate and process skills matrix
            is_valid, error_message = processor.validate_csv_structure(matrix_df, 'skills_matrix')
            
            if is_valid:
                st.success("✅ Skills matrix validated successfully!")
                
                # Clean and standardize the skills matrix
                cleaned_matrix = processor.clean_and_standardize(matrix_df, 'skills_matrix')
                
                # Store in session state
                st.session_state.skills_matrix = cleaned_matrix
                
                # Save to database if available
                if db_available:
                    if db.save_skills_matrix(cleaned_matrix):
                        st.success("Skills matrix saved to database!")
                
                # Display matrix preview
                st.subheader("📊 Skills Matrix Preview")
                st.write(f"**Skills Defined:** {len(cleaned_matrix)}")
                
                # Show detected format
                if len(matrix_df.columns) >= 3 and len(matrix_df) > 0:
                    # Check if Excel format was detected
                    first_row = matrix_df.iloc[0]
                    skill_columns = matrix_df.columns[2:]
                    numeric_count = sum(1 for col in skill_columns[:5] if pd.to_numeric(first_row[col], errors='coerce') is not None)
                    
                    skill_names_count = 0
                    for col in skill_columns[:5]:
                        cell_value = str(first_row[col]).strip()
                        if cell_value and cell_value.lower() not in ['unnamed', 'nan', ''] and not cell_value.replace('.','').isdigit():
                            skill_names_count += 1
                    
                    if skill_names_count >= 2:
                        st.info(f"Excel format detected: Row 1 contains skill names in columns C to AQ, with job titles/departments and required levels in subsequent rows")
                    else:
                        st.info("Traditional format detected: Skill names and required levels in columns")
                
                # Show skills matrix
                with st.expander("View Skills Matrix"):
                    st.dataframe(cleaned_matrix)
                
                # Show statistics
                with st.expander("Matrix Statistics"):
                    if 'Required_Level' in cleaned_matrix.columns:
                        avg_required = cleaned_matrix['Required_Level'].mean()
                        st.metric("Average Required Level", f"{avg_required:.2f}")
                        
                        # Show job titles and departments if available
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if 'Job_Title' in cleaned_matrix.columns:
                                unique_jobs = cleaned_matrix['Job_Title'].nunique()
                                st.metric("Job Titles/Designations", unique_jobs)
                                
                                if unique_jobs > 0:
                                    st.subheader("Job Titles in Matrix")
                                    job_titles = cleaned_matrix['Job_Title'].unique()
                                    for job in job_titles:
                                        job_skills = len(cleaned_matrix[cleaned_matrix['Job_Title'] == job])
                                        st.write(f"• {job}: {job_skills} skills defined")
                        
                        with col2:
                            if 'Department' in cleaned_matrix.columns:
                                unique_depts = cleaned_matrix['Department'].nunique()
                                st.metric("Departments", unique_depts)
                                
                                if unique_depts > 0:
                                    st.subheader("Departments in Matrix")
                                    departments = cleaned_matrix['Department'].unique()
                                    for dept in departments:
                                        dept_skills = len(cleaned_matrix[cleaned_matrix['Department'] == dept])
                                        st.write(f"• {dept}: {dept_skills} skills defined")
                        
                        level_distribution = cleaned_matrix['Required_Level'].value_counts().sort_index()
                        st.subheader("Required Level Distribution")
                        st.bar_chart(level_distribution)
            
            else:
                st.error(f"❌ Validation Error: {error_message}")
                st.info("Please check your skills matrix format and try again.")
        
        except Exception as e:
            st.error(f"❌ Error reading skills matrix: {str(e)}")
            st.info("Please ensure your file is a valid CSV file.")
    
    # Skills matrix format guidance
    with st.expander("Expected Skills Matrix Format"):
        st.markdown("""
        Your Skills Matrix file can be in one of two formats:
        
        **Format 1: Excel Style (Recommended for cells 1C to 1AQ)**
        - Column A: Designation/Job Title (e.g., "Manager", "Developer")
        - Column B: Department (e.g., "IT", "HR", "Sales")
        - Row 1, Columns C to AQ: Skill names only
        - Row 2+: Required levels (1-5) for each job title/department
        
        Example Excel format:
        ```
        Designation  | Department | Communication | Leadership | Technical Skills | ...
        (Row 1)      |            | Communication | Leadership | Technical Skills | ...
        Manager      | IT         | 4            | 3          | 4               | ...
        Developer    | IT         | 3            | 2          | 5               | ...
        ```
        
        **Format 2: Traditional CSV**
        ```
        Skill,Required_Level
        Communication,4
        Leadership,3
        Technical Skills,4
        ```
        
        The system automatically detects which format you're using and processes accordingly.
        """)
    
    # Clear matrix option
    if st.session_state.skills_matrix is not None:
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.success("✅ Skills matrix loaded")
            st.write(f"Skills: {len(st.session_state.skills_matrix)}")
        with col2:
            if st.button("Clear Skills Matrix", type="secondary"):
                st.session_state.skills_matrix = None
                st.session_state.processed_data = None  # Reprocess needed
                st.success("Skills matrix cleared!")
                st.rerun()
