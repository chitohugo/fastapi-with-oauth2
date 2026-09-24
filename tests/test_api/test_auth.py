def test_signup_duplicate_email(client):
    payload = {
        "email": "dup@example.com",
        "username": "dupuser",
        "first_name": "Dup",
        "last_name": "User",
        "password": "secret123",
    }
    first = client.post("/api/v1/auth/signup", json=payload)
    assert first.status_code == 200
    second = client.post("/api/v1/auth/signup", json=payload)
    assert second.status_code == 409
    assert second.json()["code"] == "duplicated"
