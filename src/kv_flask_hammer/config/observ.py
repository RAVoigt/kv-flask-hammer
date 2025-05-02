from kv_flask_hammer import constants

metrics_enabled = False
traces_enabled = False

metrics_label_prefix = ""
metrics_ip = constants.default_metrics_ip
metrics_port = constants.default_metrics_port

traces_endpoint_url: str | None = None
traces_service_name = constants.default_traces_service_name
