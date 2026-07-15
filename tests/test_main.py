import os
import pytest
import datetime
import main


@pytest.fixture(autouse=True)
def mock_data_paths(monkeypatch, tmp_path):
    # Use a temporary directory and files for the tests
    temp_data_file = tmp_path / "patrimoine_test.csv"
    temp_config_file = tmp_path / "config_test.json"

    monkeypatch.setattr(main, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(main, "DATA_FILE", str(temp_data_file))
    monkeypatch.setattr(main, "CONFIG_FILE", str(temp_config_file))

    # Initialize empty files in the test context
    main.init_empty_files()
    yield


@pytest.fixture
def client():
    main.app.config["TESTING"] = True
    with main.app.test_client() as client:
        yield client


def test_init_empty_files():
    assert os.path.exists(main.DATA_FILE)
    with open(main.DATA_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "date,valeur,note" in content


def test_save_and_load_config():
    # Initially no config
    assert main.load_config() is None

    # Save config
    main.save_config(50000, "2026-12-31")
    config = main.load_config()
    assert config is not None
    assert config["objectif"] == 50000.0
    assert config["date_fin"] == "2026-12-31"


def test_save_and_load_entries():
    # Save a few entries
    main.save_entry("2026-01-01", 1000.0, "Initial")
    main.save_entry("2026-02-01", 1200.0, "Salary")

    data = main.load_data()
    assert len(data) == 2
    assert data[0]["valeur"] == 1000.0
    assert data[0]["date"] == datetime.date(2026, 1, 1)
    assert data[0]["note"] == "Initial"

    assert data[1]["valeur"] == 1200.0
    assert data[1]["date"] == datetime.date(2026, 2, 1)

    # Update an entry (same date)
    main.save_entry("2026-01-01", 1050.0, "Initial updated")
    data = main.load_data()
    assert len(data) == 2
    assert data[0]["valeur"] == 1050.0
    assert data[0]["note"] == "Initial updated"


def test_delete_entry():
    main.save_entry("2026-01-01", 1000.0, "Initial")
    main.save_entry("2026-02-01", 1200.0, "Salary")

    main.delete_entry("2026-01-01")
    data = main.load_data()
    assert len(data) == 1
    assert data[0]["date"] == datetime.date(2026, 2, 1)


def test_get_stats():
    # Empty data stats
    latest, diff, pct = main.get_stats()
    assert latest == 0.0
    assert diff == 0.0
    assert pct == 0.0

    # Populate data
    main.save_entry("2026-01-01", 1000.0, "Initial")
    main.save_entry("2026-02-01", 1500.0, "Growth")

    latest, diff, pct = main.get_stats()
    assert latest == 1500.0
    assert diff == 500.0
    assert pct == 50.0


def test_flask_index_route(client):
    response = client.get("/")
    assert response.status_code == 200


def test_flask_api_endpoints(client):
    # Test GET /api/data
    main.save_config(20000, "2026-12-31")
    main.save_entry("2026-01-01", 10000.0, "Initial")

    response = client.get("/api/data")
    assert response.status_code == 200
    res_data = response.get_json()
    assert res_data["config"]["objectif"] == 20000.0
    assert len(res_data["entries"]) == 1
    assert res_data["entries"][0]["valeur"] == 10000.0
    assert res_data["stats"]["latest"] == 10000.0

    # Test POST /api/config
    config_payload = {"objectif": 30000.0, "date_fin": "2027-01-01"}
    response = client.post("/api/config", json=config_payload)
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"

    # Verify change
    assert main.load_config()["objectif"] == 30000.0

    # Test POST /api/entries
    entry_payload = {"date": "2026-03-01", "valeur": 12000.0, "note": "March savings"}
    response = client.post("/api/entries", json=entry_payload)
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"

    # Verify entry added
    entries = main.load_data()
    assert len(entries) == 2
    assert entries[1]["valeur"] == 12000.0

    # Test DELETE /api/entries/<date_str>
    response = client.delete("/api/entries/2026-03-01")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"

    # Verify deletion
    entries = main.load_data()
    assert len(entries) == 1
    assert entries[0]["valeur"] == 10000.0
