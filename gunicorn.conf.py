import os
import multiprocessing

# Gunicorn configuration for NIRIKSHA Production Deployment
# Reference: Problem Statement 26262 Enterprise Architecture

bind = os.getenv("BIND_ADDRESS", "0.0.0.0:8000")

# Concurrency & Workers
# Uvicorn worker handles async event loops inside each worker process
default_workers = min(multiprocessing.cpu_count() * 2, 8) if multiprocessing.cpu_count() > 1 else 2
workers = int(os.getenv("WEB_CONCURRENCY", str(default_workers)))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000

# Resilience & Timeouts
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "65"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))

# Worker Recycling (prevents memory fragmentation during heavy ML / CP-SAT runs)
max_requests = int(os.getenv("MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("MAX_REQUESTS_JITTER", "100"))

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" (%(L)ss)'

# Process Naming
proc_name = "niriksha_control_room"
