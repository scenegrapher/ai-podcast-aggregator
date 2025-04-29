from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime


def create_scheduler(job_function, interval_days=1, start_date=None):
    """
    Create a scheduler that runs a job at specified intervals.

    Args:
        job_function: The function to be scheduled
        interval_days: Number of days between runs (default: 1)
        start_date: When to start the scheduler (default: next day at 8 AM)
    """
    if start_date is None:
        start_date = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        if datetime.now().hour >= 8:
            start_date = start_date.replace(day=start_date.day + 1)

    scheduler = BlockingScheduler()
    scheduler.add_job(
        job_function, IntervalTrigger(days=interval_days), start_date=start_date
    )
    return scheduler
