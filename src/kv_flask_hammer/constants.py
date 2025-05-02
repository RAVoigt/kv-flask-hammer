default_bind_ip = "0.0.0.0"
default_bind_port = "5000"

default_gunicorn_worker_count = 1
default_gunicorn_worker_type = "gthread"
default_gunicorn_worker_timeout = 30
default_gunicorn_keepalive = 2
default_gunicorn_log_level = "info"
default_gunicorn_accesslog_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

default_metrics_ip = "0.0.0.0"
default_metrics_port = 9090

default_traces_service_name = "Flask-Hammer"

default_meta_view_prefix = "meta"
