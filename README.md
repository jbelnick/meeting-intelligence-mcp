# Meeting Intelligence MCP Server

[![Verify](https://github.com/jbelnick/meeting-intelligence-mcp/actions/workflows/verify.yml/badge.svg)](https://github.com/jbelnick/meeting-intelligence-mcp/actions/workflows/verify.yml)

An MCP server that gives any MCP client three meeting intelligence tools:
summarize a transcript into structured notes, extract the risk surface, and
draft the follow-up message with owners and dates. It wraps the public
[meeting-intelligence-pipelines](https://github.com/jbelnick/meeting-intelligence-pipelines)
package, so the pipeline logic and this integration surface stay one
codebase apart and version together.

The tools are deterministic and read-only: same transcript in, same result
out, no model calls inside the server, nothing written anywhere. That makes
the server safe to hand to an agent and trivial to test.

## 60-second quickstart

With [uv](https://docs.astral.sh/uv/) installed, add the server to Claude
Code in one command:

```bash
claude mcp add meeting-intelligence -- uvx --from git+https://github.com/jbelnick/meeting-intelligence-mcp.git meeting-intelligence-mcp
```

Then ask Claude to use it, for example: "Summarize this meeting and draft
the follow-up" with a transcript pasted or referenced from a file.

For Claude Desktop, add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "meeting-intelligence": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/jbelnick/meeting-intelligence-mcp.git",
        "meeting-intelligence-mcp"
      ]
    }
  }
}
```

## Tools

| Tool | Returns | Use when |
|---|---|---|
| `summarize_meeting` | Title, summary, key points, decisions, risks, open questions, action items, rendered markdown | You want the full notes document |
| `extract_risks` | Risks and open questions with counts | You only care about what might go wrong |
| `draft_follow_ups` | Action items (owner, task, date) plus a paste-ready follow-up message | You want the recap message drafted |

All three accept raw transcript text. Lines in `Speaker: text` form give the
best owner attribution, but plain unattributed text works.

Input validation is deliberate: empty transcripts and transcripts over the
size limit return actionable errors that tell the caller what to do instead
of failing silently.

## Try it without an MCP client

```bash
python3 -m venv .venv && source .venv/bin/activate
make install
make demo
```

The demo runs all three tools in-process against
[examples/team_sync.txt](examples/team_sync.txt) and asserts the server
registers exactly three read-only tools. CI runs the same demo, so the
integration surface is tested on every push.

## What this shows

- An MCP server as a thin, tested integration surface over an existing
  workflow package, not a rewrite of it.
- Tool design for agents: focused tools with structured output, read-only
  annotations, clear descriptions, and errors that say what to do next.
- The dependency direction that keeps showcases honest: this repo imports
  the pipeline; the pipeline knows nothing about MCP.

## Repository layout

```text
examples/                    Synthetic example transcript
scripts/demo.py              In-process integration smoke test (CI runs it)
scripts/public_safety_scan.py  Pre-publish scanner for secrets and private paths
src/meeting_intelligence_mcp/  FastMCP server and the three tools
tests/                       Tool, validation, and server-surface tests
```

## Part Of One System

- [cerebellum-local-ai-router](https://github.com/jbelnick/cerebellum-local-ai-router):
  routing and cost control, deciding which model does the work.
- [meeting-intelligence-pipelines](https://github.com/jbelnick/meeting-intelligence-pipelines):
  the workflow this server exposes.
- [llm-judge-evals](https://github.com/jbelnick/llm-judge-evals): the eval
  pattern that gates quality when models or prompts change.

## Real vs synthetic

The example transcript is synthetic and written for this repo. No client
names, private transcripts, or operational details appear anywhere, and the
public-safety scan runs in CI to keep it that way.

## License

MIT. See [LICENSE](LICENSE).
