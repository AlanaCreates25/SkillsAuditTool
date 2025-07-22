import streamlit as st
import pandas as pd
from utils.gap_analyzer import GapAnalyzer
from utils.data_processor import DataProcessor
from utils.database import SkillsDatabase
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

st.set_page_config(
    page_title="Gap Reports - Skills Audit Tool",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Skills Gap Reports")
st.markdown("Generate comprehensive reports for skills gap analysis and export data.")

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

# Check if data is available
if st.session_state.processed_data is None:
    st.warning("⚠️ No processed data available. Please upload and process your assessment data first.")
    st.info("👆 Go to the 'Data Upload' page to upload your assessment files.")
    st.stop()

# Initialize components
analyzer = GapAnalyzer(st.session_state.gap_threshold)
processor = DataProcessor()
df = st.session_state.processed_data

# Gap analysis configuration
use_matrix_gaps = st.session_state.get('use_matrix_gaps', False)
if st.session_state.skills_matrix is not None:
    st.sidebar.header("📊 Analysis Settings")
    use_matrix_gaps = st.sidebar.checkbox(
        "Use Skills Matrix Analysis",
        value=use_matrix_gaps,
        help="Compare against skills matrix standards instead of perception gaps"
    )

# Calculate comprehensive analysis
gap_analysis = analyzer.calculate_gaps(df, use_matrix_gaps)
org_insights = analyzer.get_organization_insights(df)

# Save gap analysis to database
try:
    db = SkillsDatabase()
    gap_type = "matrix" if use_matrix_gaps else "perception"
    db.save_gap_analysis(gap_analysis, gap_type)
except Exception:
    pass  # Fail silently if database not available

# Report generation options
st.header("📊 Report Generation")

report_type = st.selectbox(
    "Select Report Type:",
    [
        "Executive Summary",
        "Detailed Skills Gap Report",
        "Individual Employee Reports",
        "Skills Distribution Analysis",
        "Development Priorities Report"
    ]
)

# Generate reports based on selection
if report_type == "Executive Summary":
    st.subheader("📈 Executive Summary Report")
    
    # Key metrics summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_employees = org_insights.get('total_employees', 0)
        st.metric("Total Employees", total_employees)
    
    with col2:
        employees_with_gaps = len(gap_analysis[gap_analysis['has_gaps'] == True]) if not gap_analysis.empty else 0
        gap_percentage = (employees_with_gaps / total_employees * 100) if total_employees > 0 else 0
        st.metric("Employees with Gaps", f"{gap_percentage:.1f}%")
    
    with col3:
        avg_skill_level = gap_analysis['avg_skill_level'].mean() if not gap_analysis.empty else 0
        st.metric("Avg Organization Skill", f"{avg_skill_level:.2f}/5.0")
    
    with col4:
        skills_assessed = org_insights.get('skills_assessed', 0)
        st.metric("Skills Assessed", skills_assessed)
    
    # Executive insights
    st.markdown("### 🎯 Key Findings")
    
    findings = []
    
    # Overall assessment
    if gap_percentage > 50:
        findings.append(f"**High Priority**: {gap_percentage:.1f}% of employees have significant skills gaps requiring immediate attention.")
    elif gap_percentage > 25:
        findings.append(f"**Medium Priority**: {gap_percentage:.1f}% of employees have skills gaps that need development planning.")
    else:
        findings.append(f"**Good Status**: Only {gap_percentage:.1f}% of employees have significant skills gaps.")
    
    # Skills analysis
    if org_insights.get('overall_skill_gaps'):
        top_gaps = org_insights['overall_skill_gaps'][:3]
        gap_skills = ', '.join([gap['skill'] for gap in top_gaps])
        findings.append(f"**Training Priorities**: {gap_skills} show the lowest organization-wide ratings.")
    
    if org_insights.get('overall_skill_strengths'):
        top_strengths = org_insights['overall_skill_strengths'][:3]
        strength_skills = ', '.join([strength['skill'] for strength in top_strengths])
        findings.append(f"**Organizational Strengths**: {strength_skills} are areas of excellence that can be leveraged.")
    
    # High performers
    if org_insights.get('high_performers'):
        high_perf_count = len(org_insights['high_performers'])
        findings.append(f"**Leadership Pipeline**: {high_perf_count} high-performing employees identified for advanced development.")
    
    for finding in findings:
        st.markdown(f"• {finding}")
    
    # Recommendations
    st.markdown("### 💡 Strategic Recommendations")
    
    recommendations = [
        "🎯 **Immediate Actions**: Focus development resources on employees with significant gaps",
        "📚 **Training Programs**: Develop targeted training for skills showing organization-wide gaps",
        "🤝 **Peer Mentoring**: Leverage high-performing employees to mentor others in their strength areas",
        "📊 **Regular Assessment**: Implement quarterly skills assessments to track improvement",
        "🎖️ **Recognition Programs**: Acknowledge and reward employees demonstrating strong skills"
    ]
    
    for rec in recommendations:
        st.markdown(f"• {rec}")

elif report_type == "Detailed Skills Gap Report":
    st.subheader("🔍 Detailed Skills Gap Analysis")
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        gap_filter = st.selectbox(
            "Filter by Gap Status:",
            ["All Employees", "Employees with Gaps", "Employees without Gaps"]
        )
    
    with col2:
        skill_filter = st.selectbox(
            "Filter by Skill:",
            ["All Skills"] + [col.replace('_avg', '') for col in df.columns if col.endswith('_avg')]
        )
    
    # Apply filters
    filtered_analysis = gap_analysis.copy()
    
    if gap_filter == "Employees with Gaps":
        filtered_analysis = filtered_analysis[filtered_analysis['has_gaps'] == True]
    elif gap_filter == "Employees without Gaps":
        filtered_analysis = filtered_analysis[filtered_analysis['has_gaps'] == False]
    
    # Create detailed report table
    detailed_report = []
    
    for _, row in filtered_analysis.iterrows():
        employee = row['Employee']
        emp_data = df[df['Employee'] == employee].iloc[0]
        
        # Get skill-specific data
        if skill_filter != "All Skills":
            avg_col = f"{skill_filter}_avg"
            gap_col = f"{skill_filter}_gap"
            
            if avg_col in emp_data.index and gap_col in emp_data.index:
                detailed_report.append({
                    'Employee': employee,
                    'Skill': skill_filter,
                    'Average Rating': emp_data[avg_col] if pd.notna(emp_data[avg_col]) else 'N/A',
                    'Gap Score': emp_data[gap_col] if pd.notna(emp_data[gap_col]) else 'N/A',
                    'Has Significant Gap': 'Yes' if abs(emp_data[gap_col]) >= st.session_state.gap_threshold else 'No'
                })
        else:
            # All skills summary
            detailed_report.append({
                'Employee': employee,
                'Avg Skill Level': f"{row['avg_skill_level']:.2f}",
                'Avg Gap Score': f"{row['avg_gap_score']:.2f}",
                'Significant Gaps Count': row['significant_gaps_count'],
                'Has Significant Gaps': 'Yes' if row['has_gaps'] else 'No',
                'Strengths Count': len(row['strengths']),
                'Development Areas Count': len(row['development_areas'])
            })
    
    if detailed_report:
        report_df = pd.DataFrame(detailed_report)
        st.dataframe(report_df, use_container_width=True)
        
        # Summary statistics
        if skill_filter == "All Skills":
            st.markdown("### 📊 Summary Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_skill = filtered_analysis['avg_skill_level'].mean()
                st.metric("Average Skill Level", f"{avg_skill:.2f}")
            
            with col2:
                avg_gap = filtered_analysis['avg_gap_score'].mean()
                st.metric("Average Gap Score", f"{avg_gap:.2f}")
            
            with col3:
                total_gaps = filtered_analysis['significant_gaps_count'].sum()
                st.metric("Total Significant Gaps", total_gaps)
    else:
        st.info("No data matches the selected filters.")

elif report_type == "Individual Employee Reports":
    st.subheader("👤 Individual Employee Reports")
    
    # Employee selection
    employee_list = sorted(df['Employee'].unique())
    selected_employees = st.multiselect(
        "Select employees for individual reports:",
        employee_list,
        help="Generate detailed reports for selected employees"
    )
    
    if selected_employees:
        for employee in selected_employees:
            st.markdown(f"### 📊 Report for {employee}")
            
            # Get employee data
            employee_data = df[df['Employee'] == employee].iloc[0]
            employee_gaps = gap_analysis[gap_analysis['Employee'] == employee].iloc[0]
            
            # Employee metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Avg Skill Level", f"{employee_gaps['avg_skill_level']:.2f}")
            
            with col2:
                st.metric("Avg Gap Score", f"{employee_gaps['avg_gap_score']:.2f}")
            
            with col3:
                st.metric("Significant Gaps", employee_gaps['significant_gaps_count'])
            
            # Detailed breakdown
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Strengths:**")
                strengths = employee_gaps['strengths'][:5]
                if strengths:
                    for strength in strengths:
                        st.write(f"• {strength['skill']}: {strength['rating']:.1f}")
                else:
                    st.write("None identified")
            
            with col2:
                st.markdown("**Development Areas:**")
                dev_areas = employee_gaps['development_areas'][:5]
                if dev_areas:
                    for area in dev_areas:
                        st.write(f"• {area['skill']}: {area['rating']:.1f}")
                else:
                    st.write("None identified")
            
            # Significant gaps
            if employee_gaps['significant_gaps']:
                st.markdown("**Significant Gaps:**")
                for gap in employee_gaps['significant_gaps'][:3]:
                    st.write(f"• {gap['skill']}: {gap['gap_value']:+.1f} ({gap['direction']})")
            
            st.divider()
    else:
        st.info("Select employees to generate individual reports.")

elif report_type == "Skills Distribution Analysis":
    st.subheader("📊 Skills Distribution Analysis")
    
    # Skills analysis
    skills_list = [col.replace('_avg', '') for col in df.columns if col.endswith('_avg')]
    
    distribution_data = []
    for skill in skills_list:
        skill_dist = analyzer.get_skill_distribution(df, skill)
        if skill_dist:
            distribution_data.append({
                'Skill': skill,
                'Average Rating': f"{skill_dist['average_rating']:.2f}",
                'Median Rating': f"{skill_dist['median_rating']:.2f}",
                'Std Deviation': f"{skill_dist['std_deviation']:.2f}",
                'Min Rating': f"{skill_dist['min_rating']:.1f}",
                'Max Rating': f"{skill_dist['max_rating']:.1f}",
                'Assessments': skill_dist['total_assessments']
            })
    
    if distribution_data:
        dist_df = pd.DataFrame(distribution_data)
        st.dataframe(dist_df, use_container_width=True)
        
        # Skills ranking
        st.markdown("### 🏆 Skills Ranking")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Strongest Skills** (Highest Average)")
            top_skills = dist_df.nlargest(5, 'Average Rating')
            for _, row in top_skills.iterrows():
                st.write(f"• {row['Skill']}: {row['Average Rating']}")
        
        with col2:
            st.markdown("**Skills Needing Development** (Lowest Average)")
            bottom_skills = dist_df.nsmallest(5, 'Average Rating')
            for _, row in bottom_skills.iterrows():
                st.write(f"• {row['Skill']}: {row['Average Rating']}")

elif report_type == "Development Priorities Report":
    st.subheader("🎯 Development Priorities Report")
    
    # Priority matrix
    st.markdown("### 📊 Development Priority Matrix")
    
    priority_data = []
    
    for _, row in gap_analysis.iterrows():
        employee = row['Employee']
        
        # Calculate priority score based on gaps and skill level
        priority_score = (row['avg_gap_score'] * 2) + (5 - row['avg_skill_level'])
        
        priority_level = "High" if priority_score >= 6 else "Medium" if priority_score >= 3 else "Low"
        
        priority_data.append({
            'Employee': employee,
            'Priority Score': f"{priority_score:.2f}",
            'Priority Level': priority_level,
            'Avg Skill Level': f"{row['avg_skill_level']:.2f}",
            'Avg Gap Score': f"{row['avg_gap_score']:.2f}",
            'Significant Gaps': row['significant_gaps_count'],
            'Development Areas': len(row['development_areas'])
        })
    
    priority_df = pd.DataFrame(priority_data)
    
    # Sort by priority score
    priority_df['Priority Score Numeric'] = priority_df['Priority Score'].astype(float)
    priority_df = priority_df.sort_values('Priority Score Numeric', ascending=False)
    priority_df = priority_df.drop('Priority Score Numeric', axis=1)
    
    st.dataframe(priority_df, use_container_width=True)
    
    # Priority breakdown
    col1, col2, col3 = st.columns(3)
    
    with col1:
        high_priority = len(priority_df[priority_df['Priority Level'] == 'High'])
        st.metric("High Priority", high_priority, help="Immediate development needed")
    
    with col2:
        medium_priority = len(priority_df[priority_df['Priority Level'] == 'Medium'])
        st.metric("Medium Priority", medium_priority, help="Development planning recommended")
    
    with col3:
        low_priority = len(priority_df[priority_df['Priority Level'] == 'Low'])
        st.metric("Low Priority", low_priority, help="Maintenance and enhancement")
    
    # Development recommendations
    st.markdown("### 💡 Development Recommendations")
    
    high_priority_employees = priority_df[priority_df['Priority Level'] == 'High']['Employee'].tolist()
    
    if high_priority_employees:
        st.markdown("**High Priority Employees:**")
        for emp in high_priority_employees[:5]:  # Show top 5
            emp_gaps = gap_analysis[gap_analysis['Employee'] == emp].iloc[0]
            top_dev_areas = [area['skill'] for area in emp_gaps['development_areas'][:2]]
            st.write(f"• **{emp}**: Focus on {', '.join(top_dev_areas) if top_dev_areas else 'general skills development'}")

# Export functionality
st.divider()
st.header("📥 Export Reports")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Export Gap Analysis", type="secondary"):
        # Create comprehensive gap analysis export
        export_data = []
        
        for _, row in gap_analysis.iterrows():
            employee = row['Employee']
            emp_data = df[df['Employee'] == employee].iloc[0]
            
            # Basic info
            export_row = {
                'Employee': employee,
                'Email': emp_data.get('Email', ''),
                'Average_Skill_Level': row['avg_skill_level'],
                'Average_Gap_Score': row['avg_gap_score'],
                'Has_Significant_Gaps': row['has_gaps'],
                'Significant_Gaps_Count': row['significant_gaps_count'],
                'Strengths_Count': len(row['strengths']),
                'Development_Areas_Count': len(row['development_areas'])
            }
            
            # Add individual skill ratings
            avg_columns = [col for col in df.columns if col.endswith('_avg')]
            for col in avg_columns:
                skill_name = col.replace('_avg', '')
                export_row[f'{skill_name}_Average'] = emp_data[col] if pd.notna(emp_data[col]) else 0
            
            # Add gap scores
            gap_columns = [col for col in df.columns if col.endswith('_gap')]
            for col in gap_columns:
                skill_name = col.replace('_gap', '')
                export_row[f'{skill_name}_Gap'] = emp_data[col] if pd.notna(emp_data[col]) else 0
            
            export_data.append(export_row)
        
        export_df = pd.DataFrame(export_data)
        csv = export_df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download Gap Analysis (CSV)",
            data=csv,
            file_name=f"skills_gap_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

with col2:
    if st.button("📈 Export Skills Summary", type="secondary"):
        # Create skills summary export
        skills_summary = []
        skills_list = [col.replace('_avg', '') for col in df.columns if col.endswith('_avg')]
        
        for skill in skills_list:
            skill_dist = analyzer.get_skill_distribution(df, skill)
            if skill_dist:
                skills_summary.append({
                    'Skill': skill,
                    'Average_Rating': skill_dist['average_rating'],
                    'Median_Rating': skill_dist['median_rating'],
                    'Standard_Deviation': skill_dist['std_deviation'],
                    'Min_Rating': skill_dist['min_rating'],
                    'Max_Rating': skill_dist['max_rating'],
                    'Total_Assessments': skill_dist['total_assessments']
                })
        
        summary_df = pd.DataFrame(skills_summary)
        csv = summary_df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download Skills Summary (CSV)",
            data=csv,
            file_name=f"skills_summary_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

with col3:
    if st.button("📋 Export All Data", type="secondary"):
        # Export processed data
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download All Data (CSV)",
            data=csv,
            file_name=f"skills_audit_complete_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# Excel export option
st.markdown("### 📊 Excel Export")
if st.button("📊 Generate Excel Report", type="primary"):
    try:
        # Create Excel file with multiple sheets
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Main data sheet
            df.to_excel(writer, sheet_name='Skills Data', index=False)
            
            # Gap analysis sheet
            gap_analysis_export = gap_analysis.copy()
            # Convert list columns to strings for Excel compatibility
            gap_analysis_export['significant_gaps'] = gap_analysis_export['significant_gaps'].apply(
                lambda x: ', '.join([gap['skill'] for gap in x]) if x else ''
            )
            gap_analysis_export['strengths'] = gap_analysis_export['strengths'].apply(
                lambda x: ', '.join([s['skill'] for s in x[:5]]) if x else ''
            )
            gap_analysis_export['development_areas'] = gap_analysis_export['development_areas'].apply(
                lambda x: ', '.join([d['skill'] for d in x[:5]]) if x else ''
            )
            gap_analysis_export.to_excel(writer, sheet_name='Gap Analysis', index=False)
            
            # Skills summary sheet
            skills_summary = []
            skills_list = [col.replace('_avg', '') for col in df.columns if col.endswith('_avg')]
            
            for skill in skills_list:
                skill_dist = analyzer.get_skill_distribution(df, skill)
                if skill_dist:
                    skills_summary.append({
                        'Skill': skill,
                        'Average_Rating': skill_dist['average_rating'],
                        'Median_Rating': skill_dist['median_rating'],
                        'Standard_Deviation': skill_dist['std_deviation'],
                        'Min_Rating': skill_dist['min_rating'],
                        'Max_Rating': skill_dist['max_rating'],
                        'Total_Assessments': skill_dist['total_assessments']
                    })
            
            if skills_summary:
                pd.DataFrame(skills_summary).to_excel(writer, sheet_name='Skills Summary', index=False)
        
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Download Complete Excel Report",
            data=excel_data,
            file_name=f"skills_audit_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.success("✅ Excel report generated successfully!")
        
    except Exception as e:
        st.error(f"❌ Error generating Excel report: {str(e)}")

# Report scheduling info
st.divider()
st.header("⏰ Report Scheduling")
st.info("""
📅 **Regular Reporting Recommendations:**
- Generate monthly gap analysis reports to track progress
- Quarterly skills distribution analysis for strategic planning
- Annual comprehensive reports for performance reviews
- Export individual reports before development planning sessions
""")
