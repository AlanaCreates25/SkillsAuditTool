import streamlit as st
import pandas as pd
from utils.database import SkillsDatabase
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Database Management - Skills Audit Tool",
    page_icon="💾",
    layout="wide"
)

st.title("💾 Database Management")
st.markdown("Manage your skills assessment data and analysis sessions.")

# Initialize database
try:
    db = SkillsDatabase()
    db_available = True
except Exception as e:
    st.error(f"Database connection failed: {str(e)}")
    st.stop()

# Current session info
st.header("📊 Current Session")
current_session = db.get_session_id()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Session ID", current_session)

with col2:
    # Count employees in current session
    employee_data = db.load_assessment_data('employee')
    employee_count = len(employee_data) if employee_data is not None else 0
    st.metric("Employees", employee_count)

with col3:
    # Count skills in current session
    skills_matrix = db.load_skills_matrix()
    skills_count = len(skills_matrix) if skills_matrix is not None else 0
    st.metric("Skills Defined", skills_count)

# Session management
st.divider()
st.header("🗂️ Session Management")

# Load existing sessions
sessions = db.get_saved_sessions()

if sessions:
    # Display sessions in a table
    session_df = pd.DataFrame(sessions)
    session_df['created_at'] = pd.to_datetime(session_df['created_at'])
    session_df['created_date'] = session_df['created_at'].dt.strftime('%Y-%m-%d %H:%M')
    
    st.subheader("Available Sessions")
    
    # Session selection
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.dataframe(
            session_df[['session_id', 'employee_count', 'created_date']].rename(columns={
                'session_id': 'Session ID',
                'employee_count': 'Employees',
                'created_date': 'Created'
            }),
            use_container_width=True
        )
    
    with col2:
        st.subheader("Actions")
        
        # Session selector
        session_options = session_df['session_id'].tolist()
        selected_session = st.selectbox("Select Session", [""] + session_options)
        
        if selected_session:
            if st.button("Load Session", type="primary"):
                if db.load_session(selected_session):
                    st.success(f"Session {selected_session} loaded successfully!")
                    st.rerun()
                else:
                    st.error("Failed to load session")
            
            if st.button("Delete Session", type="secondary"):
                if db.delete_session(selected_session):
                    st.success(f"Session {selected_session} deleted!")
                    st.rerun()
                else:
                    st.error("Failed to delete session")
    
    # Session analytics
    st.divider()
    st.header("📈 Session Analytics")
    
    # Session timeline
    session_df_sorted = session_df.sort_values('created_at')
    
    fig = px.bar(
        session_df_sorted,
        x='session_id',
        y='employee_count',
        title='Sessions by Employee Count',
        labels={'session_id': 'Session ID', 'employee_count': 'Number of Employees'}
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Session creation timeline
    fig2 = px.line(
        session_df_sorted,
        x='created_at',
        y='employee_count',
        title='Session Creation Timeline',
        markers=True,
        labels={'created_at': 'Date Created', 'employee_count': 'Employees per Session'}
    )
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("No saved sessions found. Upload assessment data to create your first session.")

# Data export functionality
st.divider()
st.header("📥 Data Export")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Current Session Export")
    
    if st.button("Export Current Session Data"):
        # Load all current session data
        employee_data = db.load_assessment_data('employee')
        manager_data = db.load_assessment_data('manager')
        skills_matrix = db.load_skills_matrix()
        processed_data = db.load_processed_data()
        
        if any([employee_data is not None, manager_data is not None, skills_matrix is not None]):
            # Create export package
            export_data = {}
            
            if employee_data is not None:
                export_data['employee_assessments'] = employee_data.to_dict('records')
            
            if manager_data is not None:
                export_data['manager_assessments'] = manager_data.to_dict('records')
            
            if skills_matrix is not None:
                export_data['skills_matrix'] = skills_matrix.to_dict('records')
            
            if processed_data is not None:
                export_data['processed_data'] = processed_data.to_dict('records')
            
            # Convert to JSON for download
            import json
            export_json = json.dumps(export_data, indent=2, default=str)
            
            st.download_button(
                label="Download Session Data (JSON)",
                data=export_json,
                file_name=f"skills_audit_session_{current_session}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        else:
            st.warning("No data available in current session to export.")

with col2:
    st.subheader("Database Backup")
    
    if st.button("Create Full Database Backup"):
        # Export all sessions
        all_sessions_data = {}
        
        for session_info in sessions:
            session_id = session_info['session_id']
            
            # Temporarily load each session
            original_session = db.get_session_id()
            
            # Load session data
            employee_data = db.load_assessment_data('employee')
            manager_data = db.load_assessment_data('manager')
            skills_matrix = db.load_skills_matrix()
            
            session_data = {}
            if employee_data is not None:
                session_data['employee_assessments'] = employee_data.to_dict('records')
            if manager_data is not None:
                session_data['manager_assessments'] = manager_data.to_dict('records')
            if skills_matrix is not None:
                session_data['skills_matrix'] = skills_matrix.to_dict('records')
            
            all_sessions_data[session_id] = session_data
        
        if all_sessions_data:
            import json
            backup_json = json.dumps(all_sessions_data, indent=2, default=str)
            
            st.download_button(
                label="Download Full Backup (JSON)",
                data=backup_json,
                file_name=f"skills_audit_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        else:
            st.warning("No sessions available for backup.")

# Database statistics
st.divider()
st.header("📊 Database Statistics")

try:
    # Get database statistics
    with db.engine.connect() as conn:
        # Total assessments
        result = conn.execute(db.engine.text("SELECT COUNT(*) FROM assessments"))
        total_assessments = result.scalar()
        
        # Total employees across all sessions
        result = conn.execute(db.engine.text("SELECT COUNT(DISTINCT employee_name) FROM assessments"))
        total_employees = result.scalar()
        
        # Total skills
        result = conn.execute(db.engine.text("SELECT COUNT(DISTINCT skill_name) FROM assessments"))
        total_skills = result.scalar()
        
        # Total sessions
        result = conn.execute(db.engine.text("SELECT COUNT(DISTINCT session_id) FROM assessments"))
        total_sessions = result.scalar()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Sessions", total_sessions)
    
    with col2:
        st.metric("Total Employees", total_employees)
    
    with col3:
        st.metric("Total Skills", total_skills)
    
    with col4:
        st.metric("Total Assessments", total_assessments)

except Exception as e:
    st.error(f"Error retrieving database statistics: {str(e)}")

# Database maintenance
st.divider()
st.header("🔧 Database Maintenance")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Cleanup Options")
    
    if st.checkbox("Show cleanup options"):
        # Clean old sessions
        if sessions:
            cutoff_days = st.slider("Delete sessions older than (days):", 1, 365, 30)
            
            if st.button("Delete Old Sessions", type="secondary"):
                cutoff_date = datetime.now() - pd.Timedelta(days=cutoff_days)
                old_sessions = [s for s in sessions if s['created_at'] < cutoff_date]
                
                deleted_count = 0
                for session in old_sessions:
                    if db.delete_session(session['session_id']):
                        deleted_count += 1
                
                if deleted_count > 0:
                    st.success(f"Deleted {deleted_count} old sessions")
                    st.rerun()
                else:
                    st.info("No old sessions to delete")

with col2:
    st.subheader("Database Info")
    
    # Show connection info
    st.write("**Connection Status:** ✅ Connected")
    st.write(f"**Database URL:** {db.database_url.split('@')[1] if '@' in db.database_url else 'Connected'}")
    
    # Show table sizes
    try:
        with db.engine.connect() as conn:
            tables = ['assessments', 'skills_matrix', 'processed_assessments', 'gap_analysis']
            table_sizes = {}
            
            for table in tables:
                result = conn.execute(db.engine.text(f"SELECT COUNT(*) FROM {table}"))
                table_sizes[table] = result.scalar()
        
        st.subheader("Table Sizes")
        for table, size in table_sizes.items():
            st.write(f"**{table}:** {size} records")
            
    except Exception as e:
        st.warning(f"Could not retrieve table information: {str(e)}")