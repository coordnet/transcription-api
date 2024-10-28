import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from src.types import Transcription

DB_PATH = os.getenv("DATABASE_PATH", "transcriptions.db")


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS transcriptions (
                    job_id TEXT PRIMARY KEY,
                    transcription TEXT,
                    filename TEXT,
                    total_duration REAL,
                    running_time REAL,
                    creation_date DATETIME
                )
            """
            )

    def save_transcription(self, transcription: Transcription):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO transcriptions
                (job_id, transcription, filename, total_duration, running_time, creation_date)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    transcription.job_id,
                    transcription.transcription,
                    transcription.filename,
                    transcription.total_duration,
                    transcription.running_time,
                ),
            )

    def get_transcription(self, job_id: str) -> Transcription | None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    job_id, transcription, filename, total_duration, running_time,
                    creation_date
                FROM transcriptions
                WHERE job_id = ?
                """,
                (job_id,),
            )
            row = cursor.fetchone()
            if row:
                new_row = list(row)
                new_row[-1] = datetime.strptime(new_row[-1], "%Y-%m-%d %H:%M:%S")
                return Transcription(*new_row)
            return None


db = Database()
