from __future__ import annotations

import sys
import unittest
from pathlib import Path


CORE = Path(__file__).resolve().parents[1] / "recorder-core"
sys.path.insert(0, str(CORE))

from src.ffmpeg_options import (  # noqa: E402
    recording_corrupt_packet_options,
    recording_input_options,
    recording_log_level,
)


class RecordingOptionsTests(unittest.TestCase):
    def test_soop_live_input_is_not_throttled(self) -> None:
        self.assertEqual(recording_input_options("SOOP", "https://example.invalid/live.m3u8"),
                         ["-i", "https://example.invalid/live.m3u8"])
        self.assertEqual(recording_corrupt_packet_options("SOOP"), [])
        self.assertEqual(recording_log_level("SOOP"), "warning")

    def test_other_platforms_keep_existing_behavior(self) -> None:
        self.assertEqual(recording_input_options("TikTok直播", "https://example.invalid/live.m3u8"),
                         ["-re", "-i", "https://example.invalid/live.m3u8"])
        self.assertEqual(recording_corrupt_packet_options("TikTok直播"), ["-fflags", "+discardcorrupt"])
        self.assertEqual(recording_log_level("TikTok直播"), "error")


if __name__ == "__main__":
    unittest.main()
