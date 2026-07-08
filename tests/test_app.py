import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange: snapshot state before each test, restore after
    original = {
        name: {**data, "participants": list(data["participants"])}
        for name, data in activities.items()
    }
    yield
    activities.clear()
    activities.update(original)


client = TestClient(app)


# --- GET /activities ---

def test_get_activities_returns_200():
    # Act
    response = client.get("/activities")
    # Assert
    assert response.status_code == 200


def test_get_activities_returns_all_activities():
    # Act
    response = client.get("/activities")
    # Assert
    assert isinstance(response.json(), dict)
    assert len(response.json()) > 0


def test_get_activities_contains_expected_fields():
    # Act
    response = client.get("/activities")
    # Assert
    for activity in response.json().values():
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


# --- POST /activities/{activity_name}/signup ---

def test_signup_success():
    # Arrange
    email = "new@mergington.edu"
    # Act
    response = client.post(f"/activities/Chess Club/signup?email={email}")
    # Assert
    assert response.status_code == 200
    assert email in response.json()["message"]


def test_signup_adds_participant_to_activity():
    # Arrange
    email = "new@mergington.edu"
    # Act
    client.post(f"/activities/Chess Club/signup?email={email}")
    response = client.get("/activities")
    # Assert
    assert email in response.json()["Chess Club"]["participants"]


def test_signup_nonexistent_activity_returns_404():
    # Arrange
    email = "x@mergington.edu"
    # Act
    response = client.post(f"/activities/Nonexistent Activity/signup?email={email}")
    # Assert
    assert response.status_code == 404


def test_signup_duplicate_email_returns_400():
    # Arrange
    email = "michael@mergington.edu"  # already in Chess Club
    # Act
    response = client.post(f"/activities/Chess Club/signup?email={email}")
    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


# --- DELETE /activities/{activity_name}/signup ---

def test_unregister_success():
    # Arrange
    email = "michael@mergington.edu"  # already in Chess Club
    # Act
    response = client.delete(f"/activities/Chess Club/signup?email={email}")
    # Assert
    assert response.status_code == 200
    assert email in response.json()["message"]


def test_unregister_removes_participant_from_activity():
    # Arrange
    email = "michael@mergington.edu"
    # Act
    client.delete(f"/activities/Chess Club/signup?email={email}")
    response = client.get("/activities")
    # Assert
    assert email not in response.json()["Chess Club"]["participants"]


def test_unregister_nonexistent_activity_returns_404():
    # Arrange
    email = "x@mergington.edu"
    # Act
    response = client.delete(f"/activities/Nonexistent Activity/signup?email={email}")
    # Assert
    assert response.status_code == 404


def test_unregister_participant_not_signed_up_returns_404():
    # Arrange
    email = "nothere@mergington.edu"
    # Act
    response = client.delete(f"/activities/Chess Club/signup?email={email}")
    # Assert
    assert response.status_code == 404


# --- GET / (redirect) ---

def test_root_redirects_to_static_index():
    # Act
    response = client.get("/", follow_redirects=False)
    # Assert
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"] == "/static/index.html"
