import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Any

class SkillsVisualizer:
    """Creates interactive visualizations for skills assessment data."""
    
    def __init__(self):
        """Initialize the visualizer with default color schemes."""
        self.color_palette = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
    
    def create_employee_radar_chart(self, employee_data: pd.Series) -> go.Figure:
        """
        Create a radar chart for individual employee skills.
        
        Args:
            employee_data: Series containing employee assessment data
            
        Returns:
            Plotly figure object
        """
        # Extract skill data
        avg_columns = [col for col in employee_data.index if col.endswith('_avg')]
        skills = [col.replace('_avg', '') for col in avg_columns]
        ratings = [employee_data[col] for col in avg_columns if pd.notna(employee_data[col])]
        
        if not skills or not ratings:
            # Return empty chart if no data
            fig = go.Figure()
            fig.add_annotation(
                text="No skill data available for this employee",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        # Create radar chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=ratings,
            theta=skills,
            fill='toself',
            name=employee_data.get('Employee', 'Employee'),
            line_color='rgb(31, 119, 180)',
            fillcolor='rgba(31, 119, 180, 0.2)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5],
                    tickmode='linear',
                    tick0=0,
                    dtick=1
                )
            ),
            showlegend=True,
            title=f"Skills Profile: {employee_data.get('Employee', 'Employee')}",
            height=500
        )
        
        return fig
    
    def create_skills_comparison_chart(self, df: pd.DataFrame, selected_employees: List[str]) -> go.Figure:
        """
        Create a comparison chart for multiple employees.
        
        Args:
            df: Processed assessment data
            selected_employees: List of employee names to compare
            
        Returns:
            Plotly figure object
        """
        if not selected_employees:
            fig = go.Figure()
            fig.add_annotation(
                text="Select employees to compare",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        # Filter data for selected employees
        employee_data = df[df['Employee'].isin(selected_employees)]
        avg_columns = [col for col in df.columns if col.endswith('_avg')]
        skills = [col.replace('_avg', '') for col in avg_columns]
        
        fig = go.Figure()
        
        for i, employee in enumerate(selected_employees):
            emp_data = employee_data[employee_data['Employee'] == employee]
            if not emp_data.empty:
                ratings = [emp_data.iloc[0][col] for col in avg_columns]
                
                fig.add_trace(go.Scatterpolar(
                    r=ratings,
                    theta=skills,
                    fill='toself',
                    name=employee,
                    line_color=self.color_palette[i % len(self.color_palette)],
                    fillcolor=f'rgba{tuple(list(px.colors.hex_to_rgb(self.color_palette[i % len(self.color_palette)])) + [0.1])}'
                ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5],
                    tickmode='linear',
                    tick0=0,
                    dtick=1
                )
            ),
            showlegend=True,
            title="Skills Comparison",
            height=600
        )
        
        return fig
    
    def create_skills_gap_heatmap(self, df: pd.DataFrame) -> go.Figure:
        """
        Create a heatmap showing skills gaps across all employees.
        
        Args:
            df: Processed assessment data
            
        Returns:
            Plotly figure object
        """
        gap_columns = [col for col in df.columns if col.endswith('_gap')]
        
        if not gap_columns:
            fig = go.Figure()
            fig.add_annotation(
                text="No gap data available",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        # Prepare data for heatmap
        skills = [col.replace('_gap', '') for col in gap_columns]
        employees = df['Employee'].tolist()
        
        # Create matrix of gap values
        gap_matrix = []
        for _, row in df.iterrows():
            gap_row = [row[col] for col in gap_columns]
            gap_matrix.append(gap_row)
        
        fig = go.Figure(data=go.Heatmap(
            z=gap_matrix,
            x=skills,
            y=employees,
            colorscale='RdBu',
            zmid=0,
            text=[[f"{val:.1f}" for val in row] for row in gap_matrix],
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False,
            colorbar=dict(
                title="Gap Score",
                titleside="right"
            )
        ))
        
        fig.update_layout(
            title="Skills Gap Analysis Heatmap",
            xaxis_title="Skills",
            yaxis_title="Employees",
            height=max(400, len(employees) * 25),
            width=max(600, len(skills) * 80)
        )
        
        return fig
    
    def create_organization_overview(self, df: pd.DataFrame) -> go.Figure:
        """
        Create an organization-wide skills overview chart.
        
        Args:
            df: Processed assessment data
            
        Returns:
            Plotly figure object
        """
        avg_columns = [col for col in df.columns if col.endswith('_avg')]
        skills = [col.replace('_avg', '') for col in avg_columns]
        
        # Calculate average ratings for each skill across organization
        skill_averages = []
        skill_counts = []
        
        for col in avg_columns:
            skill_data = df[col].dropna()
            if not skill_data.empty:
                skill_averages.append(skill_data.mean())
                skill_counts.append(len(skill_data))
            else:
                skill_averages.append(0)
                skill_counts.append(0)
        
        # Create subplot with two y-axes
        fig = make_subplots(
            rows=1, cols=1,
            secondary_y=True,
            specs=[[{"secondary_y": True}]]
        )
        
        # Add bar chart for average ratings
        fig.add_trace(
            go.Bar(
                x=skills,
                y=skill_averages,
                name="Average Rating",
                marker_color='lightblue',
                yaxis='y',
                offsetgroup=1
            ),
            secondary_y=False
        )
        
        # Add line chart for assessment counts
        fig.add_trace(
            go.Scatter(
                x=skills,
                y=skill_counts,
                mode='lines+markers',
                name="Assessment Count",
                line=dict(color='red', width=2),
                marker=dict(size=8),
                yaxis='y2'
            ),
            secondary_y=True
        )
        
        # Update layout
        fig.update_layout(
            title="Organization Skills Overview",
            xaxis_title="Skills",
            height=500,
            hovermode='x unified'
        )
        
        fig.update_yaxes(title_text="Average Rating (1-5)", secondary_y=False)
        fig.update_yaxes(title_text="Number of Assessments", secondary_y=True)
        
        return fig
    
    def create_gap_distribution_chart(self, df: pd.DataFrame) -> go.Figure:
        """
        Create a chart showing distribution of skills gaps.
        
        Args:
            df: Processed assessment data
            
        Returns:
            Plotly figure object
        """
        gap_columns = [col for col in df.columns if col.endswith('_gap')]
        
        if not gap_columns:
            fig = go.Figure()
            fig.add_annotation(
                text="No gap data available",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        # Collect all gap values
        all_gaps = []
        for col in gap_columns:
            gap_data = df[col].dropna()
            all_gaps.extend(gap_data.tolist())
        
        if not all_gaps:
            fig = go.Figure()
            fig.add_annotation(
                text="No gap data to display",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        # Create histogram
        fig = go.Figure(data=[
            go.Histogram(
                x=all_gaps,
                nbinsx=20,
                marker_color='lightcoral',
                opacity=0.7,
                name='Gap Distribution'
            )
        ])
        
        # Add vertical line at zero
        fig.add_vline(
            x=0,
            line_dash="dash",
            line_color="black",
            annotation_text="No Gap"
        )
        
        fig.update_layout(
            title="Skills Gap Distribution",
            xaxis_title="Gap Score (Manager Rating - Self Rating)",
            yaxis_title="Frequency",
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_employee_performance_scatter(self, gap_analysis: pd.DataFrame) -> go.Figure:
        """
        Create a scatter plot showing employee performance vs gaps.
        
        Args:
            gap_analysis: DataFrame from GapAnalyzer.calculate_gaps()
            
        Returns:
            Plotly figure object
        """
        if gap_analysis.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No performance data available",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        # Create scatter plot
        fig = go.Figure()
        
        colors = ['red' if has_gaps else 'green' for has_gaps in gap_analysis['has_gaps']]
        
        fig.add_trace(go.Scatter(
            x=gap_analysis['avg_skill_level'],
            y=gap_analysis['avg_gap_score'],
            mode='markers',
            marker=dict(
                size=10,
                color=colors,
                opacity=0.7,
                line=dict(width=1, color='DarkSlateGrey')
            ),
            text=gap_analysis['Employee'],
            hovertemplate='<b>%{text}</b><br>' +
                         'Avg Skill Level: %{x:.2f}<br>' +
                         'Avg Gap Score: %{y:.2f}<br>' +
                         '<extra></extra>',
            name='Employees'
        ))
        
        fig.update_layout(
            title="Employee Performance vs Skills Gaps",
            xaxis_title="Average Skill Level",
            yaxis_title="Average Gap Score",
            height=500,
            showlegend=False
        )
        
        return fig
