# tests/test_main.py

import datetime
from unittest.mock import MagicMock, patch

import pytest
from src.main import app
from src.jobs import transcribe_task
from src.types import Transcription


# Fixture for the Flask test client
@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


# Fixture to mock the database
@pytest.fixture
def mock_database(mocker):
    mock_db = mocker.patch("src.main.db")
    return mock_db


# Fixture to mock RQ queue
@pytest.fixture
def mock_rq_queue(mocker):
    mock_queue = mocker.patch("src.main.rq_queue")
    return mock_queue


@patch("src.main.rq_queue.enqueue")
@patch("src.main.tempfile.NamedTemporaryFile")
def test_transcribe_success(mock_tempfile, mock_enqueue, client):
    # Setup the mock for NamedTemporaryFile
    mock_file = MagicMock()
    mock_file.name = "tempfile.wav"
    mock_tempfile.return_value = mock_file

    # Setup the mock for enqueue
    mock_job = MagicMock()
    mock_job.get_id.return_value = "12345"
    mock_enqueue.return_value = mock_job

    # Simulate POST request with binary data
    response = client.post(
        "/transcribe", data=b"test audio data", content_type="application/octet-stream"
    )

    assert response.status_code == 201
    assert response.json == {"jobId": "12345"}

    # Ensure the file was written
    mock_file.write.assert_called_once_with(b"test audio data")
    mock_file.close.assert_called_once()

    # Ensure enqueue was called with correct arguments
    mock_enqueue.assert_called_once()
    enqueue_args, enqueue_kwargs = mock_enqueue.call_args
    assert enqueue_args[0] == transcribe_task
    assert enqueue_kwargs["args"] == ("tempfile.wav",)
    assert enqueue_kwargs["result_ttl"] == 3600 * 24 * 7
    assert enqueue_kwargs["job_timeout"] == 3600 * 4


@patch("src.main.rq_queue.enqueue")
@patch("src.main.tempfile.NamedTemporaryFile")
def test_transcribe_no_data(mock_tempfile, mock_enqueue, client):
    # Simulate POST request with no data
    response = client.post("/transcribe")

    assert response.status_code == 400
    assert response.json["error"] == "No file uploaded or invalid file format."

    # Ensure enqueue was not called
    mock_enqueue.assert_not_called()


@patch("src.main.rq_queue.enqueue")
@patch("src.main.tempfile.NamedTemporaryFile")
def test_transcribe_enqueue_failure(mock_tempfile, mock_enqueue, client):
    # Setup the mock for NamedTemporaryFile
    mock_file = MagicMock()
    mock_file.name = "tempfile.wav"
    mock_tempfile.return_value = mock_file

    # Setup enqueue to raise an exception
    mock_enqueue.side_effect = Exception("Enqueue failed")

    # Simulate POST request with binary data
    response = client.post(
        "/transcribe", data=b"test audio data", content_type="application/octet-stream"
    )

    assert response.status_code == 500
    assert response.json["error"] == "Server error"

    # Ensure the file was written and closed
    mock_file.write.assert_called_once_with(b"test audio data")
    mock_file.close.assert_called_once()


@patch("src.main.rq_queue.enqueue")
@patch("src.main.tempfile.NamedTemporaryFile")
def test_transcribe_exception_during_processing(mock_tempfile, mock_enqueue, client):
    # Setup the mock for NamedTemporaryFile to raise an exception when writing
    mock_file = MagicMock()
    mock_file.write.side_effect = IOError("File write failed")
    mock_tempfile.return_value = mock_file

    # Simulate POST request with binary data
    response = client.post(
        "/transcribe", data=b"test audio data", content_type="application/octet-stream"
    )

    assert response.status_code == 500
    assert response.json["error"] == "Server error"

    # Ensure the file was attempted to be written and closed
    mock_file.write.assert_called_once_with(b"test audio data")
    mock_file.close.assert_called_once()


def test_get_job_info_success(client, mock_database):
    # Setup mock data
    job_id = "12345"
    created = datetime.datetime.now()
    transcription = Transcription(
        job_id=job_id,
        transcription="This is a test transcription.",
        filename="test_audio.mp3",
        total_duration=200.0,
        running_time=100.0,
        creation_date=created,
    )

    # Mock the database methods
    mock_database.get_transcription.return_value = transcription

    # Make the GET request
    response = client.get(f"/job/{job_id}")

    # Assert the response
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data["jobId"] == job_id
    assert data["transcription"] == transcription.transcription
    assert data["status"] == "finished"
    assert data["totalDuration"] == transcription.total_duration
    assert data["runningTime"] == transcription.running_time
    assert data["creationDate"] == created.isoformat()


def test_get_job_info_not_found(client, mock_database, mock_rq_queue):
    # Setup mock data
    job_id = "nonexistent_id"

    # Mock the database methods to return None
    mock_database.get_transcription.return_value = None

    # Mock the RQ fetch_job to return None (job not found in RQ)
    mock_rq_queue.fetch_job.return_value = None

    # Make the GET request
    response = client.get(f"/job/{job_id}")

    # Assert the response
    assert response.status_code == 404
    assert response.is_json
    data = response.get_json()
    assert data["error"] == f"Job ID {job_id} not found."


def test_get_job_info_processing(client, mock_database, mock_rq_queue):
    # Setup mock data
    job_id = "processing_id"

    # Mock the database methods to return None
    mock_database.get_transcription.return_value = None

    # Create a mock job object with 'processing' status
    mock_job = MagicMock()
    mock_job.is_failed = False
    mock_job.is_finished = False
    mock_job.is_queued = True

    # Mock the RQ fetch_job to return the mock job
    mock_rq_queue.fetch_job.return_value = mock_job

    # Make the GET request
    response = client.get(f"/job/{job_id}")

    # Assert the response
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data["jobId"] == job_id
    assert data["status"] == "processing"


def test_get_job_info_failure(client, mock_database, mock_rq_queue):
    # Setup mock data
    job_id = "failed_id"

    # Mock the database methods to return None
    mock_database.get_transcription.return_value = None

    # Create a mock job object with 'failure' status
    mock_job = MagicMock()
    mock_job.is_failed = True
    mock_job.is_finished = False
    mock_job.is_queued = False

    # Mock the RQ fetch_job to return the mock job
    mock_rq_queue.fetch_job.return_value = mock_job

    # Make the GET request
    response = client.get(f"/job/{job_id}")

    # Assert the response
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data["jobId"] == job_id
    assert data["status"] == "failure"


def test_get_job_info_unknown_status(client, mock_database, mock_rq_queue, caplog):
    # Setup mock data
    job_id = "unknown_status_id"

    # Mock the database methods to return None
    mock_database.get_transcription.return_value = None

    # Create a mock job object with an unknown status
    mock_job = MagicMock()
    mock_job.is_failed = False
    mock_job.is_finished = False
    mock_job.is_queued = False
    mock_job.is_started = False
    mock_job.is_deferred = False

    # Mock the RQ fetch_job to return the mock job
    mock_rq_queue.fetch_job.return_value = mock_job

    # Make the GET request
    response = client.get(f"/job/{job_id}")

    # Assert the response
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data["jobId"] == job_id
    assert data["status"] == "unknown"


def test_get_job_info_rq_exception(client, mock_database, mock_rq_queue, caplog):
    # Setup mock data
    job_id = "error_id"

    # Mock the database methods to return None
    mock_database.get_transcription.return_value = None

    # Mock the RQ fetch_job to raise a Redis ConnectionError
    from redis.exceptions import ConnectionError

    mock_rq_queue.fetch_job.side_effect = ConnectionError("Mocked Redis connection error")

    # Make the GET request
    response = client.get(f"/job/{job_id}")

    # Assert the response
    assert response.status_code == 500
    assert response.is_json
    data = response.get_json()
    assert data["error"] == "Server error"

    # Check if the error was logged
    assert "Error fetching job info for job_id error_id" in caplog.text
