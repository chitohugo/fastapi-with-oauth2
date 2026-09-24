def test_list_characters_empty(req):
    response = req.get("/api/v1/characters")
    assert response.status_code == 200
    assert response.json() == []


def test_character_crud(req):
    payload = {
        "name": "Luke Skywalker",
        "height": 172.0,
        "mass": 77.0,
        "hair_color": "blond",
        "skin_color": "fair",
        "eye_color": "blue",
    }
    create_response = req.post("/api/v1/characters", json=payload)
    assert create_response.status_code == 200
    character = create_response.json()
    character_id = character["id"]

    list_response = req.get("/api/v1/characters")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = req.get(f"/api/v1/characters/{character_id}")
    assert get_response.status_code == 200

    update_response = req.patch(
        f"/api/v1/characters/{character_id}",
        json={**payload, "mass": 78.0},
    )
    assert update_response.status_code == 200
    assert update_response.json()["mass"] == 78.0

    delete_response = req.delete(f"/api/v1/characters/{character_id}")
    assert delete_response.status_code == 200

    not_found = req.get(f"/api/v1/characters/{character_id}")
    assert not_found.status_code == 404


def test_character_owner_forbidden(client, auth_token):
    payload = {
        "name": "Leia Organa",
        "height": 150.0,
        "mass": 49.0,
        "hair_color": "brown",
        "skin_color": "light",
        "eye_color": "brown",
    }
    owner_headers = {"Authorization": f"Bearer {auth_token}"}
    create_response = client.post("/api/v1/characters", json=payload, headers=owner_headers)
    assert create_response.status_code == 200
    character_id = create_response.json()["id"]

    other_signup = {
        "email": "other.user@example.com",
        "username": "otheruser",
        "first_name": "Other",
        "last_name": "User",
        "password": "secret123",
    }
    client.post("/api/v1/auth/signup", json=other_signup)
    other_signin = client.post(
        "/api/v1/auth/signin",
        json={"email": other_signup["email"], "password": other_signup["password"]},
    )
    other_token = other_signin.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    forbidden_get = client.get(f"/api/v1/characters/{character_id}", headers=other_headers)
    assert forbidden_get.status_code == 403


def test_character_partial_patch(req):
    payload = {
        "name": "Yoda",
        "height": 66.0,
        "mass": 17.0,
        "hair_color": "white",
        "skin_color": "green",
        "eye_color": "brown",
    }
    created = req.post("/api/v1/characters", json=payload)
    character_id = created.json()["id"]
    patched = req.patch(f"/api/v1/characters/{character_id}", json={"mass": 18.0})
    assert patched.status_code == 200
    assert patched.json()["mass"] == 18.0
    assert patched.json()["name"] == "Yoda"
