# Lloyd

Lloyd is a Python desktop application for Windows that works as a personal bartender you can
talk to. The interface is built with **PyQt6**: an animated sphere that shows what Lloyd is
doing, a chat panel, and floating panels for recipe cards and cocktail builds.

You say "Hey Lloyd" and ask for a drink. The wake word is detected by **Vosk**, and your
request is transcribed by **Whisper** (faster-whisper). Both run locally. Lloyd's answers
come from **Claude** through the **Claude Agent SDK**, with a bartender persona and a set of
tools of its own. Replies are spoken sentence by sentence by a local **Piper** neural voice, so
Lloyd starts talking before the whole answer is written.

When you ask how to make a cocktail, Lloyd walks you through it one step at a time while an
animated build of the drink plays on screen. You can export the build to MP4 with **Manim**.
Lloyd can also show a full recipe card, scan your bar shelf through your phone's camera and
identify the bottles, tell the history behind a cocktail, present a top-shelf bottle, and
suggest drinks based on what you have. Recipes follow IBA Official Cocktails, Difford's Guide,
and the Cocktail Codex, in metric units.

## Project structure

```text
lloyd/
├── run.py
├── install.py
├── pyproject.toml
├── uv.lock
├── requirements.txt
├── .env.example
├── app/
│   ├── app.py
│   ├── agent/
│   │   ├── prompt.py
│   │   ├── client.py
│   │   ├── vision.py
│   │   ├── tools/
│   │   └── behaviours/
│   ├── animation/
│   ├── audio/
│   ├── config/
│   ├── core/
│   ├── network/
│   ├── render/
│   ├── threads/
│   ├── widgets/
│   └── widget_helpers/
├── icon/
├── models/
├── voices/
├── output/
└── runtime/
```

### Root files

| Path | Description |
|---|---|
| `run.py` | Starts the app |
| `install.py` | Downloads the models and creates the desktop launcher |
| `pyproject.toml` | Project metadata and dependencies, used by uv |
| `uv.lock` | Pinned dependency versions, used by uv |
| `requirements.txt` | The same dependencies, for pip |
| `.env.example` | Template for the voice settings in `.env` |

### `app/`

| Path | Description |
|---|---|
| `app/app.py` | Creates the Qt application and the main window |
| `app/agent/` | The bartender's logic and its connection to Claude |
| `app/agent/prompt.py` | Builds the system prompt: persona, response shape, sourcing rules |
| `app/agent/client.py` | Configures the Claude agent and its tool server |
| `app/agent/vision.py` | Sends shelf photos to Claude for bottle recognition |
| `app/agent/tools/` | Tools the agent can call: animation, recipe card, shelf scan, web search |
| `app/agent/behaviours/` | Answer formats that need no tool: stories, bottles, terminology, suggestions |
| `app/animation/` | Manim scene, vessels, and props for exported MP4 builds |
| `app/audio/` | Microphone capture, text-to-speech engines, voice catalog, playback |
| `app/config/` | Every constant in the app, grouped by area: voice, speech, theme, and so on |
| `app/core/` | Shared helpers: paths, text cleanup, connectivity checks, timing |
| `app/network/` | Local web server and upload page for phone photos |
| `app/render/` | Runs Manim in a separate process and caches finished videos |
| `app/threads/` | Background workers: agent, voice listener, speaker, phone server |
| `app/widgets/` | Qt widgets: main window, sphere, chat, recipe card, build canvas |
| `app/widget_helpers/` | Stylesheets, window placement, multi-monitor handling, dark title bar |

### Data folders

| Path | Description |
|---|---|
| `icon/` | Application icon for the desktop launcher |
| `models/` | Vosk and Whisper speech models, downloaded by `install.py` |
| `voices/` | Piper voice models (see [voices/README.md](voices/README.md)) |
| `output/` | Exported MP4 builds and incoming phone scans |
| `runtime/` | Launcher log and performance traces |

## Installation

### Requirements

- Windows 10 or 11. The installer and desktop launcher are Windows only.
- Python 3.12 or newer.
- A microphone and speakers.
- A Claude account. Sign in to Claude Code once (run `claude` and log in), or set
  `ANTHROPIC_API_KEY` in your environment.

### Python (pip)

```powershell
git clone <repository-url> lloyd
cd lloyd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

Create the environment in `.venv`. The desktop launcher looks for `.venv\Scripts\python.exe`.

> **This project was built with [uv](https://docs.astral.sh/uv/).** uv installs from
> `pyproject.toml` and `uv.lock`, so you get the exact package versions Lloyd was developed
> with.

### uv

```powershell
git clone <repository-url> lloyd
cd lloyd
uv sync
Copy-Item .env.example .env
```

In both cases, `Copy-Item` creates your `.env` from the template. The default settings work
without changes.

## Features

- **Hands-free voice.** An always-on wake word ("Hey Lloyd") runs locally on Vosk. Your request
  is transcribed locally by Whisper, and "Lloyd stop" cuts Lloyd off at any point.
- **Streaming speech.** Replies are spoken sentence by sentence as they are written, by a local
  Piper neural voice, so Lloyd starts talking before the answer is finished.
- **Text chat.** Everything that works by voice also works by typing.
- **Step-by-step builds.** Each cocktail gets an animated build: glass, ice, pours in the real
  ingredient colours, agitation, strain, garnish. It can be exported to MP4 with Manim.
- **Recipe cards.** A full recipe card with ingredients, colour swatches, measures, and numbered
  steps.
- **Shelf scanning.** Point your phone at your bar shelf and Lloyd identifies the bottles and
  tells you what you can make with them.
- **Bar knowledge.** Cocktail history, bottle presentations, bar terminology, and drink
  suggestions based on what you have.
- **Grounded answers.** Recipes follow IBA Official Cocktails, Difford's Guide, and the Cocktail
  Codex. All measures are metric.
- **Swappable voice.** Change Lloyd's voice by editing one line in `.env`.

> Lloyd's reasoning and bottle recognition run on Claude through the Claude Agent SDK, so they
> need an internet connection. Wake word, transcription, speech, and animation all run on your
> machine. When the connection drops, Lloyd says so in character instead of failing silently.

## Running Lloyd

Lloyd has two entry points.

### `install.py`: first-time setup

Run this once after installing the dependencies.

Python, with `.venv` activated:

```powershell
python install.py
```

uv:

```powershell
uv run install.py
```

It works through five steps and skips anything already on disk:

| Step | What it does |
|---|---|
| Download voice | Fetches the default Piper voice `en_GB-alan-medium` into `voices/` |
| Download Vosk model | Fetches and unpacks `vosk-model-small-en-us-0.15` into `models/` (wake word) |
| Download Whisper model | Fetches `faster-distil-whisper-small.en` into `models/whisper/` (transcription) |
| Create output folder | Creates `output/` for exported videos and phone scans |
| Create exe | Builds `Lloyd.exe` with PyInstaller and places it on your desktop |

The last step runs PyInstaller through `uv tool run`, so it needs `uv` on your `PATH` even if
you installed with pip. Without uv, the models are still downloaded; start Lloyd with `run.py`
instead.

After that, double-click **Lloyd** on your desktop. The launcher starts the app without a
console window and writes its output to `runtime/lloyd.log`.

### `run.py`: start the app

Starts Lloyd from a terminal, with logs printed to the console.

Python, with `.venv` activated:

```powershell
python run.py
```

uv:

```powershell
uv run run.py
```

The sphere shows "thinking" while the speech models load. When the mic button reads
**Mic: Listening**, say "Hey Lloyd".

## How Lloyd works

### Talking to Lloyd

| You do | Lloyd does |
|---|---|
| Say "Hey Lloyd", then your request | Wakes, transcribes your request, and answers aloud |
| Type in the chat box and press Enter | Same as voice, without the wake word |
| Say "Lloyd stop", or click **Stop** | Stops speaking, thinking, and rendering immediately |
| Say "clear the chat", or type `/clear` | Clears the history and starts a new conversation |
| Click the mic button | Mutes or unmutes the wake-word listener |
| Hover the speaker button | Opens the volume slider. Clicking it mutes Lloyd |
| Press `F11` or `Esc` | Toggles fullscreen. `Esc` closes an open panel first |

The sphere on the left reflects what Lloyd is doing: **idle**, **listening** (reacts to your
voice), **thinking**, **speaking** (reacts to Lloyd's voice), or **rendering** a video.

Lloyd keeps the whole conversation in context, so follow-ups like "next step", "what's next",
or "repeat that measurement" work without naming the drink again.

### Tools

Lloyd speaks first, then calls at most one tool per reply.

#### `render_animation`: step-by-step build

**Triggered by:** asking to be walked through making a drink ("Show me how to make a Negroni").

Lloyd plays an animated build of the whole cocktail in the **COCKTAIL BUILD** panel: chill
the glass, measure each ingredient in its real colour, add ice, muddle, stir or shake, strain,
and garnish. The spoken reply covers one step at a time, and you say "next step" to continue.

The spec is validated against a strict JSON schema before anything is drawn. If it fails, Lloyd
fixes it and retries once.

Click **MP4** on the panel to export the build as a video with Manim. Videos are saved to
`output/` and reused when you ask for the same drink again. To force a fresh render, include
"rerender", "redo", or "regenerate" in your request.

#### `show_recipe`: recipe card

**Triggered by:** asking what goes into a cocktail or for its recipe ("What's in a Paper
Plane?").

Opens a recipe card in the top-right corner with the glass, every ingredient with a colour
swatch and metric measure, and numbered steps with technique chips (shake, stir, single or
double strain). It is validated against the same kind of schema as the animation.

#### `scan_shelf`: bottle recognition

**Triggered by:** explicitly asking Lloyd to scan, look at, or check your shelf or counter.

1. A window opens with a QR code and a local address.
2. Scan the code with your phone. The phone must be on the same Wi-Fi network as the PC.
3. Take a photo of your shelf. It uploads to Lloyd over your local network (port `8080`).
4. Claude reads every label, groups the items into spirits, modifiers, and other, and marks
   anything it can't read clearly as uncertain.
5. Lloyd describes the shelf like a bartender reading a back bar: an overall impression, the
   spirits, the modifiers and mixers, and what you can make with them.

Lloyd never names a brand it isn't sure of. It describes the bottle by its colour and position
and asks you to confirm. The uploaded photo is deleted after analysis.

Windows may ask to allow Python through the firewall the first time. Allow it on private
networks.

#### `web_search`: current information

**Triggered by:** questions about something Lloyd doesn't already know, such as a new release,
a discontinued bottle, or a bar that opened this year.

Runs a DuckDuckGo search for up to five results, and Lloyd continues speaking with what it
finds. It is never used for classic cocktails, technique, terminology, or history. Repeated
queries are served from a small cache.

### Behaviours

These answer formats need no tool. Lloyd answers from its own knowledge.

#### Cocktail stories

**Triggered by:** "Tell me the story behind the Aviation", "Where does the Mai Tai come from?"

Lloyd tells the history as a bar historian would, in four spoken paragraphs:

1. A one-line hook that sets the era.
2. The year, city, venue, and people involved.
3. How the recipe came together.
4. Why the drink survived.

Ask for "the quick version" to get two sentences. Question whether the story is true, and
Lloyd tells the romantic version first and then the rival theory. Obscure drinks get their
rediscovery story.

#### Top-shelf bottle presentations

**Triggered by:** "Tell me about Lagavulin 16", "What makes this bottle special?"

Presented like a sommelier:

1. A short appreciation of your choice.
2. Pedigree and craft: region, age, cask, and still.
3. Nose, palate, and finish.
4. How to serve it.

Wine and liqueurs get the matching vocabulary: grape, vintage, and serving temperature. Lloyd
also answers whether a bottle is worth the price and how to mix it, and reassures newcomers
intimidated by peat or proof. For a bottle Lloyd doesn't know well, it searches the web instead
of guessing.

#### Bar knowledge

**Triggered by:** technique and terminology questions ("What's a jigger?", "Shaken or
stirred?").

Two or three sentences that give the rule and the reason behind it.

#### Suggestions

**Triggered by:** "I have gin, Campari, and a lemon. What can I make?"

Up to three classic drinks you can make with what you have, and what each one uses. If nothing
balanced is possible, Lloyd suggests a simple two-ingredient highball.

### House rules

These apply to every answer:

- **Sources:** IBA Official Cocktails, Difford's Guide, and the six Cocktail Codex root recipes.
  No invented combinations.
- **Units:** metric only: ml, g, and °C.
- **Technique:** drinks with citrus, egg white, or dairy are shaken. All-spirit drinks are
  stirred.
- **Voice:** short spoken sentences with no lists or markdown, and one sensory detail per drink.
  Stories, bottle presentations, and shelf scans are the long-form exceptions.
- **Offline:** without a connection Lloyd replies with an in-character line such as "Bar's dark
  tonight". The next message checks the connection again.

## Changing Lloyd's voice

Lloyd speaks with `en_GB-alan-medium` by default. To download other Piper voices and switch
between them in `.env`, see [voices/README.md](voices/README.md).