<p align="center">
  <img src="assets/logo.jpg" width="190" alt="Keshav logo"/>
</p>

<h1 align="center">🦚 Keshav</h1>

<p align="center">
  <strong>A local-first Windows AI assistant with chat, vision, documents, tools, and natural Live Mode voice.</strong>
</p>

<p align="center">
  Private by default • Powered by Ollama • Hindi, English, and Hinglish voice support
</p>

What is Keshav?

Keshav is a desktop AI assistant designed to feel fast, useful, and natural.

It runs its main language and vision models locally through Ollama, keeps conversations on your computer, understands images and documents, and supports real-time voice conversations through ElevenLabs.

Keshav is built for everyday use: asking questions, writing and reviewing code, understanding files, analyzing screenshots, planning tasks, and having natural Hindi, English, or Hinglish conversations.

Highlights

Local AI chat

Runs through Ollama on your own computer

Uses qwen3:8b for text conversations

Uses qwen3-vl:4b for image understanding

Streams responses directly from Ollama

Keeps normal chat independent from cloud LLM providers

Natural Live Mode

Realtime speech recognition with ElevenLabs Scribe

Hindi, English, and Hinglish language detection

Low-latency custom ElevenLabs voice responses

Short, conversational replies optimized for voice

Natural phrase buffering to avoid broken-word pronunciation

Images and documents

Keshav can work with:

Images: PNG, JPG, JPEG, WEBP, BMP, GIF

PDF files

DOCX documents

CSV files

XLSX and XLSM spreadsheets

PPTX presentations

Markdown, JSON, YAML, XML, HTML, TOML, INI, logs, scripts, and source-code files

Scanned or low-text PDF pages can be rendered and passed to the vision model for visual inspection.

Conversation management

Persistent chat history

Separate conversations

Conversation search

Rename and delete

Export conversations

Remember recent attachments for follow-up questions

Dark and light themes

Architecture

Normal Chat
User
  ↓
PySide6 Desktop UI
  ↓
Native Ollama API
  ↓
qwen3:8b / qwen3-vl:4b
  ↓
Streaming response

Live Mode
Microphone
  ↓
ElevenLabs Scribe Realtime
  ↓
Local Ollama
  ↓
ElevenLabs Streaming TTS
  ↓
Custom Keshav voice

Requirements

Windows 10 or Windows 11, 64-bit

Python 3.12

Ollama

Microphone and speakers or headphones

Internet connection for Live Mode

ElevenLabs API key

ElevenLabs Voice ID

A dedicated GPU is helpful but not required. Response speed depends on the selected model and your computer hardware.

Installation

1. Open the project folder

cd "path\to\Keshav"

2. Create a Python 3.12 virtual environment

py -3.12 -m venv .venv

3. Activate it

.\.venv\Scripts\Activate.ps1

Confirm the Python version:

python --version

It should show Python 3.12.

4. Upgrade installation tools

python -m pip install --upgrade pip setuptools wheel

5. Install dependencies

python -m pip install -r requirements.txt

Check the environment:

python -m pip check

Expected result:

No broken requirements found.

Ollama setup

Install Ollama, then download the required models:

ollama pull qwen3:8b
ollama pull qwen3-vl:4b

Confirm that they are available:

ollama list

Start Ollama when needed:

ollama serve

Model configuration

Create or edit:

config\config.toml

Recommended configuration:

[llm]
model = "qwen3:8b"
base_url = "http://127.0.0.1:11434/v1"
api_key = "ollama"
temperature = 0.0
max_tokens = 8192

[llm.vision]
model = "qwen3-vl:4b"
base_url = "http://127.0.0.1:11434/v1"
api_key = "ollama"
temperature = 0.0
max_tokens = 8192

ElevenLabs Live Mode setup

Create a .env file in the project root:

ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here

Important:

Never upload .env to GitHub.

Never paste your API key into screenshots or public issues.

Some Voice Library voices are unavailable through the API on free plans.

Use a Voice Design voice or another voice that your account can access through the API.

Running Keshav

Activate the environment:

.\.venv\Scripts\Activate.ps1

Start the desktop app from the project root:

python -m ui.main_window

Use the module command above instead of running ui\main_window.py directly. It ensures Python can correctly locate the app package.

Using Keshav

Text chat

Type a message and press Enter or use the send button.

Attachments

Use the attachment button to add images or supported documents. Keshav extracts readable text and sends visual content to the vision model when necessary.

Live Mode

Start Live Mode and speak naturally.

Keshav will:

Detect the end of your speech.

Convert your voice to text.

Generate a short response locally with Ollama.

Speak the response using your selected ElevenLabs voice.

Return to listening for the next turn.

Privacy

Keshav follows a local-first design.

Processed locally

Text generation

Image understanding

Document extraction

Conversation history

Attachment storage

Most application logic

Sent to ElevenLabs during Live Mode

Microphone audio for speech recognition

Assistant response text for voice synthesis

Normal text chat does not require ElevenLabs.

Project structure

Keshav/
├── app/
│   ├── chat.py
│   ├── chat_store.py
│   ├── schema.py
│   ├── tool/
│   └── ...
├── ui/
│   └── main_window.py
├── config/
│   └── config.toml
├── assets/
│   └── logo.jpg
├── .env
├── requirements.txt
├── LICENSE
└── README.md

Optional agent tools

The repository contains tools for browser automation, shell commands, file editing, MCP integrations, and other agent workflows.

Some tools may require additional setup, browser installation, or optional packages.

Playwright browser installation:

playwright install

Crawl4AI is currently optional because older dependency combinations may attempt to build LiteLLM from source on Windows. The desktop chat and Live Mode do not require Crawl4AI.

Troubleshooting

ModuleNotFoundError: No module named 'app'

Run Keshav from the project root using:

python -m ui.main_window

Ollama connection error

Check that Ollama is running:

ollama serve

Then verify installed models:

ollama list

Live Mode does not hear your voice

Check:

Windows microphone permissions

Default recording device

Internet connection

ElevenLabs API key permissions

ElevenLabs usage limits

Keshav does not speak

Check:

ELEVENLABS_VOICE_ID in .env

Whether the selected voice supports API use

Speaker or headphone output

ElevenLabs account quota

Syntax check

python -m py_compile app\chat.py ui\main_window.py

No output means the syntax check passed.

Dependency check

python -m pip check

Expected result:

No broken requirements found.

Security

Do not commit these files or directories:

.env
.env.backup
.venv/
.venv_voice/
__pycache__/
cache/
models/

If an API key is accidentally exposed, revoke it immediately and create a replacement.

Do not bypass Windows security protections to load blocked native libraries. Use supported alternatives instead.

Roadmap

Planned improvements may include:

Dedicated Agent Mode

More local tools

Better settings controls

Packaged Windows installer

Improved document analysis

Optional offline speech recognition

Safer tool permissions

More voice customization

License and attribution

Keshav is distributed under the MIT License.


Keshav's desktop interface, local Ollama chat pipeline, persistent conversation system, attachment handling, Live Mode, ElevenLabs speech integration, and related customizations were added or substantially modified for this project.

See LICENSE for full terms.
