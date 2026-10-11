# Getting started

[README](../README.md) · [Migration](migration.md) · [CLI reference](cli.md)

## 1. Separate tooling from your context

Clone this public toolkit. Keep your own agent workspace in a separate private directory or private repository. A public fork is suitable for improving generic code; it is not a safe default place for your personal agent knowledge.

The CLI needs Python 3.10 or newer. It uses only the Python standard library. Commands below run from the toolkit checkout; alternatively install that source with `python -m pip install -e .` and use the `agent-ssot` command. No PyPI release is assumed.

```sh
python --version
python -m agent_at_manef --help
python -m agent_at_manef init --target ../my-agent-context
python -m agent_at_manef init --target ../my-agent-context --apply
python -m agent_at_manef doctor --workspace ../my-agent-context
```

The preview returns JSON and leaves the requested destination absent. The apply creates `workspace.json`, a fictional researcher charter/descriptor/context and shared operating rules. Doctor returns `ok: true`, the canonical agent IDs and file count. It does not check accounts or a running model.

On Windows use `py -3` in place of `python` when needed. In PowerShell, enter examples with shell line continuations as a single line. Use normal absolute or relative paths, not a path to an existing global `.hermes`, `.codex` or `.claude` directory. On macOS/Linux `python3` may be the correct command.

## 2. Define a real role deliberately

Edit the researcher files or add another identity. Choose a stable lowercase ID, one accountable owner and a bounded mission.

```sh
python -m agent_at_manef new --workspace ../my-agent-context --id writer --name Writer --owner editorial --mission "Draft source-backed documentation for review"
python -m agent_at_manef new --workspace ../my-agent-context --id writer --name Writer --owner editorial --mission "Draft source-backed documentation for review" --apply
```

`--credential-name` may be repeated for verified runtime variable names, never values. There is no automatic Gmail account, provider account, model assignment or parent credential inheritance. See [agent specification](agent-spec.md).

Fill the charter's responsibilities, non-goals and acceptance. Curate project context with dates and source references. Add shared Markdown policies, decisions and procedures only when needed. Empty headings are not complete knowledge.

## 3. Render a platform view

```sh
python -m agent_at_manef render --workspace ../my-agent-context --platform gemini --target ../gemini-view
python -m agent_at_manef render --workspace ../my-agent-context --platform gemini --target ../gemini-view --apply
python -m agent_at_manef verify --target ../gemini-view
```

Use `--agent writer` to select one agent, or repeat it for several. The generated per-agent directory contains its own canonical files plus shared policies/decisions/skills. It does not include unrelated agents' personal context, although shared documents must themselves be appropriately scoped.

Open the generated agent directory in the actual runtime. Follow [platform instructions](platforms.md). A filesystem output is not a native application registration, process, or account login.

## 4. Accept before using for consequential work

Ask the agent to identify its owner, mission, scope, sources, unresolved context, and permitted actions. Perform one authorized read-only service test, then one bounded task. Start a second session and verify the same identity/context and required state. Record results using [acceptance](acceptance.md).

If the platform has no filesystem, load reviewed files through its authorized connector or attachment interface and report context-loaded mode. Never claim a local install occurred in a chat-only surface.
