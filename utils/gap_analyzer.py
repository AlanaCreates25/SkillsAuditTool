import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

class GapAnalyzer:
    """Analyzes skills gaps and provides insights."""
    
    def __init__(self, gap_threshold: float = 2.0):
        """
        Initialize the gap analyzer.
        
        Args:
            gap_threshold: Minimum gap value to consider significant
        """
        self.gap_threshold = gap_threshold
    
    def calculate_gaps(self, df: pd.DataFrame, use_matrix_gaps: bool = False) -> pd.DataFrame:
        """
        Calculate comprehensive skills gaps for all employees.
        
        Args:
            df: Processed assessment data
            use_matrix_gaps: If True, use skills matrix gaps instead of perception gaps
            
        Returns:
            DataFrame with gap analysis results
        """
        if df.empty:
            return pd.DataFrame()
        
        # Get skill columns
        avg_columns = [col for col in df.columns if col.endswith('_avg')]
        
        # Choose gap type based on preference
        if use_matrix_gaps and any(col.endswith('_matrix_gap') for col in df.columns):
            gap_columns = [col for col in df.columns if col.endswith('_matrix_gap')]
            gap_type = "matrix"
        else:
            gap_columns = [col for col in df.columns if col.endswith('_gap')]
            gap_type = "perception"
        
        gap_analysis = []
        
        for _, row in df.iterrows():
            employee_name = row['Employee']
            
            # Calculate average skill level
            skill_averages = [row[col] for col in avg_columns if pd.notna(row[col]) and row[col] > 0]
            avg_skill_level = np.mean(skill_averages) if skill_averages else 0
            
            # Calculate gap metrics
            skill_gaps = [abs(row[col]) for col in gap_columns if pd.notna(row[col])]
            avg_gap_score = np.mean(skill_gaps) if skill_gaps else 0
            max_gap = max(skill_gaps) if skill_gaps else 0
            
            # Identify significant gaps
            significant_gaps = self._identify_significant_gaps(row, gap_columns, gap_type)
            
            # Identify strengths (high ratings)
            strengths = self._identify_strengths(row, avg_columns)
            
            # Identify development areas (low ratings)
            development_areas = self._identify_development_areas(row, avg_columns)
            
            gap_analysis.append({
                'Employee': employee_name,
                'avg_skill_level': avg_skill_level,
                'avg_gap_score': avg_gap_score,
                'max_gap': max_gap,
                'significant_gaps_count': len(significant_gaps),
                'significant_gaps': significant_gaps,
                'strengths': strengths,
                'development_areas': development_areas,
                'has_gaps': avg_gap_score >= self.gap_threshold,
                'gap_type': gap_type
            })
        
        return pd.DataFrame(gap_analysis)
    
    def _identify_significant_gaps(self, row: pd.Series, gap_columns: List[str], gap_type: str = "perception") -> List[Dict]:
        """Identify skills with significant gaps."""
        significant_gaps = []
        
        for col in gap_columns:
            if pd.notna(row[col]) and abs(row[col]) >= self.gap_threshold:
                if gap_type == "matrix":
                    skill_name = col.replace('_matrix_gap', '')
                    gap_direction = "Above standard" if row[col] > 0 else "Below standard"
                else:
                    skill_name = col.replace('_gap', '')
                    gap_direction = "Manager rates higher" if row[col] > 0 else "Self-rates higher"
                
                significant_gaps.append({
                    'skill': skill_name,
                    'gap_value': row[col],
                    'direction': gap_direction,
                    'gap_type': gap_type
                })
        
        return sorted(significant_gaps, key=lambda x: abs(x['gap_value']), reverse=True)
    
    def _identify_strengths(self, row: pd.Series, avg_columns: List[str], threshold: float = 4.0) -> List[Dict]:
        """Identify employee strengths (high-rated skills)."""
        strengths = []
        
        for col in avg_columns:
            if pd.notna(row[col]) and row[col] >= threshold:
                skill_name = col.replace('_avg', '')
                strengths.append({
                    'skill': skill_name,
                    'rating': row[col]
                })
        
        return sorted(strengths, key=lambda x: x['rating'], reverse=True)
    
    def _identify_development_areas(self, row: pd.Series, avg_columns: List[str], threshold: float = 2.5) -> List[Dict]:
        """Identify areas needing development (low-rated skills)."""
        development_areas = []
        
        for col in avg_columns:
            if pd.notna(row[col]) and 0 < row[col] <= threshold:
                skill_name = col.replace('_avg', '')
                development_areas.append({
                    'skill': skill_name,
                    'rating': row[col]
                })
        
        return sorted(development_areas, key=lambda x: x['rating'])
    
    def get_organization_insights(self, df: pd.DataFrame) -> Dict:
        """
        Generate organization-wide insights from skills data.
        
        Args:
            df: Processed assessment data
            
        Returns:
            Dictionary with organization insights
        """
        if df.empty:
            return {}
        
        avg_columns = [col for col in df.columns if col.endswith('_avg')]
        gap_columns = [col for col in df.columns if col.endswith('_gap')]
        
        insights = {
            'total_employees': len(df),
            'skills_assessed': len(avg_columns),
            'overall_skill_strengths': [],
            'overall_skill_gaps': [],
            'high_performers': [],
            'development_priorities': []
        }
        
        # Calculate skill averages across organization
        for col in avg_columns:
            skill_name = col.replace('_avg', '')
            skill_data = df[col].dropna()
            if not skill_data.empty:
                avg_rating = skill_data.mean()
                insights['overall_skill_strengths' if avg_rating >= 3.5 else 'overall_skill_gaps'].append({
                    'skill': skill_name,
                    'average_rating': avg_rating,
                    'employee_count': len(skill_data)
                })
        
        # Sort by rating
        insights['overall_skill_strengths'].sort(key=lambda x: x['average_rating'], reverse=True)
        insights['overall_skill_gaps'].sort(key=lambda x: x['average_rating'])
        
        # Identify high performers (top 20% by average skill level)
        employee_averages = []
        for _, row in df.iterrows():
            skill_averages = [row[col] for col in avg_columns if pd.notna(row[col]) and row[col] > 0]
            if skill_averages:
                avg_skill = np.mean(skill_averages)
                employee_averages.append({
                    'employee': row['Employee'],
                    'average_skill': avg_skill
                })
        
        employee_averages.sort(key=lambda x: x['average_skill'], reverse=True)
        top_20_percent = max(1, len(employee_averages) // 5)
        insights['high_performers'] = employee_averages[:top_20_percent]
        
        return insights
    
    def get_skill_distribution(self, df: pd.DataFrame, skill_name: str) -> Dict:
        """
        Get distribution analysis for a specific skill.
        
        Args:
            df: Processed assessment data
            skill_name: Name of the skill to analyze
            
        Returns:
            Dictionary with skill distribution data
        """
        avg_col = f"{skill_name}_avg"
        gap_col = f"{skill_name}_gap"
        
        if avg_col not in df.columns:
            return {}
        
        skill_data = df[avg_col].dropna()
        gap_data = df[gap_col].dropna() if gap_col in df.columns else pd.Series()
        
        distribution = {
            'skill_name': skill_name,
            'total_assessments': len(skill_data),
            'average_rating': skill_data.mean() if not skill_data.empty else 0,
            'median_rating': skill_data.median() if not skill_data.empty else 0,
            'std_deviation': skill_data.std() if not skill_data.empty else 0,
            'min_rating': skill_data.min() if not skill_data.empty else 0,
            'max_rating': skill_data.max() if not skill_data.empty else 0,
            'rating_distribution': {},
            'gap_analysis': {}
        }
        
        # Rating distribution
        if not skill_data.empty:
            for rating in range(1, 6):  # Assuming 1-5 scale
                count = len(skill_data[skill_data.round() == rating])
                distribution['rating_distribution'][f"rating_{rating}"] = count
        
        # Gap analysis
        if not gap_data.empty:
            distribution['gap_analysis'] = {
                'average_gap': gap_data.mean(),
                'positive_gaps': len(gap_data[gap_data > 0]),  # Manager rates higher
                'negative_gaps': len(gap_data[gap_data < 0]),  # Self rates higher
                'no_gaps': len(gap_data[gap_data == 0]),
                'significant_gaps': len(gap_data[abs(gap_data) >= self.gap_threshold])
            }
        
        return distribution
