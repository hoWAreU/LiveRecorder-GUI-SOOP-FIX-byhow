from __future__ import annotations

import asyncio
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


CORE = Path(__file__).resolve().parents[1] / "recorder-core"
sys.path.insert(0, str(CORE))

from src import spider, stream  # noqa: E402
from src.soop_quality import ordered_presets  # noqa: E402


PRESETS = [
    {"label": "360p", "name": "sd"},
    {"label": "540p", "name": "hd"},
    {"label": "720p", "name": "hd4k"},
    {"label": "1080p", "name": "original"},
    {"label": "auto", "name": "auto"},
]


class SoopQualityTests(unittest.TestCase):
    def test_named_quality_is_selected_instead_of_playlist_index(self) -> None:
        self.assertEqual(ordered_presets(PRESETS, "1080P")[0]["name"], "original")
        self.assertEqual(ordered_presets(PRESETS, "720P")[0]["name"], "hd4k")
        self.assertEqual(ordered_presets(PRESETS, "2K")[0]["name"], "original")
        self.assertEqual(ordered_presets(PRESETS, "540P")[0]["name"], "hd")

    def test_nearest_lower_quality_when_requested_height_is_missing(self) -> None:
        presets = [PRESETS[0], PRESETS[1], PRESETS[2]]
        self.assertEqual(ordered_presets(presets, "1080P")[0]["name"], "hd4k")

    def test_desktop_api_uses_quality_specific_aid_and_cdn_key(self) -> None:
        calls: list[tuple[str, str]] = []

        async def fake_request(url, **kwargs):
            data = kwargs.get("data") or {}
            if data.get("type") == "live":
                return json.dumps({"CHANNEL": {
                    "RESULT": 1, "BNO": "297686121", "BJNICK": "Streamer",
                    "CDN": "gcp_cdn", "VIEWPRESET": PRESETS,
                }})
            if data.get("type") == "aid":
                calls.append(("aid", data["quality"]))
                return json.dumps({"CHANNEL": {"RESULT": 1, "AID": "test-token"}})
            if "broad_stream_assign.html" in url:
                calls.append(("manager", url))
                return json.dumps({"view_url": "https://media.sooplive.com/1080.m3u8"})
            self.fail("unexpected request")

        with patch.object(spider, "async_req", side_effect=fake_request):
            result = asyncio.run(spider.get_sooplive_stream_data(
                "https://play.sooplive.com/joahe2/297686121",
                cookies="test-cookie", requested_quality="1080P",
            ))

        self.assertTrue(result["is_live"])
        self.assertEqual(result["play_url_list"], [result["m3u8_url"]])
        recorder_data = asyncio.run(stream.get_stream_url(result, "OD", spec=True))
        self.assertEqual(recorder_data["record_url"], result["m3u8_url"])
        self.assertEqual(calls[0], ("aid", "original"))
        self.assertIn("297686121-common-original-hls", calls[1][1])


if __name__ == "__main__":
    unittest.main()
