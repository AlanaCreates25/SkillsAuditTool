import streamlit as st
import pandas as pd
from utils.gap_analyzer import GapAnalyzer
from utils.visualizations import SkillsVisualizer
from utils.database import SkillsDatabase
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Skills Analysis - Skills Audit Tool",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Skills Analysis")
st.markdown("Organization-wide skills analysis and insights.")

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
visualizer = SkillsVisualizer()
df = st.session_state.processed_data

# Gap analysis configuration
use_matrix_gaps = st.session_state.get('use_matrix_gaps', False)
if st.session_state.skills_matrix is not None:
    with st.sidebar:
        st.header("📊 Analysis Settings")
        use_matrix_gaps = st.checkbox(
            "Use Skills Matrix Analysis",
            value=use_matrix_gaps,
            help="Compare against skills matrix standards instead of perception gaps"
        )

# Calculate organization insights
org_insights = analyzer.get_organization_insights(df)
gap_analysis = analyzer.calculate_gaps(df, use_matrix_gaps)

# Save gap analysis to database
try:
    db = SkillsDatabase()
    gap_type = "matrix" if use_matrix_gaps else "perception"
    db.save_gap_analysis(gap_analysis, gap_type)
except Exception:
    pass  # Fail silently if database not available

# Organization overview
st.header("🏢 Organization Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Employees", org_insights.get('total_employees', 0))

with col2:
    st.metric("Skills Assessed", org_insights.get('skills_assessed', 0))

with col3:
    employees_with_gaps = len(gap_analysis[gap_analysis['has_gaps'] == True]) if not gap_analysis.empty else 0
    total_employees = len(gap_analysis) if not gap_analysis.empty else 1
    gap_percentage = (employees_with_gaps / total_employees) * 100
    st.metric("Employees with Gaps", f"{gap_percentage:.1f}%")

with col4:
    avg_org_skill = gap_analysis['avg_skill_level'].mean() if not gap_analysis.empty else 0
    st.metric("Org Avg Skill Level", f"{avg_org_skill:.2f}")

# Organization skills overview chart
st.divider()
st.header("📊 Skills Overview")

org_overview_chart = visualizer.create_organization_overview(df)
st.plotly_chart(org_overview_chart, use_container_width=True)

# Skills strengths and gaps
col1, col2 = st.columns(2)

with col1:
    st.subheader("💪 Organization Strengths")
    strengths = org_insights.get('overall_skill_strengths', [])
    
    if strengths:
        for strength in strengths[:5]:  # Top 5 strengths
            st.write(f"🌟 **{strength['skill']}**: {strength['average_rating']:.2f}/5.0")
            st.progress(strength['average_rating'] / 5.0)
    else:
        st.info("No particular strengths identified.")

with col2:
    st.subheader("📈 Areas Needing Development")
    gaps = org_insights.get('overall_skill_gaps', [])
    
    if gaps:
        for gap in gaps[:5]:  # Top 5 areas needing development
            st.write(f"📊 **{gap['skill']}**: {gap['average_rating']:.2f}/5.0")
            st.progress(gap['average_rating'] / 5.0)
    else:
        st.success("No significant skill gaps at organization level!")

# Skills gap heatmap
st.divider()
st.header("🔥 Skills Gap Heatmap")
st.markdown("Visualize skills gaps across all employees and skills.")

gap_heatmap = visualizer.create_skills_gap_heatmap(df)
st.plotly_chart(gap_heatmap, use_container_width=True)

# Employee performance analysis
st.divider()
st.header("👥 Employee Performance Analysis")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Performance vs Gaps Scatter Plot")
    scatter_chart = visualizer.create_employee_performance_scatter(gap_analysis)
    st.plotly_chart(scatter_chart, use_container_width=True)

with col2:
    st.subheader("🏆 High Performers")
    high_performers = org_insights.get('high_performers', [])
    
    if high_performers:
        st.markdown("**Top 20% performers:**")
        for performer in high_performers[:5]:
            st.write(f"⭐ {performer['employee']}: {performer['average_skill']:.2f}")
    else:
        st.info("Performance data not available.")

# Gap distribution analysis
st.divider()
st.header("📊 Gap Distribution Analysis")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Overall Gap Distribution")
    gap_dist_chart = visualizer.create_gap_distribution_chart(df)
    st.plotly_chart(gap_dist_chart, use_container_width=True)

with col2:
    st.subheader("Gap Statistics")
    
    if not gap_analysis.empty:
        # Calculate gap statistics
        total_with_gaps = len(gap_analysis[gap_analysis['has_gaps'] == True])
        total_without_gaps = len(gap_analysis[gap_analysis['has_gaps'] == False])
        
        st.metric("Employees with Significant Gaps", total_with_gaps)
        st.metric("Employees without Significant Gaps", total_without_gaps)
        
        avg_gap = gap_analysis['avg_gap_score'].mean()
        st.metric("Average Gap Score", f"{avg_gap:.2f}")
        
        max_gap = gap_analysis['avg_gap_score'].max()
        max_gap_employee = gap_analysis.loc[gap_analysis['avg_gap_score'].idxmax(), 'Employee']
        st.metric("Largest Gap", f"{max_gap:.2f}", help=f"Employee: {max_gap_employee}")
    else:
        st.info("No gap data available for analysis.")

# Detailed skills analysis
st.divider()
st.header("🔍 Detailed Skills Analysis")

# Skills selector
skills_list = [col.replace('_avg', '') for col in df.columns if col.endswith('_avg')]
selected_skill = st.selectbox("Select a skill to analyze:", skills_list)

if selected_skill:
    skill_distribution = analyzer.get_skill_distribution(df, selected_skill)
    
    if skill_distribution:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Average Rating", f"{skill_distribution['average_rating']:.2f}")
            st.metric("Assessments Count", skill_distribution['total_assessments'])
        
        with col2:
            st.metric("Minimum Rating", f"{skill_distribution['min_rating']:.1f}")
            st.metric("Maximum Rating", f"{skill_distribution['max_rating']:.1f}")
        
        with col3:
            st.metric("Standard Deviation", f"{skill_distribution['std_deviation']:.2f}")
            st.metric("Median Rating", f"{skill_distribution['median_rating']:.2f}")
        
        # Rating distribution chart
        rating_dist = skill_distribution.get('rating_distribution', {})
        if rating_dist:
            ratings = list(range(1, 6))
            counts = [rating_dist.get(f'rating_{r}', 0) for r in ratings]
            
            fig = go.Figure(data=[
                go.Bar(x=ratings, y=counts, marker_color='lightblue')
            ])
            fig.update_layout(
                title=f"Rating Distribution for {selected_skill}",
                xaxis_title="Rating",
                yaxis_title="Number of Employees",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Gap analysis for this skill
        gap_info = skill_distribution.get('gap_analysis', {})
        if gap_info:
            st.subheader(f"Gap Analysis for {selected_skill}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Manager Rates Higher", gap_info.get('positive_gaps', 0))
            
            with col2:
                st.metric("Self Rates Higher", gap_info.get('negative_gaps', 0))
            
            with col3:
                st.metric("Significant Gaps", gap_info.get('significant_gaps', 0))

# Employee comparison tool
st.divider()
st.header("👥 Employee Comparison")

# Multi-select for employees
employee_list = sorted(df['Employee'].unique())
selected_employees = st.multiselect(
    "Select employees to compare (max 5):",
    employee_list,
    max_selections=5,
    help="Compare skills profiles of multiple employees"
)

if selected_employees:
    comparison_chart = visualizer.create_skills_comparison_chart(df, selected_employees)
    st.plotly_chart(comparison_chart, use_container_width=True)
    
    # Comparison table
    st.subheader("Comparison Table")
    
    comparison_data = []
    avg_columns = [col for col in df.columns if col.endswith('_avg')]
    
    for employee in selected_employees:
        emp_data = df[df['Employee'] == employee].iloc[0]
        emp_gaps = gap_analysis[gap_analysis['Employee'] == employee].iloc[0]
        
        comparison_data.append({
            'Employee': employee,
            'Avg Skill Level': f"{emp_gaps['avg_skill_level']:.2f}",
            'Avg Gap Score': f"{emp_gaps['avg_gap_score']:.2f}",
            'Has Significant Gaps': "Yes" if emp_gaps['has_gaps'] else "No",
            'Strengths Count': len(emp_gaps['strengths']),
            'Development Areas': len(emp_gaps['development_areas'])
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)

# Actionable insights and recommendations
st.divider()
st.header("💡 Key Insights & Recommendations")

insights = []

# Organization-level insights
if org_insights.get('overall_skill_gaps'):
    top_org_gaps = org_insights['overall_skill_gaps'][:3]
    gap_skills = [gap['skill'] for gap in top_org_gaps]
    insights.append(f"🎯 **Priority training areas**: {', '.join(gap_skills)} - These skills show the lowest average ratings organization-wide.")

if org_insights.get('overall_skill_strengths'):
    top_strengths = org_insights['overall_skill_strengths'][:3]
    strength_skills = [strength['skill'] for strength in top_strengths]
    insights.append(f"💪 **Leverage organizational strengths**: {', '.join(strength_skills)} - Consider peer mentoring programs in these areas.")

# Gap-specific insights
if not gap_analysis.empty:
    high_gap_employees = gap_analysis[gap_analysis['avg_gap_score'] >= st.session_state.gap_threshold * 1.5]
    if not high_gap_employees.empty:
        insights.append(f"🔴 **{len(high_gap_employees)} employees** have very high skills gaps - Immediate attention needed for development planning.")
    
    perception_gaps = len(gap_analysis[gap_analysis['significant_gaps_count'] > 0])
    if perception_gaps > 0:
        insights.append(f"👁️ **{perception_gaps} employees** show perception gaps between self and manager assessments - Consider calibration discussions.")

if org_insights.get('high_performers'):
    insights.append(f"🌟 **{len(org_insights['high_performers'])} high performers** identified - Consider for leadership development or mentoring roles.")

# Display insights
if insights:
    for insight in insights:
        st.markdown(insight)
else:
    st.info("Organization shows balanced skills profile with no major concerns identified.")
