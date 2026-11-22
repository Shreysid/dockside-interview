"""Render interviewer replies with the installed macOS speech engine."""

from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

MAX_SPEECH_BYTES = 4096
MAX_WAV_BYTES = 4 * 1024 * 1024


class SpeechUnavailable(Exception):
    """The local speech engine failed to produce audio."""


def synthesize(text):
    # Bracket pairs can introduce embedded commands in the speech engine.
    spoken_text = text.translate(str.maketrans({"[": " ", "]": " "}))
    try:
        with TemporaryDirectory(prefix="dockside-speech-") as directory:
            output = Path(directory) / "reply.wav"
            subprocess.run(
                [
                    "/usr/bin/say", "--file-format=WAVE", "--data-format=LEI16@22050",
                    "-o", output, "-f", "-",
                ],
                input=spoken_text.encode("utf-8"),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
                check=True,
            )
            with output.open("rb") as audio:
                wav = audio.read(MAX_WAV_BYTES + 1)
            if len(wav) > MAX_WAV_BYTES or wav[:4] != b"RIFF" or wav[8:12] != b"WAVE":
                raise SpeechUnavailable
            return wav
    except (OSError, subprocess.SubprocessError) as exc:
        raise SpeechUnavailable from exc
