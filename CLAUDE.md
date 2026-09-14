# Lloyd — Cybernetic Mixologist & Desktop Barman Agent

## Project Overview
Lloyd is an on-demand, voice-activated desktop AI mixologist built with Python and PyQt6.
The application combines privacy-first computer vision (on-demand webcam capture), hands-free voice interaction (JARVIS/Siri persona via the wake phrase "Lloyd"), and mixology domain intelligence powered locally by the Claude Code CLI (`claude -p`).

---

## Architectural Contracts

### 1. Frontend & Concurrency (PyQt6)
- **Framework**: PyQt6 desktop application designed with a high-contrast dark holographic HUD theme.
- **Strict Concurrency Rule**: All hardware access (camera shutter, microphone capture, speech-to-text), network lookups, and CLI subprocess execution MUST run on background threads (`QThread` or Python worker threads). 
- **Thread Safety**: Never block the Qt event loop. UI updates must be emitted across thread boundaries using Qt Signals/Slots.
- **Voice Listener**: A lightweight background audio thread continuously monitors for the wake-word trigger "Lloyd" before processing follow-up directives.

### 2. Optics & Privacy Protocol (On-Demand Capture)
- **Zero Background Streaming**: The webcam must NEVER maintain an active, continuous video feed. The camera handle (`cv2.VideoCapture`) remains uninitialized/closed while idle to protect user privacy and minimize system load.
- **Capture Lifecycle**: When explicitly triggered by a user directive (voice command or UI button):
  1. Open camera device (`cv2.VideoCapture(0)`).
  2. Discard 5 initial frames to settle auto-exposure and white balance (~150 ms).
  3. Capture a single high-resolution frame and save it to `runtime/bar_snapshot.jpg`.
  4. Immediately call `cap.release()` to turn off the hardware sensor and LED indicator.
  5. Render the static frozen frame in the UI and supply its file path to the CLI query.

### 3. Claude CLI Bridge
- **Execution Mode**: Run headless queries via the authenticated local session:
  `subprocess.run(["claude", "-p", <prompt>, "--bare"], capture_output=True, text=True, encoding="utf-8")`
- **Authentication**: Relies strictly on the local machine's authenticated Claude Pro session via Claude Code CLI. No third-party API keys or token billing.
- **Web Verification**: Claude CLI's web capabilities may be used solely for looking up verified bottle specifications (ABV, botanicals) or cross-referencing classic recipes.

---

## Mixology Guardrails & Standards

- **Ground Truth Sources**: Ground all cocktail data strictly in established mixology standards:
  - International Bartenders Association (IBA) Official Cocktails.
  - Difford's Guide tested 15-point balance standards.
  - The 6 root templates from Cocktail Codex (Old Fashioned, Martini, Manhattan, Sour, Highball, Sidecar).
- **No Hallucinated Novelties**: NEVER invent bizarre or unvetted recipes (e.g., combining dairy with clear carbonated citrus sodas, random syrup mixtures).
- **Missing Ingredients Fallback**: If available bottles are insufficient for a classic cocktail, recommend standard two-ingredient Highballs (e.g., Rum & Coke, Gin & Tonic) instead of compromising balance.
- **Technique Clarity**: Clearly distinguish between **shaken** (drinks with citrus, egg white, or dairy to aerate and chill) and **stirred** (all-spirit drinks to maintain clarity and silky viscosity).
- **Dual Units**: Provide all fluid measurements in both standard ounces and milliliters (e.g., 2 oz / 60 ml).

---

## Persona & Spoken Output Constraints

- **Identity**: Lloyd — refined, calm, dry-witted AI majordomo with deep culinary and mixology authority.
- **TTS-Optimized Responses**:
  - Keep spoken text concise (2 to 4 sentences maximum per interaction turn).
  - Do NOT output markdown asterisks (`**`), emojis, bullet characters, tables, or raw URLs in text intended for speech synthesis.
  - For multi-step preparation, break the recipe down into bite-sized checkpoints rather than delivering an uninterrupted monologue.

---

## Command Registry (Strict Initial Scope)

During this phase, input parsing and output behavior are strictly restricted to the following supported directives:

### 1. Vision & Inventory
- `"Lloyd, scan the bar"` / `"Lloyd, what's on the counter?"`
  - *Action*: Triggers the on-demand camera capture lifecycle, inspects `runtime/bar_snapshot.jpg`, and lists identified spirits, mixers, and barware.

### 2. Recipe & Lore Lookup
- `"Lloyd, show me the recipe for [cocktail]"`
  - *Action*: Displays measurements, glassware, ice recommendations, and technique in the HUD.
- `"Lloyd, tell me the story behind [cocktail]"`
  - *Action*: Provides a concise historical and cultural background of the classic drink (maximum 3 sentences).
- `"Lloyd, show me how to make [cocktail]"`
  - *Action*: Prepares the UI recipe card and triggers step-by-step guidance mode.

### 3. Step-by-Step Guidance
- `"Lloyd, step one"`
  - *Action*: Provides the first ingredient to measure into the shaker/mixing glass (least expensive ingredients first: syrups and citrus).
- `"Lloyd, next step"`
  - *Action*: Advances to the subsequent addition, agitation, or straining step.
- `"Lloyd, repeat that measurement"`
  - *Action*: Restates the exact volume of the active ingredient in ounces and milliliters.

### 4. Adjustments & Science
- `"Lloyd, shake or stir?"`
  - *Action*: Explains the recommended agitation technique and the physical rationale (dilution/aeration vs. texture/clarity).
- `"Lloyd, substitute [ingredient]"`
  - *Action*: Offers proven classic substitutes with exact ratio compensations.
- `"Lloyd, scale this for [N] people"`
  - *Action*: Recalculates batch volume and factors in ~15-20% calculated dilution.
- `"Lloyd, this tastes too [sour / sweet / strong]"`
  - *Action*: Offers immediate balancing adjustments (e.g., barspoon of syrup, dash of citrus, dilution water).

> **Extensibility Notice**: This command set represents the initial strict baseline. Additional voice directives, hardware integrations, animation triggers, and inventory tracking commands will be added incrementally in subsequent development phases. 