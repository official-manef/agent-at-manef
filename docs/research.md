# Agent ecosystem review

Reviewed 11 October 2026. [README](../README.md) · [Portability](portability.md) · [Library](library.md)

This is a focused primary-documentation review, not an exhaustive audit of every source file,
release or deployed service. The implementation changes are original. No compared framework,
model weight, skill implementation or hosted runtime is bundled as a result of this review.
Research coverage must not be presented as tested integration coverage.

## Personal agents and independent OpenDot projects

| Source | Pattern worth adopting | Boundary to preserve |
|---|---|---|
| [Grok Bot](https://x.ai/news/introducing-grok-bot), [enterprise variant](https://x.ai/news/grok-bot-for-enterprise) | Stable roster, ongoing goals and visible task handoff | Hosted implementation and account isolation differ by product tier. A settings recipe is not native provisioning. |
| [Meta Muse](https://about.fb.com/ja/news/2026/09/introducing-muse-personal-ai-agent/) | Scoped access, sensitive-action approval, independent Sentinel and private credential handling | These are vendor-described protections. Adopt external enforcement as a requirement; do not claim this toolkit implements Secure VM or Sentinel. |
| [OpenAI dots](https://help.openai.com/en/articles/20001530-getting-started-with-your-dot) | Goal continuity, feedback, controls and task-specific context | Provider memory, browser sessions and local-device permissions do not transfer with a Markdown charter. Hosted dots are distinct from the Agents SDK. |
| [composio-community/open-dot](https://github.com/composio-community/open-dot) | Agent browser profiles and private credential storage | Keychain and connector accounts require their own recovery and authorization; they are not canonical context. |
| [CopilotKit/OpenDots](https://github.com/CopilotKit/OpenDots) | UI/runtime separation and durable thread state | An agent UI protocol does not establish model compatibility or native memory migration. |
| [defog-ai/opendot](https://github.com/defog-ai/opendot) | Supervisor/worker boundaries and constrained tool access | Do not inherit immediate-action defaults. Review implementation where the stated approval policy is inconsistent. |
| [vedaant00/opendot](https://github.com/vedaant00/opendot) | Recoverable local work and inspectable change history | Undoing files does not undo external side effects such as sending a message or changing a service. |

OpenDot is an ambiguous name. The listed repositories are distinct projects, not aliases for
one official platform. Select exact owner, artifact, version and license before integrating.
Their reviewed README-level patterns do not prove production readiness or license compatibility
for every component. None has been added as a native adapter in this revision.

## Harnesses, SDKs and reusable procedures

| Source | Useful lesson | Application to Agent@Manef |
|---|---|---|
| [Hermes profiles](https://hermes-agent.nousresearch.com/docs/user-guide/profiles) | Separate profile identity, settings, memory and sessions | Keep curated context recovery separate from native runtime recovery. The public output is a blueprint, not authenticated execution. |
| [OpenClaw workspace](https://github.com/openclaw/openclaw/blob/main/docs/concepts/agent-workspace.md) | Workspace files separate from configuration, credentials and sessions | Its documentation explicitly states that a workspace is not a sandbox. Isolation is a host capability, not a folder convention. |
| [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/agents/), [sessions](https://openai.github.io/openai-agents-python/sessions/), [tracing](https://openai.github.io/openai-agents-python/tracing/) | Explicit tools/handoffs, session interfaces and observability | Keep provider continuation and telemetry in the runtime. Imported source context does not grant execution permission. |
| [Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | Just-in-time retrieval, compact notes and bounded task contexts | Link relevant sources and preserve uncertainty instead of copying all history into every prompt. |
| [Agent Skills](https://agentskills.io/specification), [Anthropic skills](https://github.com/anthropics/skills) | Discover metadata first, then relevant instructions/resources | Our current Markdown-only portability is not full executable skill-bundle support. Check per-file licenses and dependencies. |
| [Vercel WorkflowAgent](https://vercel.com/kb/guide/what-is-workflowagent) | Durable steps, restart recovery, suspended approvals and bounded loops | A future MSO executor can use this pattern. Keep workflow checkpoints outside the canonical definition and make external effects idempotent before retries. |
| [Qwen-Agent](https://github.com/QwenLM/Qwen-Agent) | Modular model backends, tools and local/cloud serving | Tool parsing and sandbox behavior depend on the selected implementation. Review its executor cautions rather than equating framework support with isolation. |
| [Kimi CLI agents](https://www.kimi.com/en/help/kimi-code/cli-agents), [skills](https://www.kimi.com/en/help/kimi-code/cli-skills) | Scoped agents and progressive skill discovery | Verify actual permission inheritance and discovery precedence. A subagent name is not an independent credential boundary. |

## Providers: compatibility must be behavioral

[Z.AI function calling](https://docs.z.ai/guides/capabilities/function-calling) documents tools,
argument structures and supported selection modes. That does not imply identical forced tool
choice, parallel calls or structured output across all routes and models.

[DeepSeek Responses API](https://api-docs.deepseek.com/api/create-response/) documents stateless
behavior, full-history input and compatibility differences for roles and input types. An endpoint
using a familiar wire format does not necessarily implement the same session semantics.
[DeepSeek tool calls](https://api-docs.deepseek.com/guides/tool_calls/) and
[Qwen function calling](https://qwen.readthedocs.io/en/latest/framework/function_call.html)
also make runtime/parser choices material. [Kimi MCP](https://www.kimi.com/en/help/kimi-code/cli-mcp)
is a tool-transport contract, not a substitute for model compatibility.

This motivates the new `assess` interface: compare model, harness, host, storage and protocol
requirements independently. Missing, unknown or unsubstantiated required declarations block
compatibility. Evidence references still need independent verification and freshness checks.
This release does not run inference against these providers or certify their deployed behavior.

## Standards and instruction files

[AGENTS.md](https://agents.md/) is a plain-Markdown project instruction convention, not a required
agent-identity schema. `AGENT.md` is this toolkit's canonical charter. `SOUL.md`, `CLAUDE.md` and
`GEMINI.md` are runtime views. `SKILL.md` describes a reusable procedure; `.env` is private runtime
configuration, not portable knowledge. See [instruction files](instruction-files.md).

[MCP security guidance](https://modelcontextprotocol.io/docs/2025-11-25/tutorials/security/security_best_practices)
addresses authorization and tool boundaries. File formats, tool transport, UI events, delegation,
model behavior and VM execution are different dimensions. None should be silently substituted
for another merely to claim more platform support.

## Licensing and safety

Open source, open weights, source-available and hosted service are different categories.
[Hermes](https://github.com/NousResearch/hermes-agent/blob/main/LICENSE) and
[OpenClaw](https://github.com/openclaw/openclaw/blob/main/LICENSE) publish MIT licenses;
Qwen-Agent identifies Apache-2.0. This does not license every model, service or dependency.
Anthropic's skills README explicitly distinguishes open-source skills from source-available
document skills. Hosted Grok Bot, Muse and dots documentation does not establish a reusable
implementation license. No third-party code is copied in this contribution.

Before future reuse: select a revision, inspect its exact license and notices, review dependencies
and data handling, then test the integration. License permission is not a security assessment.
Do not strip historical attribution or advertise vendor certification that does not exist.

## Design decisions and criticism

**Keep:** a small local-first core; canonical identity separate from runtime; reviewed import;
conflict-preserving reconciliation; reversible managed-file cleanup; context-only backups;
explicit acceptance stages. Preserve old version-1 archives through the new branding.

**Improve now:** a branded library facade with one underlying implementation; declaration
assessment that exposes missing capabilities; clearer instruction-file semantics and accurate
product documentation. These are implemented/testable interfaces, not native provider integrations.

**Improve next:** split adapter registration from the filesystem core with conformance fixtures;
add real runtime acceptance for narrowly selected adapters; verify evidence provenance/freshness;
add signed/encrypted backup transport through a reviewed design; support complete licensed skill
bundles and curated catalogs; build an explicit private-context mapping for MSO consumers.

**Do not build here:** a second always-on scheduler, a hosted VM provider, a credential vault,
a clone of every personal-agent app, or an automatic social-posting system. MSO can own task
execution/UI; Agent@Manef should remain independently useful without it.

The current limits are material: Python/filesystem requirement, six file-level adapters, manual
semantic conflict review, Markdown-only skill payloads, unsigned/unencrypted archives, no native
session or account migration and no OS sandbox. Measure recovery success, retained context,
prevented overwrites, verified task outcomes and user effort, not just adapter counts.
