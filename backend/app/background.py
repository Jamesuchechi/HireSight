import os
from rq import Queue
from redis import Redis
from .services.parser import ResumeService

# Basic RQ setup; requires a Redis server running and `rq` installed.
redis_conn = Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", 6379)))
queue = Queue("hiresight", connection=redis_conn)


def enqueue_parse(file_path: str):
    """Enqueue a resume parsing job.

    Returns job instance. Worker should call `parse_worker`.
    """
    return queue.enqueue("backend.app.background.parse_worker", file_path)


def parse_worker(file_path: str):
    # This runs inside the worker process
    parsed = ResumeService.parse(file_path)
    # In a real worker we'd store parsed output in DB here
    return parsed
