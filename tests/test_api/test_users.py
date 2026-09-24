def test_get_me(req):
    response = req.get("/api/v1/users/me")
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "julian.clark@gmail.com"


def test_cannot_access_other_user(req, client, auth_token):
    other = {
        "email": "other@example.com",
        "username": "otheruser",
        "first_name": "Other",
        "last_name": "User",
        "password": "secret123",
    }
    client.post("/api/v1/auth/signup", json=other)
    signin = client.post("/api/v1/auth/signin", json={"email": other["email"], "password": other["password"]})
    other_headers = {"Authorization": f"Bearer {signin.json()['access_token']}"}
    other_id = client.get("/api/v1/users/me", headers=other_headers).json()["id"]

    forbidden = req.get(f"/api/v1/users/{other_id}")
    assert forbidden.status_code == 403
