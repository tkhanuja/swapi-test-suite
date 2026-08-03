import random
import pytest
from tests.config import log_unique_test_result
from utils import SwapiClient
import os
import struct

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

def test_random_sample_resource_schema(client, resource_name, resource_schema):
    """Fetch random items from the resource list and validate their schema shape."""
    test_name = "test_random_sample_resource_schema"
    list_response = client.get(f"{resource_name}/")
    assert list_response.status_code == 200
    assert list_response.elapsed.total_seconds() < 2.0
    
    data = list_response.json()

    if not data or not isinstance(data, list):
        pytest.skip(f"No valid item list found for resource: {resource_name}")

    total_count = len(data)
    sample_size = min(3, total_count)

    # Randomly select actual items directly from the list payload 
    # (this avoids hitting hardcoded ID ranges that might result in 404s)
    random_indexes = []
    while len(random_indexes) < sample_size:
        # Unpack 4 random bytes from the OS into an integer
        idx = struct.unpack("I", os.urandom(4))[0] % total_count
        if idx not in random_indexes:
            random_indexes.append(idx)

    sampled_items = [data[i] for i in random_indexes]

    for item in sampled_items:
        # If the list item already contains the full details, validate directly,
        # or fetch by its specific 'url' to ensure the detail endpoint works.
        item_url = item.get("url")
        if item_url:
            response = client.get_by_url(item_url)
        else:
            # Fallback if url isn't in summary
            response = client.get(f"{resource_name}/{random.randint(1, total_count)}/")

        if response.status_code == 404:
            continue
            
        assert response.status_code == 200
        item_data = response.json()
        
        # Helper call to validate against schema
        properties = resource_schema.get("properties", {})
        required_fields = resource_schema.get("required", [])

        for field in required_fields:
            assert field in item_data, f"Required schema field '{field}' missing from payload."

        type_mapping = {"string": str, "integer": int, "array": list}

        for key, value in item_data.items():
            if key in properties and value is not None:
                expected_type_str = properties[key].get("type")
                if expected_type_str in type_mapping:
                    expected_type = type_mapping[expected_type_str]
                    assert isinstance(value, expected_type), f"Field '{key}' expected type {expected_type_str}, got {type(value)}"
    
    test_case_id = f"{resource_name}-{item_url.rstrip('/').split('/')[-1]}"
        
        # Log the successful run
    log_unique_test_result(
            test_case_id=test_case_id,
            resource_name=resource_name,
            test_name=test_name,
            result="PASS",
            extra_details={"item_url": item_url}
    )
def test_pagination_and_dynamic_schema_validation(client, resource_name, resource_schema):
    """Fetch the resource list page, harvest dynamic URLs, and validate their schemas."""
    response = client.get(f"{resource_name}/")
    assert response.status_code == 200
    assert response.elapsed.total_seconds() < 2.0
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
        

def test_negative_invalid_id_handling(client, resource_name):
    """Ensure requesting non-existent or malformed IDs gracefully yields a 404."""
    bad_responses = [
        client.get(f"{resource_name}/999999/"),
        client.get(f"{resource_name}/not-an-id/")
    ]
    
    for response in bad_responses:
        assert response.status_code in [404, 400], (
            f"Expected 404 or 400 for invalid request on {resource_name}, "
            f"got {response.status_code}"
        )

def test_bidirectional_url_consistency(client, resource_name, resource_schema):
    """Test bidirectional consistency on a random item and log unique results."""
    test_name = "test_bidirectional_url_consistency"
    list_response = client.get(f"{resource_name}/")
    assert list_response.status_code == 200
    assert list_response.elapsed.total_seconds() < 2.0
    data = list_response.json()

    if not data or not isinstance(data, list):
        pytest.skip(f"No items found for resource: {resource_name}")

    total_count = len(data)
    random_idx = struct.unpack("I", os.urandom(4))[0] % total_count
    parent_item = data[random_idx]
    parent_url = parent_item["url"]

    properties = resource_schema.get("properties", {})
    one_way_fields = {"homeworld"}

    for field_name, field_def in properties.items():
        field_type = field_def.get("type")
        target_urls = []

        if field_type == "string" and field_name in parent_item and "http" in str(parent_item[field_name]):
            target_urls.append(parent_item[field_name])
        elif field_type == "array":
            urls = parent_item.get(field_name, [])
            if isinstance(urls, list):
                target_urls.extend([u for u in urls if isinstance(u, str) and "http" in u])

        if target_urls:
            sub_url = target_urls[struct.unpack("I", os.urandom(4))[0] % len(target_urls)]
            sub_response = client.get_by_url(sub_url)
            assert sub_response.status_code == 200
            
            sub_data = sub_response.json()
            if field_name in one_way_fields:
                continue

            back_reference_found = False
            for sub_key, sub_value in sub_data.items():
                if isinstance(sub_value, list) and any(parent_url in str(item) for item in sub_value):
                    back_reference_found = True
                    break
                elif isinstance(sub_value, str) and parent_url in sub_value:
                    back_reference_found = True
                    break

            assert back_reference_found

            # Unique ID combining parent URL and field relationship path
            test_case_id = f"{resource_name}-{parent_url.rstrip('/').split('/')[-1]}-{field_name}"
            
            log_unique_test_result(
                test_case_id=test_case_id,
                resource_name=resource_name,
                test_name=test_name,
                result="PASS",
                extra_details={"parent_url": parent_url, "sub_url": sub_url, "field": field_name}
            )