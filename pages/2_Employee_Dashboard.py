import streamlit as st
import pandas as pd
from utils.gap_analyzer import GapAnalyzer
from utils.visualizations import SkillsVisualizer
from utils.database import SkillsDatabase
from utils.training_resources import TrainingResourceManager
import plotly.express as px
from datetime import datetime, timedelta
import json

st.set_page_config(
    page_title="Employee Dashboard - Skills Audit Tool",
    page_icon="👤",
    layout="wide"
)

st.title("👤 Employee Dashboard")
st.markdown("View individual employee skills profiles and assessment details.")

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
training_manager = TrainingResourceManager()
df = st.session_state.processed_data

# Employee selection
st.sidebar.header("🔍 Select Employee")
employee_list = sorted(df['Employee'].unique())
selected_employee = st.sidebar.selectbox("Choose an employee:", employee_list)

# Gap analysis type selection
if st.session_state.skills_matrix is not None:
    use_matrix_gaps = st.sidebar.checkbox(
        "Use Skills Matrix Analysis",
        value=st.session_state.get('use_matrix_gaps', False),
        help="Compare against skills matrix standards"
    )
else:
    use_matrix_gaps = False

# Get employee data
employee_data = df[df['Employee'] == selected_employee].iloc[0]

# Calculate gap analysis for this employee
gap_analysis = analyzer.calculate_gaps(df, use_matrix_gaps)
employee_gaps = gap_analysis[gap_analysis['Employee'] == selected_employee].iloc[0]

# Save gap analysis to database
try:
    db = SkillsDatabase()
    gap_type = "matrix" if use_matrix_gaps else "perception"
    db.save_gap_analysis(gap_analysis, gap_type)
except Exception:
    pass  # Fail silently if database not available

# Main dashboard layout
col1, col2 = st.columns([2, 1])

with col1:
    st.header(f"📊 Skills Profile: {selected_employee}")
    
    # Create and display radar chart
    radar_chart = visualizer.create_employee_radar_chart(employee_data)
    st.plotly_chart(radar_chart, use_container_width=True)

with col2:
    st.header("📈 Key Metrics")
    
    # Key performance indicators
    st.metric(
        "Average Skill Level",
        f"{employee_gaps['avg_skill_level']:.2f}",
        help="Average rating across all skills (1-5 scale)"
    )
    
    st.metric(
        "Average Gap Score",
        f"{employee_gaps['avg_gap_score']:.2f}",
        delta=f"Threshold: {st.session_state.gap_threshold}",
        help="Average difference between manager and self-assessment"
    )
    
    st.metric(
        "Skills with Significant Gaps",
        employee_gaps['significant_gaps_count'],
        help=f"Number of skills with gaps >= {st.session_state.gap_threshold}"
    )
    
    # Gap status indicator
    if employee_gaps['has_gaps']:
        st.error("🔴 Has Significant Skills Gaps")
    else:
        st.success("🟢 No Significant Skills Gaps")

# Detailed skills breakdown
st.divider()
st.header("🔍 Detailed Skills Analysis")

# Create tabs for different views
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Skills Ratings", "Strengths", "Development Areas", "Gap Analysis", "Development Plan"])

with tab1:
    st.subheader("📊 All Skills Ratings")
    
    # Get all skill data
    avg_columns = [col for col in df.columns if col.endswith('_avg')]
    emp_columns = [col for col in df.columns if col.endswith('_emp')]
    mgr_columns = [col for col in df.columns if col.endswith('_mgr')]
    
    skills_data = []
    for avg_col in avg_columns:
        skill_name = avg_col.replace('_avg', '')
        emp_col = f"{skill_name}_emp"
        mgr_col = f"{skill_name}_mgr"
        
        # Get ratings from both datasets
        emp_rating = st.session_state.employee_data[st.session_state.employee_data['Employee'] == selected_employee][skill_name].iloc[0] if not st.session_state.employee_data.empty else 0
        mgr_rating = st.session_state.manager_data[st.session_state.manager_data['Employee'] == selected_employee][skill_name].iloc[0] if not st.session_state.manager_data.empty else 0
        
        skills_data.append({
            'Skill': skill_name,
            'Self-Assessment': emp_rating if emp_rating > 0 else 'N/A',
            'Manager Assessment': mgr_rating if mgr_rating > 0 else 'N/A',
            'Average': employee_data[avg_col] if pd.notna(employee_data[avg_col]) else 'N/A'
        })
    
    skills_df = pd.DataFrame(skills_data)
    st.dataframe(skills_df, use_container_width=True)
    
    # Skills rating distribution chart
    if skills_data:
        ratings_for_chart = []
        skills_for_chart = []
        sources = []
        
        for skill_data in skills_data:
            skill = skill_data['Skill']
            if skill_data['Self-Assessment'] != 'N/A':
                ratings_for_chart.append(skill_data['Self-Assessment'])
                skills_for_chart.append(skill)
                sources.append('Self-Assessment')
            
            if skill_data['Manager Assessment'] != 'N/A':
                ratings_for_chart.append(skill_data['Manager Assessment'])
                skills_for_chart.append(skill)
                sources.append('Manager Assessment')
        
        if ratings_for_chart:
            chart_df = pd.DataFrame({
                'Skill': skills_for_chart,
                'Rating': ratings_for_chart,
                'Source': sources
            })
            
            fig = px.bar(
                chart_df,
                x='Skill',
                y='Rating',
                color='Source',
                barmode='group',
                title='Skills Ratings Comparison',
                height=400
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("💪 Strengths")
    
    strengths = employee_gaps['strengths']
    if strengths:
        st.markdown("**Top performing skills (4.0+ rating):**")
        
        for strength in strengths[:5]:  # Show top 5 strengths
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"🌟 **{strength['skill']}**")
            with col2:
                st.write(f"{strength['rating']:.1f}/5.0")
        
        # Strengths chart
        if len(strengths) > 0:
            strengths_df = pd.DataFrame(strengths)
            fig = px.bar(
                strengths_df.head(10),
                x='rating',
                y='skill',
                orientation='h',
                title='Top Skills (Strengths)',
                color='rating',
                color_continuous_scale='Greens'
            )
            fig.update_layout(height=max(300, len(strengths) * 30))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No skills rated above 4.0 found.")

with tab3:
    st.subheader("📚 Development Areas")
    
    development_areas = employee_gaps['development_areas']
    if development_areas:
        st.markdown("**Skills needing development (2.5 or below):**")
        
        for area in development_areas[:5]:  # Show top 5 development areas
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📈 **{area['skill']}**")
            with col2:
                st.write(f"{area['rating']:.1f}/5.0")
        
        # Development areas chart
        if len(development_areas) > 0:
            dev_df = pd.DataFrame(development_areas)
            fig = px.bar(
                dev_df.head(10),
                x='rating',
                y='skill',
                orientation='h',
                title='Skills Needing Development',
                color='rating',
                color_continuous_scale='Reds'
            )
            fig.update_layout(height=max(300, len(development_areas) * 30))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("🎉 No skills requiring immediate development identified!")

with tab4:
    st.subheader("🔍 Gap Analysis")
    
    significant_gaps = employee_gaps['significant_gaps']
    if significant_gaps:
        st.markdown(f"**Skills with significant gaps (>= {st.session_state.gap_threshold}):**")
        
        for gap in significant_gaps:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 2])
                
                with col1:
                    st.write(f"**{gap['skill']}**")
                
                with col2:
                    gap_color = "🔴" if abs(gap['gap_value']) >= st.session_state.gap_threshold else "🟡"
                    st.write(f"{gap_color} {gap['gap_value']:+.1f}")
                
                with col3:
                    st.write(f"_{gap['direction']}_")
        
        # Gap analysis chart
        if len(significant_gaps) > 0:
            gaps_df = pd.DataFrame(significant_gaps)
            fig = px.bar(
                gaps_df,
                x='gap_value',
                y='skill',
                orientation='h',
                title='Significant Skills Gaps',
                color='gap_value',
                color_continuous_scale='RdBu',
                color_continuous_midpoint=0
            )
            fig.update_layout(height=max(300, len(significant_gaps) * 30))
            fig.add_vline(x=0, line_dash="dash", line_color="black", annotation_text="No Gap")
            st.plotly_chart(fig, use_container_width=True)
        
        # Gap interpretation
        st.markdown("**Gap Interpretation:**")
        if use_matrix_gaps:
            st.markdown("""
            - **Positive values**: Above required skill standard
            - **Negative values**: Below required skill standard
            - **Zero**: Meets exactly the required standard
            """)
        else:
            st.markdown("""
            - **Positive values**: Manager rates higher than self-assessment
            - **Negative values**: Self-assessment higher than manager rating
            - **Zero**: Perfect alignment between assessments
            """)
    else:
        st.success("🎉 No significant skills gaps identified!")

with tab5:
    st.subheader("📋 Individual Development Plan (IDP)")
    
    # Generate development plan
    significant_gaps = employee_gaps['significant_gaps']
    strengths = employee_gaps['strengths']
    
    if significant_gaps or len(strengths) > 0:
        # Development plan configuration
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🎯 Development Goals")
            
            # Timeline selection
            timeline_options = {
                "3 months (12 weeks)": 12,
                "6 months (26 weeks)": 26,
                "1 year (52 weeks)": 52
            }
            
            selected_timeline = st.selectbox(
                "Development Plan Duration:",
                list(timeline_options.keys()),
                index=0
            )
            timeline_weeks = timeline_options[selected_timeline]
            
            # Generate comprehensive development plan
            development_plan = training_manager.create_development_plan(
                selected_employee, 
                significant_gaps, 
                strengths, 
                timeline_weeks
            )
            
            # Display plan overview
            st.markdown("#### 📊 Plan Overview")
            plan_col1, plan_col2, plan_col3 = st.columns(3)
            
            with plan_col1:
                st.metric("Skills to Develop", len(development_plan['skills_to_develop']))
            
            with plan_col2:
                st.metric("Plan Duration", f"{timeline_weeks} weeks")
            
            with plan_col3:
                completion_date = datetime.strptime(development_plan['target_completion'], "%Y-%m-%d")
                st.metric("Target Completion", completion_date.strftime("%b %Y"))
        
        with col2:
            st.markdown("### 🎖️ Current Strengths")
            if strengths:
                for strength in strengths[:3]:
                    st.success(f"✓ {strength['skill']} ({strength['rating']:.1f}/5.0)")
            else:
                st.info("Continue building on existing skills")
        
        # Training Recommendations
        st.divider()
        st.markdown("### 📚 Recommended Training & Resources")
        
        training_recommendations = development_plan['recommended_resources']
        
        if training_recommendations:
            # Priority sections
            high_priority = [t for t in training_recommendations if t['priority'] == 'High']
            medium_priority = [t for t in training_recommendations if t['priority'] == 'Medium']
            
            if high_priority:
                st.markdown("#### 🔴 High Priority Training")
                for i, training in enumerate(high_priority[:3]):
                    with st.expander(f"{training['title']} - {training['skill']}"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Provider:** {training['provider']}")
                            st.write(f"**Duration:** {training['duration']}")
                            st.write(f"**Description:** {training['description']}")
                            st.write(f"**Skill Level:** {training['skill_level']}")
                            
                            if 'url' in training and training['url']:
                                st.markdown(f"[🔗 Access Training]({training['url']})")
                        
                        with col2:
                            st.write(f"**Type:** {training['type']}")
                            st.write(f"**Priority:** {training['priority']}")
                            
                            # Assignment checkbox
                            assigned_key = f"assigned_{selected_employee}_{i}_high"
                            if assigned_key not in st.session_state:
                                st.session_state[assigned_key] = False
                            
                            assigned = st.checkbox(
                                "Assign to Employee", 
                                key=assigned_key,
                                value=st.session_state[assigned_key]
                            )
                            
                            if assigned:
                                st.success("✅ Assigned")
                                target_date = st.date_input(
                                    "Target Completion:",
                                    value=datetime.now() + timedelta(weeks=4),
                                    key=f"target_{assigned_key}"
                                )
            
            if medium_priority:
                st.markdown("#### 🟡 Secondary Development Areas")
                for i, training in enumerate(medium_priority[:3]):
                    with st.expander(f"{training['title']} - {training['skill']}"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Provider:** {training['provider']}")
                            st.write(f"**Duration:** {training['duration']}")
                            st.write(f"**Description:** {training['description']}")
                            
                            if 'url' in training and training['url']:
                                st.markdown(f"[🔗 Access Training]({training['url']})")
                        
                        with col2:
                            st.write(f"**Type:** {training['type']}")
                            
                            # Assignment checkbox
                            assigned_key = f"assigned_{selected_employee}_{i}_medium"
                            if assigned_key not in st.session_state:
                                st.session_state[assigned_key] = False
                            
                            assigned = st.checkbox(
                                "Assign to Employee", 
                                key=assigned_key,
                                value=st.session_state[assigned_key]
                            )
                            
                            if assigned:
                                st.success("✅ Assigned")
        
        # Custom Training Resources
        st.divider()
        st.markdown("### ➕ Add Custom Training Resource")
        
        with st.expander("Add Custom Resource"):
            custom_skill = st.selectbox(
                "Select skill for custom resource:",
                development_plan['skills_to_develop'] if development_plan['skills_to_develop'] else ["General Development"]
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                custom_title = st.text_input("Training Title")
                custom_provider = st.text_input("Provider/Source")
                custom_type = st.selectbox(
                    "Training Type",
                    ["Internal Training", "External Course", "Workshop", "Mentoring", "Book/Reading", "Other"]
                )
            
            with col2:
                custom_duration = st.text_input("Duration")
                custom_url = st.text_input("URL (optional)")
                custom_description = st.text_area("Description")
            
            if st.button("Add Custom Resource"):
                if custom_title and custom_provider:
                    custom_resource = {
                        "title": custom_title,
                        "provider": custom_provider,
                        "type": custom_type,
                        "duration": custom_duration,
                        "url": custom_url,
                        "description": custom_description,
                        "skill_level": "All Levels",
                        "custom": True
                    }
                    
                    if training_manager.add_custom_resource(custom_skill, custom_resource):
                        st.success(f"Custom resource added for {custom_skill}!")
                        st.rerun()
                else:
                    st.error("Please fill in at least title and provider.")
        
        # Development Timeline & Milestones
        st.divider()
        st.markdown("### 📅 Development Timeline & Milestones")
        
        milestones = development_plan['milestones']
        
        # Create timeline visualization
        milestone_df = pd.DataFrame(milestones)
        if not milestone_df.empty:
            fig = px.timeline(
                milestone_df,
                x_start=[datetime.now() + timedelta(weeks=m['week']-1) for m in milestones],
                x_end=[datetime.now() + timedelta(weeks=m['week']) for m in milestones],
                y='milestone',
                title='Development Plan Timeline',
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Milestone checklist
        st.markdown("#### 📋 Milestone Checklist")
        for milestone in milestones:
            milestone_key = f"milestone_{selected_employee}_{milestone['week']}"
            if milestone_key not in st.session_state:
                st.session_state[milestone_key] = False
            
            completed = st.checkbox(
                f"Week {milestone['week']}: {milestone['milestone']}",
                key=milestone_key,
                value=st.session_state[milestone_key]
            )
            
            if completed:
                st.success(f"✅ Deliverable: {milestone['deliverable']}")
            else:
                st.info(f"📋 Deliverable: {milestone['deliverable']}")
        
        # Success Metrics
        st.divider()
        st.markdown("### 📈 Success Metrics & Progress Tracking")
        
        success_metrics = development_plan['success_metrics']
        
        metrics_df = pd.DataFrame(success_metrics)
        if not metrics_df.empty:
            st.dataframe(
                metrics_df[['skill', 'current_gap', 'target_improvement', 'target_timeline']].rename(columns={
                    'skill': 'Skill',
                    'current_gap': 'Current Gap',
                    'target_improvement': 'Target Improvement',
                    'target_timeline': 'Timeline'
                }),
                use_container_width=True
            )
        
        # Export Development Plan
        st.divider()
        st.markdown("### 📄 Export Development Plan")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Generate Development Plan Report"):
                # Create comprehensive report
                plan_json = json.dumps(development_plan, indent=2, default=str)
                
                st.download_button(
                    label="📥 Download Development Plan (JSON)",
                    data=plan_json,
                    file_name=f"development_plan_{selected_employee.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("📋 Create Action Plan Summary"):
                # Create summary document
                summary = f"""
Individual Development Plan - {selected_employee}
Plan Created: {development_plan['plan_created']}
Duration: {development_plan['plan_duration_weeks']} weeks
Target Completion: {development_plan['target_completion']}

SKILLS TO DEVELOP:
{chr(10).join(f"• {skill}" for skill in development_plan['skills_to_develop'])}

CURRENT STRENGTHS:
{chr(10).join(f"• {strength}" for strength in development_plan['current_strengths'])}

HIGH PRIORITY TRAINING:
{chr(10).join(f"• {t['title']} ({t['provider']})" for t in development_plan['immediate_priorities'])}

SUCCESS METRICS:
{chr(10).join(f"• {m['skill']}: Improve by {m['target_improvement']} points" for m in development_plan['success_metrics'])}
                """
                
                st.download_button(
                    label="📥 Download Action Plan (TXT)",
                    data=summary,
                    file_name=f"action_plan_{selected_employee.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
    
    else:
        st.info("🎉 This employee shows strong performance across all assessed skills. Consider advanced development opportunities or leadership training.")

# Action recommendations
st.divider()
st.header("💡 Recommendations")

# Generate recommendations based on analysis
recommendations = []

if employee_gaps['has_gaps']:
    recommendations.append("🎯 **Focus on skills with significant gaps** - Work with manager to align expectations and create development plans.")

if employee_gaps['development_areas']:
    top_dev_areas = [area['skill'] for area in employee_gaps['development_areas'][:3]]
    recommendations.append(f"📚 **Prioritize development in**: {', '.join(top_dev_areas)}")

if employee_gaps['strengths']:
    top_strengths = [strength['skill'] for strength in employee_gaps['strengths'][:3]]
    recommendations.append(f"💪 **Leverage strengths in**: {', '.join(top_strengths)} - Consider mentoring others or taking on leadership roles in these areas.")

if employee_gaps['avg_skill_level'] >= 4.0:
    recommendations.append("🌟 **High performer** - Consider advanced training or leadership development opportunities.")
elif employee_gaps['avg_skill_level'] <= 2.5:
    recommendations.append("📈 **Development focus needed** - Create comprehensive skills development plan with regular check-ins.")

if recommendations:
    for rec in recommendations:
        st.markdown(rec)
else:
    st.info("Employee shows balanced skills profile with no major concerns.")

# Export individual report
st.divider()
st.header("📄 Export Report")

if st.button("📊 Generate Individual Report", type="secondary"):
    # Create individual report data
    report_data = {
        'Employee': [selected_employee],
        'Average_Skill_Level': [employee_gaps['avg_skill_level']],
        'Average_Gap_Score': [employee_gaps['avg_gap_score']],
        'Significant_Gaps_Count': [employee_gaps['significant_gaps_count']],
        'Has_Significant_Gaps': [employee_gaps['has_gaps']],
        'Top_Strengths': [', '.join([s['skill'] for s in employee_gaps['strengths'][:3]])],
        'Development_Areas': [', '.join([d['skill'] for d in employee_gaps['development_areas'][:3]])],
        'Significant_Gaps': [', '.join([g['skill'] for g in employee_gaps['significant_gaps']])]
    }
    
    report_df = pd.DataFrame(report_data)
    
    # Convert to CSV
    csv = report_df.to_csv(index=False)
    
    st.download_button(
        label="📥 Download Individual Report (CSV)",
        data=csv,
        file_name=f"skills_report_{selected_employee.replace(' ', '_')}.csv",
        mime="text/csv"
    )
