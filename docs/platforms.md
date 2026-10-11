# Platform support matrix

[README](../README.md) · [Acceptance](acceptance.md)

Documentation checked **11 October 2026**. Runtime APIs and loading rules can change; compare these references with your installed version. Adapter output is tested locally and in CI. That does not certify end-to-end model execution on every vendor platform.

| Platform | Generated view | Automation level |
|---|---|---|
| Generic | Per-agent AGENTS.md, own context and shared Markdown | Explicit context loading |
| Codex | Per-agent AGENTS.md | Context-file preparation |
| Claude Code | Per-agent CLAUDE.md plus project `.claude/agents/<id>.md` restricted to reading | Definition-file preparation; verify native discovery |
| Gemini CLI | Per-agent GEMINI.md | Context-file preparation |
| Hermes | SOUL.md, YAML-compatible profile metadata, context, empty example and setup notes | Blueprint for an explicitly created native profile |
| Grok Bot | Name/title/description JSON, persona and setup notes | Application-settings recipe, not an import API |

## Codex

Open the rendered `agents/<id>/` directory as the relevant workspace. Read and verify the loaded AGENTS.md. Parent/global instructions and runtime permissions still apply. This toolkit does not write global Codex settings or register an orchestration graph. [Official AGENTS.md guidance](https://developers.openai.com/codex/guides/agents-md).

## Claude Code

Open the rendered root to discover the project-local `.claude/agents/` definitions, or the individual agent folder for its CLAUDE.md. Definitions allow Read/Grep/Glob only for onboarding. Their runtime parent-child shape does not create a business reporting line or a credential grant. Verify actual discovery and behavior in the installed version. [Official subagent guidance](https://code.claude.com/docs/en/sub-agents).

## Gemini CLI

Open the selected agent folder and inspect its loaded GEMINI.md context. Source links are relative to that folder. Recheck the actual memory/context state rather than assuming that file existence equals loading. [Official GEMINI.md guidance](https://geminicli.com/docs/cli/gemini-md/).

## Hermes

Create a fresh native profile through the installed Hermes version's supported mechanism. Review the generated SOUL.md and profile metadata, point the profile at its intended workspace, and configure provider/tools privately. The public toolkit does not install Hermes, copy an existing `.env`, move session databases or claim native registration. Use the platform's supported private backup/distribution path when you also require native recovery. [Profiles](https://hermes-agent.nousresearch.com/docs/user-guide/profiles) · [Configuration](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) · [Profile distributions](https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions).

## Grok Bot

Inspect the actual app roster to avoid duplicate bots. Apply the reviewed name/title/description through supported app controls and load the persona/context. Do not treat `profile-fields.json` as a guaranteed REST import payload. No hosted bot is created by this CLI. Public template sharing is a separate explicit publication action; never use it as a shortcut to move private context. [Create/manage Bots](https://docs.x.ai/grok-bot/bots) · [Templates](https://x.ai/bot/guides/templates-for-grok-bot).

Grok's public description states that bots belonging to one user share their persistent computer, files, browser and logins. Folder or env-name separation is not per-bot credential isolation. Recheck the account/product boundary before moving sensitive work. [Official shared-computer FAQ](https://x.ai/bot).

## Other platforms

Use the generic adapter. Load reviewed text through a supported workspace, attachment or connector. Report connector-only/context-loaded mode when filesystem installation is unavailable. No single repository can force identical model behavior or transfer an app's hidden/provider-side state.
