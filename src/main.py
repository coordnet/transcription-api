import logging
import os
import tempfile
from typing import Any

import sentry_sdk
from flasgger import Swagger
from flask import Flask, jsonify, request
from flask_cors import CORS
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.rq import RqIntegration

from src import callbacks
from src.db import db
from src.jobs import transcribe_task
from src.queue import rq_queue
from rq.job import Job
from src.types import Transcription

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
UPLOADS_PATH = os.getenv("UPLOADS_PATH", "./uploads")
TESTING = os.getenv("TESTING", "0")
SENTRY_DSN = os.environ.get("SENTRY_DSN")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 250 * 1024 * 1024))

# Sentry initialization
if SENTRY_DSN and TESTING == "0":
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[FlaskIntegration(), RqIntegration()],
        environment=ENVIRONMENT,
        traces_sample_rate=1.0,
    )

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# Set up CORS
CORS(app)  # , origins=["http://localhost:58751", "https://dc.coord.dev"])

# Initialize Swagger
swagger = Swagger(app)


@app.route("/transcribe", methods=["POST"])
def transcribe() -> Any:
    """
    Endpoint to transcribe an audio file.
    ---
    consumes:
      - application/octet-stream
    parameters:
      - in: body
        name: file
        required: true
        schema:
          type: string
          format: binary
        description: The audio file to transcribe.
    responses:
      201:
        description: Transcription job created successfully.
        schema:
          type: object
          properties:
            jobId:
              type: string
              description: The unique identifier for the transcription job.
      400:
        description: No file uploaded or invalid file format.
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Server error.
        schema:
          type: object
          properties:
            error:
              type: string
    """
    # Ensure the uploads directory exists
    os.makedirs(UPLOADS_PATH, exist_ok=True)

    tempFile = tempfile.NamedTemporaryFile(dir=UPLOADS_PATH, delete=False)

    # Get the file from the request body and save it to a temporary file
    file = request.data

    try:
        if not file or not isinstance(file, bytes):
            return jsonify({"error": "No file uploaded or invalid file format."}), 400

        tempFile.write(file)
        tempFile.flush()  # Ensure data is written to disk
        filename = tempFile.name

        # Enqueue the transcription task
        job = rq_queue.enqueue(
            transcribe_task,
            args=(filename,),
            result_ttl=3600 * 24 * 7,
            job_timeout=3600 * 4,
            on_success=callbacks.transcription_completed,
            on_failure=callbacks.transcription_failed,
        )

        logger.info(f"Enqueued transcription job {job.get_id()} for file {filename}")

        return jsonify({"jobId": job.get_id()}), 201

    except Exception:
        logger.exception("Error processing transcription")
        return jsonify({"error": "Server error"}), 500
    finally:
        tempFile.close()


@app.route("/job/<job_id>", methods=["GET"])
def get_job_info(job_id: str) -> Any:
    """
    Endpoint to retrieve job information by job ID.
    ---
    parameters:
      - in: path
        name: job_id
        type: string
        required: true
        description: The unique identifier for the transcription job.
    responses:
      200:
        description: Job information retrieved successfully.
        schema:
          type: object
          properties:
            jobId:
              type: string
            transcription:
              type: string
            totalDuration:
              type: number
              format: float
              nullable: true
            runningTime:
              type: number
              format: float
            creationDate:
              type: string
              format: date-time
            status:
              type: string
              enum: [finished, processing, failure, unknown]
              description: The current status of the transcription job.
      404:
        description: Job ID not found.
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Server error.
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        # Attempt to fetch the transcription record from the database
        transcription: Transcription | None = db.get_transcription(job_id)
        if transcription:
            # Construct the response data from the transcription record
            job_info: dict[str, Any] = {
                "jobId": transcription.job_id,
                "status": "finished",
                "transcription": transcription.transcription,
                "totalDuration": transcription.total_duration,
                "runningTime": transcription.running_time,
                "creationDate": transcription.creation_date.isoformat(),
            }
            return jsonify(job_info), 200

        # If transcription not found in DB, check the RQ job status
        job: Job | None = rq_queue.fetch_job(job_id)
        if job:
            # Map RQ job statuses to desired status messages
            if job.is_failed:
                status = "failure"
            elif job.is_finished:
                # Job is finished but no DB record exists
                # TODO: Handle this case
                status = "finished"
            elif job.is_queued or job.is_started or job.is_deferred:
                status = "processing"
            else:
                status = "unknown"

            return jsonify({"jobId": job_id, "status": status}), 200

        # If job not found in RQ, return 404
        return jsonify({"error": f"Job ID {job_id} not found."}), 404

    except Exception:
        logger.exception(f"Error fetching job info for job_id {job_id}")
        return jsonify({"error": "Server error"}), 500


if __name__ == "__main__":
    # Example: Run the Flask app
    app.run(host="0.0.0.0", port=5000, debug=(ENVIRONMENT == "dev"))
