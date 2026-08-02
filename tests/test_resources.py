import random
import pytest
from utils import SwapiClient

RESOURCES = ["people", "films", "starships", "vehicles", "species", "planets"]
@pytest.fixture(scope="session")
def client():
    """Session-scoped client so session-scoped fixtures can depend on it safely."""
    return SwapiClient()

@pytest.fixture(scope="session")
def get_schema(client):
    """Fetch and cache the official /people/schema/ once per test session."""
    try:
        response = client.get("people/schema/")
        print(response)
        if response.status_code != 200:
            pytest.skip("SWAPI schema endpoint unavailable.")
        return response.json()
    except Exception as e:
        pytest.skip(f"Network error connecting to SWAPI: {e}")