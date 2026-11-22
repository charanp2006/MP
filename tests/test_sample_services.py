import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest
import yaml

from demo.services import app

EXPECTED_SERVICES = {
    "fn_checkout": "fn-checkout",
    "fn_search": "fn-search",
    "fn_recommend": "fn-recommend",
}
INVOKE_PAYLOADS = {
    "fn_checkout": {"items": [{"sku": "A1", "quantity": 2, "unit_price": 10.5}]},
    "fn_search": {"query": "wireless keyboard", "limit": 3},
    "fn_recommend": {"category": "electronics", "limit": 2},
}


@pytest.fixture
def server():
    running = []

    def _start(service_name="fn_checkout", **kwargs):
        handler = app.create_app(service_name, **kwargs)
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        running.append((httpd, thread))
        return f"http://127.0.0.1:{httpd.server_port}"

    yield _start

    for httpd, thread in running:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)


def _request(base, path, *, method="GET", payload=None, raw=None):
    data = raw if raw is not None else (json.dumps(payload).encode("utf-8") if payload is not None else None)
    headers = {"Content-Type": "application/json"} if data is not None else {}
    request = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, response.read(), response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as error:
        return error.code, error.read(), error.headers.get("Content-Type", "")


def _json(base, path, **kwargs):
    status, body, content_type = _request(base, path, **kwargs)
    return status, json.loads(body), content_type


def _metrics(base):
    return _request(base, "/metrics")


def _metric(text, name, **labels):
    for line in text.splitlines():
        if not line.startswith(name + "{"):
            continue
        end = line.index("}")
        pairs = dict(pair.split("=", 1) for pair in line[len(name) + 1 : end].split(","))
        if all(pairs.get(key) == f'"{value}"' for key, value in labels.items()):
            return float(line[end + 1 :].strip())
    raise AssertionError(f"metric {name} with labels {labels} not found")


@pytest.mark.parametrize("service,function_name", sorted(EXPECTED_SERVICES.items()))
def test_root_health_and_ready_expose_service_metadata(server, service, function_name):
    base = server(service, function_name=function_name)

    status, root, _ = _json(base, "/")
    assert status == 200
    assert root["service"] == service
    assert root["function"] == function_name
    assert root["routes"] == list(app.ROUTES)

    status, health, _ = _json(base, "/health")
    assert status == 200
    assert health["status"] == "ok"
    assert health["service"] == service
    assert health["version"] == app.DEFAULT_VERSION
    assert health["uptime_s"] >= 0
    assert health["cold_start"] is True

    status, ready, _ = _json(base, "/ready")
    assert status == 200
    assert ready == {"status": "ready", "service": service, "version": app.DEFAULT_VERSION}


@pytest.mark.parametrize("service", sorted(INVOKE_PAYLOADS))
def test_invoke_returns_distinct_service_behaviors(server, service):
    base = server(service)

    status, body, _ = _json(base, "/invoke", method="POST", payload=INVOKE_PAYLOADS[service])

    assert status == 200
    assert body["service"] == service
    assert body["accepted"] is True
    assert body["payload_class"] == "small"
    assert body["duration_ms"] == app.LATENCY_PROFILE_MS[service]["small"] + app.COLD_START_PENALTY_MS
    result_key = app.RESULT_KEYS[service]
    assert result_key in body
    if service == "fn_checkout":
        assert body[result_key]["item_count"] == 1
        assert body[result_key]["total_units"] == 2
        assert body[result_key]["subtotal"] == 21.0
    elif service == "fn_search":
        assert body[result_key]["result_count"] == 3
        assert len(body[result_key]["top_results"]) == 3
        assert body[result_key]["query_tokens"] == 2
    else:
        assert body[result_key]["count"] == 2
        assert len(body[result_key]["items"]) == 2


def test_result_keys_are_unique_per_service():
    assert set(app.RESULT_KEYS.values()) == {"checkout", "search", "recommendations"}


def test_invalid_payloads_are_counted_without_stack_traces(server):
    base = server("fn_checkout")
    invalid_requests = [
        {"raw": b"{"},
        {"payload": {"payload_class": "huge"}},
        {"payload": {"payload_class": "small"}},
        {"raw": b"x" * (app.MAX_BODY_BYTES + 1)},
    ]

    for request in invalid_requests:
        status, body, _ = _json(base, "/invoke", method="POST", **request)
        assert status == 400
        assert body["accepted"] is False
        assert body["error"]["code"]
        assert "traceback" not in json.dumps(body).lower()

    labels = {"function_name": "fn-checkout", "service": "fn_checkout"}
    text = _metrics(base)[1].decode("utf-8")
    assert _metric(text, "fn_invocations_total", code="400", **labels) == 4
    assert _metric(text, "fn_invocations_total", code="200", **labels) == 0
    for reason in ("invalid_json", "invalid_payload_class", "validation_error", "payload_too_large"):
        assert _metric(text, "fn_errors_total", reason=reason, **labels) == 1
    assert _metric(text, "fn_request_duration_ms_count", **labels) == 4
    assert _metric(text, "fn_request_duration_ms_sum", **labels) == pytest.approx(4 * app.ERROR_LATENCY_MS, abs=0.001)


def test_metrics_match_dashboard_names_and_labels(server):
    base = server("fn_search", function_name="fn-search", active_containers=2)
    status, body, _ = _json(base, "/invoke", method="POST", payload={"query": "shoes"})
    assert status == 200

    status, raw_text, content_type = _metrics(base)
    text = raw_text.decode("utf-8")
    assert status == 200
    assert "text/plain" in content_type
    for name in (
        "fn_invocations_total",
        "fn_request_duration_ms_bucket",
        "fn_request_duration_ms_sum",
        "fn_request_duration_ms_count",
        "fn_errors_total",
        "fn_cold_starts_total",
        "fn_energy_w",
        "fn_active_containers",
    ):
        assert name in text

    labels = {"function_name": "fn-search", "service": "fn_search"}
    assert 'function_name="fn-search"' in text
    assert 'service="fn_search"' in text
    buckets = [
        _metric(text, "fn_request_duration_ms_bucket", le=str(le), **labels)
        for le in (5, 10, 25, 50, 100, 250, 500, 1000)
    ]
    buckets.append(_metric(text, "fn_request_duration_ms_bucket", le="+Inf", **labels))
    assert buckets == sorted(buckets)
    assert buckets[-1] == 1
    assert _metric(text, "fn_request_duration_ms_sum", **labels) == pytest.approx(body["duration_ms"], abs=0.001)
    assert _metric(text, "fn_request_duration_ms_count", **labels) == 1
    assert _metric(text, "fn_cold_starts_total", **labels) == 1
    assert _metric(text, "fn_energy_w", **labels) > 0
    assert _metric(text, "fn_active_containers", **labels) == 2
    assert _metric(text, "fn_invocations_total", code="200", **labels) == 1


def test_invoke_does_not_persist_or_echo_user_identity(server):
    base = server("fn_checkout")
    secrets = ("user-secret-42", "secret@example.com", "4111111111111111", "SKU-9")

    status, body, _ = _json(
        base,
        "/invoke",
        method="POST",
        payload={
            "payload_class": "small",
            "user_id": secrets[0],
            "email": secrets[1],
            "card_number": secrets[2],
            "items": [{"sku": secrets[3], "quantity": 1, "unit_price": 5.0}],
        },
    )

    assert status == 200
    serialized = json.dumps(body)
    metrics = _metrics(base)[1].decode("utf-8")
    for secret in secrets:
        assert secret not in serialized
        assert secret not in metrics
    for field in ("user_id", "email", "card_number"):
        assert field not in serialized


def test_cold_start_affects_first_duration_only(server):
    base = server("fn_checkout", function_name="fn-checkout")
    labels = {"function_name": "fn-checkout", "service": "fn_checkout"}

    assert _json(base, "/health")[1]["cold_start"] is True
    assert _metric(_metrics(base)[1].decode("utf-8"), "fn_cold_starts_total", **labels) == 1

    _, first, _ = _json(
        base,
        "/invoke",
        method="POST",
        payload={"items": [{"sku": "A", "quantity": 1, "unit_price": 1.0}]},
    )
    assert first["duration_ms"] == app.LATENCY_PROFILE_MS["fn_checkout"]["small"] + app.COLD_START_PENALTY_MS
    assert _json(base, "/health")[1]["cold_start"] is False

    _, second, _ = _json(
        base,
        "/invoke",
        method="POST",
        payload={"payload_class": "large", "items": [{"sku": "A", "quantity": 1, "unit_price": 1.0}]},
    )
    assert second["duration_ms"] == app.LATENCY_PROFILE_MS["fn_checkout"]["large"]
    assert second["duration_ms"] > first["duration_ms"]

    text = _metrics(base)[1].decode("utf-8")
    assert _metric(text, "fn_request_duration_ms_count", **labels) == 2
    assert _metric(text, "fn_request_duration_ms_sum", **labels) == pytest.approx(
        first["duration_ms"] + second["duration_ms"], abs=0.001
    )
    assert _metric(text, "fn_request_duration_ms_bucket", le="100", **labels) == 1
    assert _metric(text, "fn_request_duration_ms_bucket", le="250", **labels) == 2
    assert _metric(text, "fn_cold_starts_total", **labels) == 1


def test_unknown_service_name_fails_fast():
    with pytest.raises(ValueError, match="unknown SERVICE_NAME"):
        app.create_app("fn_unknown")


def test_container_artifacts_are_hardened_and_service_specific():
    compose = yaml.safe_load(Path("demo/services/docker-compose.yml").read_text(encoding="utf-8"))
    dockerfile = Path("demo/services/Dockerfile").read_text(encoding="utf-8")
    expected_ports = {"fn_checkout": "8081:8080", "fn_search": "8082:8080", "fn_recommend": "8083:8080"}

    assert set(compose["services"]) == set(EXPECTED_SERVICES)
    images = set()
    for name, function_name in EXPECTED_SERVICES.items():
        spec = compose["services"][name]
        images.add(spec["image"])
        assert spec["environment"]["SERVICE_NAME"] == name
        assert spec["environment"]["FUNCTION_NAME"] == function_name
        assert spec["environment"]["SERVICE_PORT"] == "8080"
        assert spec["ports"] == [expected_ports[name]]
        assert "/ready" in spec["healthcheck"]["test"][-1]
        resources = spec["deploy"]["resources"]
        assert float(resources["limits"]["cpus"]) > 0
        assert resources["limits"]["memory"]
        assert resources["reservations"]["memory"]
    assert len(images) == 1

    assert "USER app" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "PYTHONDONTWRITEBYTECODE=1" in dockerfile
    assert "SERVICE_PORT=8080" in dockerfile
    assert "COPY --chown=app:app" in dockerfile


def test_registry_documents_routes_and_truthful_deployment():
    registry = json.loads(Path("demo/service_registry.json").read_text(encoding="utf-8"))
    services = registry["services"]

    assert {item["service_id"] for item in services} == set(EXPECTED_SERVICES)
    for item in services:
        assert item["function_name"] == EXPECTED_SERVICES[item["service_id"]]
        assert item["routes"] == list(app.ROUTES)
        assert item["route"] == "/invoke"
        assert item["metrics_endpoint"] == "/metrics"
        assert item["health_endpoint"] == "/health"
        assert item["ready_endpoint"] == "/ready"
        assert item["image"] == "m9-sample-service:latest"
    assert registry["payload_classes"] == list(app.PAYLOAD_CLASSES)
    assert "scaffolding" in registry["deployment"]
    assert registry["production_ready"] is False
    assert registry["single_reusable_image"] is True
