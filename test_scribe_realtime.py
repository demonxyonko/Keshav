import asyncio
import base64
import json
import os
import urllib.parse
import urllib.request

import sounddevice as sd
from dotenv import load_dotenv
from websockets.asyncio.client import connect


SAMPLE_RATE = 16000
BLOCK_SIZE = 3200


def get_token() -> str:
    load_dotenv(dotenv_path=".env")
    api_key = os.getenv("ELEVENLABS_API_KEY")

    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY missing from .env")

    request = urllib.request.Request(
        "https://api.elevenlabs.io/v1/single-use-token/realtime_scribe",
        headers={"xi-api-key": api_key},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.load(response)

    token = data.get("token")

    if not token:
        raise RuntimeError("ElevenLabs did not return a token.")

    return token


async def main() -> None:
    token = get_token()

    query = urllib.parse.urlencode(
        [
            ("model_id", "scribe_v2_realtime"),
            ("token", token),
            ("audio_format", "pcm_16000"),
            ("commit_strategy", "vad"),
            ("vad_silence_threshold_secs", "1.0"),
            ("include_language_detection", "true"),
            ("keyterms", "Keshav"),
            ("keyterms", "Ollama"),
            ("keyterms", "Radhe Radhe"),
        ]
    )

    url = (
        "wss://api.elevenlabs.io/v1/"
        "speech-to-text/realtime?"
        + query
    )

    audio_queue = asyncio.Queue(maxsize=30)
    event_loop = asyncio.get_running_loop()

    def microphone_callback(
        indata,
        frames,
        time_info,
        status,
    ):
        del frames, time_info

        if status:
            print("\nMicrophone warning:", status)

        audio_bytes = bytes(indata)

        def add_audio():
            if audio_queue.full():
                try:
                    audio_queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass

            audio_queue.put_nowait(audio_bytes)

        event_loop.call_soon_threadsafe(add_audio)

    async with connect(
        url,
        max_size=None,
        ping_interval=20,
    ) as websocket:

        microphone = sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=BLOCK_SIZE,
            callback=microphone_callback,
        )

        async def send_audio():
            while True:
                chunk = await audio_queue.get()

                await websocket.send(
                    json.dumps(
                        {
                            "message_type": "input_audio_chunk",
                            "audio_base_64": base64.b64encode(
                                chunk
                            ).decode("ascii"),
                            "sample_rate": SAMPLE_RATE,
                        }
                    )
                )

        sender_task = asyncio.create_task(
            send_audio()
        )

        microphone.start()

        print("Connected successfully.")
        print("Speak now, then remain silent for one second.")
        print(
            'Try: "Keshav, kal ka study plan bana do"'
        )

        try:
            async for raw_message in websocket:
                event = json.loads(raw_message)
                event_type = event.get(
                    "message_type",
                    ""
                )

                if event_type == "session_started":
                    print("Realtime Scribe session started.")

                elif event_type == "partial_transcript":
                    print(
                        "\rPartial:",
                        event.get("text", ""),
                        " " * 20,
                        end="",
                        flush=True,
                    )

                elif event_type == "committed_transcript":
                    print(
                        "\nFinal:",
                        event.get("text", ""),
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
                        json.dumps(
                            event,
                            ensure_ascii=False,
                        )
                    )

        finally:
            microphone.stop()
            microphone.close()

            sender_task.cancel()

            await asyncio.gather(
                sender_task,
                return_exceptions=True,
            )


if __name__ == "__main__":
    asyncio.run(main())
