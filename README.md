# Chatbot Observability

A Python CLI chatbot powered by [MiniMax](https://www.minimaxi.com/) with [Langfuse](https://langfuse.com/) for full-stack LLM observability.

## Project Structure

```
├── chatbot.py     # Main loop — chat interface, history management, final answer extraction
├── llm.py         # LLM interface — API calls, message building, Langfuse tracing
├── config.py      # Configuration — env vars, Langfuse client initialization
├── .env           # Environment variables (not committed)
├── requirements.txt
└── .gitignore
```

### Files

- **`config.py`** — Loads `.env` via `python-dotenv`, initializes the Langfuse client, and exports MiniMax config (`MINIMAX_URL`, `MINIMAX_MODEL`, `MINIMAX_API_KEY`).
- **`llm.py`** — Handles LLM API calls via `requests`. The `call_llm` function is decorated with `@observe(capture_input=True, capture_output=True)` so every LLM call is automatically traced to Langfuse. Also exports message helpers (`create_system_message`, `create_user_message`, `create_assistant_message`) and `build_messages` for assembling the full message list per turn.
- **`chatbot.py`** — The main CLI loop. It keeps a conversation `history` list, builds messages per turn using `build_messages(history, user_msg)`, calls `call_llm`, and runs `extract_final_answer` to strip chain-of-thought annotations before displaying the response. Calls `langfuse.flush()` on exit.

### Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and fill in your keys

# Run the chatbot
python chatbot.py
```

### `.env` required variables

| Variable | Description |
|---|---|
| `MINIMAX_URL` | MiniMax API endpoint |
| `MINIMAX_MODEL` | Model name (e.g. `MiniMax-Text-01`) |
| `MINIMAX_API_KEY` | Your MiniMax API key |
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key |
| `LANGFUSE_BASE_URL` | Langfuse host URL (e.g. `https://cloud.langfuse.com`) |

![img1](https://github.com/nakibworkspace/chatbot-observability/blob/main/assets/img1.png?raw=true)

## Langfuse Integration

Langfuse is integrated in two places:

### 1. Automatic tracing via `@observe`

In `llm.py`, the `call_llm` function is decorated with:

```python
from langfuse import observe

@observe(capture_input=True, capture_output=True)
def call_llm(messages: list[dict], max_tokens: int = 1024) -> str:
    ...
```

Every call to `call_llm` creates a trace in Langfuse with:
- **Input** — the full message list (`[system, ...history, current user message]`)
- **Output** — the raw LLM response
- **Metadata** — model name, latency, token usage (if available from the API response)

### 2. Flush on exit

In `chatbot.py`, `langfuse.flush()` is called when the user types `exit` or `quit`:

```python
def chat():
    ...
    while True:
        ...
    langfuse.flush()
```

This ensures any buffered spans are uploaded before the process exits.

### Viewing traces

From the project directory, use the Langfuse CLI (requires `npx`):

```bash
# List last 10 traces
npx langfuse-cli --env .env api traces list --limit 10 --order-by timestamp.desc

# Get details of a specific trace
npx langfuse-cli --env .env api traces get <trace-id>

# List all prompts
npx langfuse-cli --env .env api prompts list
```


### From Langfuse UI
#### All Traces

![img1](https://github.com/nakibworkspace/chatbot-observability/blob/main/assets/img6.png?raw=true)

#### Trace View
![img1](https://github.com/nakibworkspace/chatbot-observability/blob/main/assets/img7.png?raw=true)


#### Log View
![img1](https://github.com/nakibworkspace/chatbot-observability/blob/main/assets/img8.png?raw=true)


### History management

The chatbot maintains a `history` list that grows with each turn:

```
Turn 1 → history = [user_msg_1, assistant_reply_1]
Turn 2 → history = [user_msg_1, assistant_reply_1, user_msg_2, assistant_reply_2]
...
```

Each `build_messages` call assembles `[system_prompt, ...history, current_user_msg]` — the current message is **not** prepended to history, which prevents the previous verbose chain-of-thought response from polluting the next LLM input.

`extract_final_answer` strips `<think>...` blocks and returns only the last paragraph, ensuring clean user-facing responses.

---

## Langfuse Skills in Puku

[Puku](https://puku.app/) is an AI coding assistant that reads **skills** — markdown files containing documentation references and CLI commands for specific tools. This project has the Langfuse skill installed locally.

### Installation

```bash
npx skills add langfuse/skills --skill "langfuse"
```

![img1](https://github.com/nakibworkspace/chatbot-observability/blob/main/assets/img2.png?raw=true)

This installs the skill to `.agents/skills/langfuse/`. Copy it to `.puku-cli/skills/langfuse/` for Puku's alternative convention:

```bash
cp -r .agents/skills/langfuse .puku-cli/skills/langfuse
```

### Using the skill

Ask questions in natural language. Puku will read the relevant reference guide and execute Langfuse CLI commands via `npx langfuse-cli`. Examples:

> "List my last 10 traces"

![img1](https://github.com/nakibworkspace/chatbot-observability/blob/main/assets/img3.png?raw=true)

> "Get details of trace abc123..."

![img1](https://github.com/nakibworkspace/chatbot-observability/blob/main/assets/img4.png?raw=true)

> "Analyze my recent error traces"

![img1](https://github.com/nakibworkspace/chatbot-observability/blob/main/assets/img5.png?raw=true)

### Skill structure

```
langfuse/
├── SKILL.md                    # Main skill — triggers, tools, documentation access
└── references/
    ├── cli.md                  # CLI command reference
    ├── instrumentation.md      # How to instrument LLM apps
    ├── prompt-migration.md    # Migrating prompts from code to Langfuse
    ├── user-feedback.md       # Capturing user feedback as scores
    ├── error-analysis.md       # Debugging trace errors
    ├── judge-calibration.md    # Calibrating LLM-as-Judge evaluators
    ├── sdk-upgrade.md          # Upgrading Langfuse SDK versions
    └── skill-feedback.md       # Improving the skill itself
```

### CLI access with `--env .env`

Since Puku spawns a fresh shell per command, environment variables are not inherited from your active terminal session. Always use `--env .env` to load credentials:

```bash
npx langfuse-cli --env .env api traces list --limit 5

npx langfuse-cli --env .env api traces get <trace-id>

npx langfuse-cli --env .env api prompts list
```

Without `--env .env`, the CLI will fail with authentication errors.