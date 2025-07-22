import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import json
from typing import Optional, Dict, List, Any

class SkillsDatabase:
    """Database manager for Skills Audit Tool."""
    
    def __init__(self):
        """Initialize database connection."""
        # Try to get database URL from different sources
        self.database_url = None
        
        # First try environment variable (for local development)
        if os.getenv('DATABASE_URL'):
            self.database_url = os.getenv('DATABASE_URL')
        
        # Then try Streamlit secrets (for Streamlit Cloud)
        elif hasattr(st, 'secrets') and 'connections' in st.secrets and 'postgresql' in st.secrets.connections:
            self.database_url = st.secrets.connections.postgresql.url
        elif hasattr(st, 'secrets') and 'DATABASE_URL' in st.secrets:
            self.database_url = st.secrets.DATABASE_URL
        
        if not self.database_url:
            # For deployment without database, use SQLite as fallback
            import tempfile
            db_path = os.path.join(tempfile.gettempdir(), 'skills_audit.db')
            self.database_url = f"sqlite:///{db_path}"
            st.warning("Using local SQLite database. Data will not persist between sessions.")
        
        self.engine = create_engine(self.database_url)
        self.metadata = MetaData()
        self._create_tables()
    
    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        try:
            with self.engine.connect() as conn:
                # Create assessments table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS assessments (
                        id SERIAL PRIMARY KEY,
                        session_id VARCHAR(255),
                        employee_name VARCHAR(255) NOT NULL,
                        email VARCHAR(255),
                        assessment_type VARCHAR(50) NOT NULL,
                        skill_name VARCHAR(255) NOT NULL,
                        rating FLOAT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(session_id, employee_name, assessment_type, skill_name)
                    )
                """))
                
                # Create skills_matrix table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS skills_matrix (
                        id SERIAL PRIMARY KEY,
                        session_id VARCHAR(255),
                        skill_name VARCHAR(255) NOT NULL,
                        required_level FLOAT NOT NULL,
                        description TEXT,
                        category VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(session_id, skill_name)
                    )
                """))
                
                # Create processed_assessments table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS processed_assessments (
                        id SERIAL PRIMARY KEY,
                        session_id VARCHAR(255),
                        employee_name VARCHAR(255) NOT NULL,
                        email VARCHAR(255),
                        skill_name VARCHAR(255) NOT NULL,
                        employee_rating FLOAT,
                        manager_rating FLOAT,
                        average_rating FLOAT,
                        perception_gap FLOAT,
                        matrix_gap FLOAT,
                        required_level FLOAT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(session_id, employee_name, skill_name)
                    )
                """))
                
                # Create gap_analysis table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS gap_analysis (
                        id SERIAL PRIMARY KEY,
                        session_id VARCHAR(255),
                        employee_name VARCHAR(255) NOT NULL,
                        avg_skill_level FLOAT,
                        avg_gap_score FLOAT,
                        max_gap FLOAT,
                        significant_gaps_count INTEGER,
                        has_gaps BOOLEAN,
                        gap_type VARCHAR(50),
                        strengths_data TEXT,
                        development_areas_data TEXT,
                        significant_gaps_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(session_id, employee_name, gap_type)
                    )
                """))
                
                conn.commit()
                
        except SQLAlchemyError as e:
            st.error(f"Database setup error: {str(e)}")
    
    def get_session_id(self) -> str:
        """Get or create session ID."""
        if 'db_session_id' not in st.session_state:
            st.session_state.db_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return st.session_state.db_session_id
    
    def save_assessment_data(self, df: pd.DataFrame, assessment_type: str) -> bool:
        """Save assessment data to database."""
        try:
            session_id = self.get_session_id()
            
            with self.engine.connect() as conn:
                # Clear existing data for this session and assessment type
                conn.execute(text("""
                    DELETE FROM assessments 
                    WHERE session_id = :session_id AND assessment_type = :assessment_type
                """), {"session_id": session_id, "assessment_type": assessment_type})
                
                # Identify skill columns
                skill_columns = [col for col in df.columns if col not in ['Employee', 'Email', 'assessment_type']]
                
                # Insert new data
                for _, row in df.iterrows():
                    employee_name = row['Employee']
                    email = row.get('Email', '')
                    
                    for skill in skill_columns:
                        if pd.notna(row[skill]) and row[skill] > 0:
                            conn.execute(text("""
                                INSERT INTO assessments 
                                (session_id, employee_name, email, assessment_type, skill_name, rating)
                                VALUES (:session_id, :employee_name, :email, :assessment_type, :skill_name, :rating)
                                ON CONFLICT (session_id, employee_name, assessment_type, skill_name)
                                DO UPDATE SET rating = EXCLUDED.rating, created_at = CURRENT_TIMESTAMP
                            """), {
                                "session_id": session_id,
                                "employee_name": employee_name,
                                "email": email,
                                "assessment_type": assessment_type,
                                "skill_name": skill,
                                "rating": float(row[skill])
                            })
                
                conn.commit()
            return True
            
        except SQLAlchemyError as e:
            st.error(f"Error saving assessment data: {str(e)}")
            return False
    
    def save_skills_matrix(self, df: pd.DataFrame) -> bool:
        """Save skills matrix to database."""
        try:
            session_id = self.get_session_id()
            
            with self.engine.connect() as conn:
                # Clear existing matrix for this session
                conn.execute(text("""
                    DELETE FROM skills_matrix WHERE session_id = :session_id
                """), {"session_id": session_id})
                
                # Insert new matrix data
                for _, row in df.iterrows():
                    conn.execute(text("""
                        INSERT INTO skills_matrix 
                        (session_id, skill_name, required_level, description, category)
                        VALUES (:session_id, :skill_name, :required_level, :description, :category)
                        ON CONFLICT (session_id, skill_name)
                        DO UPDATE SET 
                            required_level = EXCLUDED.required_level,
                            description = EXCLUDED.description,
                            category = EXCLUDED.category,
                            created_at = CURRENT_TIMESTAMP
                    """), {
                        "session_id": session_id,
                        "skill_name": row['Skill'],
                        "required_level": float(row['Required_Level']),
                        "description": row.get('Description', ''),
                        "category": row.get('Category', '')
                    })
                
                conn.commit()
            return True
            
        except SQLAlchemyError as e:
            st.error(f"Error saving skills matrix: {str(e)}")
            return False
    
    def save_processed_data(self, df: pd.DataFrame) -> bool:
        """Save processed assessment data to database."""
        try:
            session_id = self.get_session_id()
            
            with self.engine.connect() as conn:
                # Clear existing processed data for this session
                conn.execute(text("""
                    DELETE FROM processed_assessments WHERE session_id = :session_id
                """), {"session_id": session_id})
                
                # Get skill columns
                avg_columns = [col for col in df.columns if col.endswith('_avg')]
                
                for _, row in df.iterrows():
                    employee_name = row['Employee']
                    email = row.get('Email', '')
                    
                    for avg_col in avg_columns:
                        skill_name = avg_col.replace('_avg', '')
                        emp_col = f"{skill_name}_emp"
                        mgr_col = f"{skill_name}_mgr"
                        gap_col = f"{skill_name}_gap"
                        matrix_gap_col = f"{skill_name}_matrix_gap"
                        
                        # Get required level from skills matrix
                        required_level = self._get_required_level_from_db(skill_name, session_id)
                        
                        conn.execute(text("""
                            INSERT INTO processed_assessments 
                            (session_id, employee_name, email, skill_name, employee_rating, 
                             manager_rating, average_rating, perception_gap, matrix_gap, required_level)
                            VALUES (:session_id, :employee_name, :email, :skill_name, :employee_rating,
                                    :manager_rating, :average_rating, :perception_gap, :matrix_gap, :required_level)
                            ON CONFLICT (session_id, employee_name, skill_name)
                            DO UPDATE SET 
                                employee_rating = EXCLUDED.employee_rating,
                                manager_rating = EXCLUDED.manager_rating,
                                average_rating = EXCLUDED.average_rating,
                                perception_gap = EXCLUDED.perception_gap,
                                matrix_gap = EXCLUDED.matrix_gap,
                                required_level = EXCLUDED.required_level,
                                created_at = CURRENT_TIMESTAMP
                        """), {
                            "session_id": session_id,
                            "employee_name": employee_name,
                            "email": email,
                            "skill_name": skill_name,
                            "employee_rating": float(row.get(emp_col, 0)) if pd.notna(row.get(emp_col, 0)) else None,
                            "manager_rating": float(row.get(mgr_col, 0)) if pd.notna(row.get(mgr_col, 0)) else None,
                            "average_rating": float(row[avg_col]) if pd.notna(row[avg_col]) else None,
                            "perception_gap": float(row.get(gap_col, 0)) if pd.notna(row.get(gap_col, 0)) else None,
                            "matrix_gap": float(row.get(matrix_gap_col, 0)) if pd.notna(row.get(matrix_gap_col, 0)) else None,
                            "required_level": required_level
                        })
                
                conn.commit()
            return True
            
        except SQLAlchemyError as e:
            st.error(f"Error saving processed data: {str(e)}")
            return False
    
    def save_gap_analysis(self, gap_df: pd.DataFrame, gap_type: str) -> bool:
        """Save gap analysis results to database."""
        try:
            session_id = self.get_session_id()
            
            with self.engine.connect() as conn:
                # Clear existing gap analysis for this session and type
                conn.execute(text("""
                    DELETE FROM gap_analysis 
                    WHERE session_id = :session_id AND gap_type = :gap_type
                """), {"session_id": session_id, "gap_type": gap_type})
                
                # Insert new gap analysis data
                for _, row in gap_df.iterrows():
                    conn.execute(text("""
                        INSERT INTO gap_analysis 
                        (session_id, employee_name, avg_skill_level, avg_gap_score, max_gap,
                         significant_gaps_count, has_gaps, gap_type, strengths_data, 
                         development_areas_data, significant_gaps_data)
                        VALUES (:session_id, :employee_name, :avg_skill_level, :avg_gap_score, :max_gap,
                                :significant_gaps_count, :has_gaps, :gap_type, :strengths_data,
                                :development_areas_data, :significant_gaps_data)
                        ON CONFLICT (session_id, employee_name, gap_type)
                        DO UPDATE SET 
                            avg_skill_level = EXCLUDED.avg_skill_level,
                            avg_gap_score = EXCLUDED.avg_gap_score,
                            max_gap = EXCLUDED.max_gap,
                            significant_gaps_count = EXCLUDED.significant_gaps_count,
                            has_gaps = EXCLUDED.has_gaps,
                            strengths_data = EXCLUDED.strengths_data,
                            development_areas_data = EXCLUDED.development_areas_data,
                            significant_gaps_data = EXCLUDED.significant_gaps_data,
                            created_at = CURRENT_TIMESTAMP
                    """), {
                        "session_id": session_id,
                        "employee_name": row['Employee'],
                        "avg_skill_level": float(row['avg_skill_level']),
                        "avg_gap_score": float(row['avg_gap_score']),
                        "max_gap": float(row['max_gap']),
                        "significant_gaps_count": int(row['significant_gaps_count']),
                        "has_gaps": bool(row['has_gaps']),
                        "gap_type": gap_type,
                        "strengths_data": json.dumps(row['strengths']),
                        "development_areas_data": json.dumps(row['development_areas']),
                        "significant_gaps_data": json.dumps(row['significant_gaps'])
                    })
                
                conn.commit()
            return True
            
        except SQLAlchemyError as e:
            st.error(f"Error saving gap analysis: {str(e)}")
            return False
    
    def load_assessment_data(self, assessment_type: str) -> Optional[pd.DataFrame]:
        """Load assessment data from database."""
        try:
            session_id = self.get_session_id()
            
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT employee_name, email, skill_name, rating
                    FROM assessments 
                    WHERE session_id = :session_id AND assessment_type = :assessment_type
                    ORDER BY employee_name, skill_name
                """), {"session_id": session_id, "assessment_type": assessment_type})
                
                data = result.fetchall()
                
                if not data:
                    return None
                
                # Convert to DataFrame with skills as columns
                df_data = {}
                for row in data:
                    emp_name = row[0]
                    email = row[1]
                    skill = row[2]
                    rating = row[3]
                    
                    if emp_name not in df_data:
                        df_data[emp_name] = {'Employee': emp_name, 'Email': email}
                    
                    df_data[emp_name][skill] = rating
                
                df = pd.DataFrame(list(df_data.values()))
                df['assessment_type'] = assessment_type
                return df
                
        except SQLAlchemyError as e:
            st.error(f"Error loading assessment data: {str(e)}")
            return None
    
    def load_skills_matrix(self) -> Optional[pd.DataFrame]:
        """Load skills matrix from database."""
        try:
            session_id = self.get_session_id()
            
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT skill_name, required_level, description, category
                    FROM skills_matrix 
                    WHERE session_id = :session_id
                    ORDER BY skill_name
                """), {"session_id": session_id})
                
                data = result.fetchall()
                
                if not data:
                    return None
                
                df = pd.DataFrame(data, columns=['Skill', 'Required_Level', 'Description', 'Category'])
                return df
                
        except SQLAlchemyError as e:
            st.error(f"Error loading skills matrix: {str(e)}")
            return None
    
    def load_processed_data(self) -> Optional[pd.DataFrame]:
        """Load processed assessment data from database."""
        try:
            session_id = self.get_session_id()
            
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT employee_name, email, skill_name, employee_rating, 
                           manager_rating, average_rating, perception_gap, matrix_gap
                    FROM processed_assessments 
                    WHERE session_id = :session_id
                    ORDER BY employee_name, skill_name
                """), {"session_id": session_id})
                
                data = result.fetchall()
                
                if not data:
                    return None
                
                # Convert to DataFrame with skills as columns
                df_data = {}
                for row in data:
                    emp_name = row[0]
                    email = row[1]
                    skill = row[2]
                    emp_rating = row[3]
                    mgr_rating = row[4]
                    avg_rating = row[5]
                    perc_gap = row[6]
                    matrix_gap = row[7]
                    
                    if emp_name not in df_data:
                        df_data[emp_name] = {'Employee': emp_name, 'Email': email}
                    
                    if emp_rating is not None:
                        df_data[emp_name][f"{skill}_emp"] = emp_rating
                    if mgr_rating is not None:
                        df_data[emp_name][f"{skill}_mgr"] = mgr_rating
                    if avg_rating is not None:
                        df_data[emp_name][f"{skill}_avg"] = avg_rating
                    if perc_gap is not None:
                        df_data[emp_name][f"{skill}_gap"] = perc_gap
                    if matrix_gap is not None:
                        df_data[emp_name][f"{skill}_matrix_gap"] = matrix_gap
                
                df = pd.DataFrame(list(df_data.values()))
                return df
                
        except SQLAlchemyError as e:
            st.error(f"Error loading processed data: {str(e)}")
            return None
    
    def _get_required_level_from_db(self, skill_name: str, session_id: str) -> float:
        """Get required level for a skill from database."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT required_level FROM skills_matrix 
                    WHERE session_id = :session_id AND LOWER(skill_name) = LOWER(:skill_name)
                """), {"session_id": session_id, "skill_name": skill_name})
                
                row = result.fetchone()
                return float(row[0]) if row else 3.0
                
        except SQLAlchemyError:
            return 3.0
    
    def get_saved_sessions(self) -> List[Dict[str, Any]]:
        """Get list of saved sessions."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT DISTINCT session_id, 
                           COUNT(DISTINCT employee_name) as employee_count,
                           MIN(created_at) as created_at
                    FROM assessments 
                    GROUP BY session_id 
                    ORDER BY created_at DESC
                """))
                
                sessions = []
                for row in result:
                    sessions.append({
                        'session_id': row[0],
                        'employee_count': row[1],
                        'created_at': row[2]
                    })
                
                return sessions
                
        except SQLAlchemyError as e:
            st.error(f"Error loading sessions: {str(e)}")
            return []
    
    def load_session(self, session_id: str) -> bool:
        """Load a specific session."""
        try:
            st.session_state.db_session_id = session_id
            
            # Load data into session state
            employee_data = self.load_assessment_data('employee')
            manager_data = self.load_assessment_data('manager')
            skills_matrix = self.load_skills_matrix()
            processed_data = self.load_processed_data()
            
            st.session_state.employee_data = employee_data
            st.session_state.manager_data = manager_data
            st.session_state.skills_matrix = skills_matrix
            st.session_state.processed_data = processed_data
            
            return True
            
        except Exception as e:
            st.error(f"Error loading session: {str(e)}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its data."""
        try:
            with self.engine.connect() as conn:
                # Delete from all tables
                conn.execute(text("DELETE FROM gap_analysis WHERE session_id = :session_id"), {"session_id": session_id})
                conn.execute(text("DELETE FROM processed_assessments WHERE session_id = :session_id"), {"session_id": session_id})
                conn.execute(text("DELETE FROM skills_matrix WHERE session_id = :session_id"), {"session_id": session_id})
                conn.execute(text("DELETE FROM assessments WHERE session_id = :session_id"), {"session_id": session_id})
                
                conn.commit()
            return True
            
        except SQLAlchemyError as e:
            st.error(f"Error deleting session: {str(e)}")
            return False