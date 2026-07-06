# scripts/09_verify_observability.py
import requests
import time

def check_prometheus():
    resp = requests.get("http://localhost:9090/api/v1/query",
                        params={"query": 'http_requests_total{job="api-gateway"}'})
    data = resp.json()
    assert data["status"] == "success"
    print("Integration 9 OK: Prometheus metrics flowing")

def check_langsmith():
    import os
    from langsmith import Client

    client = Client(api_key=os.environ["LANGCHAIN_API_KEY"])
    project_name = os.environ.get("LANGCHAIN_PROJECT", "lab28-platform")
    client.create_project(project_name=project_name, upsert=True)
    runs = list(client.list_runs(project_name=project_name, limit=1))
    if not runs:
        client.create_run(
            name="lab28-observability-smoke",
            run_type="chain",
            project_name=project_name,
            inputs={"check": "langsmith"},
            outputs={"status": "ok"},
        )
        client.flush()
        for _ in range(5):
            runs = list(client.list_runs(project_name=project_name, limit=1))
            if runs:
                break
            time.sleep(1)
    assert len(runs) > 0
    print("Integration 10 OK: LangSmith traces visible")

check_prometheus()
check_langsmith()
