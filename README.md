# Skills Audit Tool

A comprehensive web application for organizational skills assessment and development planning.

## Features

- **Data Upload**: Import MS Forms assessment data (Employee Self-Assessments, Manager Assessments, Skills Matrix)
- **Individual Development Plans**: Automated training recommendations and assignment capabilities
- **Skills Analysis**: Organization-wide analytics and insights
- **Gap Reports**: Comprehensive reporting with export capabilities
- **Database Management**: Session management, analytics, and backup features

## Quick Start

1. **Upload Assessment Data**: Use the Data Upload page to import your CSV files from MS Forms
2. **Define Skills Matrix**: Set required skill levels for your organization
3. **Analyze Results**: View individual employee dashboards and organization-wide analytics
4. **Create Development Plans**: Assign training and track progress

## Data Format

### Employee Self-Assessment CSV
Expected columns:
- Employee Name
- Skill columns (e.g., "Communication", "Leadership", "Technical Skills")
- Rating scale: 1-5

### Manager Assessment CSV
Expected columns:
- Employee Name
- Same skill columns as employee assessment
- Rating scale: 1-5

### Skills Matrix CSV
Expected columns:
- Skill Name
- Required Level (1-5)

## Deployment

### Streamlit Community Cloud
1. Fork this repository
2. Connect to Streamlit Community Cloud
3. Add database URL to secrets (optional)
4. Deploy

### Local Development
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Database Configuration

The application supports both PostgreSQL and SQLite:

- **PostgreSQL**: Add `DATABASE_URL` to your environment or Streamlit secrets
- **SQLite**: Automatically used as fallback (local development only)

## Usage Tips

1. **Skills Matrix**: Define this first to enable gap analysis against organizational standards
2. **Data Quality**: Ensure employee names match exactly between assessment files
3. **Training Resources**: Use the built-in library or add custom internal resources
4. **Export Options**: Download development plans and reports for offline use

## Support

For questions or issues, refer to the in-app help sections or contact your system administrator.