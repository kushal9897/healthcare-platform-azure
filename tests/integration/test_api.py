"""
Integration Tests - Healthcare Platform
Tests cross-service interactions and API contracts.

Usage:
    pytest tests/integration/ --base-url=https://dev-api.healthcare.internal
"""

import os
import pytest
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def api_url():
    return BASE_URL


class TestPatientServiceIntegration:
    def test_health_endpoint(self, api_url):
        resp = requests.get(f"{api_url}/health", timeout=10)
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_create_and_retrieve_patient(self, api_url):
        # Create
        patient_data = {
            "given_name": "Integration",
            "family_name": "Test",
            "birth_date": "1990-05-15",
            "gender": "female",
        }
        create_resp = requests.post(f"{api_url}/patients", json=patient_data, timeout=10)
        assert create_resp.status_code == 201
        patient_id = create_resp.json()["id"]

        # Retrieve
        get_resp = requests.get(f"{api_url}/patients/{patient_id}", timeout=10)
        assert get_resp.status_code == 200
        assert get_resp.json()["given_name"] == "Integration"

        # Search
        search_resp = requests.get(f"{api_url}/patients?name=Integration", timeout=10)
        assert search_resp.status_code == 200
        assert search_resp.json()["total"] >= 1

        # FHIR format
        fhir_resp = requests.get(f"{api_url}/patients/{patient_id}/fhir", timeout=10)
        assert fhir_resp.status_code == 200
        assert fhir_resp.json()["resourceType"] == "Patient"

    def test_patient_not_found(self, api_url):
        resp = requests.get(f"{api_url}/patients/nonexistent", timeout=10)
        assert resp.status_code == 404

    def test_metrics_endpoint(self, api_url):
        resp = requests.get(f"{api_url}/metrics", timeout=10)
        assert resp.status_code == 200
        assert "http_requests_total" in resp.text


class TestClinicalServiceIntegration:
    CLINICAL_URL = os.getenv("CLINICAL_URL", "http://localhost:8001")

    def test_health_endpoint(self):
        resp = requests.get(f"{self.CLINICAL_URL}/health", timeout=10)
        assert resp.status_code == 200

    def test_create_assessment(self):
        assessment = {
            "patient_id": "test-patient-001",
            "assessment_type": "primary_care",
            "chief_complaint": "Persistent headache for 3 days with moderate severity",
        }
        resp = requests.post(f"{self.CLINICAL_URL}/assess", json=assessment, timeout=30)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "completed"
        assert len(data["findings"]) > 0
        assert len(data["recommendations"]) > 0


class TestCrossServiceCommunication:
    def test_end_to_end_patient_assessment(self, api_url):
        """Full flow: create patient -> request assessment -> verify results."""
        # Step 1: Create patient
        patient = {
            "given_name": "E2E",
            "family_name": "TestPatient",
            "birth_date": "1985-03-20",
            "gender": "male",
        }
        patient_resp = requests.post(f"{api_url}/patients", json=patient, timeout=10)
        assert patient_resp.status_code == 201
        patient_id = patient_resp.json()["id"]

        # Step 2: Request clinical assessment
        clinical_url = os.getenv("CLINICAL_URL", "http://localhost:8001")
        assessment = {
            "patient_id": patient_id,
            "assessment_type": "emergency",
            "chief_complaint": "Chest pain, shortness of breath, onset 2 hours ago",
            "vitals": {"blood_pressure": "140/90", "heart_rate": 110, "temperature": 98.8},
        }
        assess_resp = requests.post(f"{clinical_url}/assess", json=assessment, timeout=30)
        assert assess_resp.status_code == 201
        assert assess_resp.json()["patient_id"] == patient_id
        assert assess_resp.json()["risk_level"] in ["low", "moderate", "high", "critical"]
