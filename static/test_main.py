import pytest
from fastapi.testclient import TestClient
from main import app   # make sure your main FastAPI file is named main.py

client = TestClient(app)


# ------------------- TEST: CREATE COMPLAINT -------------------
def test_create_complaint():
    response = client.post("/create-complaint", json={
        "title": "WiFi Issue",
        "description": "WiFi not working in room 242",
        "category": "Infrastructure",
        "priority": "Low",
        "user_id": 1
    })

    assert response.status_code == 200
    assert "message" in response.json()


# ------------------- TEST: GET USER COMPLAINTS -------------------
def test_get_user_complaints():
    response = client.get("/user-complaints/1")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ------------------- TEST: ASSIGN COMPLAINT -------------------
def test_assign_complaint():
    response = client.post("/assign-complaint", json={
        "complaint_id": 1,
        "staff_id": 2
    })

    assert response.status_code == 200
    assert "message" in response.json()


# ------------------- TEST: ADD COMMENT -------------------
def test_add_comment():
    response = client.post("/add-comment", json={
        "complaint_id": 1,
        "message": "Issue is being resolved"
    })

    assert response.status_code == 200
    assert "message" in response.json()


# ------------------- TEST: UPDATE STATUS -------------------
def test_update_status():
    response = client.post("/update-status", json={
        "complaint_id": 1,
        "status": "Resolved"
    })

    assert response.status_code == 200
    assert "message" in response.json()


# ------------------- TEST: LOGIN -------------------
def test_login():
    response = client.post("/login", json={
        "username": "testuser",
        "password": "1234"
    })

    # Even if user doesn't exist, API should respond properly
    assert response.status_code in [200, 401]


# ------------------- TEST: REGISTER -------------------
def test_register():
    response = client.post("/register", json={
        "username": "newuser",
        "password": "1234",
        "role": "student"
    })

    assert response.status_code == 200
    assert "message" in response.json()


# ------------------- TEST: NOTIFICATIONS -------------------
def test_get_notifications():
    response = client.get("/notifications/1")

    assert response.status_code == 200
    assert isinstance(response.json(), list)