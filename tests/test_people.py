import random
import pytest
from utils import SwapiClient

RESOURCES = ["people", "films", "starships", "vehicles", "species", "planets"]

@pytest.fixture(scope="session")
def client():
    """Session-scoped client so session-scoped fixtures can depend on it safely."""
    return SwapiClient()

@pytest.fixture(scope="session", params=RESOURCES)
def resource_name(request):
    """Parameterizes tests to run for each resource type."""
    return request.param

@pytest.fixture(scope="session")
def resource_schema(client, resource_name):
    """Fetch and cache the official schema for the given resource once per session."""
    try:
        response = client.get(f"{resource_name}/schema/")
        if response.status_code != 200:
            pytest.skip(f"SWAPI schema endpoint unavailable for {resource_name}.")
        return response.json()
    except Exception as e:
        pytest.skip(f"Network error connecting to SWAPI for {resource_name}: {e}")
        

def validate_schema(data, schema):
    """Helper to assert that a given person dictionary matches the fetched JSON schema rules."""
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])

    for field in required_fields:
        assert field in data, f"Required schema field '{field}' missing from payload."

    type_mapping = {
        "string": str,
        "integer": int,
        "array": list
    }

    for key, value in data.items():
        if key in properties and value is not None:
            expected_type_str = properties[key].get("type")
            if expected_type_str in type_mapping:
                expected_type = type_mapping[expected_type_str]
                assert isinstance(value, expected_type), f"Field '{key}' expected type {expected_type_str}, got {type(value)}"

def test_random_sample_schema(client, resource_name, resource_schema):
    """Fetch random resource IDs and validate their schema shape."""
    list_response = client.get(f"{resource_name}/")
    if list_response.status_code == 404:
        pytest.skip(f"Failed to fetch {resource_name} list.")
    assert list_response.status_code == 200
    data = list_response.json()
    total_count = len(data)

    if total_count == 0:
        pytest.skip(f"No items found for resource: {resource_name}")

    sample_size = min(3, total_count)
    sample_ids = random.sample(range(1, total_count + 1), sample_size)

    for item_id in sample_ids:
        response = client.get(f"{resource_name}/{item_id}/")
        if response.status_code == 404:
                pytest.skip(f"Failed to fetch {resource_name} list.")
        assert response.status_code == 200
        item_data = response.json()
        validate_schema(item_data, resource_schema)

def test_pagination_and_dynamic_schema_validation(client, resource_name, resource_schema):
    """Fetch the resource list page, harvest dynamic URLs, and validate their schemas."""
    response = client.get(f"{resource_name}/")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) > 0

    first_item_summary = data[0]
    item_url = first_item_summary["url"]

    detail_response = client.get_by_url(item_url)
    assert detail_response.status_code == 200
    item_detail = detail_response.json()

    validate_schema(item_detail, resource_schema)
    
    # Check a common identifier field if present (e.g., 'name' or 'title')
    identifier_key = "title" if "title" in first_item_summary else "name"
    if identifier_key in first_item_summary and identifier_key in item_detail:
        assert item_detail[identifier_key] == first_item_summary[identifier_key]

def test_bidirectional_url_consistency(client, resource_name, resource_schema):
    """Test that URLs in the API response (both strings and arrays) link correctly and point back."""
    list_response = client.get(f"{resource_name}/")
    assert list_response.status_code == 200
    data = list_response.json()

    assert len(data) > 0
    parent_item = data[0]
    parent_url = parent_item["url"]

    properties = resource_schema.get("properties", {})

    for field_name, field_def in properties.items():
        field_type = field_def.get("type")
        target_urls = []

        # Case 1: Relationship is a single URL string (like 'homeworld')
        if field_type == "string" and field_name in parent_item and "http" in str(parent_item[field_name]):
            target_urls.append(parent_item[field_name])

        # Case 2: Relationship is an array of URLs (like 'films', 'starships', 'residents')
        elif field_type == "array":
            urls = parent_item.get(field_name, [])
            if isinstance(urls, list):
                target_urls.extend([u for u in urls if isinstance(u, str) and "http" in u])

        # Test the first available link for this field to ensure connectivity and back-reference
        if target_urls:
            sub_url = target_urls[0]
            sub_response = client.get_by_url(sub_url)
            assert sub_response.status_code == 200, f"Failed to fetch sub-resource URL: {sub_url}"
            
            sub_data = sub_response.json()

            # Verify that the sub-resource references the parent back somewhere in its payload
            back_reference_found = False
            for sub_key, sub_value in sub_data.items():
                if isinstance(sub_value, list) and any(parent_url in str(item) for item in sub_value):
                    back_reference_found = True
                    break
                elif isinstance(sub_value, str) and parent_url in sub_value:
                    back_reference_found = True
                    break

            assert back_reference_found, (
                f"Bidirectional mismatch: {parent_url} points to {sub_url} via '{field_name}', "
                f"but {sub_url} does not reference back to the parent."
            )