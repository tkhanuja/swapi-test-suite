import pytest
from utils.api_client import SwapiClient

@pytest.fixture
def client():
    return SwapiClient()

@pytest.mark.parametrize("person_id, expected_name", [
    (1, "Luke Skywalker"),
    (2, "C-3PO"),
    (3, "R2-D2")
])
def test_get_specific_person(client, person_id, expected_name):
    response = client.get(f"people/{person_id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == expected_name

def test_get_person_not_found(client):
    response = client.get("people/99999/")
    assert response.status_code == 404