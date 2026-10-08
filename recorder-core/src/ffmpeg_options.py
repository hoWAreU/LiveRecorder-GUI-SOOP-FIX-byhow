"""Small, side-effect-free FFmpeg options for recording live inputs."""


def recording_log_level(platform: str) -> str:
    # Surface input warnings for SOOP while keeping other platforms unchanged.
    return "warning" if platform == "SOOP" else "error"


def recording_input_options(platform: str, url: str) -> list[str]:
    # SOOP is already a live input. -re throttles reads and can lose packets.
    return ([] if platform == "SOOP" else ["-re"]) + ["-i", url]


def recording_corrupt_packet_options(platform: str) -> list[str]:
    # Preserve SOOP packets for the player instead of dropping every flagged
    # transport packet during capture. Other platforms retain their behavior.
    return [] if platform == "SOOP" else ["-fflags", "+discardcorrupt"]
