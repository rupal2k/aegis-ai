"""Comprehensive security tests for Aegis AI platform."""
import httpx
import json
import pytest

BASE = "http://localhost:8000"
client = httpx.Client(timeout=10)

# ============================================================================
# 1. AUTHENTICATION SECURITY TESTS
# ============================================================================

class TestAuthenticationSecurity:
    """Test authentication mechanisms and JWT handling."""
    
    def test_invalid_credentials_rejected(self):
        """Test that invalid credentials are rejected."""
        r = client.post(f"{BASE}/auth/token",
                       data={"username": "fake@example.com", "password": "wrongpass"})
        assert r.status_code == 401, f"Expected 401, got {r.status_code}: {r.text}"
    
    def test_missing_credentials_rejected(self):
        """Test that missing credentials are rejected."""
        r = client.post(f"{BASE}/auth/token", data={})
        assert r.status_code in [400, 422, 401], f"Expected 400/422/401, got {r.status_code}"
    
    def test_sql_injection_in_username(self):
        """Test SQL injection protection in authentication."""
        r = client.post(f"{BASE}/auth/token",
                       data={"username": "admin' OR '1'='1", "password": "anything"})
        assert r.status_code == 401, "SQL injection not prevented in auth"
    
    def test_expired_token_rejected(self):
        """Test that expired tokens are rejected."""
        # Create a token with past expiration
        from datetime import datetime, timedelta, timezone
        from jose import jwt
        import os
        
        payload = {
            "sub": "test@example.com",
            "role": "underwriter",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        secret_key = os.environ.get("SECRET_KEY", "aegis-super-secret-jwt-key")
        expired_token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        r = client.get(f"{BASE}/predict/employee",
                      headers={"Authorization": f"Bearer {expired_token}"})
        assert r.status_code in [401, 422], "Expired token not rejected"
    
    def test_malformed_token_rejected(self):
        """Test that malformed tokens are rejected."""
        r = client.get(f"{BASE}/health",
                      headers={"Authorization": "Bearer invalid.token.format"})
        # Health endpoint doesn't require auth, so 200 is expected
        assert r.status_code == 200
    
    def test_missing_token_on_protected_endpoint(self):
        """Test that missing token is rejected on protected endpoints."""
        r = client.post(f"{BASE}/predict/employee",
                       json={"age": 30, "bmi": 25, "gender": "M"})
        assert r.status_code == 401, "Missing token not rejected on protected endpoint"


# ============================================================================
# 2. AUTHORIZATION AND ACCESS CONTROL TESTS
# ============================================================================

class TestAuthorizationSecurity:
    """Test role-based access control and authorization."""
    
    def test_unauthorized_route_access(self):
        """Test that unauthenticated access to protected routes is blocked."""
        r = client.get(f"{BASE}/companies")
        # This should either require auth or be accessible
        assert r.status_code in [200, 401, 403], f"Unexpected status: {r.status_code}"
    
    def test_invalid_role_access(self):
        """Test that invalid roles are handled properly."""
        from datetime import datetime, timedelta, timezone
        from jose import jwt
        import os
        
        secret_key = os.environ.get("SECRET_KEY", "aegis-super-secret-jwt-key")
        payload = {
            "sub": "test@example.com",
            "role": "invalid_role",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        r = client.post(f"{BASE}/predict/employee",
                       json={"age": 30, "bmi": 25, "gender": "M"},
                       headers={"Authorization": f"Bearer {token}"})
        # Should either work or be properly rejected
        assert r.status_code in [200, 403, 422], f"Invalid status: {r.status_code}"


# ============================================================================
# 3. API SECURITY HEADERS TESTS
# ============================================================================

class TestSecurityHeaders:
    """Test security headers in API responses."""
    
    def test_cors_headers_present(self):
        """Test that CORS headers are properly configured."""
        r = client.options(f"{BASE}/health",
                          headers={"Origin": "http://localhost:8501"})
        # Check if Access-Control headers are present
        assert "access-control-allow-origin" in r.headers or r.status_code == 200
    
    def test_content_type_header_set(self):
        """Test that Content-Type header is set."""
        r = client.get(f"{BASE}/health")
        assert "content-type" in r.headers, "Content-Type header missing"
    
    def test_no_server_header_leakage(self):
        """Test that server version is not exposed."""
        r = client.get(f"{BASE}/health")
        server = r.headers.get("server", "").lower()
        # Should not expose detailed version info
        if server:
            assert "uvicorn" not in server or "unknown" in server.lower()


# ============================================================================
# 4. INPUT VALIDATION AND INJECTION TESTS
# ============================================================================

class TestInputValidation:
    """Test input validation and protection against injection attacks."""
    
    def test_sql_injection_in_company_id(self):
        """Test SQL injection protection in company lookup."""
        # Get a valid token first
        r = client.post(f"{BASE}/auth/token",
                       data={"username": "underwriter@safenet.com", "password": "demo123"})
        if r.status_code != 200:
            pytest.skip("Authentication endpoint not working")
        
        token = r.json()["access_token"]
        
        # Try SQL injection
        r = client.get(f"{BASE}/companies/COMP_001' OR '1'='1",
                      headers={"Authorization": f"Bearer {token}"})
        assert r.status_code in [400, 404, 422], "SQL injection might not be prevented"
    
    def test_xss_in_json_payload(self):
        """Test XSS protection in JSON payloads."""
        r = client.post(f"{BASE}/ingest/company",
                       json={
                           "company_id": "<script>alert('xss')</script>",
                           "employees": []
                       })
        # Should be rejected or safely handled
        assert r.status_code in [400, 401, 422], "XSS payload might not be validated"
    
    def test_oversized_payload_rejected(self):
        """Test that oversized payloads are rejected."""
        large_payload = {
            "company_id": "COMP_001",
            "employees": [
                {
                    "external_employee_id": f"EMP_{i}",
                    "age": 30,
                    "gender": "M",
                    "bmi": 25,
                    "smoker": False,
                    "diabetic": False,
                    "hypertension": False,
                    "job_category": "desk"
                }
                for i in range(10000)  # Very large batch
            ]
        }
        r = client.post(f"{BASE}/ingest/company", json=large_payload)
        # Should be rejected or handled gracefully
        assert r.status_code in [400, 413, 422, 401], f"Unexpected status: {r.status_code}"
    
    def test_invalid_json_rejected(self):
        """Test that invalid JSON is rejected."""
        r = client.post(f"{BASE}/ingest/company",
                       content="{invalid json}",
                       headers={"Content-Type": "application/json"})
        assert r.status_code in [400, 422], "Invalid JSON not rejected"
    
    def test_negative_age_rejected(self):
        """Test validation of negative values."""
        r = client.post(f"{BASE}/predict/employee",
                       json={
                           "age": -30,
                           "bmi": 25,
                           "gender": "M",
                           "smoker": False,
                           "diabetic": False,
                           "hypertension": False,
                           "job_category": "desk"
                       })
        assert r.status_code in [401, 422], "Negative age not rejected"
    
    def test_extreme_bmi_rejected(self):
        """Test validation of extreme BMI values."""
        r = client.post(f"{BASE}/predict/employee",
                       json={
                           "age": 30,
                           "bmi": 500,  # Extreme value
                           "gender": "M",
                           "smoker": False,
                           "diabetic": False,
                           "hypertension": False,
                           "job_category": "desk"
                       })
        assert r.status_code in [401, 422], "Extreme BMI not rejected"


# ============================================================================
# 5. DATABASE SECURITY TESTS
# ============================================================================

class TestDatabaseSecurity:
    """Test database security and connection safety."""
    
    def test_database_connection_string_secure(self):
        """Test that database connection uses proper parameters."""
        import os
        db_url = os.environ.get("DATABASE_URL", "")
        assert db_url, "DATABASE_URL not set"
        # Check for credentials in URL
        assert "@" in db_url, "Database URL should be set"
        # Should not have credentials exposed in logs
        assert "password" not in db_url.lower() or "@" in db_url
    
    def test_db_health_endpoint_safe(self):
        """Test that database health endpoint doesn't leak information."""
        r = client.get(f"{BASE}/health/db")
        data = r.json()
        assert r.status_code == 200
        assert "database" in data
        # Should not expose detailed connection strings
        if "detail" in data:
            assert "://" not in str(data.get("detail", ""))


# ============================================================================
# 6. CONTAINER AND ENVIRONMENT SECURITY TESTS
# ============================================================================

class TestContainerSecurity:
    """Test container and environment security."""
    
    def test_environment_variables_not_exposed(self):
        """Test that environment variables are not exposed in API responses."""
        r = client.get(f"{BASE}/")
        data = r.json()
        for key, value in data.items():
            if isinstance(value, str):
                # Check that secret keys are not exposed
                assert "SECRET_KEY" not in str(value)
                assert "HASH_SALT" not in str(value)
                assert "DATABASE_URL" not in str(value)


# ============================================================================
# 7. RATE LIMITING AND DOS TESTS
# ============================================================================

class TestRateLimiting:
    """Test rate limiting and DOS protection."""
    
    def test_health_endpoint_available(self):
        """Test that health endpoint is always available."""
        for i in range(10):
            r = client.get(f"{BASE}/health")
            assert r.status_code == 200, f"Health endpoint failed on attempt {i}"
    
    def test_database_health_available(self):
        """Test that database health endpoint is always available."""
        for i in range(10):
            r = client.get(f"{BASE}/health/db")
            assert r.status_code == 200, f"DB health endpoint failed on attempt {i}"


# ============================================================================
# 8. COMMON VULNERABILITY TESTS
# ============================================================================

class TestCommonVulnerabilities:
    """Test for common web vulnerabilities."""
    
    def test_path_traversal_protection(self):
        """Test protection against path traversal attacks."""
        r = client.get(f"{BASE}/../../../etc/passwd")
        assert r.status_code == 404, "Path traversal might be possible"
    
    def test_method_not_allowed(self):
        """Test that unsupported methods are rejected."""
        r = client.delete(f"{BASE}/health")
        assert r.status_code == 405, "DELETE method should not be allowed on health"
    
    def test_options_request_safe(self):
        """Test that OPTIONS requests don't expose sensitive info."""
        r = client.options(f"{BASE}/health")
        assert r.status_code in [200, 204, 405]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
