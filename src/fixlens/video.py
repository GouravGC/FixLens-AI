
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import cv2
import numpy as np


SUPPORTED_FORMATS = {".mp4", ".mov", ".avi"}


def extract_video_frames(
    video_bytes: bytes,
    filename: str = "upload.mp4",
    max_frames: int = 4,
    max_width: int = 1024,
) -> list[tuple[float, bytes]]:
    """Extract evenly spaced JPEG frames with timestamps from a video."""

    if not video_bytes:
        raise ValueError("The uploaded video is empty.")

    if max_frames < 1:
        raise ValueError("max_frames must be at least 1.")

    if max_width < 1:
        raise ValueError("max_width must be at least 1.")

    suffix = Path(filename).suffix.lower()

    if suffix not in SUPPORTED_FORMATS:
        raise ValueError("Supported video formats: MP4, MOV, AVI.")

    temp_path = None
    capture = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as temp:
            temp.write(video_bytes)
            temp_path = temp.name

        capture = cv2.VideoCapture(temp_path)

        if not capture.isOpened():
            raise ValueError(
                "Could not open the video. Try an MP4 encoded with H.264."
            )

        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(capture.get(cv2.CAP_PROP_FPS))

        if total_frames <= 0:
            raise ValueError("The video contains no readable frames.")

        if not np.isfinite(fps) or fps <= 0:
            fps = 1.0

        indexes = np.linspace(
            0,
            total_frames - 1,
            num=min(max_frames, total_frames),
            dtype=int,
        )

        extracted = []

        for frame_index in sorted(set(indexes.tolist())):
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            success, frame = capture.read()

            if not success or frame is None:
                continue

            height, width = frame.shape[:2]

            if width > max_width:
                resized_height = max(
                    1,
                    round(height * max_width / width),
                )
                frame = cv2.resize(
                    frame,
                    (max_width, resized_height),
                    interpolation=cv2.INTER_AREA,
                )

            success, encoded = cv2.imencode(
                ".jpg",
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, 85],
            )

            if success:
                timestamp = round(frame_index / fps, 2)
                extracted.append((timestamp, encoded.tobytes()))

        if not extracted:
            raise ValueError("No readable frames could be extracted.")

        return extracted

    finally:
        if capture is not None:
            capture.release()

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
