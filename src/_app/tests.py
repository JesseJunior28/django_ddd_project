import json
from datetime import datetime, timezone
from unittest.mock import patch

from django.db import connection, OperationalError
from django.http import JsonResponse
from django.test import TestCase, RequestFactory

from .health import live, ready
from .observability import RequestMetricsMiddleware
from .management.commands.sync_execution_occurrences import occurrence_for_day


class InfrastructureTests(TestCase):
    def test_liveness_does_not_query_database(self):
        with self.assertNumQueries(0):
            response = live(RequestFactory().get("/health/live"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"status": "alive"})

    def test_readiness_queries_real_postgresql(self):
        self.assertEqual(connection.vendor, "postgresql")
        with self.assertNumQueries(1):
            response = ready(RequestFactory().get("/health/ready"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"status": "ready"})

    def test_readiness_failure_is_503_without_exception_details(self):
        with patch.object(connection, "cursor", side_effect=OperationalError("password=private")):
            response = ready(RequestFactory().get("/health/ready"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(json.loads(response.content), {"status": "unavailable"})

    def test_health_is_get_only(self):
        self.assertEqual(self.client.post("/health/live").status_code, 405)
        self.assertEqual(self.client.post("/health/ready").status_code, 405)

    def test_metrics_preserve_response_and_measure_sql_without_sensitive_data(self):
        expected = JsonResponse({"untouched": True}, status=201)
        expected["X-Test"] = "same"

        def view(request):
            with connection.cursor() as cursor:
                cursor.execute("SELECT %s", ["private-sql-parameter"])
                cursor.fetchone()
            return expected

        request = RequestFactory().post("/unknown?password=private-query", {"password": "private-body"},
                                        HTTP_AUTHORIZATION="Bearer private-token")
        with self.assertLogs("infrastructure.http", level="INFO") as logs:
            response = RequestMetricsMiddleware(view)(request)
        self.assertIs(response, expected)
        record = json.loads(logs.records[0].message)
        self.assertEqual(record["status"], 201)
        self.assertEqual(record["sql_count"], 1)
        self.assertEqual(record["sql_errors"], 0)
        self.assertGreaterEqual(record["sql_ms"], 0)
        self.assertGreater(record["rss_peak_kib"], 0)
        self.assertNotIn("private", logs.records[0].message)
        self.assertNotIn("SELECT", logs.records[0].message)
        self.assertEqual(record["route"], "unmatched")

    def test_metrics_propagate_exception_and_remove_wrappers(self):
        def broken(request):
            raise ValueError("private-error")

        initial = list(connection.execute_wrappers)
        with self.assertLogs("infrastructure.http", level="INFO") as logs:
            with self.assertRaises(ValueError):
                RequestMetricsMiddleware(broken)(RequestFactory().get("/broken"))
        self.assertEqual(connection.execute_wrappers, initial)
        record = json.loads(logs.records[0].message)
        self.assertEqual(record["status"], 500)
        self.assertNotIn("private-error", logs.records[0].message)


class ExecutionOccurrenceScheduleTests(TestCase):
    def test_daily_occurrence_is_kept_when_the_job_runs_later_that_day(self):
        start = datetime(2026, 9, 30, 11, 44, tzinfo=timezone.utc)

        self.assertEqual(
            occurrence_for_day(start, "DAILY", datetime(2026, 9, 30, 12, 6, tzinfo=timezone.utc).date()),
            start,
        )
