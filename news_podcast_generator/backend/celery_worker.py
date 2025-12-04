from services.celery_tasks import app

worker_options = [
    "worker",
    "--loglevel=INFO",
    "--concurrency=4",
    "--hostname=podcast_agent_worker@%h",
    "--pool=threads",
]

if __name__ == "__main__":
    print("Starting PodcastAgent workers...", flush=True)
    app.worker_main(worker_options)