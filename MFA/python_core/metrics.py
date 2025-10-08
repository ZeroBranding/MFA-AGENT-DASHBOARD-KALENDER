from prometheus_client import start_http_server, Counter, Histogram

mail_processed = Counter("mail_processed_total", "Processed mails")
mail_errors = Counter("mail_errors_total", "Processing errors")
latency = Histogram("pipeline_latency_seconds", "End-to-end latency", buckets=(0.5, 1, 2, 5, 10))

def start_metrics_server(port=9100):
    start_http_server(port)
