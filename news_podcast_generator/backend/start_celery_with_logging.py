"""
Start Celery worker with logging to file
Usage: python start_celery_with_logging.py
"""
import sys
import os
from datetime import datetime

# Create logs directory if it doesn't exist
logs_dir = "logs"
os.makedirs(logs_dir, exist_ok=True)

# Create log file with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(logs_dir, f"celery_worker_{timestamp}.log")

print(f"Starting Celery worker...")
print(f"Logging to: {log_file}")
print("=" * 80)

# Redirect stdout and stderr to log file
log_fd = open(log_file, 'w', encoding='utf-8')

class TeeOutput:
    def __init__(self, *files):
        self.files = files
    
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    
    def flush(self):
        for f in self.files:
            f.flush()

# Tee output to both console and file
tee = TeeOutput(sys.stdout, log_fd)
sys.stdout = tee
sys.stderr = tee

# Now start Celery
from services.celery_tasks import app

worker_options = [
    "worker",
    "--loglevel=INFO",
    "--concurrency=4",
    "--hostname=podcast_agent_worker@%h",
    "--pool=threads",
]

if __name__ == "__main__":
    print("Starting PodcastAgent workers...")
    try:
        app.worker_main(worker_options)
    except KeyboardInterrupt:
        print("\nShutting down Celery worker...")
    finally:
        log_fd.close()
        print(f"\nLog saved to: {log_file}")

