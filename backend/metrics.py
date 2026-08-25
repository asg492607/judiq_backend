"""
JudiQ AI — Enterprise Prometheus Metrics & Observability Exporter
Instruments legal engine execution, API latency, fatal defect detection, and database health.
"""

import time
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# 1. Platform Ingress & Traffic Metrics
JUDIQ_REQUESTS_TOTAL = Counter(
    "judiq_requests_total",
    "Total incoming HTTP requests across all endpoints",
    ["method", "endpoint", "status_code"]
)

JUDIQ_REQUEST_DURATION_SECONDS = Histogram(
    "judiq_request_duration_seconds",
    "HTTP request latency distribution in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# 2. Litigation Intelligence & Engine Metrics
JUDIQ_ANALYSIS_EXECUTIONS = Counter(
    "judiq_analysis_executions_total",
    "Total legal intelligence analysis runs",
    ["domain", "risk_level"]
)

JUDIQ_ENGINE_DURATION_SECONDS = Histogram(
    "judiq_engine_duration_seconds",
    "Execution duration of specific legal rule and scoring engines",
    ["engine_name"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

JUDIQ_FATAL_DEFECTS_DETECTED = Counter(
    "judiq_fatal_defects_detected_total",
    "Count of fatal procedural or statutory defects uncovered",
    ["domain", "defect_code"]
)

# 3. Document Generation Studio Metrics
JUDIQ_DOCUMENTS_GENERATED = Counter(
    "judiq_documents_generated_total",
    "Total court documents, petitions, and PDF dossiers generated",
    ["document_type", "format"]
)

# 4. Database & Infrastructure Saturation
JUDIQ_ACTIVE_CASEROOMS = Gauge(
    "judiq_active_caserooms_gauge",
    "Number of currently active collaborative caseroom sessions"
)

JUDIQ_KNOWLEDGE_BASE_SIZE = Gauge(
    "judiq_knowledge_base_size_gauge",
    "Total verified legal precedents indexed across all domains",
    ["domain"]
)


def record_engine_metric(engine_name: str, duration_sec: float):
    JUDIQ_ENGINE_DURATION_SECONDS.labels(engine_name=engine_name).observe(duration_sec)


def record_analysis_metric(domain: str, risk_level: str):
    JUDIQ_ANALYSIS_EXECUTIONS.labels(domain=domain, risk_level=risk_level).inc()


def record_defect_metric(domain: str, defect_code: str):
    JUDIQ_FATAL_DEFECTS_DETECTED.labels(domain=domain, defect_code=defect_code).inc()


def record_document_metric(doc_type: str, doc_format: str):
    JUDIQ_DOCUMENTS_GENERATED.labels(document_type=doc_type, format=doc_format).inc()


async def prometheus_metrics_endpoint():
    """Prometheus exposition endpoint scraping target"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
