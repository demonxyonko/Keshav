import sys
import asyncio
import base64
import json
import math
import os
import queue
import re
import threading
import urllib.error
import urllib.parse
import urllib.request
import time
import wave
from datetime import datetime
from html import escape
from pathlib import Path

import markdown
import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from pygments.formatters import HtmlFormatter
from websockets.asyncio.client import connect

from PySide6.QtCore import (
    Qt,
    Signal,
    QTimer,
    QObject,
    QSettings,
    Property,
    QPropertyAnimation,
    QEasingCurve,
    QRectF,
    QBuffer,
    QIODevice,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtMultimedia import (
    QAudioFormat,
    QAudioSource,
    QMediaDevices,
)
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.chat_store import chat_store

from app.chat import (
    ask_keshav,
    clear_conversation,
    delete_conversation,
    get_active_conversation_id,
    list_conversations,
    load_conversation,
    rename_conversation,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PEACOCK_FEATHER_PATH = (
    PROJECT_ROOT
    / "assets"
    / "peacock_feather.png"
)

VOICE_NOTE_DIR = (
    PROJECT_ROOT
    / "data"
    / "voice_notes"
)

WHISPER_MODEL_NAME = "openai/whisper-tiny"
VOICE_SAMPLE_RATE = 16000
MAX_VOICE_SECONDS = 60

CALL_MONITOR_INTERVAL_MS = 120
CALL_SILENCE_TO_SEND_MS = 1000
CALL_MIN_SPEECH_MS = 300
CALL_EMPTY_RESTART_MS = 30000
CALL_MIN_RMS_LEVEL = 0.012

ELEVENLABS_ENV_PATH = PROJECT_ROOT / ".env"
ELEVENLABS_TOKEN_URL = (
    "https://api.elevenlabs.io/v1/"
    "single-use-token/realtime_scribe"
)
ELEVENLABS_SCRIBE_URL = (
    "wss://api.elevenlabs.io/v1/"
    "speech-to-text/realtime"
)
SCRIBE_MODEL_ID = "scribe_v2_realtime"
SCRIBE_SAMPLE_RATE = 16000
SCRIBE_BLOCK_SIZE = 1600
SCRIBE_SILENCE_SECONDS = 0.65
SCRIBE_VAD_THRESHOLD = 0.4
SCRIBE_MIN_SPEECH_MS = 150
SCRIBE_MIN_SILENCE_MS = 120
SCRIBE_KEYTERMS = (
    "Keshav",
    "Ollama",
    "Radhe Radhe",
    "Hinglish",
)

ELEVENLABS_TTS_URL = (
    "https://api.elevenlabs.io/v1/"
    "text-to-speech/{voice_id}/stream"
)
ELEVENLABS_TTS_MODEL = "eleven_flash_v2_5"
ELEVENLABS_TTS_OUTPUT_FORMAT = "pcm_24000"
ELEVENLABS_TTS_SAMPLE_RATE = 24000
ELEVENLABS_TTS_STABILITY = 0.45
ELEVENLABS_TTS_SIMILARITY = 0.80
ELEVENLABS_TTS_SPEED = 1.0

MAX_ATTACHMENT_COUNT = 10
MAX_ATTACHMENT_BYTES = 100 * 1024 * 1024
IMAGE_ATTACHMENT_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".gif",
}
DOCUMENT_ATTACHMENT_SUFFIXES = {
    ".pdf",
    ".txt",
    ".md",
    ".markdown",
    ".docx",
    ".csv",
    ".xlsx",
    ".xlsm",
    ".pptx",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".xml",
    ".html",
    ".htm",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".kts",
    ".sql",
    ".toml",
    ".ini",
    ".cfg",
    ".log",
    ".sh",
    ".bat",
    ".ps1",
}

VIDEO_ATTACHMENT_SUFFIXES = {
    ".mp4",
    ".mov",
    ".mkv",
    ".webm",
    ".avi",
    ".m4v",
}


THEMES = {
    "dark": {
        "window": "#0B1020",
        "sidebar": "#0F172A",
        "panel": "#182235",
        "panel_alt": "#18233A",
        "panel_hover": "#24324F",
        "search": "#111C31",
        "border": "#334155",
        "border_soft": "#2A3853",
        "text": "#F8FAFC",
        "muted": "#94A3B8",
        "list_text": "#E2E8F0",
        "user_bubble": "#4CAF50",
        "user_text": "#FFFFFF",
        "accent": "#4CAF50",
        "accent_hover": "#5DCB61",
        "disabled": "#355E38",
        "disabled_text": "#B8C8BA",
        "selection": "#365B91",
        "code_bg": "#090F1C",
        "inline_code": "#28364D",
        "quote": "#CBD5E1",
        "link": "#7DD3FC",
        "table_header": "#223049",
    },
    "light": {
        "window": "#F4F7FB",
        "sidebar": "#EAF0F8",
        "panel": "#FFFFFF",
        "panel_alt": "#FFFFFF",
        "panel_hover": "#DDE7F3",
        "search": "#FFFFFF",
        "border": "#B8C5D6",
        "border_soft": "#CCD6E3",
        "text": "#172033",
        "muted": "#5E6B7D",
        "list_text": "#263247",
        "user_bubble": "#3FA34D",
        "user_text": "#FFFFFF",
        "accent": "#3FA34D",
        "accent_hover": "#49B85A",
        "disabled": "#A8C7AD",
        "disabled_text": "#EEF5EF",
        "selection": "#A9C7EE",
        "code_bg": "#F1F4F8",
        "inline_code": "#E4EAF2",
        "quote": "#526174",
        "link": "#1769AA",
        "table_header": "#E3EAF3",
    },
}


PYGMENTS_CSS = {
    "dark": HtmlFormatter(
        style="github-dark"
    ).get_style_defs(".codehilite"),

    "light": HtmlFormatter(
        style="default"
    ).get_style_defs(".codehilite"),
}


def get_theme(
    theme_name: str,
) -> dict:
    return THEMES.get(
        theme_name,
        THEMES["dark"],
    )


def build_document_css(
    theme_name: str,
    font_size: int = 15,
) -> str:
    theme = get_theme(theme_name)

    return f"""
    {PYGMENTS_CSS.get(theme_name, PYGMENTS_CSS["dark"])}

    html, body {{
        margin: 0;
        padding: 0;
        background: transparent;
        color: {theme["text"]};
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: {font_size}px;
        line-height: 1.6;
    }}

    body > :first-child {{
        margin-top: 0;
    }}

    body > :last-child {{
        margin-bottom: 0;
    }}

    p {{
        margin: 9px 0;
    }}

    h1, h2, h3, h4 {{
        margin: 14px 0 8px;
        color: {theme["text"]};
        line-height: 1.3;
    }}

    h1 {{
        font-size: 24px;
    }}

    h2 {{
        font-size: 21px;
    }}

    h3 {{
        font-size: 18px;
    }}

    pre {{
        margin: 13px 0;
        padding: 14px;
        background: {theme["code_bg"]};
        border: 1px solid {theme["border"]};
        border-radius: 10px;
        white-space: pre-wrap;
        word-wrap: break-word;
    }}

    code {{
        font-family: Consolas, "Courier New", monospace;
        background: {theme["inline_code"]};
        border-radius: 5px;
        padding: 2px 5px;
    }}

    pre code {{
        background: transparent;
        padding: 0;
    }}

    .codehilite {{
        margin: 13px 0;
        background: {theme["code_bg"]};
        border: 1px solid {theme["border"]};
        border-radius: 10px;
    }}

    .codehilite pre {{
        margin: 0;
        border: none;
    }}

    blockquote {{
        margin: 12px 0;
        padding: 8px 0 8px 13px;
        border-left: 4px solid {theme["accent"]};
        color: {theme["quote"]};
    }}

    table {{
        width: 100%;
        margin: 13px 0;
        border-collapse: collapse;
    }}

    th, td {{
        padding: 8px 9px;
        border: 1px solid {theme["border"]};
        text-align: left;
    }}

    th {{
        background: {theme["table_header"]};
    }}

    a {{
        color: {theme["link"]};
        text-decoration: none;
    }}

    ul, ol {{
        margin: 9px 0;
        padding-left: 25px;
    }}

    li {{
        margin: 4px 0;
    }}

    hr {{
        margin: 15px 0;
        border: none;
        border-top: 1px solid {theme["border"]};
    }}
    """


def wrap_html(
    content: str,
    theme_name: str,
    font_size: int = 15,
) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>{build_document_css(theme_name, font_size)}</style>
    </head>
    <body>{content}</body>
    </html>
    """


def markdown_to_html(
    text: str,
    theme_name: str,
    font_size: int = 15,
) -> str:
    rendered = markdown.markdown(
        text or "",
        extensions=[
            "fenced_code",
            "tables",
            "codehilite",
            "nl2br",
            "sane_lists",
        ],
    )

    return wrap_html(
        rendered,
        theme_name,
        font_size,
    )


def plain_text_to_html(
    text: str,
    theme_name: str,
    font_size: int = 15,
) -> str:
    safe_text = escape(
        text or ""
    ).replace(
        "\n",
        "<br>",
    )

    return wrap_html(
        f"<p>{safe_text}</p>",
        theme_name,
        font_size,
    )


def markdown_to_speech_text(text: str) -> str:
    """
    Convert an assistant Markdown reply into cleaner spoken text.

    Code blocks and raw URLs are skipped so Keshav does not read
    formatting symbols or long code aloud.
    """
    spoken = text or ""

    spoken = re.sub(
        r"```.*?(?:```|$)",
        " Code block omitted. ",
        spoken,
        flags=re.DOTALL,
    )
    spoken = re.sub(
        r"`([^`]+)`",
        r"\1",
        spoken,
    )
    spoken = re.sub(
        r"!\[([^\]]*)\]\([^)]+\)",
        r"\1",
        spoken,
    )
    spoken = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        spoken,
    )
    spoken = re.sub(
        r"https?://\S+",
        " ",
        spoken,
    )
    spoken = re.sub(
        r"^\s{0,3}#{1,6}\s*",
        "",
        spoken,
        flags=re.MULTILINE,
    )
    spoken = re.sub(
        r"^\s*[-*+]\s+",
        "",
        spoken,
        flags=re.MULTILINE,
    )
    spoken = re.sub(
        r"^\s*\d+[.)]\s+",
        "",
        spoken,
        flags=re.MULTILINE,
    )
    spoken = re.sub(
        r"[*_~>|]",
        " ",
        spoken,
    )
    spoken = re.sub(
        r"\s+",
        " ",
        spoken,
    ).strip()

    if len(spoken) > 5000:
        spoken = (
            spoken[:5000].rsplit(" ", 1)[0]
            + ". The rest of the response is visible on screen."
        )

    return spoken


class SpeechEvents(QObject):
    speaking_changed = Signal(bool)
    error = Signal(str)


class ElevenLabsSpeechWorker:
    """
    Low-latency ElevenLabs voice output.

    Normal text replies use the HTTP streaming endpoint. Live Mode
    uses one Text-to-Speech WebSocket, allowing Ollama's hidden text
    stream to become audio before the full reply is complete.
    """

    def __init__(self) -> None:
        self.events = SpeechEvents()

        self._commands: queue.Queue[
            tuple[str, str | None]
        ] = queue.Queue()

        self._stop_requested = threading.Event()
        self._shutdown_requested = threading.Event()
        self._active = threading.Event()

        self._response_lock = threading.Lock()
        self._current_response = None

        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="KeshavElevenLabsSpeechWorker",
        )
        self._thread.start()

    def speak(self, text: str) -> None:
        clean_text = text.strip()

        if not clean_text:
            return

        self.stop()
        self._commands.put(
            ("speak", clean_text)
        )

    def begin_stream(self) -> None:
        self.stop()
        self._commands.put(
            ("begin_stream", None)
        )

    def enqueue_stream(
        self,
        text: str,
    ) -> None:
        clean_text = text

        if not clean_text:
            return

        self._commands.put(
            ("stream_chunk", clean_text)
        )

    def finish_stream(self) -> None:
        self._commands.put(
            ("stream_end", None)
        )

    def has_pending(self) -> bool:
        return (
            self._active.is_set()
            or not self._commands.empty()
        )

    def stop(self) -> None:
        self._stop_requested.set()

        try:
            while True:
                self._commands.get_nowait()
        except queue.Empty:
            pass

        self._commands.put(
            ("stop", None)
        )

        with self._response_lock:
            response = self._current_response

        if response is not None:
            try:
                response.close()
            except Exception:
                pass

    def shutdown(self) -> None:
        self._shutdown_requested.set()
        self.stop()
        self._commands.put(
            ("shutdown", None)
        )
        self._thread.join(timeout=2.0)

    @staticmethod
    def _load_credentials() -> tuple[str, str]:
        load_dotenv(
            dotenv_path=ELEVENLABS_ENV_PATH,
            override=True,
        )

        api_key = os.getenv(
            "ELEVENLABS_API_KEY",
            "",
        ).strip()
        voice_id = os.getenv(
            "ELEVENLABS_VOICE_ID",
            "",
        ).strip()

        if not api_key:
            raise RuntimeError(
                "ELEVENLABS_API_KEY is missing from "
                "the project .env file."
            )

        if not voice_id:
            raise RuntimeError(
                "ELEVENLABS_VOICE_ID is missing from "
                "the project .env file."
            )

        return api_key, voice_id

    def _open_audio_response(
        self,
        text: str,
    ):
        api_key, voice_id = (
            self._load_credentials()
        )

        encoded_voice_id = urllib.parse.quote(
            voice_id,
            safe="",
        )

        endpoint = (
            ELEVENLABS_TTS_URL.format(
                voice_id=encoded_voice_id
            )
            + "?"
            + urllib.parse.urlencode(
                {
                    "output_format": (
                        ELEVENLABS_TTS_OUTPUT_FORMAT
                    ),
                    "optimize_streaming_latency": 3,
                }
            )
        )

        request_body = json.dumps(
            {
                "text": text,
                "model_id": ELEVENLABS_TTS_MODEL,
                "voice_settings": {
                    "stability": (
                        ELEVENLABS_TTS_STABILITY
                    ),
                    "similarity_boost": (
                        ELEVENLABS_TTS_SIMILARITY
                    ),
                    "style": 0.0,
                    "use_speaker_boost": True,
                    "speed": (
                        ELEVENLABS_TTS_SPEED
                    ),
                },
            }
        ).encode("utf-8")

        request = urllib.request.Request(
            endpoint,
            data=request_body,
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "audio/pcm",
            },
            method="POST",
        )

        try:
            return urllib.request.urlopen(
                request,
                timeout=60,
            )

        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode(
                    "utf-8",
                    errors="replace",
                ).strip()
            except Exception:
                detail = ""

            raise RuntimeError(
                "ElevenLabs voice request failed"
                + (
                    f": {detail}"
                    if detail
                    else f" with HTTP {exc.code}."
                )
            ) from exc

        except urllib.error.URLError as exc:
            raise RuntimeError(
                "Could not connect to ElevenLabs "
                "for voice output."
            ) from exc

    @staticmethod
    def _write_pcm_chunk(
        output_stream,
        raw_audio: bytes,
        pending_byte: bytes,
    ) -> bytes:
        audio_data = pending_byte + raw_audio
        usable_length = (
            len(audio_data)
            - len(audio_data) % 2
        )

        if usable_length:
            output_stream.write(
                audio_data[:usable_length]
            )

        return audio_data[usable_length:]

    def _stream_and_play_http(
        self,
        text: str,
    ) -> None:
        response = self._open_audio_response(
            text
        )

        with self._response_lock:
            self._current_response = response

        pending_byte = b""

        try:
            with sd.RawOutputStream(
                samplerate=(
                    ELEVENLABS_TTS_SAMPLE_RATE
                ),
                channels=1,
                dtype="int16",
                blocksize=0,
                latency="low",
            ) as output_stream:
                while not (
                    self._stop_requested.is_set()
                    or self._shutdown_requested.is_set()
                ):
                    audio_chunk = response.read(
                        4096
                    )

                    if not audio_chunk:
                        break

                    pending_byte = (
                        self._write_pcm_chunk(
                            output_stream,
                            audio_chunk,
                            pending_byte,
                        )
                    )

        except Exception:
            if (
                self._stop_requested.is_set()
                or self._shutdown_requested.is_set()
            ):
                return

            raise

        finally:
            try:
                response.close()
            except Exception:
                pass

            with self._response_lock:
                if self._current_response is response:
                    self._current_response = None

    async def _run_live_websocket(
        self,
    ) -> None:
        api_key, voice_id = (
            self._load_credentials()
        )

        encoded_voice_id = urllib.parse.quote(
            voice_id,
            safe="",
        )

        websocket_url = (
            "wss://api.elevenlabs.io/v1/"
            f"text-to-speech/{encoded_voice_id}/"
            "stream-input?"
            + urllib.parse.urlencode(
                {
                    "model_id": ELEVENLABS_TTS_MODEL,
                    "output_format": (
                        ELEVENLABS_TTS_OUTPUT_FORMAT
                    ),
                    "auto_mode": "true",
                    "inactivity_timeout": 60,
                }
            )
        )

        pending_byte = b""

        async with connect(
            websocket_url,
            additional_headers={
                "xi-api-key": api_key,
            },
            max_size=None,
            ping_interval=20,
            close_timeout=2,
        ) as websocket:
            await websocket.send(
                json.dumps(
                    {
                        "text": " ",
                        "voice_settings": {
                            "stability": (
                                ELEVENLABS_TTS_STABILITY
                            ),
                            "similarity_boost": (
                                ELEVENLABS_TTS_SIMILARITY
                            ),
                            "use_speaker_boost": True,
                            "speed": (
                                ELEVENLABS_TTS_SPEED
                            ),
                        },
                    }
                )
            )

            with sd.RawOutputStream(
                samplerate=(
                    ELEVENLABS_TTS_SAMPLE_RATE
                ),
                channels=1,
                dtype="int16",
                blocksize=0,
                latency="low",
            ) as output_stream:

                async def send_text() -> str:
                    while True:
                        command, payload = (
                            await asyncio.to_thread(
                                self._commands.get
                            )
                        )

                        if command in {
                            "stop",
                            "shutdown",
                        }:
                            return command

                        if command == "stream_chunk":
                            clean_text = (
                                payload or ""
                            ).strip()

                            if not clean_text:
                                continue

                            await websocket.send(
                                json.dumps(
                                    {
                                        "text": clean_text + " ",
                                    }
                                )
                            )

                        elif command == "stream_end":
                            await websocket.send(
                                json.dumps(
                                    {
                                        "text": " ",
                                        "flush": True,
                                    }
                                )
                            )
                            await websocket.send(
                                json.dumps(
                                    {
                                        "text": "",
                                    }
                                )
                            )
                            return "finished"

                async def receive_audio() -> None:
                    nonlocal pending_byte

                    async for raw_message in websocket:
                        event = json.loads(
                            raw_message
                        )

                        encoded_audio = event.get(
                            "audio"
                        )

                        if encoded_audio:
                            audio_chunk = (
                                base64.b64decode(
                                    encoded_audio
                                )
                            )

                            pending_byte = (
                                self._write_pcm_chunk(
                                    output_stream,
                                    audio_chunk,
                                    pending_byte,
                                )
                            )

                        if (
                            event.get("isFinal")
                            or event.get("is_final")
                        ):
                            return

                sender_task = asyncio.create_task(
                    send_text()
                )
                receiver_task = asyncio.create_task(
                    receive_audio()
                )

                sender_result = await sender_task

                if sender_result in {
                    "stop",
                    "shutdown",
                }:
                    receiver_task.cancel()
                    await asyncio.gather(
                        receiver_task,
                        return_exceptions=True,
                    )
                    return

                await receiver_task

    def _run(self) -> None:
        try:
            while not self._shutdown_requested.is_set():
                command, payload = (
                    self._commands.get()
                )

                if command == "shutdown":
                    break

                if command == "stop":
                    continue

                if command == "speak" and payload:
                    self._stop_requested.clear()
                    self._active.set()
                    self.events.speaking_changed.emit(
                        True
                    )

                    try:
                        self._stream_and_play_http(
                            payload
                        )
                    finally:
                        self._active.clear()
                        self.events.speaking_changed.emit(
                            False
                        )

                elif command == "begin_stream":
                    self._stop_requested.clear()
                    self._active.set()
                    self.events.speaking_changed.emit(
                        True
                    )

                    try:
                        asyncio.run(
                            self._run_live_websocket()
                        )
                    finally:
                        self._active.clear()
                        self.events.speaking_changed.emit(
                            False
                        )

        except Exception as exc:
            self._active.clear()
            self.events.speaking_changed.emit(
                False
            )
            self.events.error.emit(
                str(exc)
            )

        finally:
            self.stop()




# ==========================================================
# Permanent asyncio worker
# ==========================================================

class AsyncWorker:
    """
    Runs every async AI request on one permanent event loop.
    """

    def __init__(self) -> None:
        self.loop = asyncio.new_event_loop()

        self.thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="KeshavAsyncWorker",
        )

        self.thread.start()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def submit(self, coroutine):
        return asyncio.run_coroutine_threadsafe(
            coroutine,
            self.loop,
        )


# ==========================================================
# Animated PNG peacock-feather background
# ==========================================================

class PeacockFeatherBackground(QWidget):
    """
    Displays assets/peacock_feather.png behind the chat.

    The feather fades and scales into view whenever a chat is
    opened, then remains in the center with a subtle floating
    movement.
    """

    def __init__(
        self,
        image_path: Path,
        theme_name: str = "dark",
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.theme_name = theme_name
        self.image_path = image_path
        self.pixmap = QPixmap(
            str(image_path)
        )

        self._reveal = 1.0
        self._phase = 0.0

        self.setAttribute(
            Qt.WA_TransparentForMouseEvents,
            True,
        )
        self.setAttribute(
            Qt.WA_TranslucentBackground,
            True,
        )
        self.setAutoFillBackground(False)

        self.reveal_animation = QPropertyAnimation(
            self,
            b"reveal",
            self,
        )
        self.reveal_animation.setDuration(1150)
        self.reveal_animation.setStartValue(0.0)
        self.reveal_animation.setEndValue(1.0)
        self.reveal_animation.setEasingCurve(
            QEasingCurve.OutCubic
        )

        self.float_timer = QTimer(self)
        self.float_timer.timeout.connect(
            self._advance_float
        )
        self.float_timer.start(45)

        if self.pixmap.isNull():
            print(
                "Warning: peacock feather image could not "
                f"be loaded from: {image_path}"
            )

    def get_reveal(self) -> float:
        return self._reveal

    def set_reveal(
        self,
        value: float,
    ) -> None:
        self._reveal = max(
            0.0,
            min(1.0, float(value)),
        )
        self.update()

    reveal = Property(
        float,
        get_reveal,
        set_reveal,
    )

    def _advance_float(self) -> None:
        self._phase += 0.035
        self.update()

    def restart_animation(self) -> None:
        self.reveal_animation.stop()
        self.set_reveal(0.0)
        self.reveal_animation.start()

    def set_theme(
        self,
        theme_name: str,
    ) -> None:
        self.theme_name = theme_name
        self.update()

    def paintEvent(self, event) -> None:
        del event

        if (
            self.pixmap.isNull()
            or self.width() < 100
            or self.height() < 100
        ):
            return

        painter = QPainter(self)

        if not painter.isActive():
            return

        try:
            painter.setRenderHint(
                QPainter.SmoothPixmapTransform,
                True,
            )
            painter.setRenderHint(
                QPainter.Antialiasing,
                True,
            )

            reveal = self._reveal

            natural_ratio = (
                self.pixmap.width()
                / max(1, self.pixmap.height())
            )

            target_height = min(
                610.0,
                self.height() * 0.68,
            )
            target_width = (
                target_height * natural_ratio
            )

            maximum_width = self.width() * 0.56

            if target_width > maximum_width:
                target_width = maximum_width
                target_height = (
                    target_width / natural_ratio
                )

            breathing_scale = (
                1.0
                + math.sin(self._phase * 0.72)
                * 0.008
            )
            reveal_scale = (
                0.83 + reveal * 0.17
            )
            final_scale = (
                breathing_scale * reveal_scale
            )

            draw_width = (
                target_width * final_scale
            )
            draw_height = (
                target_height * final_scale
            )

            float_x = (
                math.sin(self._phase * 0.55)
                * 4.0
                * reveal
            )
            float_y = (
                math.sin(self._phase)
                * 6.0
                * reveal
            )

            center_x = (
                self.width() / 2.0
                + float_x
            )
            center_y = (
                self.height() / 2.0
                + float_y
                + (1.0 - reveal) * 45.0
            )

            destination = QRectF(
                center_x - draw_width / 2.0,
                center_y - draw_height / 2.0,
                draw_width,
                draw_height,
            )

            base_opacity = (
                0.22
                if self.theme_name == "dark"
                else 0.14
            )

            painter.setOpacity(
                base_opacity * reveal
            )
            painter.drawPixmap(
                destination,
                self.pixmap,
                QRectF(
                    self.pixmap.rect()
                ),
            )

        finally:
            painter.end()


# ==========================================================
# Animated Live Mode orb
# ==========================================================

class LiveOrb(QWidget):
    """Animated orb for Keshav Live Mode."""

    def __init__(
        self,
        theme_name: str = "dark",
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.theme_name = theme_name
        self.state = "idle"
        self.audio_level = 0.0
        self.phase = 0.0

        self.setMinimumSize(260, 260)
        self.setMaximumSize(360, 360)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.animation_timer = QTimer(self)
        self.animation_timer.setInterval(30)
        self.animation_timer.timeout.connect(
            self._advance_animation
        )
        self.animation_timer.start()

    def set_theme(
        self,
        theme_name: str,
    ) -> None:
        self.theme_name = theme_name
        self.update()

    def set_state(
        self,
        state: str,
    ) -> None:
        self.state = state
        self.update()

    def set_audio_level(
        self,
        level: float,
    ) -> None:
        self.audio_level = max(
            0.0,
            min(1.0, float(level)),
        )
        self.update()

    def _advance_animation(self) -> None:
        self.phase += 0.055

        if self.state != "listening":
            self.audio_level *= 0.90

        self.update()

    def _state_colors(
        self,
    ) -> tuple[QColor, QColor]:
        if self.state == "listening":
            return QColor("#62E6A7"), QColor("#2FA96B")

        if self.state == "thinking":
            return QColor("#A78BFA"), QColor("#6D4DD6")

        if self.state == "speaking":
            return QColor("#67D8FF"), QColor("#267DCE")

        if self.state == "error":
            return QColor("#FF8585"), QColor("#C83C3C")

        return QColor("#8EA6C9"), QColor("#4B607D")

    def paintEvent(self, event) -> None:
        del event

        painter = QPainter(self)

        if not painter.isActive():
            return

        try:
            painter.setRenderHint(
                QPainter.Antialiasing,
                True,
            )

            width = float(self.width())
            height = float(self.height())
            center_x = width / 2.0
            center_y = height / 2.0
            base_radius = min(width, height) * 0.235

            pulse = 1.0 + math.sin(self.phase) * 0.045

            if self.state == "listening":
                pulse += self.audio_level * 0.16
            elif self.state == "thinking":
                pulse += math.sin(self.phase * 1.8) * 0.025
            elif self.state == "speaking":
                pulse += abs(math.sin(self.phase * 1.35)) * 0.08

            radius = base_radius * pulse
            inner_color, outer_color = self._state_colors()
            glow_alpha = 72 if self.theme_name == "dark" else 48

            for multiplier, alpha_scale in (
                (1.95, 0.22),
                (1.62, 0.34),
                (1.34, 0.50),
            ):
                glow_color = QColor(inner_color)
                glow_color.setAlpha(
                    int(glow_alpha * alpha_scale)
                )
                painter.setPen(Qt.NoPen)
                painter.setBrush(glow_color)
                glow_radius = radius * multiplier
                painter.drawEllipse(
                    QRectF(
                        center_x - glow_radius,
                        center_y - glow_radius,
                        glow_radius * 2.0,
                        glow_radius * 2.0,
                    )
                )

            gradient = QRadialGradient(
                center_x - radius * 0.22,
                center_y - radius * 0.28,
                radius * 1.2,
            )
            bright = QColor(inner_color).lighter(128)
            gradient.setColorAt(0.0, bright)
            gradient.setColorAt(0.48, inner_color)
            gradient.setColorAt(1.0, outer_color)

            painter.setBrush(gradient)
            outline = QColor(inner_color)
            outline.setAlpha(190)
            painter.setPen(
                QPen(
                    outline,
                    max(2.0, radius * 0.025),
                )
            )
            painter.drawEllipse(
                QRectF(
                    center_x - radius,
                    center_y - radius,
                    radius * 2.0,
                    radius * 2.0,
                )
            )

            highlight = QColor("#FFFFFF")
            highlight.setAlpha(70)
            painter.setPen(Qt.NoPen)
            painter.setBrush(highlight)
            painter.drawEllipse(
                QRectF(
                    center_x - radius * 0.48,
                    center_y - radius * 0.52,
                    radius * 0.48,
                    radius * 0.26,
                )
            )

        finally:
            painter.end()


# ==========================================================
# Chat bubble
# ==========================================================

class ChatBubble(QFrame):

    BOT_CARD_WIDTH = 760
    BOT_DOCUMENT_WIDTH = 700

    def __init__(
        self,
        text: str = "",
        is_user: bool = False,
        theme_name: str = "dark",
        font_size: int = 15,
    ) -> None:
        super().__init__()

        self.is_user = is_user
        self.theme_name = theme_name
        self.font_size = font_size
        self.raw_text = text
        self.is_streaming = False

        self.setStyleSheet(
            "QFrame { background: transparent; }"
        )

        outer = QHBoxLayout(self)
        outer.setContentsMargins(12, 7, 12, 7)

        if is_user:
            self.label = QLabel()
            self.label.setWordWrap(True)
            self.label.setTextInteractionFlags(
                Qt.TextSelectableByMouse
            )
            self.label.setMaximumWidth(580)

            outer.addStretch()
            outer.addWidget(self.label)

        else:
            self.card = QFrame()
            self.card.setObjectName("assistantCard")
            self.card.setFixedWidth(
                self.BOT_CARD_WIDTH
            )
            self.card.setSizePolicy(
                QSizePolicy.Fixed,
                QSizePolicy.Fixed,
            )

            card_layout = QVBoxLayout(self.card)
            card_layout.setContentsMargins(
                17,
                14,
                17,
                14,
            )
            card_layout.setSpacing(0)

            self.browser = QTextBrowser()
            self.browser.setOpenExternalLinks(True)
            self.browser.setFrameShape(
                QFrame.NoFrame
            )
            self.browser.setVerticalScrollBarPolicy(
                Qt.ScrollBarAlwaysOff
            )
            self.browser.setHorizontalScrollBarPolicy(
                Qt.ScrollBarAlwaysOff
            )
            self.browser.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed,
            )

            self.browser.document().setDocumentMargin(0)
            card_layout.addWidget(self.browser)

            outer.addWidget(self.card)
            outer.addStretch()

        self.apply_theme(
            theme_name,
            font_size=font_size,
            rerender=False,
        )

        if is_user:
            self.set_user_text(text)
        else:
            self.set_markdown(text)

    def apply_theme(
        self,
        theme_name: str,
        font_size: int | None = None,
        rerender: bool = True,
    ) -> None:
        self.theme_name = theme_name

        if font_size is not None:
            self.font_size = font_size
        theme = get_theme(theme_name)

        if self.is_user:
            self.label.setStyleSheet(
                f"""
                QLabel {{
                    background: {theme["user_bubble"]};
                    color: {theme["user_text"]};
                    padding: 13px 16px;
                    border-radius: 18px;
                    font-size: {self.font_size}px;
                }}
                """
            )

        else:
            self.card.setStyleSheet(
                f"""
                QFrame#assistantCard {{
                    background: {theme["panel"]};
                    border: 1px solid {theme["border_soft"]};
                    border-radius: 18px;
                }}
                """
            )

            self.browser.setStyleSheet(
                f"""
                QTextBrowser {{
                    background: transparent;
                    border: none;
                    color: {theme["text"]};
                    padding: 0;
                    selection-background-color: {theme["selection"]};
                }}
                """
            )

        if not rerender:
            return

        if self.is_user:
            self.label.setText(
                self.raw_text
            )

        elif self.is_streaming:
            self.browser.setHtml(
                plain_text_to_html(
                    self.raw_text,
                    self.theme_name,
                    self.font_size,
                )
            )
            self._schedule_resize()

        else:
            self.browser.setHtml(
                markdown_to_html(
                    self.raw_text,
                    self.theme_name,
                    self.font_size,
                )
            )
            self._schedule_resize()

    def set_user_text(
        self,
        text: str,
    ) -> None:
        self.raw_text = text

        if self.is_user:
            self.label.setText(text)

    def set_stream_text(
        self,
        text: str,
    ) -> None:
        self.raw_text = text
        self.is_streaming = True

        if self.is_user:
            self.label.setText(text)
            return

        self.browser.setHtml(
            plain_text_to_html(
                text,
                self.theme_name,
                self.font_size,
            )
        )
        self._schedule_resize()

    def set_markdown(
        self,
        text: str,
    ) -> None:
        self.raw_text = text
        self.is_streaming = False

        if self.is_user:
            self.label.setText(text)
            return

        self.browser.setHtml(
            markdown_to_html(
                text,
                self.theme_name,
                self.font_size,
            )
        )
        self._schedule_resize()

    def _schedule_resize(self) -> None:
        QTimer.singleShot(
            0,
            self._resize_to_document,
        )

    def _resize_to_document(self) -> None:
        document = self.browser.document()
        document.setTextWidth(
            self.BOT_DOCUMENT_WIDTH
        )
        document.adjustSize()

        browser_height = max(
            30,
            int(document.size().height()) + 4,
        )

        self.browser.setFixedHeight(
            browser_height
        )

        card_height = browser_height + 28

        self.card.setFixedHeight(
            card_height
        )

        self.setFixedHeight(
            card_height + 14
        )


# ==========================================================
# Settings dialog
# ==========================================================

class SettingsDialog(QDialog):

    def __init__(
        self,
        theme_name: str,
        font_size: int,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("Keshav Settings")
        self.setModal(True)
        self.setMinimumWidth(390)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        heading = QLabel("⚙  Settings")
        heading.setFont(
            QFont(
                "Segoe UI",
                17,
                QFont.Bold,
            )
        )
        layout.addWidget(heading)

        form = QFormLayout()
        form.setSpacing(12)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Dark", "dark")
        self.theme_combo.addItem("Light", "light")

        theme_index = self.theme_combo.findData(
            theme_name
        )
        self.theme_combo.setCurrentIndex(
            max(0, theme_index)
        )

        self.font_spin = QSpinBox()
        self.font_spin.setRange(12, 22)
        self.font_spin.setValue(font_size)
        self.font_spin.setSuffix(" px")

        form.addRow("Theme:", self.theme_combo)
        form.addRow(
            "Chat font size:",
            self.font_spin,
        )

        layout.addLayout(form)

        note = QLabel(
            "Press Save to keep appearance changes."
        )
        note.setWordWrap(True)
        note.setObjectName("settingsNote")
        layout.addWidget(note)

        self.new_chat_button = QPushButton(
            "Start a Fresh Chat"
        )
        self.new_chat_button.setObjectName(
            "settingsSecondaryButton"
        )
        layout.addWidget(self.new_chat_button)

        self.delete_all_button = QPushButton(
            "Delete All Saved Chats"
        )
        self.delete_all_button.setObjectName(
            "dangerButton"
        )
        layout.addWidget(self.delete_all_button)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_theme(self) -> str:
        return str(
            self.theme_combo.currentData()
        )

    def selected_font_size(self) -> int:
        return int(
            self.font_spin.value()
        )


# ==========================================================
# Local voice-note transcription
# ==========================================================

class ElevenLabsRealtimeScribe:
    """
    Realtime Hinglish-friendly transcription through ElevenLabs
    Scribe v2 Realtime.

    The permanent API key remains in the local .env file. A short-lived
    single-use token is requested for every microphone session.
    """

    @staticmethod
    def get_single_use_token() -> str:
        load_dotenv(
            dotenv_path=ELEVENLABS_ENV_PATH
        )

        api_key = os.getenv(
            "ELEVENLABS_API_KEY",
            "",
        ).strip()

        if not api_key:
            raise RuntimeError(
                "ELEVENLABS_API_KEY is missing from the "
                "project .env file."
            )

        request = urllib.request.Request(
            ELEVENLABS_TOKEN_URL,
            headers={
                "xi-api-key": api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=20,
            ) as response:
                data = json.load(response)

        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode(
                    "utf-8",
                    errors="replace",
                ).strip()
            except Exception:
                detail = ""

            raise RuntimeError(
                "ElevenLabs authentication failed"
                + (
                    f": {detail}"
                    if detail
                    else f" with HTTP {exc.code}."
                )
            ) from exc

        except urllib.error.URLError as exc:
            raise RuntimeError(
                "Could not connect to ElevenLabs. "
                "Check the internet connection."
            ) from exc

        token = str(
            data.get("token", "")
        ).strip()

        if not token:
            raise RuntimeError(
                "ElevenLabs did not return a realtime "
                "speech token."
            )

        return token

    @staticmethod
    def build_websocket_url(
        token: str,
    ) -> str:
        query_items = [
            (
                "model_id",
                SCRIBE_MODEL_ID,
            ),
            (
                "token",
                token,
            ),
            (
                "audio_format",
                "pcm_16000",
            ),
            (
                "commit_strategy",
                "vad",
            ),
            (
                "vad_silence_threshold_secs",
                str(SCRIBE_SILENCE_SECONDS),
            ),
            (
                "vad_threshold",
                str(SCRIBE_VAD_THRESHOLD),
            ),
            (
                "min_speech_duration_ms",
                str(SCRIBE_MIN_SPEECH_MS),
            ),
            (
                "min_silence_duration_ms",
                str(SCRIBE_MIN_SILENCE_MS),
            ),
            (
                "include_language_detection",
                "true",
            ),
        ]

        query_items.extend(
            (
                "keyterms",
                keyterm,
            )
            for keyterm in SCRIBE_KEYTERMS
        )

        return (
            ELEVENLABS_SCRIBE_URL
            + "?"
            + urllib.parse.urlencode(
                query_items
            )
        )

def pcm_rms_level(
    raw_data: bytes,
    audio_format: QAudioFormat,
) -> float:
    """Return a normalized RMS level for a small PCM chunk."""

    if not raw_data:
        return 0.0

    sample_format = audio_format.sampleFormat()

    try:
        if sample_format == QAudioFormat.SampleFormat.Int16:
            audio = np.frombuffer(
                raw_data,
                dtype=np.int16,
            ).astype(np.float32) / 32768.0

        elif sample_format == QAudioFormat.SampleFormat.Int32:
            audio = np.frombuffer(
                raw_data,
                dtype=np.int32,
            ).astype(np.float32) / 2147483648.0

        elif sample_format == QAudioFormat.SampleFormat.UInt8:
            audio = (
                np.frombuffer(
                    raw_data,
                    dtype=np.uint8,
                ).astype(np.float32)
                - 128.0
            ) / 128.0

        elif sample_format == QAudioFormat.SampleFormat.Float:
            audio = np.frombuffer(
                raw_data,
                dtype=np.float32,
            ).astype(np.float32)

        else:
            return 0.0

    except ValueError:
        return 0.0

    if audio.size == 0:
        return 0.0

    channel_count = max(
        1,
        audio_format.channelCount(),
    )

    usable_length = (
        audio.size
        - audio.size % channel_count
    )

    if usable_length <= 0:
        return 0.0

    audio = audio[:usable_length]

    if channel_count > 1:
        audio = audio.reshape(
            -1,
            channel_count,
        ).mean(axis=1)

    return float(
        np.sqrt(
            np.mean(
                np.square(audio)
            )
        )
    )


def pcm_to_float32(
    raw_data: bytes,
    audio_format: QAudioFormat,
) -> np.ndarray:
    """Convert Qt raw PCM audio to mono 16 kHz float32."""

    sample_format = audio_format.sampleFormat()

    if sample_format == QAudioFormat.SampleFormat.Int16:
        audio = np.frombuffer(
            raw_data,
            dtype=np.int16,
        ).astype(np.float32) / 32768.0

    elif sample_format == QAudioFormat.SampleFormat.Int32:
        audio = np.frombuffer(
            raw_data,
            dtype=np.int32,
        ).astype(np.float32) / 2147483648.0

    elif sample_format == QAudioFormat.SampleFormat.UInt8:
        audio = (
            np.frombuffer(
                raw_data,
                dtype=np.uint8,
            ).astype(np.float32)
            - 128.0
        ) / 128.0

    elif sample_format == QAudioFormat.SampleFormat.Float:
        audio = np.frombuffer(
            raw_data,
            dtype=np.float32,
        ).astype(np.float32)

    else:
        raise RuntimeError(
            "The microphone returned an unsupported "
            "audio sample format."
        )

    channel_count = max(
        1,
        audio_format.channelCount(),
    )

    usable_length = (
        audio.size
        - audio.size % channel_count
    )
    audio = audio[:usable_length]

    if channel_count > 1:
        audio = audio.reshape(
            -1,
            channel_count,
        ).mean(axis=1)

    source_rate = max(
        1,
        audio_format.sampleRate(),
    )

    if (
        source_rate != VOICE_SAMPLE_RATE
        and audio.size > 1
    ):
        target_length = max(
            1,
            int(
                audio.size
                * VOICE_SAMPLE_RATE
                / source_rate
            ),
        )

        old_positions = np.arange(
            audio.size,
            dtype=np.float64,
        )
        new_positions = np.linspace(
            0,
            audio.size - 1,
            target_length,
            dtype=np.float64,
        )

        audio = np.interp(
            new_positions,
            old_positions,
            audio,
        ).astype(np.float32)

    return np.clip(
        audio,
        -1.0,
        1.0,
    ).astype(np.float32)


def save_voice_note_wav(
    audio: np.ndarray,
) -> Path:
    VOICE_NOTE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_name = (
        "voice_note_"
        + datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )
        + ".wav"
    )
    output_path = VOICE_NOTE_DIR / file_name

    pcm = (
        np.clip(audio, -1.0, 1.0)
        * 32767.0
    ).astype(np.int16)

    with wave.open(
        str(output_path),
        "wb",
    ) as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(
            VOICE_SAMPLE_RATE
        )
        wav_file.writeframes(
            pcm.tobytes()
        )

    return output_path


# ==========================================================
# Attachment UI helpers
# ==========================================================

def format_file_size(size_bytes: int) -> str:
    size = float(max(0, size_bytes))

    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0 or unit == "GB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024.0

    return f"{size:.1f} GB"


def attachment_type_icon(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix in IMAGE_ATTACHMENT_SUFFIXES:
        return "🖼"

    if suffix in VIDEO_ATTACHMENT_SUFFIXES:
        return "🎞"

    if suffix == ".pdf":
        return "📕"

    if suffix in {".doc", ".docx", ".odt", ".rtf"}:
        return "📝"

    if suffix in {
        ".xls",
        ".xlsx",
        ".xlsm",
        ".csv",
    }:
        return "📊"

    if suffix in {".ppt", ".pptx"}:
        return "📽"

    if suffix in {".zip", ".rar", ".7z"}:
        return "🗜"

    return "📄"


class AttachmentChip(QFrame):
    remove_requested = Signal(str)

    def __init__(
        self,
        file_path: Path,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.file_path = Path(file_path)
        self.setObjectName("attachmentChip")
        self.setToolTip(str(self.file_path))
        self.setMaximumWidth(300)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 6, 6)
        layout.setSpacing(8)

        self.preview = QLabel()
        self.preview.setObjectName(
            "attachmentPreview"
        )
        self.preview.setFixedSize(40, 40)
        self.preview.setAlignment(Qt.AlignCenter)

        suffix = self.file_path.suffix.lower()

        if suffix in IMAGE_ATTACHMENT_SUFFIXES:
            pixmap = QPixmap(str(self.file_path))

            if not pixmap.isNull():
                self.preview.setPixmap(
                    pixmap.scaled(
                        38,
                        38,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
            else:
                self.preview.setText(
                    attachment_type_icon(
                        self.file_path
                    )
                )
        else:
            self.preview.setText(
                attachment_type_icon(
                    self.file_path
                )
            )

        layout.addWidget(self.preview)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(1)

        self.name_label = QLabel(
            self.file_path.name
        )
        self.name_label.setObjectName(
            "attachmentName"
        )
        self.name_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )
        self.name_label.setMaximumWidth(190)

        try:
            file_size = format_file_size(
                self.file_path.stat().st_size
            )
        except OSError:
            file_size = "Unknown size"

        self.meta_label = QLabel(file_size)
        self.meta_label.setObjectName(
            "attachmentMeta"
        )

        text_layout.addWidget(
            self.name_label
        )
        text_layout.addWidget(
            self.meta_label
        )
        layout.addLayout(text_layout)

        self.remove_btn = QPushButton("×")
        self.remove_btn.setObjectName(
            "attachmentRemove"
        )
        self.remove_btn.setFixedSize(28, 28)
        self.remove_btn.setToolTip(
            f"Remove {self.file_path.name}"
        )
        self.remove_btn.clicked.connect(
            lambda: self.remove_requested.emit(
                str(self.file_path)
            )
        )
        layout.addWidget(self.remove_btn)


# ==========================================================
# Main window
# ==========================================================

class KeshavWindow(QWidget):

    reply_signal = Signal(str)
    stream_chunk_signal = Signal(str)
    voice_partial_signal = Signal(str)
    voice_transcription_signal = Signal(str)
    voice_error_signal = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("🦚 Keshav")
        self.resize(1280, 820)

        self.current_conversation_id = (
            get_active_conversation_id()
        )

        self.current_bot_bubble: ChatBubble | None = None
        self.full_reply = ""
        self.current_index = 0

        self.streamed_reply = ""
        self.stream_speech_buffer = ""
        self.live_tts_buffer = ""
        self.stream_received_chunk = False
        self.stream_voice_started = False

        self.async_worker = AsyncWorker()
        self.current_future = None

        self.audio_source = None
        self.voice_buffer = None
        self.voice_format = None
        self.is_recording = False
        self.is_transcribing = False
        self.voice_seconds = 0

        self.recording_for_call = False
        self.transcription_for_call = False
        self.call_mode_enabled = False
        self.call_auto_sending = False
        self.call_waiting_for_speech_end = False
        self.call_last_buffer_size = 0
        self.call_elapsed_ms = 0
        self.call_speech_ms = 0
        self.call_silence_ms = 0
        self.call_speech_detected = False
        self.call_noise_floor = 0.003

        self.normal_input_placeholder = (
            "Message Keshav..."
        )

        self.pending_attachments: list[Path] = []
        self.setAcceptDrops(True)

        self.voice_timer = QTimer(self)
        self.voice_timer.timeout.connect(
            self._update_recording_time
        )

        self.call_monitor_timer = QTimer(self)
        self.call_monitor_timer.setInterval(
            CALL_MONITOR_INTERVAL_MS
        )
        self.call_monitor_timer.timeout.connect(
            self._monitor_call_audio
        )

        self.typing_timer = QTimer(self)
        self.typing_timer.timeout.connect(
            self.type_next_chunk
        )

        self.settings = QSettings(
            "Keshav",
            "Keshav Desktop",
        )

        self.theme_name = self.settings.value(
            "appearance/theme",
            "dark",
            type=str,
        )

        if self.theme_name not in THEMES:
            self.theme_name = "dark"

        self.font_size = self.settings.value(
            "appearance/font_size",
            15,
            type=int,
        )

        self.font_size = max(
            12,
            min(22, self.font_size),
        )

        self.voice_output_enabled = self.settings.value(
            "voice/output_enabled",
            False,
            type=bool,
        )
        self.voice_rate = self.settings.value(
            "voice/rate",
            165,
            type=int,
        )
        self.voice_name = self.settings.value(
            "voice/name",
            "Microsoft David Desktop",
            type=str,
        )
        self.is_speaking = False
        self.speech_worker: ElevenLabsSpeechWorker | None = None

        self.scribe_generation = 0
        self.scribe_future = None
        self.voice_partial_text = ""
        self.voice_input_prefix = ""

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        root_layout.setSpacing(0)

        # ==================================================
        # Sidebar
        # ==================================================

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(260)

        sidebar_layout = QVBoxLayout(
            self.sidebar
        )
        sidebar_layout.setContentsMargins(
            14,
            16,
            14,
            16,
        )
        sidebar_layout.setSpacing(10)

        self.new_chat_btn = QPushButton(
            "+ New Chat"
        )
        self.new_chat_btn.setObjectName(
            "newChatButton"
        )
        sidebar_layout.addWidget(
            self.new_chat_btn
        )

        sidebar_title = QLabel("Chats")
        sidebar_title.setObjectName(
            "sidebarTitle"
        )
        sidebar_layout.addWidget(
            sidebar_title
        )

        self.chat_search = QLineEdit()
        self.chat_search.setObjectName(
            "chatSearch"
        )
        self.chat_search.setPlaceholderText(
            "Search chats..."
        )
        self.chat_search.setClearButtonEnabled(True)
        sidebar_layout.addWidget(
            self.chat_search
        )

        self.conversation_list = QListWidget()
        self.conversation_list.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.conversation_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.conversation_list.setContextMenuPolicy(
            Qt.CustomContextMenu
        )
        sidebar_layout.addWidget(
            self.conversation_list
        )

        self.settings_btn = QPushButton(
            "⚙  Settings"
        )
        self.settings_btn.setObjectName(
            "settingsButton"
        )
        sidebar_layout.addWidget(
            self.settings_btn
        )

        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName(
            "themeButton"
        )
        sidebar_layout.addWidget(
            self.theme_btn
        )

        root_layout.addWidget(
            self.sidebar
        )

        # ==================================================
        # Main content
        # ==================================================

        self.main_panel = QWidget()
        main_layout = QVBoxLayout(
            self.main_panel
        )
        main_layout.setContentsMargins(
            18,
            16,
            18,
            18,
        )
        main_layout.setSpacing(12)

        self.title_label = QLabel("🦚 Keshav")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(
            QFont(
                "Segoe UI",
                22,
                QFont.Bold,
            )
        )
        main_layout.addWidget(
            self.title_label
        )

        self.chat_stage = QWidget()
        self.chat_stage.setObjectName(
            "chatStage"
        )

        chat_stage_layout = QGridLayout(
            self.chat_stage
        )
        chat_stage_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        chat_stage_layout.setSpacing(0)

        self.feather_background = (
            PeacockFeatherBackground(
                image_path=PEACOCK_FEATHER_PATH,
                theme_name=self.theme_name,
            )
        )
        chat_stage_layout.addWidget(
            self.feather_background,
            0,
            0,
        )

        self.scroll = QScrollArea()
        self.scroll.setObjectName(
            "chatScroll"
        )
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(
            QFrame.NoFrame
        )
        self.scroll.setAutoFillBackground(False)

        self.scroll.viewport().setAutoFillBackground(
            False
        )
        self.scroll.viewport().setAttribute(
            Qt.WA_TranslucentBackground,
            True,
        )

        self.chat_widget = QWidget()
        self.chat_widget.setObjectName(
            "chatContent"
        )
        self.chat_widget.setAutoFillBackground(False)
        self.chat_widget.setAttribute(
            Qt.WA_TranslucentBackground,
            True,
        )

        self.chat_layout = QVBoxLayout(
            self.chat_widget
        )
        self.chat_layout.setAlignment(
            Qt.AlignTop
        )
        self.chat_layout.setSpacing(4)
        self.chat_layout.setContentsMargins(
            6,
            6,
            6,
            6,
        )

        self.scroll.setWidget(
            self.chat_widget
        )
        chat_stage_layout.addWidget(
            self.scroll,
            0,
            0,
        )

        self.feather_background.lower()
        self.scroll.raise_()

        self.live_overlay = QFrame()
        self.live_overlay.setObjectName(
            "liveOverlay"
        )
        self.live_overlay.setVisible(False)

        live_layout = QVBoxLayout(
            self.live_overlay
        )
        live_layout.setContentsMargins(
            40,
            34,
            40,
            34,
        )
        live_layout.setSpacing(12)
        live_layout.setAlignment(
            Qt.AlignCenter
        )

        self.live_brand_label = QLabel(
            "🦚  Keshav Live"
        )
        self.live_brand_label.setObjectName(
            "liveBrand"
        )
        self.live_brand_label.setAlignment(
            Qt.AlignCenter
        )
        live_layout.addWidget(
            self.live_brand_label
        )

        live_layout.addStretch(1)

        self.live_orb = LiveOrb(
            theme_name=self.theme_name,
            parent=self.live_overlay,
        )
        orb_row = QHBoxLayout()
        orb_row.addStretch()
        orb_row.addWidget(self.live_orb)
        orb_row.addStretch()
        live_layout.addLayout(orb_row)

        self.live_status_label = QLabel("Ready")
        self.live_status_label.setObjectName(
            "liveStatus"
        )
        self.live_status_label.setAlignment(
            Qt.AlignCenter
        )
        live_layout.addWidget(
            self.live_status_label
        )

        self.live_detail_label = QLabel(
            "Start speaking naturally"
        )
        self.live_detail_label.setObjectName(
            "liveDetail"
        )
        self.live_detail_label.setAlignment(
            Qt.AlignCenter
        )
        self.live_detail_label.setWordWrap(True)
        live_layout.addWidget(
            self.live_detail_label
        )

        self.live_user_preview = QLabel("")
        self.live_user_preview.setObjectName(
            "liveUserPreview"
        )
        self.live_user_preview.setAlignment(
            Qt.AlignCenter
        )
        self.live_user_preview.setWordWrap(True)
        self.live_user_preview.setMaximumWidth(760)
        self.live_user_preview.setVisible(False)

        user_preview_row = QHBoxLayout()
        user_preview_row.addStretch()
        user_preview_row.addWidget(
            self.live_user_preview
        )
        user_preview_row.addStretch()
        live_layout.addLayout(user_preview_row)

        self.live_assistant_preview = QLabel("")
        self.live_assistant_preview.setObjectName(
            "liveAssistantPreview"
        )
        self.live_assistant_preview.setAlignment(
            Qt.AlignCenter
        )
        self.live_assistant_preview.setWordWrap(True)
        self.live_assistant_preview.setMaximumWidth(820)
        self.live_assistant_preview.setVisible(False)

        assistant_preview_row = QHBoxLayout()
        assistant_preview_row.addStretch()
        assistant_preview_row.addWidget(
            self.live_assistant_preview
        )
        assistant_preview_row.addStretch()
        live_layout.addLayout(
            assistant_preview_row
        )

        live_layout.addStretch(1)

        self.live_end_btn = QPushButton(
            "End Live"
        )
        self.live_end_btn.setObjectName(
            "endLiveButton"
        )
        self.live_end_btn.setFixedWidth(150)

        end_row = QHBoxLayout()
        end_row.addStretch()
        end_row.addWidget(self.live_end_btn)
        end_row.addStretch()
        live_layout.addLayout(end_row)

        chat_stage_layout.addWidget(
            self.live_overlay,
            0,
            0,
        )
        self.live_overlay.raise_()

        main_layout.addWidget(
            self.chat_stage
        )

        self._auto_scroll_passes = 0

        self.auto_scroll_timer = QTimer(self)
        self.auto_scroll_timer.setSingleShot(True)
        self.auto_scroll_timer.timeout.connect(
            self._perform_auto_scroll
        )

        self.scroll.verticalScrollBar().rangeChanged.connect(
            self._on_scroll_range_changed
        )

        # Selected attachment preview bar.
        self.attachment_bar = QFrame()
        self.attachment_bar.setObjectName(
            "attachmentBar"
        )
        self.attachment_bar.setVisible(False)

        attachment_bar_layout = QVBoxLayout(
            self.attachment_bar
        )
        attachment_bar_layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )
        attachment_bar_layout.setSpacing(6)

        attachment_header = QHBoxLayout()
        attachment_header.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.attachment_hint = QLabel(
            "Attachments ready for analysis"
        )
        self.attachment_hint.setObjectName(
            "attachmentHint"
        )
        attachment_header.addWidget(
            self.attachment_hint
        )
        attachment_header.addStretch()

        self.clear_attachments_btn = QPushButton(
            "Clear all"
        )
        self.clear_attachments_btn.setObjectName(
            "clearAttachmentsButton"
        )
        attachment_header.addWidget(
            self.clear_attachments_btn
        )
        attachment_bar_layout.addLayout(
            attachment_header
        )

        self.attachment_scroll = QScrollArea()
        self.attachment_scroll.setObjectName(
            "attachmentScroll"
        )
        self.attachment_scroll.setWidgetResizable(True)
        self.attachment_scroll.setFrameShape(
            QFrame.NoFrame
        )
        self.attachment_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.attachment_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self.attachment_scroll.setFixedHeight(64)

        self.attachment_content = QWidget()
        self.attachment_content.setObjectName(
            "attachmentContent"
        )

        self.attachment_layout = QHBoxLayout(
            self.attachment_content
        )
        self.attachment_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self.attachment_layout.setSpacing(8)
        self.attachment_layout.setAlignment(
            Qt.AlignLeft
        )

        self.attachment_scroll.setWidget(
            self.attachment_content
        )
        attachment_bar_layout.addWidget(
            self.attachment_scroll
        )
        main_layout.addWidget(
            self.attachment_bar
        )

        self.bottom_bar = QFrame()
        self.bottom_bar.setObjectName(
            "bottomBar"
        )

        bottom_layout = QHBoxLayout(
            self.bottom_bar
        )
        bottom_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        bottom_layout.setSpacing(10)

        self.attach_btn = QPushButton("📎")
        self.attach_btn.setObjectName(
            "attachButton"
        )
        self.attach_btn.setFixedWidth(58)
        self.attach_btn.setToolTip(
            "Attach images, documents, Excel/CSV, PowerPoint, or code files"
        )
        self.attach_btn.setAccessibleName(
            "Attach files"
        )

        self.mic_btn = QPushButton("🎙")
        self.mic_btn.setObjectName(
            "voiceButton"
        )
        self.mic_btn.setFixedWidth(58)
        self.mic_btn.setToolTip(
            "Record a voice note"
        )
        self.mic_btn.setAccessibleName(
            "Record voice note"
        )

        self.voice_output_btn = QPushButton()
        self.voice_output_btn.setObjectName(
            "voiceOutputButton"
        )
        self.voice_output_btn.setCheckable(True)
        self.voice_output_btn.setChecked(
            self.voice_output_enabled
        )
        self.voice_output_btn.setFixedWidth(58)
        self.voice_output_btn.setAccessibleName(
            "Toggle spoken replies"
        )

        self.stop_speaking_btn = QPushButton("■")
        self.stop_speaking_btn.setObjectName(
            "stopSpeakingButton"
        )
        self.stop_speaking_btn.setFixedWidth(58)
        self.stop_speaking_btn.setToolTip(
            "Stop Keshav speaking"
        )
        self.stop_speaking_btn.setAccessibleName(
            "Stop Keshav speaking"
        )
        self.stop_speaking_btn.setEnabled(False)

        self.call_btn = QPushButton("✦ Live")
        self.call_btn.setObjectName(
            "liveButton"
        )
        self.call_btn.setFixedWidth(82)
        self.call_btn.setToolTip(
            "Start Keshav Live Mode"
        )
        self.call_btn.setAccessibleName(
            "Start Keshav Live Mode"
        )

        self.input = QLineEdit()
        self.input.setPlaceholderText(
            self.normal_input_placeholder
        )

        self.send_btn = QPushButton("Send")

        bottom_layout.addWidget(
            self.attach_btn
        )
        bottom_layout.addWidget(
            self.mic_btn
        )
        bottom_layout.addWidget(
            self.voice_output_btn
        )
        bottom_layout.addWidget(
            self.stop_speaking_btn
        )
        bottom_layout.addWidget(
            self.call_btn
        )
        bottom_layout.addWidget(
            self.input
        )
        bottom_layout.addWidget(
            self.send_btn
        )

        main_layout.addWidget(
            self.bottom_bar
        )

        root_layout.addWidget(
            self.main_panel,
            1,
        )

        # ==================================================
        # Signals
        # ==================================================

        self.send_btn.clicked.connect(
            self.send_message
        )
        self.input.returnPressed.connect(
            self.send_message
        )
        self.reply_signal.connect(
            self.show_reply
        )
        self.stream_chunk_signal.connect(
            self._receive_stream_chunk
        )
        self.voice_partial_signal.connect(
            self._voice_partial_ready
        )
        self.voice_transcription_signal.connect(
            self._voice_transcription_ready
        )
        self.voice_error_signal.connect(
            self._voice_transcription_failed
        )
        self.attach_btn.clicked.connect(
            self.select_attachments
        )
        self.clear_attachments_btn.clicked.connect(
            self.clear_pending_attachments
        )
        self.mic_btn.clicked.connect(
            self.toggle_voice_recording
        )
        self.voice_output_btn.toggled.connect(
            self.toggle_voice_output
        )
        self.stop_speaking_btn.clicked.connect(
            self.stop_speaking
        )
        self.call_btn.clicked.connect(
            self.toggle_call_mode
        )
        self.live_end_btn.clicked.connect(
            self.end_call_mode
        )
        self.new_chat_btn.clicked.connect(
            self.start_new_chat
        )
        self.conversation_list.itemClicked.connect(
            self.open_conversation_from_item
        )
        self.conversation_list.customContextMenuRequested.connect(
            self.show_chat_context_menu
        )
        self.chat_search.textChanged.connect(
            self.filter_conversations
        )
        self.theme_btn.clicked.connect(
            self.toggle_theme
        )
        self.settings_btn.clicked.connect(
            self.open_settings
        )

        self.speech_worker = (
            ElevenLabsSpeechWorker()
        )
        self.speech_worker.events.speaking_changed.connect(
            self._speech_state_changed
        )
        self.speech_worker.events.error.connect(
            self._speech_error
        )
        self._refresh_voice_output_button()
        self._refresh_call_button()

        self.apply_app_theme()
        self.refresh_conversation_list()
        self.load_current_conversation()

    # ======================================================
    # Appearance
    # ======================================================

    def build_app_stylesheet(self) -> str:
        theme = get_theme(
            self.theme_name
        )

        return f"""
        QWidget {{
            background: {theme["window"]};
            color: {theme["text"]};
            font-family: "Segoe UI";
        }}

        QFrame#sidebar {{
            background: {theme["sidebar"]};
            border-right: 1px solid {theme["border"]};
        }}

        QLabel#sidebarTitle {{
            color: {theme["muted"]};
            font-size: 13px;
            font-weight: 600;
            padding: 4px 2px;
        }}

        QListWidget {{
            background: transparent;
            border: none;
            outline: none;
            color: {theme["list_text"]};
            font-size: {max(12, self.font_size - 1)}px;
        }}

        QListWidget::item {{
            background: transparent;
            border-radius: 10px;
            padding: 10px 10px;
            margin: 2px 0;
        }}

        QListWidget::item:hover {{
            background: {theme["panel_hover"]};
        }}

        QListWidget::item:selected {{
            background: {theme["panel_hover"]};
            color: {theme["text"]};
            border: 1px solid {theme["border"]};
        }}

        QMenu {{
            background: {theme["panel_alt"]};
            color: {theme["list_text"]};
            border: 1px solid {theme["border"]};
            border-radius: 8px;
            padding: 6px;
        }}

        QMenu::item {{
            padding: 8px 24px 8px 12px;
            border-radius: 6px;
        }}

        QMenu::item:selected {{
            background: {theme["panel_hover"]};
        }}

        QWidget#chatStage,
        QWidget#chatContent,
        QScrollArea#chatScroll,
        QScrollArea#chatScroll > QWidget,
        QScrollArea#chatScroll > QWidget > QWidget {{
            background: transparent;
            border: none;
        }}

        QScrollArea {{
            border: none;
            background: transparent;
        }}

        QLineEdit {{
            background: {theme["panel_alt"]};
            color: {theme["text"]};
            border: 2px solid {theme["border"]};
            border-radius: 16px;
            padding: 13px 15px;
            font-size: {self.font_size}px;
        }}

        QLineEdit:focus {{
            border: 2px solid {theme["accent"]};
        }}

        QLineEdit#chatSearch {{
            background: {theme["search"]};
            color: {theme["list_text"]};
            border: 1px solid {theme["border"]};
            border-radius: 10px;
            padding: 8px 10px;
            font-size: {max(12, self.font_size - 2)}px;
        }}

        QLineEdit#chatSearch:focus {{
            border: 1px solid {theme["accent"]};
        }}

        QPushButton {{
            background: {theme["accent"]};
            color: white;
            border: none;
            border-radius: 15px;
            padding: 13px 22px;
            font-size: {self.font_size}px;
            font-weight: 600;
        }}

        QPushButton:hover {{
            background: {theme["accent_hover"]};
        }}

        QPushButton:disabled {{
            background: {theme["disabled"]};
            color: {theme["disabled_text"]};
        }}

        QPushButton#newChatButton,
        QPushButton#settingsButton,
        QPushButton#themeButton {{
            background: {theme["panel_alt"]};
            color: {theme["text"]};
            border: 1px solid {theme["border"]};
            border-radius: 12px;
            padding: 11px;
            font-size: 14px;
        }}

        QPushButton#newChatButton:hover,
        QPushButton#settingsButton:hover,
        QPushButton#themeButton:hover {{
            background: {theme["panel_hover"]};
            border: 1px solid {theme["accent"]};
        }}

        QFrame#liveOverlay {{
            background: {theme["window"]};
            border: none;
        }}

        QLabel#liveBrand {{
            color: {theme["muted"]};
            font-size: 18px;
            font-weight: 650;
            padding: 4px;
        }}

        QLabel#liveStatus {{
            color: {theme["text"]};
            font-size: 30px;
            font-weight: 700;
            padding-top: 4px;
        }}

        QLabel#liveDetail {{
            color: {theme["muted"]};
            font-size: 15px;
            padding: 2px 8px 8px 8px;
        }}

        QLabel#liveUserPreview {{
            background: {theme["panel_alt"]};
            color: {theme["text"]};
            border: 1px solid {theme["border_soft"]};
            border-radius: 16px;
            padding: 11px 16px;
            font-size: 15px;
        }}

        QLabel#liveAssistantPreview {{
            color: {theme["text"]};
            padding: 8px 14px;
            font-size: 17px;
            font-weight: 500;
        }}

        QPushButton#endLiveButton {{
            background: #C83C3C;
            color: white;
            border: 1px solid #F87171;
            border-radius: 18px;
            padding: 12px 24px;
            font-size: 15px;
            font-weight: 700;
        }}

        QPushButton#endLiveButton:hover {{
            background: #D94A4A;
        }}

        QFrame#attachmentBar {{
            background: {theme["panel_alt"]};
            border: 1px solid {theme["border_soft"]};
            border-radius: 13px;
        }}

        QLabel#attachmentHint {{
            color: {theme["muted"]};
            font-size: {max(12, self.font_size - 2)}px;
            font-weight: 600;
        }}

        QScrollArea#attachmentScroll,
        QWidget#attachmentContent {{
            background: transparent;
            border: none;
        }}

        QFrame#attachmentChip {{
            background: {theme["window"]};
            border: 1px solid {theme["border"]};
            border-radius: 10px;
        }}

        QLabel#attachmentPreview {{
            background: {theme["panel_hover"]};
            color: {theme["text"]};
            border: 1px solid {theme["border_soft"]};
            border-radius: 8px;
            font-size: 20px;
        }}

        QLabel#attachmentName {{
            color: {theme["text"]};
            font-size: {max(12, self.font_size - 2)}px;
            font-weight: 600;
        }}

        QLabel#attachmentMeta {{
            color: {theme["muted"]};
            font-size: {max(11, self.font_size - 3)}px;
        }}

        QPushButton#attachmentRemove {{
            background: transparent;
            color: {theme["muted"]};
            border: none;
            border-radius: 8px;
            padding: 0;
            font-size: 20px;
            font-weight: 500;
        }}

        QPushButton#attachmentRemove:hover {{
            background: #B83232;
            color: white;
        }}

        QPushButton#clearAttachmentsButton {{
            background: transparent;
            color: {theme["muted"]};
            border: none;
            border-radius: 8px;
            padding: 4px 8px;
            font-size: {max(11, self.font_size - 3)}px;
        }}

        QPushButton#clearAttachmentsButton:hover {{
            background: {theme["panel_hover"]};
            color: {theme["text"]};
        }}

        QPushButton#attachButton,
        QPushButton#voiceButton,
        QPushButton#voiceOutputButton,
        QPushButton#stopSpeakingButton,
        QPushButton#liveButton {{
            background: {theme["panel_alt"]};
            color: {theme["text"]};
            border: 2px solid {theme["border"]};
            border-radius: 15px;
            padding: 11px 8px;
            font-size: 17px;
        }}

        QPushButton#attachButton:hover,
        QPushButton#voiceButton:hover,
        QPushButton#voiceOutputButton:hover,
        QPushButton#stopSpeakingButton:hover,
        QPushButton#liveButton:hover {{
            background: {theme["panel_hover"]};
            border: 2px solid {theme["accent"]};
        }}

        QPushButton#voiceButton[recording="true"] {{
            background: #C83C3C;
            color: white;
            border: 2px solid #F87171;
        }}

        QPushButton#voiceOutputButton[enabledVoice="true"] {{
            background: {theme["accent"]};
            color: white;
            border: 2px solid {theme["accent_hover"]};
        }}

        QPushButton#stopSpeakingButton[speaking="true"] {{
            background: #C83C3C;
            color: white;
            border: 2px solid #F87171;
        }}

        QPushButton#liveButton[inLive="true"] {{
            background: #C83C3C;
            color: white;
            border: 2px solid #F87171;
        }}

        QPushButton#attachButton:disabled,
        QPushButton#voiceButton:disabled,
        QPushButton#voiceOutputButton:disabled,
        QPushButton#stopSpeakingButton:disabled,
        QPushButton#liveButton:disabled {{
            background: {theme["panel_alt"]};
            color: {theme["muted"]};
            border: 2px solid {theme["border_soft"]};
        }}

        QDialog {{
            background: {theme["window"]};
            color: {theme["text"]};
        }}

        QLabel#settingsNote {{
            color: {theme["muted"]};
            font-size: {max(12, self.font_size - 2)}px;
        }}

        QComboBox,
        QSpinBox {{
            background: {theme["panel_alt"]};
            color: {theme["text"]};
            border: 1px solid {theme["border"]};
            border-radius: 9px;
            padding: 8px 10px;
            min-height: 22px;
        }}

        QPushButton#settingsSecondaryButton {{
            background: {theme["panel_alt"]};
            color: {theme["text"]};
            border: 1px solid {theme["border"]};
        }}

        QPushButton#settingsSecondaryButton:hover {{
            background: {theme["panel_hover"]};
        }}

        QPushButton#dangerButton {{
            background: #B83232;
            color: white;
        }}

        QPushButton#dangerButton:hover {{
            background: #D44343;
        }}

        QMessageBox,
        QInputDialog,
        QFileDialog {{
            background: {theme["window"]};
            color: {theme["text"]};
        }}
        """

    def apply_app_theme(self) -> None:
        self.setStyleSheet(
            self.build_app_stylesheet()
        )

        if hasattr(self, "theme_btn"):
            if self.theme_name == "dark":
                self.theme_btn.setText(
                    "☀  Switch to Light"
                )
            else:
                self.theme_btn.setText(
                    "🌙  Switch to Dark"
                )

        if hasattr(
            self,
            "feather_background",
        ):
            self.feather_background.set_theme(
                self.theme_name
            )

        if hasattr(
            self,
            "live_orb",
        ):
            self.live_orb.set_theme(
                self.theme_name
            )

        if hasattr(self, "chat_layout"):
            for index in range(
                self.chat_layout.count()
            ):
                widget = (
                    self.chat_layout
                    .itemAt(index)
                    .widget()
                )

                if isinstance(
                    widget,
                    ChatBubble,
                ):
                    widget.apply_theme(
                        self.theme_name,
                        font_size=self.font_size,
                    )

    def toggle_theme(self) -> None:
        if self.theme_name == "dark":
            self.theme_name = "light"
        else:
            self.theme_name = "dark"

        self.settings.setValue(
            "appearance/theme",
            self.theme_name,
        )

        self.apply_app_theme()


    def open_settings(self) -> None:
        if not self.input.isEnabled():
            return

        dialog = SettingsDialog(
            theme_name=self.theme_name,
            font_size=self.font_size,
            parent=self,
        )

        dialog.setStyleSheet(
            self.build_app_stylesheet()
        )

        dialog.new_chat_button.clicked.connect(
            lambda: self.start_fresh_chat_from_settings(
                dialog
            )
        )
        dialog.delete_all_button.clicked.connect(
            lambda: self.delete_all_chats_from_settings(
                dialog
            )
        )

        if dialog.exec() != QDialog.Accepted:
            return

        self.theme_name = dialog.selected_theme()
        self.font_size = dialog.selected_font_size()

        self.settings.setValue(
            "appearance/theme",
            self.theme_name,
        )
        self.settings.setValue(
            "appearance/font_size",
            self.font_size,
        )

        self.apply_app_theme()

    def start_fresh_chat_from_settings(
        self,
        dialog: QDialog,
    ) -> None:
        dialog.close()
        self.start_new_chat()

    def delete_all_chats_from_settings(
        self,
        dialog: QDialog,
    ) -> None:
        answer = QMessageBox.question(
            dialog,
            "Delete All Chats",
            (
                "Delete every saved conversation?\n\n"
                "This action cannot be undone."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        conversations = list_conversations()

        for conversation in conversations:
            delete_conversation(
                conversation["id"]
            )

        self.current_conversation_id = (
            get_active_conversation_id()
        )

        dialog.close()

        self.clear_chat_messages()
        self.clear_pending_attachments()
        self.input.clear()
        self.refresh_conversation_list()
        self.show_welcome_message()
        self.animate_feather_background()
        self.scroll_to_bottom(
            passes=7
        )

        QMessageBox.information(
            self,
            "Chats Deleted",
            "All saved chats were removed.",
        )

    # ======================================================
    # Sidebar / history
    # ======================================================

    def refresh_conversation_list(self) -> None:
        conversations = list_conversations()

        self.conversation_list.blockSignals(True)
        self.conversation_list.clear()

        selected_row = -1

        for index, conversation in enumerate(
            conversations
        ):
            title = (
                conversation["title"]
                or "New Chat"
            )

            conversation_id = (
                conversation["id"]
            )

            item = QListWidgetItem(title)
            item.setData(
                Qt.UserRole,
                conversation_id,
            )
            item.setToolTip(title)

            self.conversation_list.addItem(
                item
            )

            if (
                conversation_id
                == self.current_conversation_id
            ):
                selected_row = index

        if selected_row >= 0:
            self.conversation_list.setCurrentRow(
                selected_row
            )

        self.conversation_list.blockSignals(False)

        self.filter_conversations(
            self.chat_search.text()
        )

    def filter_conversations(
        self,
        search_text: str,
    ) -> None:
        clean_search = search_text.strip().lower()

        for index in range(
            self.conversation_list.count()
        ):
            item = self.conversation_list.item(
                index
            )

            title = item.text().lower()

            should_hide = (
                bool(clean_search)
                and clean_search not in title
            )

            item.setHidden(
                should_hide
            )

    def open_conversation_from_item(
        self,
        item: QListWidgetItem,
    ) -> None:
        conversation_id = item.data(
            Qt.UserRole
        )

        if not conversation_id:
            return

        self.open_conversation(
            conversation_id
        )

    def open_conversation(
        self,
        conversation_id: str,
    ) -> None:
        if self.call_mode_enabled:
            return

        if not self.input.isEnabled():
            return

        self.stop_speaking()
        self.typing_timer.stop()
        self.full_reply = ""
        self.current_index = 0
        self.current_bot_bubble = None

        messages = load_conversation(
            conversation_id
        )

        self.current_conversation_id = (
            conversation_id
        )

        self.clear_chat_messages()
        self.clear_pending_attachments()

        if messages:
            for message in messages:
                role = getattr(
                    message.role,
                    "value",
                    message.role,
                )

                if role == "user":
                    self.add_user_message(
                        message.content or ""
                    )

                elif role == "assistant":
                    self.add_bot_message(
                        message.content or ""
                    )
        else:
            self.show_welcome_message()

        self.refresh_conversation_list()
        self.set_input_enabled(True)
        self.animate_feather_background()
        self.scroll_to_bottom(
            passes=7
        )

    def load_current_conversation(
        self,
    ) -> None:
        self.open_conversation(
            self.current_conversation_id
        )

    # ======================================================
    # Rename / delete menu
    # ======================================================

    def show_chat_context_menu(
        self,
        position,
    ) -> None:
        if not self.input.isEnabled():
            return

        item = self.conversation_list.itemAt(
            position
        )

        if item is None:
            return

        menu = QMenu(self)

        rename_action = menu.addAction(
            "Rename Chat"
        )
        export_action = menu.addAction(
            "Export Chat"
        )

        menu.addSeparator()

        delete_action = menu.addAction(
            "Delete Chat"
        )

        selected_action = menu.exec(
            self.conversation_list.viewport().mapToGlobal(
                position
            )
        )

        if selected_action == rename_action:
            self.rename_chat_item(item)

        elif selected_action == export_action:
            self.export_chat_item(item)

        elif selected_action == delete_action:
            self.delete_chat_item(item)

    def rename_chat_item(
        self,
        item: QListWidgetItem,
    ) -> None:
        conversation_id = item.data(
            Qt.UserRole
        )

        current_title = item.text()

        new_title, accepted = QInputDialog.getText(
            self,
            "Rename Chat",
            "Enter a new title:",
            text=current_title,
        )

        if not accepted:
            return

        clean_title = new_title.strip()

        if not clean_title:
            QMessageBox.information(
                self,
                "Rename Chat",
                "The chat title cannot be empty.",
            )
            return

        rename_conversation(
            conversation_id,
            clean_title,
        )

        self.refresh_conversation_list()

    def export_chat_item(
        self,
        item: QListWidgetItem,
    ) -> None:
        conversation_id = item.data(
            Qt.UserRole
        )
        title = item.text().strip() or "Keshav Chat"

        messages = chat_store.get_messages(
            conversation_id
        )

        if not messages:
            QMessageBox.information(
                self,
                "Export Chat",
                "This chat does not contain any messages yet.",
            )
            return

        safe_title = "".join(
            character
            if character not in '<>:"/\\|?*'
            else "_"
            for character in title
        ).strip()

        safe_title = safe_title[:60] or "Keshav Chat"

        default_path = str(
            Path.home()
            / "Documents"
            / f"{safe_title}.md"
        )

        file_path, selected_filter = (
            QFileDialog.getSaveFileName(
                self,
                "Export Chat",
                default_path,
                (
                    "Markdown File (*.md);;"
                    "Text File (*.txt)"
                ),
            )
        )

        if not file_path:
            return

        output_path = Path(file_path)

        if not output_path.suffix:
            if "Text File" in selected_filter:
                output_path = output_path.with_suffix(
                    ".txt"
                )
            else:
                output_path = output_path.with_suffix(
                    ".md"
                )

        try:
            if output_path.suffix.lower() == ".txt":
                lines = [
                    title,
                    "=" * len(title),
                    "",
                ]

                for message in messages:
                    role = message["role"]
                    content = message["content"]

                    if role == "user":
                        speaker = "You"
                    elif role == "assistant":
                        speaker = "Keshav"
                    else:
                        speaker = role.title()

                    lines.extend(
                        [
                            f"{speaker}:",
                            content,
                            "",
                        ]
                    )

            else:
                lines = [
                    f"# {title}",
                    "",
                    "_Exported from Keshav_",
                    "",
                ]

                for message in messages:
                    role = message["role"]
                    content = message["content"]

                    if role == "user":
                        speaker = "You"
                    elif role == "assistant":
                        speaker = "Keshav"
                    else:
                        speaker = role.title()

                    lines.extend(
                        [
                            f"## {speaker}",
                            "",
                            content,
                            "",
                        ]
                    )

            output_path.write_text(
                "\n".join(lines).rstrip() + "\n",
                encoding="utf-8",
            )

        except OSError as exc:
            QMessageBox.critical(
                self,
                "Export Failed",
                (
                    "The chat could not be exported.\n\n"
                    f"{exc}"
                ),
            )
            return

        QMessageBox.information(
            self,
            "Export Complete",
            (
                "Chat exported successfully to:\n\n"
                f"{output_path}"
            ),
        )

    def delete_chat_item(
        self,
        item: QListWidgetItem,
    ) -> None:
        conversation_id = item.data(
            Qt.UserRole
        )
        title = item.text()

        answer = QMessageBox.question(
            self,
            "Delete Chat",
            (
                f'Delete "{title}"?\n\n'
                "This conversation will be permanently removed."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        next_conversation_id = delete_conversation(
            conversation_id
        )

        self.current_conversation_id = (
            next_conversation_id
        )

        self.refresh_conversation_list()
        self.open_conversation(
            next_conversation_id
        )

    # ======================================================
    # Chat helpers
    # ======================================================

    def show_welcome_message(
        self,
    ) -> None:
        self.add_bot_message(
            "# 🌸 Radhe Radhe!\n\n"
            "Main **Keshav** hoon.\n\n"
            "Batao, aaj kis baat ki uljhan lekar aaye ho?"
        )

    def animate_feather_background(self) -> None:
        QTimer.singleShot(
            40,
            self.feather_background.restart_animation,
        )

    def scroll_to_bottom(
        self,
        passes: int = 4,
    ) -> None:
        # QTextBrowser and layouts can finish resizing after
        # the first event-loop pass, so scroll a few times.
        self._auto_scroll_passes = max(
            self._auto_scroll_passes,
            passes,
        )

        if not self.auto_scroll_timer.isActive():
            self.auto_scroll_timer.start(0)

    def _perform_auto_scroll(self) -> None:
        scroll_bar = (
            self.scroll.verticalScrollBar()
        )

        scroll_bar.setValue(
            scroll_bar.maximum()
        )

        self._auto_scroll_passes -= 1

        if self._auto_scroll_passes > 0:
            self.auto_scroll_timer.start(35)

    def _on_scroll_range_changed(
        self,
        minimum: int,
        maximum: int,
    ) -> None:
        del minimum

        if maximum > 0:
            self.scroll_to_bottom(
                passes=3
            )

    def add_user_message(
        self,
        text: str,
    ) -> ChatBubble:
        bubble = ChatBubble(
            f"👤 {text}",
            is_user=True,
            theme_name=self.theme_name,
            font_size=self.font_size,
        )

        self.chat_layout.addWidget(
            bubble
        )

        self.scroll_to_bottom()
        return bubble

    def add_bot_message(
        self,
        text: str = "",
    ) -> ChatBubble:
        bubble = ChatBubble(
            text,
            is_user=False,
            theme_name=self.theme_name,
            font_size=self.font_size,
        )

        self.chat_layout.addWidget(
            bubble
        )

        self.scroll_to_bottom()
        return bubble

    def set_input_enabled(
        self,
        enabled: bool,
    ) -> None:
        chat_controls_enabled = (
            enabled
            and not self.is_recording
            and not self.is_transcribing
            and not self.call_mode_enabled
        )

        self.input.setEnabled(
            chat_controls_enabled
        )
        self.send_btn.setEnabled(
            chat_controls_enabled
        )
        self.attach_btn.setEnabled(
            chat_controls_enabled
        )
        self.mic_btn.setEnabled(
            enabled
            and not self.is_transcribing
        )
        self.new_chat_btn.setEnabled(
            chat_controls_enabled
        )
        self.conversation_list.setEnabled(
            chat_controls_enabled
        )
        self.theme_btn.setEnabled(
            chat_controls_enabled
        )
        self.settings_btn.setEnabled(
            chat_controls_enabled
        )

        self.voice_output_btn.setEnabled(
            not self.call_mode_enabled
        )
        self.stop_speaking_btn.setEnabled(
            self.voice_output_enabled
            and self.is_speaking
        )
        self.call_btn.setEnabled(
            not self.is_transcribing
            or self.call_mode_enabled
        )

        if chat_controls_enabled:
            self.input.setFocus()

    def clear_chat_messages(
        self,
    ) -> None:
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    # ======================================================
    # Attachments: picker, drag/drop, preview, removal
    # ======================================================

    def select_attachments(self) -> None:
        if not self.input.isEnabled():
            return

        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Attach Files",
            str(Path.home()),
            (
                "Supported Files "
                "(*.png *.jpg *.jpeg *.webp *.bmp *.gif "
                "*.pdf *.txt *.md *.markdown *.docx *.csv "
                "*.json *.jsonl *.yaml *.yml *.xml *.html *.htm "
                "*.py *.js *.ts *.tsx *.jsx *.java *.c *.h "
                "*.cpp *.hpp *.cs *.go *.rs *.php *.rb *.swift "
                "*.kt *.kts *.sql *.toml *.ini *.cfg *.log "
                "*.sh *.bat *.ps1);;"
                "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif);;"
                "Documents (*.pdf *.txt *.md *.markdown *.docx *.csv);;"
                "Code and Data (*.json *.jsonl *.yaml *.yml *.xml "
                "*.html *.htm *.py *.js *.ts *.tsx *.jsx *.java "
                "*.c *.h *.cpp *.hpp *.cs *.go *.rs *.php *.rb "
                "*.swift *.kt *.kts *.sql *.toml *.ini *.cfg "
                "*.log *.sh *.bat *.ps1);;"
                "All Files (*)"
            ),
        )

        if file_paths:
            self.add_attachments(
                [Path(path) for path in file_paths]
            )

    def add_attachments(
        self,
        file_paths: list[Path],
    ) -> None:
        existing_paths = {
            str(path.resolve()).lower()
            for path in self.pending_attachments
        }

        rejected: list[str] = []

        for raw_path in file_paths:
            path = Path(raw_path)

            if not path.exists() or not path.is_file():
                rejected.append(
                    f"{path.name}: file not found"
                )
                continue

            normalized = str(
                path.resolve()
            ).lower()

            if normalized in existing_paths:
                continue

            if len(self.pending_attachments) >= MAX_ATTACHMENT_COUNT:
                rejected.append(
                    f"Maximum {MAX_ATTACHMENT_COUNT} files allowed"
                )
                break

            try:
                file_size = path.stat().st_size
            except OSError as exc:
                rejected.append(
                    f"{path.name}: {exc}"
                )
                continue

            if file_size > MAX_ATTACHMENT_BYTES:
                rejected.append(
                    f"{path.name}: larger than "
                    f"{format_file_size(MAX_ATTACHMENT_BYTES)}"
                )
                continue

            self.pending_attachments.append(path)
            existing_paths.add(normalized)

        self.refresh_attachment_chips()

        if rejected:
            QMessageBox.information(
                self,
                "Some Files Were Not Added",
                "\n".join(rejected),
            )

    def refresh_attachment_chips(self) -> None:
        while self.attachment_layout.count():
            item = self.attachment_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        for file_path in self.pending_attachments:
            chip = AttachmentChip(
                file_path,
                parent=self.attachment_content,
            )
            chip.remove_requested.connect(
                self.remove_attachment
            )
            self.attachment_layout.addWidget(chip)

        count = len(self.pending_attachments)
        self.attachment_bar.setVisible(
            count > 0
        )

        if count == 1:
            self.attachment_hint.setText(
                "1 attachment selected"
            )
        else:
            self.attachment_hint.setText(
                f"{count} attachments selected"
            )

    def remove_attachment(
        self,
        file_path: str,
    ) -> None:
        target = str(
            Path(file_path).resolve()
        ).lower()

        self.pending_attachments = [
            path
            for path in self.pending_attachments
            if str(path.resolve()).lower() != target
        ]
        self.refresh_attachment_chips()

    def clear_pending_attachments(self) -> None:
        self.pending_attachments.clear()
        self.refresh_attachment_chips()

    def dragEnterEvent(self, event) -> None:
        mime_data = event.mimeData()

        if mime_data.hasUrls() and any(
            url.isLocalFile()
            for url in mime_data.urls()
        ):
            event.acceptProposedAction()
            return

        event.ignore()

    def dropEvent(self, event) -> None:
        file_paths = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]

        self.add_attachments(file_paths)
        event.acceptProposedAction()

    def _build_attachment_message(
        self,
        prompt: str,
        attachments: list[Path],
    ) -> str:
        lines = [prompt.strip()] if prompt.strip() else []

        if attachments:
            if lines:
                lines.append("")

            lines.append("Attached files:")

            for path in attachments:
                try:
                    size_text = format_file_size(
                        path.stat().st_size
                    )
                except OSError:
                    size_text = "Unknown size"

                lines.append(
                    f"- {attachment_type_icon(path)} "
                    f"{path.name} ({size_text})"
                )

        return "\n".join(lines).strip()

    @staticmethod
    def _split_attachment_types(
        attachments: list[Path],
    ) -> tuple[
        list[Path],
        list[Path],
        list[Path],
    ]:
        image_paths = [
            path
            for path in attachments
            if path.suffix.lower()
            in IMAGE_ATTACHMENT_SUFFIXES
        ]

        document_paths = [
            path
            for path in attachments
            if path.suffix.lower()
            in DOCUMENT_ATTACHMENT_SUFFIXES
        ]

        unsupported_paths = [
            path
            for path in attachments
            if (
                path.suffix.lower()
                not in IMAGE_ATTACHMENT_SUFFIXES
                and path.suffix.lower()
                not in DOCUMENT_ATTACHMENT_SUFFIXES
            )
        ]

        return (
            image_paths,
            document_paths,
            unsupported_paths,
        )

    # ======================================================
    # Hands-free call mode
    # ======================================================

    def _refresh_call_button(self) -> None:
        self.call_btn.setProperty(
            "inLive",
            self.call_mode_enabled,
        )
        self.call_btn.setText("✦ Live")
        self.call_btn.setFixedWidth(82)
        self.call_btn.setToolTip(
            "Keshav Live Mode is active"
            if self.call_mode_enabled
            else "Start Keshav Live Mode"
        )

        self.call_btn.style().unpolish(
            self.call_btn
        )
        self.call_btn.style().polish(
            self.call_btn
        )
        self.call_btn.update()

    def _show_live_overlay(self) -> None:
        self.sidebar.setVisible(False)
        self.title_label.setVisible(False)
        self.attachment_bar.setVisible(False)
        self.bottom_bar.setVisible(False)

        self.live_user_preview.clear()
        self.live_user_preview.setVisible(False)
        self.live_assistant_preview.clear()
        self.live_assistant_preview.setVisible(False)

        self.live_overlay.setVisible(True)
        self.live_overlay.raise_()

    def _hide_live_overlay(self) -> None:
        self.live_overlay.setVisible(False)
        self.sidebar.setVisible(True)
        self.title_label.setVisible(True)
        self.bottom_bar.setVisible(True)
        self.attachment_bar.setVisible(
            bool(self.pending_attachments)
        )

    def _set_live_state(
        self,
        state: str,
        status: str,
        detail: str = "",
    ) -> None:
        if not self.call_mode_enabled:
            return

        self.live_orb.set_state(state)
        self.live_status_label.setText(status)
        self.live_detail_label.setText(detail)

    def _set_live_user_preview(
        self,
        text: str,
    ) -> None:
        clean_text = text.strip()
        self.live_user_preview.setText(
            f'You: “{clean_text}”'
        )
        self.live_user_preview.setVisible(
            bool(clean_text)
        )

    def _set_live_assistant_preview(
        self,
        text: str,
    ) -> None:
        clean_text = markdown_to_speech_text(
            text
        ).strip()

        if len(clean_text) > 420:
            clean_text = (
                clean_text[:420].rsplit(
                    " ",
                    1,
                )[0]
                + "…"
            )

        self.live_assistant_preview.setText(
            clean_text
        )
        self.live_assistant_preview.setVisible(
            bool(clean_text)
        )

    def toggle_call_mode(self) -> None:
        if self.call_mode_enabled:
            self.end_call_mode()
        else:
            self.start_call_mode()

    def start_call_mode(self) -> None:
        if (
            self.call_mode_enabled
            or self.is_recording
            or self.is_transcribing
            or self.current_future is not None
            or self.typing_timer.isActive()
        ):
            return

        if self.pending_attachments:
            QMessageBox.information(
                self,
                "Live Mode",
                (
                    "Please send or remove the selected "
                    "attachments before starting a call."
                ),
            )
            return

        self.call_mode_enabled = True
        self.call_auto_sending = False
        self.call_waiting_for_speech_end = False

        self._show_live_overlay()
        self._set_live_state(
            "connecting",
            "Connecting",
            "Preparing your microphone…",
        )

        self.voice_output_enabled = True
        self.settings.setValue(
            "voice/output_enabled",
            True,
        )

        self._refresh_voice_output_button()
        self._refresh_call_button()
        self.set_input_enabled(False)

        self.input.clear()
        self.input.setPlaceholderText(
            "Live mode: preparing microphone..."
        )

        QTimer.singleShot(
            180,
            self.start_call_listening,
        )

    def end_call_mode(self) -> None:
        if not self.call_mode_enabled:
            return

        self.call_mode_enabled = False
        self.call_auto_sending = False
        self.call_waiting_for_speech_end = False

        self.call_monitor_timer.stop()
        self.voice_timer.stop()
        self.stop_speaking()
        self._cancel_elevenlabs_recognition()

        if self.is_recording:
            self._discard_current_recording()

        self.is_transcribing = False
        self.transcription_for_call = False

        self.input.clear()
        self.input.setPlaceholderText(
            self.normal_input_placeholder
        )

        self._refresh_call_button()
        self._hide_live_overlay()
        self.set_input_enabled(True)

    def _cancel_elevenlabs_recognition(
        self,
    ) -> None:
        self.scribe_generation += 1

        future = self.scribe_future
        self.scribe_future = None

        if (
            future is not None
            and not future.done()
        ):
            future.cancel()

    def _start_elevenlabs_recognition(
        self,
        for_live_mode: bool,
    ) -> None:
        self._cancel_elevenlabs_recognition()

        generation = self.scribe_generation

        self.is_transcribing = True
        self.transcription_for_call = (
            for_live_mode
        )
        self.voice_partial_text = ""

        self.scribe_future = (
            self.async_worker.submit(
                self._run_elevenlabs_recognition(
                    generation=generation,
                    for_live_mode=for_live_mode,
                )
            )
        )

    async def _run_elevenlabs_recognition(
        self,
        generation: int,
        for_live_mode: bool,
    ) -> None:
        del for_live_mode

        microphone = None
        sender_task = None

        try:
            token = await asyncio.to_thread(
                ElevenLabsRealtimeScribe
                .get_single_use_token
            )

            if generation != self.scribe_generation:
                return

            websocket_url = (
                ElevenLabsRealtimeScribe
                .build_websocket_url(token)
            )

            audio_queue = asyncio.Queue(
                maxsize=30
            )
            event_loop = (
                asyncio.get_running_loop()
            )

            def microphone_callback(
                indata,
                frames,
                time_info,
                status,
            ) -> None:
                del frames, time_info

                if generation != self.scribe_generation:
                    return

                audio_bytes = bytes(indata)

                def add_audio() -> None:
                    if generation != self.scribe_generation:
                        return

                    if audio_queue.full():
                        try:
                            audio_queue.get_nowait()
                        except asyncio.QueueEmpty:
                            pass

                    try:
                        audio_queue.put_nowait(
                            audio_bytes
                        )
                    except asyncio.QueueFull:
                        pass

                try:
                    event_loop.call_soon_threadsafe(
                        add_audio
                    )
                except RuntimeError:
                    pass

                if status:
                    print(
                        "ElevenLabs microphone warning:",
                        status,
                    )

            async with connect(
                websocket_url,
                max_size=None,
                ping_interval=20,
                close_timeout=2,
            ) as websocket:
                # Wait until ElevenLabs confirms the session before
                # opening the microphone. This avoids losing or
                # misreading the first audio chunk.
                first_raw_message = (
                    await asyncio.wait_for(
                        websocket.recv(),
                        timeout=15,
                    )
                )
                first_event = json.loads(
                    first_raw_message
                )

                if (
                    first_event.get(
                        "message_type"
                    )
                    != "session_started"
                ):
                    raise RuntimeError(
                        "ElevenLabs did not start the "
                        "realtime transcription session."
                    )

                if generation != self.scribe_generation:
                    return

                microphone = sd.RawInputStream(
                    samplerate=SCRIBE_SAMPLE_RATE,
                    channels=1,
                    dtype="int16",
                    blocksize=SCRIBE_BLOCK_SIZE,
                    callback=microphone_callback,
                    latency="low",
                )

                async def send_audio() -> None:
                    while True:
                        chunk = await audio_queue.get()

                        await websocket.send(
                            json.dumps(
                                {
                                    "message_type": (
                                        "input_audio_chunk"
                                    ),
                                    "audio_base_64": (
                                        base64.b64encode(
                                            chunk
                                        ).decode("ascii")
                                    ),
                                    "sample_rate": (
                                        SCRIBE_SAMPLE_RATE
                                    ),
                                }
                            )
                        )

                sender_task = asyncio.create_task(
                    send_audio()
                )

                microphone.start()

                while True:
                    raw_message = (
                        await websocket.recv()
                    )
                    event = json.loads(
                        raw_message
                    )
                    event_type = str(
                        event.get(
                            "message_type",
                            "",
                        )
                    )

                    if generation != self.scribe_generation:
                        return

                    if event_type == "partial_transcript":
                        partial_text = str(
                            event.get(
                                "text",
                                "",
                            )
                        ).strip()

                        if partial_text:
                            self.voice_partial_signal.emit(
                                partial_text
                            )

                    elif event_type in {
                        "committed_transcript",
                        "committed_transcript_with_timestamps",
                    }:
                        transcript = str(
                            event.get(
                                "text",
                                "",
                            )
                        ).strip()

                        # Background noise can occasionally create an
                        # empty VAD commit. Ignore it and keep listening.
                        if not transcript:
                            continue

                        self.voice_transcription_signal.emit(
                            transcript
                        )
                        return

                    elif (
                        "error" in event_type
                        or event_type
                        in {
                            "auth_error",
                            "quota_exceeded",
                            "rate_limited",
                        }
                    ):
                        raise RuntimeError(
                            "ElevenLabs Scribe error: "
                            + json.dumps(
                                event,
                                ensure_ascii=False,
                            )
                        )

        except asyncio.CancelledError:
            return

        except Exception as exc:
            if generation == self.scribe_generation:
                self.voice_error_signal.emit(
                    str(exc)
                )

        finally:
            if microphone is not None:
                try:
                    microphone.stop()
                except Exception:
                    pass

                try:
                    microphone.close()
                except Exception:
                    pass

            if sender_task is not None:
                sender_task.cancel()

                await asyncio.gather(
                    sender_task,
                    return_exceptions=True,
                )


    def _create_audio_capture(self) -> bool:
        audio_device = (
            QMediaDevices.defaultAudioInput()
        )

        if audio_device.isNull():
            QMessageBox.warning(
                self,
                "Microphone Not Found",
                "Windows did not provide a microphone "
                "to Keshav.",
            )
            return False

        desired_format = QAudioFormat()
        desired_format.setSampleRate(
            VOICE_SAMPLE_RATE
        )
        desired_format.setChannelCount(1)
        desired_format.setSampleFormat(
            QAudioFormat.SampleFormat.Int16
        )

        if audio_device.isFormatSupported(
            desired_format
        ):
            self.voice_format = desired_format
        else:
            self.voice_format = (
                audio_device.preferredFormat()
            )

        self.voice_buffer = QBuffer(self)

        if not self.voice_buffer.open(
            QIODevice.OpenModeFlag.WriteOnly
        ):
            self.voice_buffer = None
            QMessageBox.warning(
                self,
                "Voice Error",
                "The recording buffer could not be opened.",
            )
            return False

        try:
            self.audio_source = QAudioSource(
                audio_device,
                self.voice_format,
                self,
            )
            self.audio_source.start(
                self.voice_buffer
            )

        except Exception as exc:
            self.voice_buffer.close()
            self.voice_buffer = None
            self.audio_source = None
            self.voice_format = None

            QMessageBox.warning(
                self,
                "Voice Error",
                str(exc),
            )
            return False

        return True

    def start_call_listening(self) -> None:
        if (
            not self.call_mode_enabled
            or self.is_transcribing
            or self.current_future is not None
            or self.typing_timer.isActive()
            or self.is_speaking
        ):
            return

        self.input.clear()
        self.input.setPlaceholderText(
            "Live mode: listening..."
        )
        self._set_live_state(
            "listening",
            "Listening",
            "Speak naturally. I’ll respond when you pause.",
        )
        self.live_orb.set_audio_level(0.28)

        self.mic_btn.setProperty(
            "recording",
            True,
        )
        self.mic_btn.setText("🎧")
        self.mic_btn.setFixedWidth(58)
        self.mic_btn.setToolTip(
            "ElevenLabs Scribe is listening"
        )
        self._refresh_mic_style()

        self.set_input_enabled(False)
        self._start_elevenlabs_recognition(
            for_live_mode=True
        )

    def _monitor_call_audio(self) -> None:
        if (
            not self.call_mode_enabled
            or not self.is_recording
            or not self.recording_for_call
            or self.voice_buffer is None
            or self.voice_format is None
        ):
            self.call_monitor_timer.stop()
            return

        raw_data = bytes(
            self.voice_buffer.data()
        )

        current_size = len(raw_data)
        new_data = raw_data[
            self.call_last_buffer_size:
        ]
        self.call_last_buffer_size = current_size
        self.call_elapsed_ms += (
            CALL_MONITOR_INTERVAL_MS
        )

        level = pcm_rms_level(
            new_data,
            self.voice_format,
        )

        visual_level = min(
            1.0,
            level / max(
                CALL_MIN_RMS_LEVEL * 4.5,
                0.001,
            ),
        )
        self.live_orb.set_audio_level(
            visual_level
        )

        if (
            not self.call_speech_detected
            and self.call_elapsed_ms <= 700
        ):
            self.call_noise_floor = (
                self.call_noise_floor * 0.8
                + level * 0.2
            )

        speech_threshold = max(
            CALL_MIN_RMS_LEVEL,
            self.call_noise_floor * 3.2,
        )

        if level >= speech_threshold:
            self.call_speech_detected = True
            self.call_speech_ms += (
                CALL_MONITOR_INTERVAL_MS
            )
            self.call_silence_ms = 0
            self.input.setPlaceholderText(
                "Live mode: hearing you..."
            )
            self._set_live_state(
                "listening",
                "Listening",
                "I’m hearing you…",
            )

        elif self.call_speech_detected:
            self.call_silence_ms += (
                CALL_MONITOR_INTERVAL_MS
            )

        if (
            self.call_speech_detected
            and self.call_speech_ms
            >= CALL_MIN_SPEECH_MS
            and self.call_silence_ms
            >= CALL_SILENCE_TO_SEND_MS
        ):
            self.stop_voice_recording()
            return

        if (
            not self.call_speech_detected
            and self.call_elapsed_ms
            >= CALL_EMPTY_RESTART_MS
        ):
            self._restart_empty_call_capture()

    def _restart_empty_call_capture(self) -> None:
        if not self.call_mode_enabled:
            return

        self.call_monitor_timer.stop()
        self._discard_current_recording()

        self.input.setPlaceholderText(
            "Live mode: still listening..."
        )
        self._set_live_state(
            "listening",
            "Listening",
            "Still here — start speaking whenever you’re ready.",
        )

        QTimer.singleShot(
            180,
            self.start_call_listening,
        )

    def _discard_current_recording(self) -> None:
        self.call_monitor_timer.stop()
        self.voice_timer.stop()

        if self.audio_source is not None:
            self.audio_source.stop()

        if self.voice_buffer is not None:
            self.voice_buffer.close()

        self.audio_source = None
        self.voice_buffer = None
        self.voice_format = None
        self.is_recording = False
        self.recording_for_call = False

        self.mic_btn.setProperty(
            "recording",
            False,
        )
        self.mic_btn.setText("🎙")
        self.mic_btn.setFixedWidth(58)
        self.mic_btn.setToolTip(
            "Record a voice note"
        )
        self._refresh_mic_style()

    # ======================================================
    # Spoken assistant replies
    # ======================================================

    def _refresh_voice_output_button(self) -> None:
        enabled = bool(
            self.voice_output_enabled
        )

        self.voice_output_btn.blockSignals(True)
        self.voice_output_btn.setChecked(enabled)
        self.voice_output_btn.blockSignals(False)

        self.voice_output_btn.setProperty(
            "enabledVoice",
            enabled,
        )
        self.voice_output_btn.setText(
            "🔊" if enabled else "🔇"
        )
        self.voice_output_btn.setToolTip(
            "Spoken replies are ON"
            if enabled
            else "Spoken replies are OFF"
        )

        self.voice_output_btn.style().unpolish(
            self.voice_output_btn
        )
        self.voice_output_btn.style().polish(
            self.voice_output_btn
        )
        self.voice_output_btn.update()

        self.stop_speaking_btn.setEnabled(
            enabled and self.is_speaking
        )

    def toggle_voice_output(
        self,
        enabled: bool,
    ) -> None:
        if self.call_mode_enabled and not enabled:
            self._refresh_voice_output_button()
            return

        self.voice_output_enabled = bool(enabled)
        self.settings.setValue(
            "voice/output_enabled",
            self.voice_output_enabled,
        )

        if not self.voice_output_enabled:
            self.stop_speaking()

        self._refresh_voice_output_button()

    def speak_assistant_reply(
        self,
        reply: str,
    ) -> None:
        if (
            not self.voice_output_enabled
            or self.speech_worker is None
        ):
            if self.call_mode_enabled:
                QTimer.singleShot(
                    250,
                    self.start_call_listening,
                )
            return

        spoken_text = markdown_to_speech_text(
            reply
        )

        if spoken_text:
            self.call_waiting_for_speech_end = (
                self.call_mode_enabled
            )
            self.input.setPlaceholderText(
                "Live mode: Keshav is speaking..."
                if self.call_mode_enabled
                else self.normal_input_placeholder
            )

            if self.call_mode_enabled:
                self._set_live_assistant_preview(
                    reply
                )
                self._set_live_state(
                    "speaking",
                    "Speaking",
                    "Keshav is responding…",
                )
            self.speech_worker.speak(
                spoken_text
            )

        elif self.call_mode_enabled:
            QTimer.singleShot(
                250,
                self.start_call_listening,
            )

    def stop_speaking(self) -> None:
        if self.speech_worker is not None:
            self.speech_worker.stop()

    def _speech_state_changed(
        self,
        speaking: bool,
    ) -> None:
        self.is_speaking = bool(speaking)

        if self.call_mode_enabled and self.is_speaking:
            self._set_live_state(
                "speaking",
                "Speaking",
                "Keshav is responding…",
            )

        speech_queue_pending = (
            self.speech_worker.has_pending()
            if self.speech_worker is not None
            else False
        )

        should_resume_call = (
            not self.is_speaking
            and not speech_queue_pending
            and self.call_mode_enabled
            and self.call_waiting_for_speech_end
        )

        if should_resume_call:
            self.call_waiting_for_speech_end = False

        self.stop_speaking_btn.setProperty(
            "speaking",
            self.is_speaking,
        )
        self.stop_speaking_btn.setEnabled(
            self.voice_output_enabled
            and self.is_speaking
        )

        self.stop_speaking_btn.style().unpolish(
            self.stop_speaking_btn
        )
        self.stop_speaking_btn.style().polish(
            self.stop_speaking_btn
        )
        self.stop_speaking_btn.update()

        if should_resume_call:
            self.input.setPlaceholderText(
                "Live mode: listening again..."
            )
            self._set_live_state(
                "listening",
                "Listening",
                "Your turn — speak whenever you’re ready.",
            )
            QTimer.singleShot(
                300,
                self.start_call_listening,
            )

    def _speech_error(
        self,
        error_message: str,
    ) -> None:
        self.is_speaking = False
        self.voice_output_enabled = False
        self.settings.setValue(
            "voice/output_enabled",
            False,
        )
        self._refresh_voice_output_button()

        if self.call_mode_enabled:
            self._set_live_state(
                "error",
                "Voice unavailable",
                "Live Mode had to stop.",
            )
            self.end_call_mode()

        QMessageBox.warning(
            self,
            "Voice Output Error",
            (
                "Keshav could not start ElevenLabs voice.\n\n"
                f"{error_message}"
            ),
        )

    # ======================================================
    # Voice notes
    # ======================================================

    def _refresh_mic_style(self) -> None:
        self.mic_btn.style().unpolish(
            self.mic_btn
        )
        self.mic_btn.style().polish(
            self.mic_btn
        )
        self.mic_btn.update()

    def toggle_voice_recording(self) -> None:
        if self.call_mode_enabled:
            return

        if self.is_transcribing:
            self._cancel_elevenlabs_recognition()
            self.is_transcribing = False
            self.transcription_for_call = False
            self._restore_voice_controls()
            return

        self.start_voice_recording()

    def start_voice_recording(self) -> None:
        if (
            self.is_recording
            or self.is_transcribing
            or not self.input.isEnabled()
        ):
            return

        self.mic_btn.setProperty(
            "recording",
            True,
        )
        self.mic_btn.setText("■")
        self.mic_btn.setFixedWidth(58)
        self.mic_btn.setToolTip(
            "Stop ElevenLabs speech recognition"
        )
        self._refresh_mic_style()

        self.voice_input_prefix = (
            self.input.text().strip()
        )
        self.input.setPlaceholderText(
            "Listening with ElevenLabs Scribe..."
        )
        self.input.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.attach_btn.setEnabled(False)
        self.new_chat_btn.setEnabled(False)
        self.conversation_list.setEnabled(False)
        self.theme_btn.setEnabled(False)
        self.settings_btn.setEnabled(False)

        self._start_elevenlabs_recognition(
            for_live_mode=False
        )

    def _update_recording_time(self) -> None:
        if not self.is_recording:
            self.voice_timer.stop()
            return

        self.voice_seconds += 1
        minutes, seconds = divmod(
            self.voice_seconds,
            60,
        )

        self.mic_btn.setText(
            f"■ {minutes:02d}:{seconds:02d}"
        )

        if self.voice_seconds >= MAX_VOICE_SECONDS:
            self.stop_voice_recording()

    def stop_voice_recording(self) -> None:
        if not self.is_recording:
            return

        was_call_recording = bool(
            self.recording_for_call
        )

        self.call_monitor_timer.stop()
        self.voice_timer.stop()
        self.is_recording = False
        self.recording_for_call = False

        if self.audio_source is not None:
            self.audio_source.stop()

        raw_data = b""

        if self.voice_buffer is not None:
            raw_data = bytes(
                self.voice_buffer.data()
            )
            self.voice_buffer.close()

        audio_format = self.voice_format

        self.audio_source = None
        self.voice_buffer = None
        self.voice_format = None

        self.mic_btn.setProperty(
            "recording",
            False,
        )
        self.mic_btn.setText("…")
        self.mic_btn.setFixedWidth(58)
        self.mic_btn.setEnabled(False)
        self.mic_btn.setToolTip(
            "Transcribing voice note"
        )
        self._refresh_mic_style()

        self.is_transcribing = True
        self.transcription_for_call = (
            was_call_recording
        )
        self.input.setPlaceholderText(
            "Live mode: understanding you..."
            if was_call_recording
            else "Transcribing with ElevenLabs Scribe..."
        )

        if was_call_recording:
            self._set_live_state(
                "thinking",
                "Understanding",
                "Turning your speech into text…",
            )

        if (
            not raw_data
            or audio_format is None
        ):
            self.voice_error_signal.emit(
                "No microphone audio was captured."
            )
            return

        try:
            audio = pcm_to_float32(
                raw_data,
                audio_format,
            )

        except Exception as exc:
            self.voice_error_signal.emit(
                str(exc)
            )
            return

        minimum_samples = int(
            VOICE_SAMPLE_RATE * 0.35
        )

        if audio.size < minimum_samples:
            self.voice_error_signal.emit(
                "The voice note was too short. "
                "Please record for at least one second."
            )
            return

        worker = threading.Thread(
            target=self._transcribe_voice_worker,
            args=(audio,),
            daemon=True,
            name="KeshavVoiceTranscriber",
        )
        worker.start()

    def _transcribe_voice_worker(
        self,
        audio: np.ndarray,
    ) -> None:
        del audio

        self.voice_error_signal.emit(
            "Legacy Whisper transcription is disabled. "
            "ElevenLabs Scribe is active instead."
        )

    def _restore_voice_controls(self) -> None:
        self.is_transcribing = False
        self.is_recording = False
        self.recording_for_call = False

        self.mic_btn.setProperty(
            "recording",
            False,
        )
        self.mic_btn.setText("🎙")
        self.mic_btn.setFixedWidth(58)
        self.mic_btn.setToolTip(
            "Record a voice note"
        )
        self._refresh_mic_style()

        if self.call_mode_enabled:
            self.input.setPlaceholderText(
                "Live mode: processing..."
            )
            self.set_input_enabled(False)
        else:
            self.input.setPlaceholderText(
                self.normal_input_placeholder
            )
            self.set_input_enabled(True)

    def _voice_partial_ready(
        self,
        partial_text: str,
    ) -> None:
        clean_partial = partial_text.strip()

        if not clean_partial:
            return

        self.voice_partial_text = clean_partial

        if self.call_mode_enabled:
            self._set_live_user_preview(
                clean_partial
            )
            self._set_live_state(
                "listening",
                "Listening",
                "I’m hearing you…",
            )
            self.live_orb.set_audio_level(
                0.62
            )
            return

        if self.is_transcribing:
            pieces = [
                value
                for value in (
                    self.voice_input_prefix,
                    clean_partial,
                )
                if value
            ]
            preview_text = " ".join(
                pieces
            )

            self.input.setText(
                preview_text
            )
            self.input.setCursorPosition(
                len(preview_text)
            )

    def _voice_transcription_ready(
        self,
        transcript: str,
    ) -> None:
        was_call_transcription = bool(
            self.transcription_for_call
        )
        self.transcription_for_call = False
        self._restore_voice_controls()

        clean_transcript = transcript.strip()
        input_prefix = self.voice_input_prefix
        self.voice_input_prefix = ""
        self.voice_partial_text = ""

        if was_call_transcription:
            if not self.call_mode_enabled:
                self.input.clear()
                return

            if not clean_transcript:
                QTimer.singleShot(
                    250,
                    self.start_call_listening,
                )
                return

            self.input.setText(
                clean_transcript
            )
            self._set_live_user_preview(
                clean_transcript
            )
            self._set_live_state(
                "thinking",
                "Thinking",
                "Keshav is preparing a response…",
            )
            self.call_auto_sending = True

            try:
                self.send_message()
            finally:
                self.call_auto_sending = False

            return

        pieces = [
            value
            for value in (
                input_prefix,
                clean_transcript,
            )
            if value
        ]
        final_text = " ".join(
            pieces
        )

        self.input.setText(final_text)
        self.input.setCursorPosition(
            len(final_text)
        )
        self.input.setFocus()

    def _voice_transcription_failed(
        self,
        error_message: str,
    ) -> None:
        self.voice_partial_text = ""
        self.voice_input_prefix = ""

        was_call_transcription = bool(
            self.transcription_for_call
        )
        self.transcription_for_call = False
        self._restore_voice_controls()

        if was_call_transcription:
            if self.call_mode_enabled:
                self.input.clear()
                self.input.setPlaceholderText(
                    "Live mode: I did not catch that. Listening again..."
                )
                self._set_live_state(
                    "listening",
                    "Listening",
                    "I didn’t catch that clearly. Please try again.",
                )
                QTimer.singleShot(
                    500,
                    self.start_call_listening,
                )
            return

        QMessageBox.warning(
            self,
            "Voice Note Error",
            error_message,
        )

    # ======================================================
    # New chat
    # ======================================================

    def start_new_chat(self) -> None:
        if self.call_mode_enabled:
            return

        if not self.input.isEnabled():
            return

        self.stop_speaking()
        self.typing_timer.stop()
        self.full_reply = ""
        self.current_index = 0
        self.current_bot_bubble = None

        self.current_conversation_id = (
            clear_conversation()
        )

        self.clear_chat_messages()
        self.clear_pending_attachments()
        self.input.clear()
        self.set_input_enabled(True)
        self.show_welcome_message()
        self.refresh_conversation_list()
        self.animate_feather_background()
        self.scroll_to_bottom(
            passes=7
        )

    # ======================================================
    # Send / async result
    # ======================================================

    def send_message(self) -> None:
        self.stop_speaking()

        prompt = self.input.text().strip()
        attachments = list(
            self.pending_attachments
        )

        call_send_allowed = (
            self.call_mode_enabled
            and self.call_auto_sending
        )

        if (
            (not prompt and not attachments)
            or (
                not self.input.isEnabled()
                and not call_send_allowed
            )
        ):
            return

        (
            image_attachments,
            document_attachments,
            unsupported_attachments,
        ) = self._split_attachment_types(
            attachments
        )

        if unsupported_attachments:
            unsupported_names = "\n".join(
                f"- {path.name}"
                for path in unsupported_attachments
            )

            QMessageBox.information(
                self,
                "Unsupported File Type",
                (
                    "Keshav can currently analyze images, "
                    "PDF, DOCX, TXT, Markdown, CSV, XLSX, "
                    "XLSM, PPTX, JSON, and common code files."
                    "\n\nLegacy .xls and .ppt files are not "
                    "supported yet. Please remove these files "
                    "before sending:\n"
                    f"{unsupported_names}"
                ),
            )
            return

        if not prompt:
            if image_attachments and document_attachments:
                prompt = (
                    "Please analyze the attached images and "
                    "documents together."
                )
            elif image_attachments:
                prompt = (
                    "Please describe and analyze the attached "
                    "image or images."
                )
            elif document_attachments:
                prompt = (
                    "Please summarize and analyze the attached "
                    "document or documents."
                )

        supported_attachments = (
            image_attachments
            + document_attachments
        )

        message_text = self._build_attachment_message(
            prompt,
            supported_attachments,
        )

        self.input.clear()
        self.clear_pending_attachments()
        self.add_user_message(message_text)

        self.streamed_reply = ""
        self.stream_speech_buffer = ""
        self.live_tts_buffer = ""
        self.stream_received_chunk = False
        self.stream_voice_started = False
        self.call_waiting_for_speech_end = False

        if (
            self.call_mode_enabled
            and self.voice_output_enabled
            and self.speech_worker is not None
        ):
            self.stream_voice_started = True
            self.speech_worker.begin_stream()

        self.current_bot_bubble = (
            self.add_bot_message(
                "🦚 **Looking at files...**"
                if (
                    image_attachments
                    and document_attachments
                )
                else "🦚 **Looking at the image...**"
                if image_attachments
                else "🦚 **Reading the document...**"
                if document_attachments
                else "🦚 **Thinking...**"
            )
        )

        self.set_input_enabled(False)

        conversation_id = (
            self.current_conversation_id
        )

        self.current_future = (
            self.async_worker.submit(
                ask_keshav(
                    message_text,
                    conversation_id=conversation_id,
                    image_paths=[
                        str(path)
                        for path in image_attachments
                    ],
                    document_paths=[
                        str(path)
                        for path in document_attachments
                    ],
                    on_chunk=self._emit_stream_chunk,
                    live_mode=self.call_mode_enabled,
                )
            )
        )

        self.current_future.add_done_callback(
            self._on_ai_future_done
        )

    def _emit_stream_chunk(
        self,
        chunk: str,
    ) -> None:
        """
        Called by the Ollama worker thread. Qt safely delivers the
        text to the main UI thread through stream_chunk_signal.
        """

        if chunk:
            self.stream_chunk_signal.emit(
                chunk
            )

    def _take_stream_speech_segments(
        self,
        final: bool = False,
    ) -> list[str]:
        """
        Pull complete spoken sentences from the streaming buffer.

        A long line can also be released at a sensible word boundary
        so Live Mode does not wait forever for punctuation.
        """

        segments: list[str] = []
        buffer = self.stream_speech_buffer

        while buffer:
            boundary = None

            for match in re.finditer(
                r'[.!?।](?:["\')\]]{0,2})(?=\s|$)',
                buffer,
            ):
                if match.end() >= 18:
                    boundary = match.end()
                    break

            if boundary is None:
                newline_index = buffer.find(
                    "\n"
                )

                if newline_index >= 60:
                    boundary = newline_index + 1

            if (
                boundary is None
                and len(buffer) > 280
            ):
                boundary = buffer.rfind(
                    " ",
                    0,
                    240,
                )

                if boundary < 80:
                    boundary = 240

            if boundary is None:
                break

            segment = buffer[
                :boundary
            ].strip()
            buffer = buffer[
                boundary:
            ].lstrip()

            if segment:
                segments.append(
                    segment
                )

        if final and buffer.strip():
            segments.append(
                buffer.strip()
            )
            buffer = ""

        self.stream_speech_buffer = buffer
        return segments

    def _queue_stream_speech(
        self,
        chunk: str = "",
        final: bool = False,
    ) -> None:
        """
        Queue complete sentences while Ollama is still generating.

        This is used in Live Mode, so Keshav can begin speaking before
        the full answer has finished generating.
        """

        if chunk:
            self.stream_speech_buffer += (
                chunk
            )

        if (
            not self.call_mode_enabled
            or not self.voice_output_enabled
            or self.speech_worker is None
        ):
            return

        for segment in self._take_stream_speech_segments(
            final=final
        ):
            spoken_text = markdown_to_speech_text(
                segment
            )

            if not spoken_text:
                continue

            self.stream_voice_started = True
            self.speech_worker.enqueue(
                spoken_text
            )

    def _flush_live_tts_buffer(
        self,
        final: bool = False,
    ) -> None:
        """
        Send complete phrases to ElevenLabs instead of raw Ollama
        token fragments, which can split a single word into pieces.
        """

        if (
            not self.call_mode_enabled
            or not self.voice_output_enabled
            or self.speech_worker is None
        ):
            return

        while self.live_tts_buffer:
            buffer = self.live_tts_buffer
            boundary = None

            # Prefer punctuation because it gives the voice natural
            # phrasing and intonation.
            for match in re.finditer(
                r'[.!?।,:;](?:["\')\]]{0,2})(?=\s|$)',
                buffer,
            ):
                if match.end() >= 28:
                    boundary = match.end()
                    break

            # Start quickly after a short phrase, but cut only at an
            # actual whitespace boundary so words remain intact.
            target_length = (
                52
                if not self.stream_voice_started
                else 88
            )

            if (
                boundary is None
                and len(buffer) >= target_length
            ):
                candidate = buffer.rfind(
                    " ",
                    0,
                    target_length + 1,
                )

                if candidate >= 28:
                    boundary = candidate

            if final and boundary is None:
                boundary = len(buffer)

            if boundary is None:
                break

            phrase = buffer[:boundary].strip()
            self.live_tts_buffer = (
                buffer[boundary:].lstrip()
            )

            spoken_phrase = markdown_to_speech_text(
                phrase
            )

            if not spoken_phrase:
                continue

            self.stream_voice_started = True
            self.speech_worker.enqueue_stream(
                spoken_phrase
            )

    def _receive_stream_chunk(
        self,
        chunk: str,
    ) -> None:
        if not chunk:
            return

        self.stream_received_chunk = True
        self.streamed_reply += chunk
        self.full_reply = self.streamed_reply

        if self.call_mode_enabled:
            # Keep visual token streaming hidden. Buffer the model's
            # text until a complete phrase is safe to pronounce.
            self.live_tts_buffer += chunk
            self._flush_live_tts_buffer(
                final=False
            )
            return

        if self.current_bot_bubble is None:
            self.current_bot_bubble = (
                self.add_bot_message("")
            )

        self.current_bot_bubble.set_stream_text(
            self.streamed_reply
        )

        self.scroll_to_bottom(
            passes=2
        )

    def _on_ai_future_done(
        self,
        future,
    ) -> None:
        try:
            reply = future.result()

            if not reply:
                reply = (
                    "I couldn't generate a response."
                )

        except Exception as exc:
            reply = (
                "## ❌ Error\n\n"
                "```text\n"
                + escape(str(exc))
                + "\n```"
            )

        self.reply_signal.emit(reply)

    # ======================================================
    # Typing animation
    # ======================================================

    def show_reply(
        self,
        text: str,
    ) -> None:
        self.typing_timer.stop()
        self.current_future = None

        final_reply = (
            text
            or self.streamed_reply
            or "I couldn't generate a response."
        ).strip()

        self.full_reply = final_reply

        if self.current_bot_bubble is None:
            self.current_bot_bubble = (
                self.add_bot_message("")
            )

        # Live Mode displays the complete answer once, rather than
        # revealing it token by token.
        self.current_bot_bubble.set_markdown(
            final_reply
        )

        if self.call_mode_enabled:
            self._set_live_assistant_preview(
                final_reply
            )

            if (
                self.voice_output_enabled
                and self.speech_worker is not None
            ):
                if not self.stream_received_chunk:
                    self.live_tts_buffer = (
                        final_reply
                    )

                self._flush_live_tts_buffer(
                    final=True
                )

                if self.stream_voice_started:
                    self.call_waiting_for_speech_end = True
                    self.speech_worker.finish_stream()
                else:
                    self.call_waiting_for_speech_end = False
                    QTimer.singleShot(
                        200,
                        self.start_call_listening,
                    )

            else:
                self.call_waiting_for_speech_end = False
                QTimer.singleShot(
                    200,
                    self.start_call_listening,
                )

        else:
            self.speak_assistant_reply(
                final_reply
            )

        self.current_bot_bubble = None
        self.set_input_enabled(True)
        self.refresh_conversation_list()
        self.scroll_to_bottom(
            passes=5
        )

        self.stream_speech_buffer = ""

    def type_next_chunk(self) -> None:
        if self.current_index >= len(
            self.full_reply
        ):
            self.typing_timer.stop()

            if self.current_bot_bubble is not None:
                self.current_bot_bubble.set_markdown(
                    self.full_reply
                )

            completed_reply = self.full_reply

            self.current_bot_bubble = None
            self.set_input_enabled(True)
            self.refresh_conversation_list()
            self.scroll_to_bottom(
                passes=6
            )
            self.speak_assistant_reply(
                completed_reply
            )
            return

        chunk_size = (
            12
            if self.call_mode_enabled
            else 4
        )

        self.current_index = min(
            self.current_index + chunk_size,
            len(self.full_reply),
        )

        current_text = self.full_reply[
            :self.current_index
        ]

        if self.current_bot_bubble is not None:
            self.current_bot_bubble.set_stream_text(
                current_text
            )

        if self.call_mode_enabled:
            self._set_live_assistant_preview(
                current_text
            )

        self.scroll_to_bottom()


    def closeEvent(self, event) -> None:
        self.call_mode_enabled = False
        self.call_monitor_timer.stop()
        self.voice_timer.stop()
        self.stop_speaking()
        self._cancel_elevenlabs_recognition()

        if self.speech_worker is not None:
            self.speech_worker.shutdown()

        if self.audio_source is not None:
            self.audio_source.stop()

        if self.voice_buffer is not None:
            self.voice_buffer.close()

        super().closeEvent(event)


# ==========================================================
# Main
# ==========================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Keshav")

    window = KeshavWindow()
    window.show()

    sys.exit(app.exec())
