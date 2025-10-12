"""Automated test suite for Vega Web middleware system"""

from starlette.testclient import TestClient
from test_middleware import app


def test_middleware_system():
    """Test all middleware functionality"""
    client = TestClient(app)

    print("=" * 60)
    print("VEGA WEB MIDDLEWARE TEST SUITE")
    print("=" * 60)

    # Test 1: No middleware route
    print("\n[TEST 1] Route without middleware")
    r = client.get("/")
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.json()}")
    assert r.status_code == 200
    assert "No middleware" in r.json()["message"]
    print("  [PASS]")

    # Test 2: Auth middleware - missing token (should fail)
    print("\n[TEST 2] Auth middleware - no token")
    r = client.get("/api/protected")
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.json()}")
    assert r.status_code == 401
    assert "Missing authentication" in r.json()["detail"]
    assert "WWW-Authenticate" in r.headers
    print("  [PASS]")

    # Test 3: Auth middleware - invalid token
    print("\n[TEST 3] Auth middleware - invalid token")
    r = client.get("/api/protected", headers={"Authorization": "Bearer invalid"})
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.json()}")
    assert r.status_code == 401
    assert "Invalid or expired" in r.json()["detail"]
    print("  [PASS]")

    # Test 4: Auth middleware - valid token
    print("\n[TEST 4] Auth middleware - valid token")
    r = client.get("/api/protected", headers={"Authorization": "Bearer mytoken"})
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.json()}")
    assert r.status_code == 200
    assert "authenticated" in r.json()["message"]
    print("  [PASS]")

    # Test 5: Timing middleware
    print("\n[TEST 5] Timing middleware")
    r = client.get("/api/timed")
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.json()}")
    print(f"  Process Time: {r.headers.get('X-Process-Time', 'N/A')}s")
    assert r.status_code == 200
    assert "X-Process-Time" in r.headers
    process_time = float(r.headers["X-Process-Time"])
    assert process_time >= 0.1  # Should take at least 0.1s due to sleep
    print("  [PASS]")

    # Test 6: Cache control middleware
    print("\n[TEST 6] Cache control middleware")
    r = client.get("/api/cached")
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.json()}")
    print(f"  Cache-Control: {r.headers.get('Cache-Control', 'N/A')}")
    assert r.status_code == 200
    assert "Cache-Control" in r.headers
    assert "max-age=3600" in r.headers["Cache-Control"]
    print("  [PASS]")

    # Test 7: Custom header middleware
    print("\n[TEST 7] Custom header middleware")
    r = client.get("/api/custom")
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.json()}")
    print(f"  Custom Header: {r.headers.get('X-Custom-Header', 'N/A')}")
    assert r.status_code == 200
    assert "X-Custom-Header" in r.headers
    assert r.headers["X-Custom-Header"] == "CustomValue"
    print("  [PASS]")

    # Test 8: Validation middleware - missing header (should fail)
    print("\n[TEST 8] Validation middleware - missing required header")
    r = client.post("/api/validated", json={"test": "data"})
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.json()}")
    assert r.status_code == 400
    assert "Missing X-API-Version" in r.json()["detail"]
    print("  [PASS]")

    # Test 9: Validation middleware - with header (should succeed)
    print("\n[TEST 9] Validation middleware - with required header")
    r = client.post(
        "/api/validated",
        json={"test": "data"},
        headers={"X-API-Version": "1.0"}
    )
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.json()}")
    print(f"  Echo Header: {r.headers.get('X-API-Version-Echo', 'N/A')}")
    assert r.status_code == 200
    assert "validated" in r.json()["message"]
    assert "X-API-Version-Echo" in r.headers
    assert r.headers["X-API-Version-Echo"] == "1.0"
    print("  [PASS]")

    # Test 10: Multiple chained middleware
    print("\n[TEST 10] Multiple chained middleware")
    r = client.get("/api/chained")
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.json()}")
    print(f"  Process Time: {r.headers.get('X-Process-Time', 'N/A')}s")
    print(f"  Cache-Control: {r.headers.get('Cache-Control', 'N/A')}")
    assert r.status_code == 200
    assert "X-Process-Time" in r.headers
    assert "Cache-Control" in r.headers
    assert "max-age=60" in r.headers["Cache-Control"]
    print("  [PASS]")

    print("\n" + "=" * 60)
    print("[SUCCESS] All middleware tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_middleware_system()
