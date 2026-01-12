"""
Automated Task Scheduler
Schedules daily stats updates and other background tasks
"""
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import sys
import io

# Force UTF-8 output
if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass  # Already wrapped or can't wrap


def scheduled_update():
    """Function that runs on schedule to update stats"""
    from update_stats import update_all_players

    print(f"\n{'=' * 60}")
    print(f"SCHEDULED UPDATE TRIGGERED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}")

    try:
        result = update_all_players()

        if result["success"]:
            print(f"\n[SUCCESS] Scheduled update completed!")
            print(f"  - Players updated: {result['players_updated']}")
            print(f"  - New games added: {result['new_games']}")
        else:
            print(f"\n[ERROR] Scheduled update failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"\n[ERROR] Scheduled update exception: {e}")


def init_scheduler():
    """Initialize and start the background scheduler"""

    scheduler = BackgroundScheduler()

    # Schedule daily update at 8 AM (when most games are finished)
    # Adjust the hour to your preference
    scheduler.add_job(
        scheduled_update,
        trigger='cron',
        hour=8,
        minute=0,
        id='daily_stats_update',
        name='Daily Stats Update',
        replace_existing=True
    )

    scheduler.start()

    print("[INFO] Scheduler initialized")
    print("[INFO] Daily stats update scheduled for 8:00 AM")

    return scheduler


# For testing: run an update immediately
if __name__ == "__main__":
    print("Running immediate update for testing...")
    scheduled_update()
