"""Test Vega Web endpoints"""

from starlette.testclient import TestClient
from test_vega_web import app

def test_all_endpoints():
    client = TestClient(app)

    # Test 1: Root endpoint
    print('=== Test 1: GET / ===')
    r = client.get('/')
    print(f'Status: {r.status_code}')
    print(f'Response: {r.json()}')
    assert r.status_code == 200
    assert r.json() == {"message": "Hello from Vega Web!"}
    print('[PASS]\n')

    # Test 2: Health check
    print('=== Test 2: GET /health ===')
    r = client.get('/health')
    print(f'Status: {r.status_code}')
    print(f'Response: {r.json()}')
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
    print('[PASS]\n')

    # Test 3: Get user
    print('=== Test 3: GET /api/users/123 ===')
    r = client.get('/api/users/123')
    print(f'Status: {r.status_code}')
    print(f'Response: {r.json()}')
    assert r.status_code == 200
    assert r.json()["id"] == "123"
    print('[PASS]\n')

    # Test 4: User not found (404)
    print('=== Test 4: GET /api/users/invalid ===')
    r = client.get('/api/users/invalid')
    print(f'Status: {r.status_code}')
    print(f'Response: {r.json()}')
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()
    print('[PASS]\n')

    # Test 5: Create user
    print('=== Test 5: POST /api/users ===')
    r = client.post('/api/users', json={'name': 'Alice', 'email': 'alice@example.com'})
    print(f'Status: {r.status_code}')
    print(f'Response: {r.json()}')
    # POST returns 201 by default (or 200 if endpoint doesn't specify)
    assert r.status_code in [200, 201]
    assert r.json()["name"] == "Alice"
    assert r.json()["email"] == "alice@example.com"
    print('[PASS]\n')

    print('[SUCCESS] All tests passed successfully!')


if __name__ == "__main__":
    test_all_endpoints()
