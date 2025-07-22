import pandas as pd
import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

class TrainingResourceManager:
    """Manages training resources and assignments for skills development."""
    
    def __init__(self):
        """Initialize training resource manager."""
        self.default_resources = self._load_default_resources()
    
    def _load_default_resources(self) -> Dict[str, List[Dict]]:
        """Load default training resources by skill category."""
        return {
            "Communication": [
                {
                    "title": "Effective Communication Fundamentals",
                    "type": "Free Online Course",
                    "provider": "Coursera",
                    "duration": "4 weeks",
                    "url": "https://www.coursera.org/learn/communication",
                    "description": "Learn the basics of effective workplace communication",
                    "skill_level": "Beginner"
                },
                {
                    "title": "Public Speaking Mastery",
                    "type": "Video Series",
                    "provider": "YouTube - TED",
                    "duration": "2 hours",
                    "url": "https://www.youtube.com/results?search_query=ted+talks+public+speaking",
                    "description": "Collection of TED talks on public speaking techniques",
                    "skill_level": "Intermediate"
                },
                {
                    "title": "Business Writing Workshop",
                    "type": "Internal Training",
                    "provider": "Internal",
                    "duration": "1 day",
                    "description": "Company-specific business writing standards and practices",
                    "skill_level": "All Levels"
                }
            ],
            "Leadership": [
                {
                    "title": "Leadership Principles",
                    "type": "Free Online Course",
                    "provider": "edX",
                    "duration": "6 weeks",
                    "url": "https://www.edx.org/course/leadership",
                    "description": "Fundamental leadership skills and principles",
                    "skill_level": "Beginner"
                },
                {
                    "title": "Managing Teams Effectively",
                    "type": "Webinar Series",
                    "provider": "LinkedIn Learning",
                    "duration": "3 hours",
                    "description": "Best practices for team management and motivation",
                    "skill_level": "Intermediate"
                },
                {
                    "title": "Executive Leadership Program",
                    "type": "Internal Training",
                    "provider": "Internal",
                    "duration": "3 months",
                    "description": "Comprehensive leadership development program",
                    "skill_level": "Advanced"
                }
            ],
            "Technical Skills": [
                {
                    "title": "Introduction to Data Analysis",
                    "type": "Free Online Course",
                    "provider": "Khan Academy",
                    "duration": "4 weeks",
                    "url": "https://www.khanacademy.org/math/statistics-probability",
                    "description": "Basic data analysis and statistics",
                    "skill_level": "Beginner"
                },
                {
                    "title": "Programming Fundamentals",
                    "type": "Interactive Course",
                    "provider": "Codecademy",
                    "duration": "8 weeks",
                    "url": "https://www.codecademy.com/",
                    "description": "Learn programming basics",
                    "skill_level": "Beginner"
                },
                {
                    "title": "Advanced Technical Training",
                    "type": "Internal Training",
                    "provider": "Internal",
                    "duration": "2 weeks",
                    "description": "Role-specific technical skills development",
                    "skill_level": "Advanced"
                }
            ],
            "Project Management": [
                {
                    "title": "Project Management Basics",
                    "type": "Free Online Course",
                    "provider": "Google Career Certificates",
                    "duration": "6 months",
                    "url": "https://grow.google/certificates/project-management/",
                    "description": "Comprehensive project management fundamentals",
                    "skill_level": "Beginner"
                },
                {
                    "title": "Agile Methodology",
                    "type": "Workshop",
                    "provider": "Internal",
                    "duration": "2 days",
                    "description": "Agile project management practices",
                    "skill_level": "Intermediate"
                }
            ],
            "Problem Solving": [
                {
                    "title": "Critical Thinking Course",
                    "type": "Free Online Course",
                    "provider": "FutureLearn",
                    "duration": "3 weeks",
                    "url": "https://www.futurelearn.com/courses/critical-thinking",
                    "description": "Develop critical thinking and problem-solving skills",
                    "skill_level": "All Levels"
                },
                {
                    "title": "Design Thinking Workshop",
                    "type": "Internal Training",
                    "provider": "Internal",
                    "duration": "1 day",
                    "description": "Human-centered problem solving approach",
                    "skill_level": "Intermediate"
                }
            ]
        }
    
    def get_recommended_training(self, skill_gaps: List[Dict], current_skill_level: float = 0) -> List[Dict]:
        """Get recommended training based on skills gaps."""
        recommendations = []
        
        for gap in skill_gaps:
            skill_name = gap['skill']
            gap_value = abs(gap['gap_value'])
            
            # Find training resources for this skill
            skill_resources = self._find_resources_for_skill(skill_name)
            
            # Determine appropriate skill level based on current rating
            if current_skill_level <= 2:
                target_level = "Beginner"
            elif current_skill_level <= 3.5:
                target_level = "Intermediate"
            else:
                target_level = "Advanced"
            
            # Filter resources by skill level
            filtered_resources = [
                r for r in skill_resources 
                if r['skill_level'] == target_level or r['skill_level'] == "All Levels"
            ]
            
            # Add priority based on gap size
            for resource in filtered_resources[:3]:  # Top 3 recommendations per skill
                resource_copy = resource.copy()
                resource_copy['skill'] = skill_name
                resource_copy['gap_value'] = gap_value
                resource_copy['priority'] = "High" if gap_value >= 2 else "Medium" if gap_value >= 1 else "Low"
                recommendations.append(resource_copy)
        
        # Sort by priority and gap value
        priority_order = {"High": 3, "Medium": 2, "Low": 1}
        recommendations.sort(key=lambda x: (priority_order[x['priority']], x['gap_value']), reverse=True)
        
        return recommendations
    
    def _find_resources_for_skill(self, skill_name: str) -> List[Dict]:
        """Find training resources for a specific skill."""
        # Direct match
        if skill_name in self.default_resources:
            return self.default_resources[skill_name]
        
        # Fuzzy matching for common skill variations
        skill_mappings = {
            "communication skills": "Communication",
            "verbal communication": "Communication",
            "written communication": "Communication",
            "leadership skills": "Leadership",
            "team leadership": "Leadership",
            "management": "Leadership",
            "technical expertise": "Technical Skills",
            "technology": "Technical Skills",
            "computer skills": "Technical Skills",
            "project coordination": "Project Management",
            "project planning": "Project Management",
            "analytical thinking": "Problem Solving",
            "critical thinking": "Problem Solving",
            "decision making": "Problem Solving"
        }
        
        skill_lower = skill_name.lower()
        for key, mapped_skill in skill_mappings.items():
            if key in skill_lower or skill_lower in key:
                return self.default_resources.get(mapped_skill, [])
        
        # Return general development resources if no match
        return [
            {
                "title": f"{skill_name} Development Plan",
                "type": "Custom Training",
                "provider": "Internal",
                "duration": "Varies",
                "description": f"Customized development plan for {skill_name}",
                "skill_level": "All Levels"
            }
        ]
    
    def create_development_plan(self, employee_name: str, skills_gaps: List[Dict], 
                              strengths: List[Dict], timeline_weeks: int = 12) -> Dict[str, Any]:
        """Create a comprehensive individual development plan."""
        
        # Get training recommendations
        training_recommendations = self.get_recommended_training(skills_gaps)
        
        # Create timeline
        start_date = datetime.now()
        end_date = start_date + timedelta(weeks=timeline_weeks)
        
        # Organize training by priority and timeline
        high_priority = [t for t in training_recommendations if t['priority'] == 'High']
        medium_priority = [t for t in training_recommendations if t['priority'] == 'Medium']
        
        development_plan = {
            "employee_name": employee_name,
            "plan_created": start_date.strftime("%Y-%m-%d"),
            "plan_duration_weeks": timeline_weeks,
            "target_completion": end_date.strftime("%Y-%m-%d"),
            "skills_to_develop": [gap['skill'] for gap in skills_gaps],
            "current_strengths": [strength['skill'] for strength in strengths],
            "immediate_priorities": high_priority[:3],  # Top 3 high priority
            "secondary_development": medium_priority[:3],  # Top 3 medium priority
            "success_metrics": self._generate_success_metrics(skills_gaps),
            "milestones": self._generate_milestones(timeline_weeks),
            "recommended_resources": training_recommendations
        }
        
        return development_plan
    
    def _generate_success_metrics(self, skills_gaps: List[Dict]) -> List[Dict]:
        """Generate success metrics for the development plan."""
        metrics = []
        for gap in skills_gaps:
            skill = gap['skill']
            current_gap = abs(gap['gap_value'])
            
            metrics.append({
                "skill": skill,
                "current_gap": current_gap,
                "target_improvement": min(current_gap, 1.5),  # Realistic improvement target
                "measurement_method": "Skills assessment score improvement",
                "target_timeline": "3 months"
            })
        
        return metrics
    
    def _generate_milestones(self, timeline_weeks: int) -> List[Dict]:
        """Generate development milestones."""
        milestones = []
        
        # Week 2: Initial assessment and resource selection
        milestones.append({
            "week": 2,
            "milestone": "Complete initial skills assessment and select training resources",
            "deliverable": "Development plan agreement with manager"
        })
        
        # Week 4: Begin primary training
        milestones.append({
            "week": 4,
            "milestone": "Begin primary skills development activities",
            "deliverable": "Training enrollment confirmation"
        })
        
        # Mid-point review
        mid_point = timeline_weeks // 2
        milestones.append({
            "week": mid_point,
            "milestone": "Mid-point progress review",
            "deliverable": "Progress assessment and plan adjustment if needed"
        })
        
        # Week timeline_weeks - 2: Pre-completion assessment
        milestones.append({
            "week": timeline_weeks - 2,
            "milestone": "Pre-completion skills assessment",
            "deliverable": "Skills improvement measurement"
        })
        
        # Final week: Plan completion
        milestones.append({
            "week": timeline_weeks,
            "milestone": "Development plan completion and evaluation",
            "deliverable": "Final assessment and next steps planning"
        })
        
        return milestones
    
    def add_custom_resource(self, skill: str, resource: Dict) -> bool:
        """Add a custom training resource."""
        if 'custom_resources' not in st.session_state:
            st.session_state.custom_resources = {}
        
        if skill not in st.session_state.custom_resources:
            st.session_state.custom_resources[skill] = []
        
        st.session_state.custom_resources[skill].append(resource)
        return True
    
    def get_all_available_resources(self, skill: str) -> List[Dict]:
        """Get all available resources for a skill including custom ones."""
        resources = self._find_resources_for_skill(skill)
        
        # Add custom resources if available
        if ('custom_resources' in st.session_state and 
            skill in st.session_state.custom_resources):
            resources.extend(st.session_state.custom_resources[skill])
        
        return resources