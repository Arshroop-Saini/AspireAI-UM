import os
import multiprocessing

# Gunicorn config variables
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gevent'
bind = f"0.0.0.0:{int(os.environ.get('PORT', 5000))}"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
worker_connections = 1000

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# SSL (if needed)
# keyfile = 'path/to/keyfile'
# certfile = 'path/to/certfile'

# For debugging and testing
reload = os.environ.get('FLASK_ENV') == 'development'
reload_engine = 'auto'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190 