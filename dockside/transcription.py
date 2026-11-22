"""Transcribe a short browser recording with local tools."""

from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import wave

MAX_AUDIO_BYTES = 2 * 1024 * 1024
MAX_AUDIO_SECONDS = 30
SAMPLE_RATE = 16000
MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "ggml-base.en.bin"
DEMUXERS = {"audio/webm": "matroska", "audio/mp4": "mov", "audio/ogg": "ogg"}
NON_SPEECH_LINE = re.compile(r"\[[^\]]+\]|\([^\)]+\)|[♪♫ ]+")


class InvalidRecording(ValueError):
    """The input is unsupported, malformed, or outside recording limits."""


class TranscriberUnavailable(Exception):
    """A local transcription tool failed or timed out."""


def transcribe(audio: bytes, media_type: str) -> str:
    """Return the recognized words, or an empty string when no speech is found."""
    demuxer = DEMUXERS.get(media_type.partition(";")[0].strip().lower())
    if not demuxer or not 0 < len(audio) <= MAX_AUDIO_BYTES:
        raise InvalidRecording("Unsupported recording format or size")

    try:
        with TemporaryDirectory(prefix="dockside-audio-") as directory:
            wav_path = Path(directory) / "recording.wav"
            converted = subprocess.run(
                [
                    "ffmpeg", "-nostdin", "-v", "error", "-xerror",
                    "-protocol_whitelist", "pipe", "-f", demuxer, "-i", "pipe:0",
                    "-map", "0:a:0", "-t", str(MAX_AUDIO_SECONDS + 1),
                    "-ac", "1", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le",
                    str(wav_path),
                ],
                input=audio,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
            )
            if converted.returncode:
                raise InvalidRecording("Could not decode recording")

            with wave.open(str(wav_path), "rb") as wav:
                frames = wav.getnframes()
                if frames > SAMPLE_RATE * MAX_AUDIO_SECONDS:
                    raise InvalidRecording("Recording exceeds the time limit")
                if not any(wav.readframes(frames)):
                    return ""

            result_path = Path(directory) / "transcript"
            subprocess.run(
                [
                    "whisper-cli", "-m", str(MODEL_PATH), "-f", str(wav_path),
                    "-l", "en", "-np", "-sns", "-otxt", "-of", str(result_path),
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=45,
                check=True,
            )
            lines = result_path.with_suffix(".txt").read_text(encoding="utf-8").splitlines()
    except (OSError, subprocess.SubprocessError, wave.Error, EOFError, UnicodeError) as exc:
        raise TranscriberUnavailable from exc

    return " ".join(
        line for line in map(str.strip, lines) if line and not NON_SPEECH_LINE.fullmatch(line)
    )
