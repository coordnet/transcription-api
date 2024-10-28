import logging
import os
import time
from datetime import datetime, timezone

from faster_whisper import WhisperModel
from rq import get_current_job

from src.types import Transcription

GPU = os.getenv("GPU", "0").lower() == "1"


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def transcribe_task(filename: str) -> Transcription:
    logger.info(f"Transcribing {filename}")
    job = get_current_job()

    try:
        # Ensure the file exists before attempting to transcribe
        if not os.path.exists(filename):
            raise FileNotFoundError(f"File {filename} does not exist")

        model = WhisperModel(
            model_size_or_path="/app/models",
            local_files_only=True,  # Ensure we use the model from the container
            device="cuda" if GPU else "cpu",
            compute_type="float16" if GPU else "float32",
        )

        # Initialize variables for the concatenated transcription durations
        transcription_text = ""
        total_duration = 0.0
        start_time = time.time()

        segments, info = model.transcribe(filename, beam_size=5, language="en")

        # Loop through segments to build the full transcription and calculate total duration
        for segment in segments:
            transcription_text += segment.text.strip() + " "
            total_duration = max(total_duration, segment.end)

        # Strip trailing whitespace from the concatenated transcription
        transcription_text = transcription_text.strip()

        end_time = time.time()
        running_time = end_time - start_time  # Calculate job running time in seconds

        return Transcription(
            job_id=job.id,
            transcription=transcription_text,
            filename=filename,
            total_duration=total_duration,
            running_time=running_time,
            creation_date=datetime.now(timezone.utc),
        )

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred during transcription: {e}")
        raise
