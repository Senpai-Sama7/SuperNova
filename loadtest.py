"""Locust load test for SuperNova API.

Run:
    pip install locust
    locust -f loadtest.py --host http://localhost:8000

Web UI: http://localhost:8089
Headless: locust -f loadtest.py --host http://localhost:8000 --headless -u 50 -r 5 -t 60s
"""

from locust import HttpUser, between, task


class SuperNovaUser(HttpUser):
    """Simulates a dashboard user polling endpoints + occasional agent messages."""

    wait_time = between(0.5, 2.0)

    def on_start(self):
        """Acquire JWT token on session start."""
        r = self.client.post("/auth/token", json={"username": "loadtest"})
        if r.status_code == 200:
            self.token = r.json().get("access_token", "")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = ""
            self.headers = {}

    # ------------------------------------------------------------------
    # High-frequency: dashboard polling (70% of traffic)
    # ------------------------------------------------------------------

    @task(10)
    def health_check(self):
        self.client.get("/health")

    @task(8)
    def dashboard_snapshot(self):
        self.client.get("/dashboard/snapshot", headers=self.headers)

    @task(5)
    def metrics(self):
        self.client.get("/metrics")

    # ------------------------------------------------------------------
    # Medium-frequency: memory + admin (20% of traffic)
    # ------------------------------------------------------------------

    @task(3)
    def semantic_search(self):
        self.client.get(
            "/memory/semantic",
            params={"q": "load test query"},
            headers=self.headers,
        )

    @task(2)
    def fleet_status(self):
        self.client.get("/admin/fleet", headers=self.headers)

    @task(2)
    def cost_status(self):
        self.client.get("/admin/costs", headers=self.headers)

    # ------------------------------------------------------------------
    # Low-frequency: agent messages (10% of traffic)
    # ------------------------------------------------------------------

    @task(1)
    def agent_message(self):
        self.client.post(
            "/agent/message",
            json={"message": "What is 2+2?", "session_id": "loadtest-session"},
            headers=self.headers,
            timeout=30,
        )

    @task(1)
    def onboarding_status(self):
        self.client.get("/onboarding/status")
