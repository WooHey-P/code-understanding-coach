# Conversation scenarios

The skill is a set of instructions, so its behavior only shows up in real conversations.
This folder replays scripted multi-turn conversations against a coding agent and records
what happened.

| File | Purpose |
|---|---|
| `scenarios.json` | Scenario definitions: fixed user turns, simulated-developer turns, code mutations |
| `oracle.md` | Hand-written facts about the fixture. Given only to the simulated developer |
| `run.py` | The runner |
| `CHECKLIST.md` | What a human checks in each transcript |
| `../fixtures/book-rental/` | Synthetic project the skill examines |
| `recorded/` | Transcripts behind the README demo GIFs (`DEMO-en`, `DEMO-ko` runs), kept so the GIFs can be traced and re-rendered |

## What is automatic and what is not

**Automatic** (`run.py`, per scenario): whether the skill triggered as expected; write-tool
attempts; shell commands that write, execute code, or run Git; files changed by the
agent; reads of the fixture's `.env`; the `.env` canary appearing anywhere.

**Manual** (`CHECKLIST.md`): one question per message, no answer leakage, correct
grading of correct / partial / wrong answers, transfer questions, summaries.

## Running

Requirements: Python 3.9+, and the agent CLI (`claude` or `codex`) installed and signed
in. **Each run makes real model calls** on your plan or API account — roughly one call
per turn plus one per simulated answer.

```sh
python3 tests/scenarios/run.py --agent claude --scenario S1          # one scenario
python3 tests/scenarios/run.py --agent claude --scenario all --jobs 4
python3 tests/scenarios/run.py --agent codex  --scenario all --jobs 4
```

Results land in `tests/scenarios/results/<timestamp>/` (git-ignored):
`summary-<agent>.md`, and per scenario `transcript.md`, `result.json`, `events.jsonl`.

## Isolation

- The fixture is copied to a fresh temporary directory per scenario, and the skill is
  installed there at **project scope** (`.claude/skills/` or `.agents/skills/`). Nothing
  is installed globally and your real projects are never touched.
- Claude runs use `--setting-sources project --strict-mcp-config`, so your personal
  settings, personal skills, plugins, and MCP servers are not loaded.
- Codex runs use `--sandbox read-only`. Codex still loads your user-level skills and
  instructions; keep that in mind when reading results.
- Simulated-developer answers come from a separate `claude -p` call in an empty
  directory. It sees `oracle.md` and the assistant's last message, never the project.

## README demo GIFs

`docs/assets/demo-*.gif` are rendered from real runs of the `DEMO-en` / `DEMO-ko`
scenarios, never written by hand:

```sh
python3 tests/scenarios/run.py --agent claude --scenario DEMO-en,DEMO-ko
cp tests/scenarios/results/<run>/claude/DEMO-en/transcript.md tests/scenarios/recorded/demo-en.md
pip install pillow   # in a virtual environment; development only
python3 scripts/render_demo.py tests/scenarios/recorded/demo-en.md docs/assets/demo-en.gif
```

The renderer removes markdown markers and summarizes tool calls as one status line; the
words are the agent's output.

## Limits

- Model output varies between runs. One passing run is an observation, not a guarantee.
- The simulated developer may not hit the intended level exactly (for example a
  "partial" answer that accidentally includes the cause). Check its note in the
  transcript before blaming the skill.
- The scenario "the assistant asked a question with a false premise, and the developer
  points it out" cannot be produced by replay; it needs a hand-made conversation.
