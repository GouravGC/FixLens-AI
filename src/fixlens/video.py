
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import cv2


SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi"}


def extract_video_frames(
    video_bytes: bytes,
    filename: str = "uploaded_video.mp4",
    max_frames: int = 4,
    max_width: int = 1024,
) -> list[tuple[float, bytes]]:
    """Extract representative frames from an uploaded video.

    Returns a list of (timestamp_seconds, JPEG_bytes) tuples.
    """
    if not video_bytes:
        raise ValueError("The uploaded video is empty.")

    if max_frames < 1:
        raise ValueError("max_frames must be at least 1.")

    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_VIDEO_EXTENSIONS:
        raise ValueError(
            f"Unsupported video format: {extension or 'unknown'}. "
            "Upload an MP4, MOV, or AVI video."
        )

    temp_path = None
    capture = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=extension, delete=False
        ) as temp_file:
            temp_file.write(video_bytes)
            temp_path = temp_file.name

        capture = cv2.VideoCapture(temp_path)

        if not capture.isOpened():
            raise ValueError(
                "Could not open the uploaded video. "
                "Check that the file is a valid video."
            )

        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(capture.get(cv2.CAP_PROP_FPS))

        if frame_count <= 0:
            raise ValueError("The video contains no readable frames.")

        # Sample frames at evenly spaced positions across the video.
        sample_count = min(max_frames, frame_count)
        if sample_count == 1:
            frame_indices = [0]
        else:
            frame_indices = [
                round(i * (frame_count - 1) / (sample_count - 1))
                for i in range(sample_count)
            ]

        extracted: list[tuple[float, bytes]] = []

        for frame_index in frame_indices:
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            success, frame = capture.read()

            if not success or frame is None:
                continue

            height, width = frame.shape[:2]
            if width > max_width:
                new_height = max(1, round(height * max_width / width))
                frame = cv2.resize(
                    frame,
                    (max_width, new_height),
                    interpolation=cv2.INTER_AREA,
                )

            success, encoded = cv2.imencode(
                ".jpg",
                frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), 85],
            )

            if success:
                timestamp = (
                    frame_index / fps
                    if fps > 0
                    else 0.0
                )
                extracted.append((timestamp, encoded.tobytes()))

        if not extracted:
            raise ValueError("Could not extract any readable frames.")

        return extracted

    finally:
        if capture is not None:
            capture.release()

        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
