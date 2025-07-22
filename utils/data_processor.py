import pandas as pd
import numpy as np
import streamlit as st
from typing import Tuple, List, Dict, Any

class DataProcessor:
    """Handles processing of MS Forms CSV data for skills assessments."""
    
    def __init__(self):
        self.required_columns = ['Employee', 'Email']  # Minimum required columns
    
    def validate_csv_structure(self, df: pd.DataFrame, assessment_type: str) -> Tuple[bool, str]:
        """
        Validate the structure of uploaded CSV data.
        
        Args:
            df: DataFrame to validate
            assessment_type: Type of assessment ('employee', 'manager', or 'skills_matrix')
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if df.empty:
            return False, "File is empty"
        
        # Check for required columns based on assessment type
        if assessment_type in ['employee', 'manager']:
            # Check for employee name column
            name_columns = [col for col in df.columns if 
                          any(keyword in col.lower() for keyword in ['name', 'employee', 'person'])]
            
            if not name_columns:
                return False, "No employee name column found. Expected column containing 'name', 'employee', or 'person'"
            
            # Check for skill columns (should be numeric ratings)
            skill_columns = self._identify_skill_columns(df)
            
            if len(skill_columns) < 1:
                return False, "No skill assessment columns found. Expected columns with numeric ratings (1-5)"
            
            return True, ""
        
        elif assessment_type == 'skills_matrix':
            # Handle Excel-style skills matrix (skill names in row 1, columns C to AQ)
            if len(df) >= 1:  # Must have at least one row of data
                # Check if this looks like an Excel export with skill names in row 1, columns C onwards
                skill_columns = [col for col in df.columns[2:] if col and str(col).strip()]  # Start from column C (index 2)
                
                if len(skill_columns) > 0:
                    # Check if row 1 contains skill names (text) and subsequent rows contain numeric levels
                    first_row = df.iloc[0]
                    skill_names_found = 0
                    for col in skill_columns[:5]:  # Check first 5 columns
                        cell_value = str(first_row[col]).strip()
                        if cell_value and cell_value.lower() not in ['unnamed', 'nan', ''] and not cell_value.replace('.','').isdigit():
                            skill_names_found += 1
                    
                    if skill_names_found >= 2:  # If at least 2 columns have skill names
                        return True, ""
            
            # Check for traditional format (skill name and required level columns)
            required_columns = ['skill', 'required_level']
            df_columns_lower = [col.lower() for col in df.columns]
            missing_columns = []
            
            for req_col in required_columns:
                if not any(req_col in col_lower for col_lower in df_columns_lower):
                    missing_columns.append(req_col)
            
            if missing_columns and len(df.columns) < 3:
                return False, f"Skills matrix should either have columns from C to AQ with skills data in row 1, or traditional format with columns: {', '.join(required_columns)}"
            
            return True, ""
        
        return False, "Unknown assessment type"
    
    def _identify_skill_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Identify columns that contain skill assessments.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            List of skill column names
        """
        # Exclude system columns and identify skill columns
        exclude_columns = [
            'Employee', 'Email', 'Timestamp', 'Start time', 'Completion time',
            'Name', 'ID', 'Submit Date', 'Response ID', 'Submission ID'
        ]
        
        skill_columns = []
        for col in df.columns:
            if col not in exclude_columns:
                # Check if column contains numeric data (ratings)
                try:
                    numeric_data = pd.to_numeric(df[col], errors='coerce')
                    if not numeric_data.isna().all():
                        skill_columns.append(col)
                except:
                    continue
        
        return skill_columns
    
    def process_skills_matrix_excel_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process skills matrix in Excel format where:
        - Column A contains Designation/Job Title
        - Column B contains Department
        - Row 1, Columns C to AQ contain skill names only
        - Required levels are in subsequent rows
        
        Args:
            df: Raw DataFrame from Excel/CSV
            
        Returns:
            Standardized skills matrix DataFrame with Skill, Required_Level, Job_Title, and Department columns
        """
        skills_data = []
        
        # Extract skill names from row 1, columns C onwards (index 2+)
        skill_columns = df.columns[2:]  # Start from column C (index 2)
        
        # Get skill names from the first row (row 1)
        skill_names = {}
        if len(df) > 0:
            first_row = df.iloc[0]
            for col_idx, col in enumerate(skill_columns):
                skill_name = str(first_row[col]).strip() if not pd.isna(first_row[col]) else str(col).strip()
                if skill_name and skill_name.lower() not in ['unnamed', 'nan', '']:
                    skill_names[col] = skill_name
        
        # Process each data row (starting from row 2, which is index 1)
        for row_idx in range(1 if len(df) > 1 else 0, len(df)):
            row = df.iloc[row_idx]
            
            # Get job title and department from columns A and B
            job_title = str(row[df.columns[0]]).strip() if len(df.columns) > 0 and not pd.isna(row[df.columns[0]]) else "General"
            department = str(row[df.columns[1]]).strip() if len(df.columns) > 1 and not pd.isna(row[df.columns[1]]) else "General"
            
            # Process skill levels for this row
            for col, skill_name in skill_names.items():
                try:
                    required_level = float(row[col])
                    if 1 <= required_level <= 5:  # Valid skill level
                        skills_data.append({
                            'Skill': skill_name,
                            'Required_Level': required_level,
                            'Job_Title': job_title,
                            'Department': department
                        })
                except (ValueError, TypeError):
                    # Skip columns with non-numeric values
                    continue
        
        # Fallback: if no data found in subsequent rows, try the first row approach
        if not skills_data and len(df) > 0:
            first_row = df.iloc[0]
            job_title = str(first_row[df.columns[0]]).strip() if len(df.columns) > 0 and not pd.isna(first_row[df.columns[0]]) else "General"
            department = str(first_row[df.columns[1]]).strip() if len(df.columns) > 1 and not pd.isna(first_row[df.columns[1]]) else "General"
            
            for col in skill_columns:
                skill_name = str(col).strip()
                if not skill_name or skill_name.lower() in ['unnamed', 'nan', '']:
                    continue
                
                try:
                    required_level = float(first_row[col])
                    if 1 <= required_level <= 5:
                        skills_data.append({
                            'Skill': skill_name,
                            'Required_Level': required_level,
                            'Job_Title': job_title,
                            'Department': department
                        })
                except (ValueError, TypeError):
                    continue
        
        return pd.DataFrame(skills_data)

    def clean_and_standardize(self, df: pd.DataFrame, assessment_type: str) -> pd.DataFrame:
        """
        Clean and standardize the assessment data.
        
        Args:
            df: Raw DataFrame from CSV
            assessment_type: Type of assessment ('employee' or 'manager')
            
        Returns:
            Cleaned and standardized DataFrame
        """
        # Create a copy to avoid modifying original
        cleaned_df = df.copy()
        
        # Standardize employee names and emails
        if 'Employee' in cleaned_df.columns:
            cleaned_df['Employee'] = cleaned_df['Employee'].str.strip().str.title()
        
        if 'Email' in cleaned_df.columns:
            cleaned_df['Email'] = cleaned_df['Email'].str.strip().str.lower()
        
        if assessment_type in ['employee', 'manager']:
            # Identify and clean skill columns
            skill_columns = self._identify_skill_columns(cleaned_df)
            
            for skill in skill_columns:
                # Convert to numeric, handling various formats
                cleaned_df[skill] = pd.to_numeric(cleaned_df[skill], errors='coerce')
                
                # Fill NaN values with 0 (assuming no response = no skill)
                cleaned_df[skill] = cleaned_df[skill].fillna(0)
                
                # Ensure ratings are within valid range (1-5 scale typically)
                cleaned_df[skill] = cleaned_df[skill].clip(0, 5)
        
        elif assessment_type == 'skills_matrix':
            # First, try to detect Excel format (skills in columns C to AQ, values in row 1)
            if len(df.columns) >= 3:  # Must have at least columns A, B, C
                # Check if this looks like Excel format
                skill_columns = df.columns[2:]  # From column C onwards
                
                # Look for skill names in row 1 and numeric values in subsequent rows
                excel_format_detected = False
                if len(df) > 0:
                    first_row = df.iloc[0]
                    skill_names_count = 0
                    
                    # Check if row 1 contains skill names (text, not numbers)
                    for col in skill_columns[:5]:  # Check first 5 skill columns
                        cell_value = str(first_row[col]).strip()
                        if cell_value and cell_value.lower() not in ['unnamed', 'nan', ''] and not cell_value.replace('.','').isdigit():
                            skill_names_count += 1
                    
                    if skill_names_count >= 2:  # If at least 2 columns have skill names
                        excel_format_detected = True
                
                if excel_format_detected:
                    return self.process_skills_matrix_excel_format(df)
            
            # Traditional format processing
            skill_col = None
            level_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'skill' in col_lower and skill_col is None:
                    skill_col = col
                elif any(keyword in col_lower for keyword in ['level', 'required', 'target']) and level_col is None:
                    level_col = col
            
            if skill_col and level_col:
                # Rename columns to standard names
                cleaned_df = cleaned_df.rename(columns={skill_col: 'Skill', level_col: 'Required_Level'})
                
                # Clean skill names
                cleaned_df['Skill'] = cleaned_df['Skill'].astype(str).str.strip()
                
                # Convert required level to numeric
                cleaned_df['Required_Level'] = pd.to_numeric(cleaned_df['Required_Level'], errors='coerce')
                
                # Remove rows with missing data
                cleaned_df = cleaned_df.dropna(subset=['Skill', 'Required_Level'])
                
                # Filter valid skill levels (1-5)
                cleaned_df = cleaned_df[(cleaned_df['Required_Level'] >= 1) & (cleaned_df['Required_Level'] <= 5)]
            
            return cleaned_df
        
        # Add assessment type identifier
        cleaned_df['assessment_type'] = assessment_type
        
        # Remove rows with missing employee information
        cleaned_df = cleaned_df.dropna(subset=['Employee'])
        
        return cleaned_df
    
    def merge_assessments(self, employee_df: pd.DataFrame, manager_df: pd.DataFrame, skills_matrix: pd.DataFrame = None) -> pd.DataFrame:
        """
        Merge employee self-assessments with manager assessments.
        
        Args:
            employee_df: Employee self-assessment data
            manager_df: Manager assessment data
            skills_matrix: Optional skills matrix with required levels
            
        Returns:
            Merged DataFrame with calculated averages and matrix gaps
        """
        # Get skill columns from both datasets
        emp_skills = self._identify_skill_columns(employee_df)
        mgr_skills = self._identify_skill_columns(manager_df)
        
        # Find common skills between both assessments
        common_skills = list(set(emp_skills) | set(mgr_skills))
        
        if not common_skills:
            raise ValueError("No common skills found between employee and manager assessments.")
        
        # Prepare data for merging
        emp_data = employee_df[['Employee', 'Email'] + [skill for skill in common_skills if skill in employee_df.columns]].copy()
        mgr_data = manager_df[['Employee', 'Email'] + [skill for skill in common_skills if skill in manager_df.columns]].copy()
        
        # Add suffixes to distinguish between assessments
        emp_data = emp_data.add_suffix('_emp').rename(columns={'Employee_emp': 'Employee', 'Email_emp': 'Email'})
        mgr_data = mgr_data.add_suffix('_mgr').rename(columns={'Employee_mgr': 'Employee', 'Email_mgr': 'Email'})
        
        # Merge on employee name
        merged_df = pd.merge(emp_data, mgr_data, on='Employee', how='outer', suffixes=('_emp', '_mgr'))
        
        # Calculate averages for each skill
        for skill in common_skills:
            emp_col = f"{skill}_emp"
            mgr_col = f"{skill}_mgr"
            avg_col = f"{skill}_avg"
            gap_col = f"{skill}_gap"
            matrix_gap_col = f"{skill}_matrix_gap"
            
            # Handle cases where columns might not exist
            emp_values = merged_df[emp_col] if emp_col in merged_df.columns else 0
            mgr_values = merged_df[mgr_col] if mgr_col in merged_df.columns else 0
            
            # Calculate average (excluding zeros in calculation)
            merged_df[avg_col] = merged_df.apply(
                lambda row: self._calculate_skill_average(
                    row.get(emp_col, 0), 
                    row.get(mgr_col, 0)
                ), axis=1
            )
            
            # Calculate perception gap (manager rating - employee rating)
            merged_df[gap_col] = merged_df.apply(
                lambda row: self._calculate_skill_gap(
                    row.get(emp_col, 0), 
                    row.get(mgr_col, 0)
                ), axis=1
            )
            
            # Calculate skills matrix gap if matrix provided
            if skills_matrix is not None:
                # Apply required levels, considering job titles and departments if available
                def calculate_matrix_gap(row):
                    job_title = row.get('Job_Title', None) if 'Job_Title' in merged_df.columns else None
                    department = row.get('Department', None) if 'Department' in merged_df.columns else None
                    required_level = self._get_required_level(skill, skills_matrix, job_title, department)
                    return row[avg_col] - required_level
                
                merged_df[matrix_gap_col] = merged_df.apply(calculate_matrix_gap, axis=1)
        
        # Clean up email columns
        merged_df['Email'] = merged_df['Email_emp'].fillna(merged_df.get('Email_mgr', ''))
        merged_df = merged_df.drop(columns=[col for col in merged_df.columns if col.endswith('_emp') or col.endswith('_mgr')])
        
        return merged_df
    
    def _calculate_skill_average(self, emp_rating: float, mgr_rating: float) -> float:
        """Calculate average skill rating, handling missing values."""
        ratings = [r for r in [emp_rating, mgr_rating] if r > 0]
        return sum(ratings) / len(ratings) if ratings else 0
    
    def _calculate_skill_gap(self, emp_rating: float, mgr_rating: float) -> float:
        """Calculate skill gap (manager perception vs self-assessment)."""
        if mgr_rating > 0 and emp_rating > 0:
            return mgr_rating - emp_rating
        return 0
    
    def get_skills_list(self, df: pd.DataFrame) -> List[str]:
        """
        Get list of skills from processed DataFrame.
        
        Args:
            df: Processed DataFrame
            
        Returns:
            List of skill names
        """
        return [col.replace('_avg', '') for col in df.columns if col.endswith('_avg')]
    
    def _get_required_level(self, skill_name: str, skills_matrix: pd.DataFrame, job_title: str = None, department: str = None) -> float:
        """Get required level for a skill from skills matrix, optionally filtered by job title and department."""
        if skills_matrix is None or skills_matrix.empty:
            return 3.0  # Default required level
        
        # Filter by job title and department if available
        filtered_matrix = skills_matrix
        
        # First try to filter by both job title and department
        if job_title and department and 'Job_Title' in skills_matrix.columns and 'Department' in skills_matrix.columns:
            combined_filtered = skills_matrix[
                (skills_matrix['Job_Title'].str.lower() == job_title.lower()) &
                (skills_matrix['Department'].str.lower() == department.lower())
            ]
            if not combined_filtered.empty:
                filtered_matrix = combined_filtered
        # If no match with both, try job title only
        elif job_title and 'Job_Title' in skills_matrix.columns:
            job_filtered = skills_matrix[skills_matrix['Job_Title'].str.lower() == job_title.lower()]
            if not job_filtered.empty:
                filtered_matrix = job_filtered
        # If no match with job title, try department only
        elif department and 'Department' in skills_matrix.columns:
            dept_filtered = skills_matrix[skills_matrix['Department'].str.lower() == department.lower()]
            if not dept_filtered.empty:
                filtered_matrix = dept_filtered
        
        skill_row = filtered_matrix[filtered_matrix['Skill'].str.lower() == skill_name.lower()]
        if not skill_row.empty:
            return float(skill_row.iloc[0]['Required_Level'])
        return 3.0  # Default if skill not found in matrix
    
    def export_to_excel(self, df: pd.DataFrame, filename: str) -> bytes:
        """
        Export DataFrame to Excel format.
        
        Args:
            df: DataFrame to export
            filename: Name of the file
            
        Returns:
            Excel file as bytes
        """
        from io import BytesIO
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Skills Assessment', index=False)
        
        return output.getvalue()
