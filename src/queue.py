import os

import redis
from rq import Queue


redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
redis_connection = redis.from_url(redis_url)
rq_queue = Queue(connection=redis_connection)
