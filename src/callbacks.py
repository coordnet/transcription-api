import logging
import os
from typing import Any

from rq.job import Job

from src.db import db
from src.types import Transcription

DELETE_UPLOADED_FILES = os.getenv("DELETE_UPLOADED_FILES", "1") == "1"


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def transcription_completed(job: Job, connection: Any, result: Transcription):
    """
    Callback function to handle successful transcription.
    Saves the transcription to the database and deletes the temporary file.
    """
    logger.info(f"Transcription job finished successfully: {job.id}")

    logger.info("Writing transcription to database")
    db.save_transcription(result)

    # Delete the temporary file
    delete_job_file(job)


def transcription_failed(
    job: Job, connection: Any, exc_type: type, exc_value: Exception, traceback: Any
):
    """
    Callback function to handle failed transcription.
    Logs the failure details and deletes the temporary file.
    """
    try:
        logger.error(f"Transcription job failed: {job.id}")
        logger.error(f"Failure type: {exc_type}")
        logger.error(f"Failure value: {exc_value}")
        logger.error(f"Failure traceback: {traceback}")
    except Exception as e:
        logger.exception(f"Error while logging job failure for {job.id}: {e}")

    # Delete the temporary file
    delete_job_file(job)


def delete_job_file(job: Job):
    """
    Retrieves the temporary file path from the job arguments and deletes it.
    """
    if not DELETE_UPLOADED_FILES:
        logger.info("DELETE_UPLOADED_FILES is disabled. Skipping file deletion.")
        return
    try:
        # Ensure that job.args exists and has at least one element
        if job.args and len(job.args) >= 1:
            temp_file_path = job.args[0]
            if temp_file_path:
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                        logger.info(f"Deleted temporary file: {temp_file_path}")
                    else:
                        logger.warning(f"Temporary file does not exist: {temp_file_path}")
                except Exception as e:
                    logger.error(f"Error deleting temporary file {temp_file_path}: {e}")
        else:
            logger.warning(f"No arguments found for job {job.id}. Cannot delete temporary file.")
    except Exception as e:
        logger.error(f"Error retrieving temporary file path for job {job.id}: {e}")
