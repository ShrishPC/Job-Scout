import sys
with open('backend/app/main.py', 'r') as f:
    content = f.read()

# Add imports
if 'from datetime import datetime, timedelta' not in content:
    content = content.replace('from sqlalchemy.orm import Session', 'from sqlalchemy.orm import Session\nfrom sqlalchemy import func\nfrom datetime import datetime, timedelta')

# Update stats endpoint
old_stats = """
        return {
            "total_jobs": total_jobs,
            "total_resumes": total_resumes,
            "system_cpu_usage_percent": cpu_usage,
            "system_ram_usage_percent": ram.percent,
            "celery_active_tasks": active_count
        }"""

new_stats = """
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        jobs_by_day = db.query(
            func.date(Job.created_at).label('date'),
            func.count(Job.id).label('count')
        ).filter(Job.created_at >= seven_days_ago).group_by(func.date(Job.created_at)).all()
        
        jobs_chart = [{"date": str(row.date), "count": row.count} for row in jobs_by_day]

        return {
            "total_jobs": total_jobs,
            "total_resumes": total_resumes,
            "system_cpu_usage_percent": cpu_usage,
            "system_ram_usage_percent": ram.percent,
            "celery_active_tasks": active_count,
            "jobs_chart_data": jobs_chart
        }"""

content = content.replace(old_stats, new_stats)

with open('backend/app/main.py', 'w') as f:
    f.write(content)
