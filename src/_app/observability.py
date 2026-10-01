"""Synchronous request diagnostics; never records SQL, parameters or payloads."""
from contextlib import ExitStack
from datetime import datetime, timezone
import json
import logging
import os
import resource
import time
import uuid

from django.db import connections

logger = logging.getLogger("infrastructure.http")


class RequestMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.perf_counter()
        cpu_started = time.process_time()
        count = 0
        sql_seconds = 0.0
        sql_errors = 0
        status = 500

        def measure(execute, sql, params, many, context):
            nonlocal count, sql_seconds, sql_errors
            count += 1
            before = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            except Exception:
                sql_errors += 1
                raise
            finally:
                sql_seconds += time.perf_counter() - before

        try:
            with ExitStack() as stack:
                for connection in connections.all():
                    stack.enter_context(connection.execute_wrapper(measure))
                response = self.get_response(request)
                status = response.status_code
                return response
        finally:
            match = getattr(request, "resolver_match", None)
            logger.info(json.dumps({
                "event": "http_request", "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": str(uuid.uuid4()), "pid": os.getpid(),
                "method": request.method, "route": match.route if match else "unmatched",
                "status": status, "duration_ms": round((time.perf_counter() - started) * 1000, 4),
                "cpu_ms": round((time.process_time() - cpu_started) * 1000, 4),
                "rss_peak_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "sql_count": count, "sql_ms": round(sql_seconds * 1000, 4), "sql_errors": sql_errors,
            }))
