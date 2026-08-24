from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient


class DetectorAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("detector.views.run_query")
    def test_health_success(self, mock_run_query):
        mock_run_query.return_value = [{"1": 1}]
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "database": "connected"})

    @patch("detector.views.run_query")
    def test_health_database_error(self, mock_run_query):
        mock_run_query.side_effect = Exception("DB connection failed")
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "error", "database": "unavailable"})

    @patch("detector.views.run_query")
    def test_account_list_success(self, mock_run_query):
        mock_run_query.return_value = [
            {
                "id": "acc_001",
                "name": "Alice Smith",
                "account_type": "personal",
                "created_at": None,
                "transaction_count": 5,
            }
        ]
        response = self.client.get("/api/accounts")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], "acc_001")
        self.assertEqual(data[0]["name"], "Alice Smith")

    @patch("detector.views.run_query")
    def test_account_detail_not_found(self, mock_run_query):
        mock_run_query.return_value = []
        response = self.client.get("/api/accounts/nonexistent")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "account not found"})

    @patch("detector.views.run_query")
    def test_account_detail_success(self, mock_run_query):
        mock_run_query.return_value = [
            {
                "id": "acc_001",
                "name": "Alice Smith",
                "account_type": "personal",
                "created_at": None,
                "transaction_count": 5,
            }
        ]
        response = self.client.get("/api/accounts/acc_001")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], "acc_001")

    @patch("detector.views.detect_cycles")
    def test_detection_cycles(self, mock_detect_cycles):
        mock_detect_cycles.return_value = [
            {
                "pattern": "cycle",
                "length": 3,
                "accounts": ["acc_001", "acc_002", "acc_003"],
                "total_amount": 1500.0,
            }
        ]
        response = self.client.get("/api/detections/cycles")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(len(data["cycles"]), 1)

    @patch("detector.views.detect_convergence")
    @patch("detector.views.detect_fanout")
    def test_detection_fanout_and_convergence(self, mock_fanout, mock_convergence):
        mock_fanout.return_value = [
            {
                "source_account": "acc_source",
                "recipients": ["acc_1", "acc_2", "acc_3"],
            }
        ]
        mock_convergence.return_value = []
        response = self.client.get("/api/detections/fanout")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["fanout"]["count"], 1)
        self.assertEqual(data["convergence"]["count"], 0)
