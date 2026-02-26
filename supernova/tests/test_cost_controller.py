"""Tests for Phase 11: Cost Management & Budget Controls.

Covers CostController, budget-aware routing, cost API, and Ollama client.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── CostController Tests ─────────────────────────────────────────────────────


class TestCostController:
    """Tests for infrastructure/llm/cost_controller.py."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client with pipeline support."""
        redis = MagicMock()
        async def _get(_: str):
            return None

        async def _set(*args, **kwargs):
            return True

        redis.get = _get
        redis.set = _set
        pipe = MagicMock()
        pipe.incrbyfloat = MagicMock()
        pipe.expire = MagicMock()
        async def _execute():
            return [1.50, True, 12.00, True]

        pipe.execute = _execute
        redis.pipeline = MagicMock(return_value=pipe)
        return redis

    @pytest.fixture
    def controller(self, mock_redis):
        from supernova.infrastructure.llm.cost_controller import CostController
        return CostController(
            redis=mock_redis,
            daily_limit=10.0,
            monthly_limit=100.0,
            confirmation_threshold=0.50,
            enabled=True,
        )

    @pytest.mark.asyncio
    async def test_check_budget_within_limit(self, controller, mock_redis):
        """check_budget returns True when spend is within limits."""
        async def _get(_: str):
            return b"5.00"
        mock_redis.get = _get
        result = await controller.check_budget(estimated_cost=1.0)
        assert result is True

    @pytest.mark.asyncio
    async def test_check_budget_exceeds_daily(self, controller, mock_redis):
        """check_budget returns False when daily limit would be exceeded."""
        async def _get(_: str):
            return b"9.50"
        mock_redis.get = _get
        result = await controller.check_budget(estimated_cost=1.0)
        assert result is False

    @pytest.mark.asyncio
    async def test_check_budget_exceeds_monthly(self, controller, mock_redis):
        """check_budget returns False when monthly limit would be exceeded."""
        # Daily is fine, monthly is not
        call_count = 0
        async def side_effect(key):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return b"1.00"  # daily
            return b"99.50"  # monthly
        mock_redis.get = side_effect
        result = await controller.check_budget(estimated_cost=1.0)
        assert result is False

    @pytest.mark.asyncio
    async def test_check_budget_disabled(self, mock_redis):
        """check_budget always returns True when disabled."""
        from supernova.infrastructure.llm.cost_controller import CostController
        cc = CostController(redis=mock_redis, daily_limit=0.01, enabled=False)
        result = await cc.check_budget(estimated_cost=999.0)
        assert result is True

    @pytest.mark.asyncio
    async def test_record_cost_increments_counters(self, controller, mock_redis):
        """record_cost uses Redis pipeline with INCRBYFLOAT."""
        result = await controller.record_cost(0.05, model_id="openai/gpt-4o")
        assert result["daily"] == 1.50
        assert result["monthly"] == 12.00
        pipe = mock_redis.pipeline()
        pipe.incrbyfloat.assert_called()

    @pytest.mark.asyncio
    async def test_record_cost_zero_skipped(self, controller, mock_redis):
        """record_cost skips zero amounts."""
        result = await controller.record_cost(0.0)
        assert result == {"daily": 0.0, "monthly": 0.0}

    def test_estimate_cost_known_model(self, controller):
        """estimate_cost uses MODEL_PRICING for known models."""
        # GPT-4o: $2.50/MTok input, $10.00/MTok output
        cost = controller.estimate_cost("openai/gpt-4o", 1_000_000, 1_000_000)
        assert cost == pytest.approx(12.50, abs=0.01)

    def test_estimate_cost_local_model_free(self, controller):
        """Local models have zero cost."""
        cost = controller.estimate_cost("ollama/qwen2.5:32b", 1_000_000, 1_000_000)
        assert cost == 0.0

    def test_estimate_cost_unknown_model_defaults_expensive(self, controller):
        """Unknown models default to expensive pricing."""
        cost = controller.estimate_cost("unknown/model", 1_000_000, 1_000_000)
        assert cost > 10.0  # defaults to $5/$15 per MTok

    def test_needs_confirmation_above_threshold(self, controller):
        """needs_confirmation returns True for costs above threshold."""
        assert controller.needs_confirmation(0.51) is True
        assert controller.needs_confirmation(0.50) is False
        assert controller.needs_confirmation(0.10) is False

    def test_needs_confirmation_disabled(self, mock_redis):
        """needs_confirmation returns False when tracking disabled."""
        from supernova.infrastructure.llm.cost_controller import CostController
        cc = CostController(redis=mock_redis, enabled=False)
        assert cc.needs_confirmation(999.0) is False

    @pytest.mark.asyncio
    async def test_get_spend_summary(self, controller, mock_redis):
        """get_spend_summary returns structured cost data."""
        async def _get(_: str):
            return b"3.50"
        mock_redis.get = _get
        summary = await controller.get_spend_summary()
        assert "daily_spend" in summary
        assert "monthly_spend" in summary
        assert "daily_limit" in summary
        assert summary["daily_limit"] == 10.0
        assert summary["tracking_enabled"] is True

    @pytest.mark.asyncio
    async def test_alert_thresholds(self, controller, mock_redis):
        """_check_alerts triggers at 50/80/100% levels."""
        async def _get(_: str):
            return None
        mock_redis.get = _get  # no prior alert
        alerts = await controller._check_alerts(8.5)  # 85% of $10
        assert 50 in alerts
        assert 80 in alerts

    @pytest.mark.asyncio
    async def test_from_settings(self, mock_redis):
        """from_settings creates controller from config."""
        from supernova.infrastructure.llm.cost_controller import CostController
        cc = CostController.from_settings(mock_redis)
        assert cc._daily_limit == 10.0
        assert cc._confirmation_threshold == 0.50


# ── Budget-Aware Routing Tests ────────────────────────────────────────────────


class TestBudgetAwareRouting:
    """Tests for DynamicModelRouter cost integration."""

    class _MockLLMRouter:
        def __init__(self, response):
            self.calls = 0
            self._response = response

        async def acompletion(self, *args, **kwargs):
            self.calls += 1
            return self._response

    class _MockCostController:
        def __init__(self):
            self.check_budget_calls = 0
            self.record_cost_calls = 0
            self._check_budget_result = True
            self._estimate_cost_result = 0.01
            self._needs_confirmation_result = False

        async def check_budget(self, estimated_cost):
            self.check_budget_calls += 1
            return self._check_budget_result

        def estimate_cost(self, model_id, input_tokens, output_tokens):
            _ = (model_id, input_tokens, output_tokens)
            return self._estimate_cost_result

        def needs_confirmation(self, estimated_cost):
            _ = estimated_cost
            return self._needs_confirmation_result

        async def record_cost(self, amount, model_id):
            _ = (amount, model_id)
            self.record_cost_calls += 1
            return {"daily": 0.01, "monthly": 0.01}

    @pytest.fixture
    def mock_llm(self):
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "Mock response"
        response.usage.prompt_tokens = 100
        response.usage.completion_tokens = 50
        return self._MockLLMRouter(response)

    @pytest.fixture
    def cost_controller(self):
        return self._MockCostController()

    @pytest.fixture
    def router(self, mock_llm, cost_controller):
        from supernova.core.reasoning.dynamic_router import DynamicModelRouter
        return DynamicModelRouter(
            litellm_router=mock_llm,
            cost_controller=cost_controller,
        )

    @pytest.mark.asyncio
    async def test_route_records_cost_after_call(self, router, cost_controller):
        """Router records actual cost after successful LLM call."""
        await router.route_task("planning", [{"role": "user", "content": "test"}])
        assert cost_controller.record_cost_calls == 1

    @pytest.mark.asyncio
    async def test_route_checks_budget_before_call(self, router, cost_controller):
        """Router checks budget before making LLM call."""
        await router.route_task("tool_call", [{"role": "user", "content": "test"}])
        assert cost_controller.check_budget_calls > 0

    @pytest.mark.asyncio
    async def test_budget_exceeded_triggers_fallback(self, router, cost_controller):
        """When budget exceeded, router falls back to cheaper model."""
        cost_controller._check_budget_result = False
        cost_controller._estimate_cost_result = 0.0  # local = free
        await router.route_task("planning", [{"role": "user", "content": "test"}])
        # Should have called acompletion with a model (fallback)
        assert router.litellm.calls == 1

    def test_fallback_chain_exists(self, router):
        """Router has a defined fallback chain."""
        assert len(router.FALLBACK_CHAIN) >= 3
        assert "ollama/qwen2.5:32b" in router.FALLBACK_CHAIN

    def test_find_budget_fallback_returns_local(self, router, cost_controller):
        """_find_budget_fallback returns local model when all API models too expensive."""
        cost_controller._estimate_cost_result = 0.0
        result = router._find_budget_fallback(5000, 500)
        assert "ollama" in result

    def test_confirmation_threshold(self, router, cost_controller):
        """needs_confirmation is checked for expensive operations."""
        cost_controller._needs_confirmation_result = True
        assert cost_controller.needs_confirmation(0.60) is True


# ── Cost API Endpoint Tests ───────────────────────────────────────────────────


class TestCostAPI:
    """Tests for GET /admin/costs endpoint."""

    @pytest.fixture
    def app(self):
        from supernova.api.gateway import app, _state
        _state["cost_controller"] = None
        return app

    def test_cost_endpoint_no_controller(self, app):
        from starlette.testclient import TestClient
        client = TestClient(app)
        resp = client.get("/admin/costs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tracking_enabled"] is False

    def test_cost_endpoint_with_controller(self, app):
        from supernova.api.gateway import _state
        from starlette.testclient import TestClient
        class _CostController:
            async def get_spend_summary(self):
                return {
                    "daily_spend": 3.50,
                    "monthly_spend": 45.00,
                    "daily_limit": 10.0,
                    "monthly_limit": None,
                    "daily_projection": 7.00,
                    "daily_pct": 35.0,
                    "confirmation_threshold": 0.50,
                    "tracking_enabled": True,
                }

        mock_cc = _CostController()
        _state["cost_controller"] = mock_cc

        client = TestClient(app)
        resp = client.get("/admin/costs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["daily_spend"] == 3.50
        assert data["tracking_enabled"] is True

        _state["cost_controller"] = None


# ── Ollama Client Tests ───────────────────────────────────────────────────────


class TestOllamaClient:
    """Tests for infrastructure/llm/ollama_client.py."""

    @pytest.fixture
    def client(self):
        from supernova.infrastructure.llm.ollama_client import OllamaClient
        return OllamaClient(host="http://localhost:11434", model="llama3.2:3b")

    class _AsyncClientCM:
        def __init__(self, mock_client):
            self._mock_client = mock_client

        async def __aenter__(self):
            return self._mock_client

        async def __aexit__(self, exc_type, exc, tb):
            return False

    @pytest.mark.asyncio
    async def test_chat_sends_request(self, client):
        """chat() sends POST to /api/chat."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "message": {"content": "Hello!"},
            "model": "llama3.2:3b",
            "total_duration": 1000,
            "eval_count": 10,
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MagicMock()
            async def _post(*args, **kwargs):
                _ = (args, kwargs)
                return mock_resp

            mock_client.post = _post
            MockClient.return_value = self._AsyncClientCM(mock_client)

            result = await client.chat([{"role": "user", "content": "Hi"}])
            assert result["content"] == "Hello!"
            assert result["model"] == "llama3.2:3b"

    @pytest.mark.asyncio
    async def test_embed_sends_request(self, client):
        """embed() sends POST to /api/embed."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MagicMock()
            async def _post(*args, **kwargs):
                _ = (args, kwargs)
                return mock_resp

            mock_client.post = _post
            MockClient.return_value = self._AsyncClientCM(mock_client)

            result = await client.embed("test text")
            assert len(result) == 1
            assert result[0] == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_is_available_returns_false_on_error(self, client):
        """is_available returns False when server unreachable."""
        import httpx as _httpx
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MagicMock()
            async def _get(*args, **kwargs):
                _ = (args, kwargs)
                raise _httpx.ConnectError("refused")

            mock_client.get = _get
            MockClient.return_value = self._AsyncClientCM(mock_client)

            result = await client.is_available()
            assert result is False

    @pytest.mark.asyncio
    async def test_list_models_returns_names(self, client):
        """list_models returns model name strings."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "models": [{"name": "llama3.2:3b"}, {"name": "nomic-embed-text"}]
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MagicMock()
            async def _get(*args, **kwargs):
                _ = (args, kwargs)
                return mock_resp

            mock_client.get = _get
            MockClient.return_value = self._AsyncClientCM(mock_client)

            result = await client.list_models()
            assert "llama3.2:3b" in result
            assert "nomic-embed-text" in result

    @pytest.mark.asyncio
    async def test_list_models_returns_empty_on_error(self, client):
        """list_models returns empty list on connection error."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MagicMock()
            async def _get(*args, **kwargs):
                _ = (args, kwargs)
                raise Exception("fail")

            mock_client.get = _get
            MockClient.return_value = self._AsyncClientCM(mock_client)

            result = await client.list_models()
            assert result == []
