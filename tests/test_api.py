"""
Comprehensive test suite for Investment Insights AI backend.
Tests: health check, profile CRUD, chat, history endpoints.
Uses an in-memory SQLite DB so tests are isolated and fast.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool
from unittest.mock import patch, MagicMock

# ── Override DB before importing the app ──────────────────────────────────────
import backend.database as db_module

TEST_ENGINE = create_engine(
    "sqlite://",  # in-memory
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

db_module.engine = TEST_ENGINE


def override_get_session():
    with Session(TEST_ENGINE) as session:
        yield session


# ── Now import the app and wire overrides ─────────────────────────────────────
from backend.main import app, get_session  # noqa: E402

app.dependency_overrides[get_session] = override_get_session

# Create tables in the test DB
SQLModel.metadata.create_all(TEST_ENGINE)


@pytest.fixture(autouse=True)
def clean_tables():
    """Wipe tables between tests for isolation."""
    yield
    from sqlalchemy import text as sa_text
    with Session(TEST_ENGINE) as s:
        s.exec(sa_text("DELETE FROM chatmessage"))
        s.exec(sa_text("DELETE FROM userprofile"))
        s.commit()


@pytest.fixture
def client():
    return TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Health Check
# ─────────────────────────────────────────────────────────────────────────────
class TestHealthCheck:
    def test_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200, resp.text

    def test_root_message(self, client):
        data = client.get("/").json()
        assert "message" in data
        assert "running" in data["message"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# 2. Profile – Create
# ─────────────────────────────────────────────────────────────────────────────
VALID_PROFILE = {
    "goal": "Retirement",
    "time_horizon": 20,
    "monthly_budget": 1000.0,
    "risk_tolerance": "medium",
    "existing_holdings": "AAPL,MSFT",
}


class TestProfileCreate:
    def test_create_profile_200(self, client):
        resp = client.post("/profile", json=VALID_PROFILE)
        assert resp.status_code == 200, resp.text

    def test_create_profile_returns_id(self, client):
        data = client.post("/profile", json=VALID_PROFILE).json()
        assert "id" in data
        assert data["id"] is not None

    def test_create_profile_fields_match(self, client):
        data = client.post("/profile", json=VALID_PROFILE).json()
        assert data["goal"] == VALID_PROFILE["goal"]
        assert data["time_horizon"] == VALID_PROFILE["time_horizon"]
        assert data["monthly_budget"] == VALID_PROFILE["monthly_budget"]
        assert data["risk_tolerance"] == VALID_PROFILE["risk_tolerance"]

    def test_create_profile_missing_required_field(self, client):
        bad = {k: v for k, v in VALID_PROFILE.items() if k != "goal"}
        resp = client.post("/profile", json=bad)
        assert resp.status_code == 422  # Unprocessable Entity


# ─────────────────────────────────────────────────────────────────────────────
# 3. Profile – Read
# ─────────────────────────────────────────────────────────────────────────────
class TestProfileRead:
    def test_get_existing_profile(self, client):
        profile_id = client.post("/profile", json=VALID_PROFILE).json()["id"]
        resp = client.get(f"/profile/{profile_id}")
        assert resp.status_code == 200, resp.text

    def test_get_nonexistent_profile_404(self, client):
        resp = client.get("/profile/99999")
        assert resp.status_code == 404

    def test_get_profile_data_correct(self, client):
        profile_id = client.post("/profile", json=VALID_PROFILE).json()["id"]
        data = client.get(f"/profile/{profile_id}").json()
        assert data["goal"] == VALID_PROFILE["goal"]
        assert data["risk_tolerance"] == VALID_PROFILE["risk_tolerance"]


# ─────────────────────────────────────────────────────────────────────────────
# 4. Profile – Update
# ─────────────────────────────────────────────────────────────────────────────
class TestProfileUpdate:
    def test_update_profile_200(self, client):
        profile_id = client.post("/profile", json=VALID_PROFILE).json()["id"]
        updated = {**VALID_PROFILE, "goal": "College Fund", "monthly_budget": 500.0}
        resp = client.put(f"/profile/{profile_id}", json=updated)
        assert resp.status_code == 200, resp.text

    def test_update_profile_reflects_changes(self, client):
        profile_id = client.post("/profile", json=VALID_PROFILE).json()["id"]
        updated = {**VALID_PROFILE, "goal": "College Fund"}
        client.put(f"/profile/{profile_id}", json=updated)
        data = client.get(f"/profile/{profile_id}").json()
        assert data["goal"] == "College Fund"

    def test_update_nonexistent_profile_404(self, client):
        resp = client.put("/profile/99999", json=VALID_PROFILE)
        assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# 5. Chat Endpoint (LLM mocked to keep tests fast & offline)
# ─────────────────────────────────────────────────────────────────────────────
MOCK_AI_RESPONSE = "Mock AI: Consider a diversified portfolio. This is not financial advice."


class TestChat:
    @patch("backend.main.generate_response", return_value=MOCK_AI_RESPONSE)
    def test_chat_with_valid_user_200(self, mock_llm, client):
        profile_id = client.post("/profile", json=VALID_PROFILE).json()["id"]
        resp = client.post("/chat", json={"user_id": profile_id, "message": "What should I invest in?"})
        assert resp.status_code == 200, resp.text

    @patch("backend.main.generate_response", return_value=MOCK_AI_RESPONSE)
    def test_chat_returns_response_field(self, mock_llm, client):
        profile_id = client.post("/profile", json=VALID_PROFILE).json()["id"]
        data = client.post("/chat", json={"user_id": profile_id, "message": "Advice?"}).json()
        assert "response" in data
        assert len(data["response"]) > 0

    @patch("backend.main.generate_response", return_value=MOCK_AI_RESPONSE)
    def test_chat_without_profile_still_works(self, mock_llm, client):
        """Chat should work even for an unknown user_id (uses default profile)."""
        resp = client.post("/chat", json={"user_id": 99999, "message": "Hello?"})
        assert resp.status_code == 200, resp.text

    @patch("backend.main.generate_response", return_value=MOCK_AI_RESPONSE)
    def test_chat_stores_messages(self, mock_llm, client):
        profile_id = client.post("/profile", json=VALID_PROFILE).json()["id"]
        client.post("/chat", json={"user_id": profile_id, "message": "Test question"})
        history = client.get(f"/history/{profile_id}").json()
        assert len(history) == 2  # user + assistant

    def test_chat_missing_message_422(self, client):
        resp = client.post("/chat", json={"user_id": 1})
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 6. Chat History
# ─────────────────────────────────────────────────────────────────────────────
class TestHistory:
    def test_history_empty_for_new_user(self, client):
        resp = client.get("/history/99999")
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("backend.main.generate_response", return_value=MOCK_AI_RESPONSE)
    def test_history_grows_with_messages(self, mock_llm, client):
        profile_id = client.post("/profile", json=VALID_PROFILE).json()["id"]
        client.post("/chat", json={"user_id": profile_id, "message": "First"})
        client.post("/chat", json={"user_id": profile_id, "message": "Second"})
        history = client.get(f"/history/{profile_id}").json()
        assert len(history) == 4  # 2 user + 2 assistant

    @patch("backend.main.generate_response", return_value=MOCK_AI_RESPONSE)
    def test_history_message_roles(self, mock_llm, client):
        profile_id = client.post("/profile", json=VALID_PROFILE).json()["id"]
        client.post("/chat", json={"user_id": profile_id, "message": "Question"})
        history = client.get(f"/history/{profile_id}").json()
        roles = [m["role"] for m in history]
        assert "user" in roles
        assert "assistant" in roles


# ─────────────────────────────────────────────────────────────────────────────
# 7. Finance Tools (unit tests, no real network calls)
# ─────────────────────────────────────────────────────────────────────────────
class TestFinanceTools:
    @patch("yfinance.Ticker")
    def test_get_stock_price_success(self, mock_ticker):
        mock_instance = MagicMock()
        mock_instance.info = {
            "regularMarketPrice": 500.0,
            "currency": "USD",
            "longName": "SPDR S&P 500 ETF Trust",
        }
        import pandas as pd
        mock_instance.history.return_value = pd.DataFrame(
            {"Close": [400.0, 500.0]},
            index=pd.to_datetime(["2024-01-01", "2025-01-01"])
        )
        mock_ticker.return_value = mock_instance

        from backend.finance_tools import get_stock_price
        result = get_stock_price("SPY")
        assert result["ticker"] == "SPY"
        assert result["price"] == 500.0
        assert "1y_return" in result

    @patch("yfinance.Ticker")
    def test_get_stock_price_handles_errors(self, mock_ticker):
        mock_ticker.side_effect = Exception("Network error")
        from backend.finance_tools import get_stock_price
        result = get_stock_price("INVALID")
        assert "error" in result


# ─────────────────────────────────────────────────────────────────────────────
# 8. Database Connectivity
# ─────────────────────────────────────────────────────────────────────────────
class TestDatabase:
    def test_engine_is_accessible(self):
        from sqlmodel import text
        with Session(TEST_ENGINE) as s:
            result = s.exec(text("SELECT 1")).first()
            assert result[0] == 1

    def test_tables_exist(self):
        from sqlalchemy import inspect
        insp = inspect(TEST_ENGINE)
        tables = insp.get_table_names()
        assert "userprofile" in tables
        assert "chatmessage" in tables
