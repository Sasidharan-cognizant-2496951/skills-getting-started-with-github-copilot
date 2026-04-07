"""
Comprehensive test suite for the FastAPI activities management API.

Tests cover all endpoints (GET /activities, POST signup, DELETE signup)
including happy paths and error cases.
"""

import pytest


class TestGetActivities:
    """Tests for the GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client):
        """Verify that all activities are returned."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Should have 9 activities
        assert len(data) == 9
        
        # Verify specific activities exist
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Basketball Team" in data
    
    def test_get_activities_response_structure(self, client):
        """Verify the response structure for each activity."""
        response = client.get("/activities")
        data = response.json()
        
        # Check that each activity has the required fields
        for activity_name, activity_data in data.items():
            assert isinstance(activity_name, str)
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            
            # Verify field types
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)
    
    def test_get_activities_participants_accuracy(self, client):
        """Verify that participants list is accurate for activities."""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club should have michael and daniel
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
        
        # Basketball Team should have no participants initially
        assert len(data["Basketball Team"]["participants"]) == 0
    
    def test_get_activities_capacity_info(self, client):
        """Verify that capacity information is present and reasonable."""
        response = client.get("/activities")
        data = response.json()
        
        # Check max_participants is reasonable
        chess_club = data["Chess Club"]
        assert chess_club["max_participants"] > 0
        assert chess_club["max_participants"] >= len(chess_club["participants"])
    
    def test_root_redirects_to_static(self, client):
        """Verify that the root endpoint redirects to static files."""
        response = client.get("/", follow_redirects=False)
        
        # Should redirect (307 by default in FastAPI)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_successful(self, client, sample_email):
        """Successfully sign up a student for an activity."""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": sample_email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert sample_email in data["message"]
        assert "Basketball Team" in data["message"]
        
        # Verify student is now in participants
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert sample_email in activities_data["Basketball Team"]["participants"]
    
    def test_signup_multiple_students_same_activity(self, client, sample_emails):
        """Sign up multiple students for the same activity."""
        activity_name = "Soccer Club"
        
        # Sign up first student
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_emails["student1"]}
        )
        assert response1.status_code == 200
        
        # Sign up second student
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_emails["student2"]}
        )
        assert response2.status_code == 200
        
        # Verify both are in participants
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert sample_emails["student1"] in participants
        assert sample_emails["student2"] in participants
    
    def test_signup_duplicate_email_returns_400(self, client, sample_emails):
        """Attempting to sign up with duplicate email should return 400."""
        activity_name = "Chess Club"
        email = sample_emails["already_registered"]  # michael@mergington.edu already in Chess Club
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_activity_not_found_returns_404(self, client, sample_email):
        """Attempting to sign up for non-existent activity should return 404."""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": sample_email}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_same_student_different_activities(self, client, sample_email):
        """A student can sign up for multiple different activities."""
        email = sample_email
        
        # Sign up for first activity
        response1 = client.post(
            "/activities/Basketball Team/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Sign up for second activity
        response2 = client.post(
            "/activities/Soccer Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify student is in both activities
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data["Basketball Team"]["participants"]
        assert email in activities_data["Soccer Club"]["participants"]


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/signup endpoint."""
    
    def test_unregister_successful(self, client, sample_email):
        """Successfully unregister a student from an activity."""
        activity_name = "Basketball Team"
        
        # First sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        assert signup_response.status_code == 200
        
        # Then unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        assert unregister_response.status_code == 200
        data = unregister_response.json()
        assert "message" in data
        assert sample_email in data["message"]
        
        # Verify student is no longer in participants
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert sample_email not in activities_data[activity_name]["participants"]
    
    def test_unregister_from_already_registered_activity(self, client, sample_emails):
        """Unregister from an activity with pre-registered participants."""
        activity_name = "Chess Club"
        email = sample_emails["already_registered"]  # michael@mergington.edu
        
        # Verify is registered before unregister
        activities_before = client.get("/activities").json()
        assert email in activities_before[activity_name]["participants"]
        initial_count = len(activities_before[activity_name]["participants"])
        
        # Unregister
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify is no longer registered
        activities_after = client.get("/activities").json()
        assert email not in activities_after[activity_name]["participants"]
        assert len(activities_after[activity_name]["participants"]) == initial_count - 1
    
    def test_unregister_email_not_registered_returns_404(self, client, sample_email):
        """Attempting to unregister non-registered email returns 404."""
        activity_name = "Basketball Team"
        
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        
        assert response.status_code == 404
        assert "not registered" in response.json()["detail"].lower()
    
    def test_unregister_activity_not_found_returns_404(self, client, sample_email):
        """Attempting to unregister from non-existent activity returns 404."""
        response = client.delete(
            "/activities/Nonexistent Activity/signup",
            params={"email": sample_email}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_then_register_again(self, client, sample_email):
        """A student can unregister and then register again for an activity."""
        activity_name = "Basketball Team"
        
        # Sign up
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        assert response1.status_code == 200
        
        # Unregister
        response2 = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        assert response2.status_code == 200
        
        # Sign up again
        response3 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        assert response3.status_code == 200
        
        # Verify registered again
        activities_response = client.get("/activities")
        assert sample_email in activities_response.json()[activity_name]["participants"]


class TestIntegration:
    """Integration tests combining multiple operations."""
    
    def test_multiple_students_signup_and_unregister(self, client, sample_emails):
        """Test signup and unregister operations for multiple students."""
        activity_name = "Drama Club"
        
        # Sign up three students
        for email_key in ["student1", "student2", "student3"]:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": sample_emails[email_key]}
            )
            assert response.status_code == 200
        
        # Verify all three are registered
        activities = client.get("/activities").json()
        for email_key in ["student1", "student2", "student3"]:
            assert sample_emails[email_key] in activities[activity_name]["participants"]
        
        # Unregister the second student
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": sample_emails["student2"]}
        )
        assert response.status_code == 200
        
        # Verify only two remain
        activities = client.get("/activities").json()
        assert sample_emails["student1"] in activities[activity_name]["participants"]
        assert sample_emails["student2"] not in activities[activity_name]["participants"]
        assert sample_emails["student3"] in activities[activity_name]["participants"]
    
    def test_student_signup_to_multiple_activities(self, client, sample_email):
        """Test a student signing up for multiple activities."""
        activities_to_join = ["Chess Club", "Programming Class", "Art Club"]
        
        # Sign up for each activity (skip Gym Class where already registered)
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": sample_email}
            )
            assert response.status_code == 200
        
        # Verify registered for all activities
        activities_response = client.get("/activities").json()
        for activity in activities_to_join:
            assert sample_email in activities_response[activity]["participants"]
    
    def test_activity_capacity_tracking(self, client):
        """Verify that participant count is tracked correctly."""
        activity_name = "Science Club"
        students = [f"student{i}@mergington.edu" for i in range(5)]
        
        # Initial count
        initial_activities = client.get("/activities").json()
        initial_count = len(initial_activities[activity_name]["participants"])
        
        # Sign up 5 students
        for email in students:
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
        
        # Check count increased by 5
        after_signup = client.get("/activities").json()
        assert len(after_signup[activity_name]["participants"]) == initial_count + 5
        
        # Unregister 2 students
        for email in students[:2]:
            client.delete(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
        
        # Check count decreased by 2
        after_unregister = client.get("/activities").json()
        assert len(after_unregister[activity_name]["participants"]) == initial_count + 3
