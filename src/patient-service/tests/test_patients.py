"""Unit tests for Patient Service."""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthEndpoints:
    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "patient-service"

    def test_readiness(self):
        response = client.get("/ready")
        assert response.status_code == 200

    def test_metrics(self):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text


class TestPatientCRUD:
    def _create_patient(self):
        return client.post("/patients", json={
            "given_name": "John",
            "family_name": "Doe",
            "birth_date": "1990-01-15",
            "gender": "male",
            "phone": "+1234567890",
            "email": "john.doe@example.com",
        })

    def test_create_patient(self):
        response = self._create_patient()
        assert response.status_code == 201
        data = response.json()
        assert data["given_name"] == "John"
        assert data["family_name"] == "Doe"
        assert "id" in data

    def test_get_patient(self):
        create_resp = self._create_patient()
        patient_id = create_resp.json()["id"]

        response = client.get(f"/patients/{patient_id}")
        assert response.status_code == 200
        assert response.json()["id"] == patient_id

    def test_get_patient_not_found(self):
        response = client.get("/patients/nonexistent-id")
        assert response.status_code == 404

    def test_search_patients(self):
        self._create_patient()
        response = client.get("/patients?name=John")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_search_patients_by_gender(self):
        self._create_patient()
        response = client.get("/patients?gender=male")
        assert response.status_code == 200

    def test_delete_patient(self):
        create_resp = self._create_patient()
        patient_id = create_resp.json()["id"]

        response = client.delete(f"/patients/{patient_id}")
        assert response.status_code == 204

    def test_delete_patient_not_found(self):
        response = client.delete("/patients/nonexistent-id")
        assert response.status_code == 404


class TestFHIREndpoints:
    def test_get_patient_fhir(self):
        create_resp = client.post("/patients", json={
            "given_name": "Jane",
            "family_name": "Smith",
            "birth_date": "1985-06-20",
            "gender": "female",
        })
        patient_id = create_resp.json()["id"]

        response = client.get(f"/patients/{patient_id}/fhir")
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Patient"
        assert data["gender"] == "female"

    def test_fhir_not_found(self):
        response = client.get("/patients/nonexistent-id/fhir")
        assert response.status_code == 404


class TestValidation:
    def test_invalid_gender(self):
        response = client.post("/patients", json={
            "given_name": "Test",
            "family_name": "User",
            "birth_date": "1990-01-01",
            "gender": "invalid",
        })
        assert response.status_code == 422

    def test_invalid_birth_date(self):
        response = client.post("/patients", json={
            "given_name": "Test",
            "family_name": "User",
            "birth_date": "not-a-date",
            "gender": "male",
        })
        assert response.status_code == 422

    def test_empty_name(self):
        response = client.post("/patients", json={
            "given_name": "",
            "family_name": "User",
            "birth_date": "1990-01-01",
            "gender": "male",
        })
        assert response.status_code == 422
