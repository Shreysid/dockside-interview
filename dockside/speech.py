"""Render interviewer replies with local Kokoro-82M."""

from functools import cache
from io import BytesIO
from pathlib import Path
import wave

MAX_SPEECH_BYTES = 4096
MAX_WAV_BYTES = 4 * 1024 * 1024
MODEL_DIR = Path(__file__).resolve().parent.parent / "models"


class SpeechUnavailable(Exception):
    """The local speech engine failed to produce audio."""


@cache
def _engine():
    from kokoro_onnx import Kokoro

    return Kokoro(
        str(MODEL_DIR / "kokoro-v1.0.int8.onnx"),
        str(MODEL_DIR / "voices-v1.0.bin"),
    )


def synthesize(text):
    try:
        samples, sample_rate = _engine().create(text, voice="af_heart", lang="en-us")
    except Exception as exc:
        # Model loading, phonemization and inference can all fail independently.
        raise SpeechUnavailable from exc

    # A PCM WAV has a 44-byte header and two bytes per mono sample.
    if not samples.size or 44 + samples.size * 2 > MAX_WAV_BYTES:
        raise SpeechUnavailable

    pcm = (samples.clip(-1, 1) * 32767).astype("<i2")
    output = BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setparams((1, 2, sample_rate, 0, "NONE", "not compressed"))
        audio.writeframes(pcm.tobytes())
    return output.getvalue()
