# swapi-test-suite

## 1. Executive Summary & Overview
When building automated test suites for public or third-party REST APIs, writing basic "happy path" checks is rarely enough. This project evolved from a simple schema validation script into a fully generalized, data-driven, schema-compliant, and bidirectional test framework built using Pytest and Python.

The framework dynamically discovers resource schemas (people, films, starships, vehicles, species, planets), validates complex relationships bidirectionally, enforces OS-level cryptographic entropy for true randomness, and logs unique execution states.

## 2. Architecture & Test Suite Breakdown
The test suite is structured into distinct validation tiers covering both structural integrity and relational data consistency:

A. Session-Scoped Parameterized Fixtures
Resource Matrix: Automatically parametrizes test execution across all major SWAPI endpoints.
Schema Caching: Fetches and caches official JSON schemas (/schema/) once per session to maintain high execution speed while testing dynamic types.
B. Dynamic Schema Validation
Type Safety & Mapping: Maps JSON schema types (string, integer, array, null) to Python native types.
Edge-Case Tolerance: Gracefully handles nullable fields, missing numerical data, and descriptive strings like "n/a", "none", or "unknown" without triggering false test failures.
C. Genuinely Random Sampling (OS Entropy)
Bypasses standard pseudo-random number limitations and Pytest's seed-locking mechanisms by pulling cryptographic entropy straight from the operating system (os.urandom) to ensure unique, unpredictable test targets on every run.
D. Bidirectional URL Consistency & Relationship Validation
Automatically inspects schema array and string properties to identify relationship maps (e.g., a person pointing to a film, or a starship pointing to a pilot).
Verifies that when Resource A links to Resource B, Resource B references back appropriately.
E. Negative Testing & Boundary Handling
Validates API resilience by intentionally submitting malformed strings, out-of-bounds indices, and invalid IDs, asserting that the system responds appropriately with 404 Not Found or 400 Bad Request rather than crashing.
F. Unique Execution Logging
Records structured execution metrics (Test Case ID, Resource Name, Test Name, Result, and Payload Metadata) to a JSON log file while filtering out duplicates to maintain a clean review history.

 