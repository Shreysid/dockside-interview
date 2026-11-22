from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
import wave

from dockside.transcription import (
    MAX_AUDIO_BYTES,
    MAX_AUDIO_SECONDS,
    SAMPLE_RATE,
    InvalidRecording,
    TranscriberUnavailable,
    transcribe,
)


class TranscriptionTests(unittest.TestCase):
    @patch("dockside.transcription.subprocess.run")
    def test_rejects_invalid_input_before_running_tools(self, run):
        for audio, media_type in (
            (b"", "audio/webm"),
            (b"a" * (MAX_AUDIO_BYTES + 1), "audio/webm"),
            (b"a", "text/plain"),
        ):
            with self.subTest(size=len(audio), media_type=media_type):
                with self.assertRaises(InvalidRecording):
                    transcribe(audio, media_type)
        run.assert_not_called()

    @patch("dockside.transcription.subprocess.run")
    def test_decoder_errors_and_timeouts(self, run):
        run.return_value = subprocess.CompletedProcess([], 1)
        with self.assertRaises(InvalidRecording):
            transcribe(b"invalid", "audio/webm")

        run.side_effect = subprocess.TimeoutExpired("ffmpeg", 10)
        with self.assertRaises(TranscriberUnavailable):
            transcribe(b"recording", "audio/webm")

    @patch("dockside.transcription.subprocess.run")
    def test_silence_and_long_audio_do_not_reach_whisper(self, run):
        for frames in (SAMPLE_RATE, SAMPLE_RATE * MAX_AUDIO_SECONDS + 1):
            with self.subTest(frames=frames):
                run.reset_mock()
                run.side_effect = lambda command, **kwargs: self.write_wav(command[-1], frames)
                if frames == SAMPLE_RATE:
                    self.assertEqual(transcribe(b"recording", "audio/webm"), "")
                else:
                    with self.assertRaises(InvalidRecording):
                        transcribe(b"recording", "audio/webm")
                run.assert_called_once()

    @patch("dockside.transcription.subprocess.run")
    def test_returns_words_and_removes_temporary_files(self, run):
        def write_output(command, **kwargs):
            if command[0] == "ffmpeg":
                self.assertEqual(command[command.index("-f") + 1], "matroska")
                return self.write_wav(command[-1], SAMPLE_RATE, b"\x01\x00")
            transcript_path = Path(command[-1]).with_suffix(".txt")
            transcript_path.write_text("[BLANK_AUDIO]\nI would sort the intervals.\n")
            return subprocess.CompletedProcess(command, 0)

        run.side_effect = write_output
        self.assertEqual(
            transcribe(b"recording", "audio/webm;codecs=opus"),
            "I would sort the intervals.",
        )
        wav_path = Path(run.call_args_list[0].args[0][-1])
        self.assertFalse(wav_path.parent.exists())

    def write_wav(self, path, frames, sample=b"\x00\x00"):
        with wave.open(path, "wb") as output:
            output.setparams((1, 2, SAMPLE_RATE, 0, "NONE", "not compressed"))
            output.writeframes(sample * frames)
        return subprocess.CompletedProcess([], 0)
