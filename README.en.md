# Unreal And Blender MCP Skill

[中文](README.md) | English

A single Codex skill for live Unreal Engine and Blender editors. It merges `ue-blender-mcp-cli` and `reliable-ue-blender-mcp`: a bundled stdio CLI handles discovery and calls; unified instructions handle sequencing, verification, and uncertain outcomes.

## Requirements

- Python 3.11+ for the CLI, using only the standard library.
- Unreal Monolith/UEMCP and/or BlenderMCP installed and configured separately, with the relevant editor and addon running.
- A stdio MCP server named `unreal` or `blender`. Only the host you use is required. HTTP/SSE configurations require an available direct MCP fallback.
- Codex or another agent able to load `SKILL.md` and execute commands.

This repository does not install editors, MCP servers, or addons. Unreal convenience commands assume Monolith's namespace/action API; generic calls use advertised tools.

## Install

Clone the repository and copy **only `skills/ue-blender`** into your personal skills directory.

Windows PowerShell:

```powershell
git clone https://github.com/YuZtArt/ue-blender-skill.git
$skillParent = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $HOME '.codex/skills' }
New-Item -ItemType Directory -Force $skillParent | Out-Null
Copy-Item -Recurse ./ue-blender-skill/skills/ue-blender $skillParent
```

macOS/Linux:

```bash
git clone https://github.com/YuZtArt/ue-blender-skill.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R ue-blender-skill/skills/ue-blender "${CODEX_HOME:-$HOME/.codex}/skills/"
```

For updates, replace the existing `ue-blender` folder with the new version. If either predecessor is installed, move its folder outside the active skills directory after installing the replacement. Keeping all three active creates overlapping routing instructions. Start a new agent session to load the skill.

Example: `Use $ue-blender to inspect the current Blender scene and verify its scale before exporting to Unreal.`

## Configure And Check

Reuse your Codex `config.toml` or project `.mcp.json`. Server commands must point to your own installed MCP bridge. This JSON shows the configuration shape, not an installable server distribution:

```json
{
  "mcpServers": {
    "blender": {
      "command": "python",
      "args": ["/absolute/path/to/your/blender_mcp_server.py"]
    }
  }
}
```

From your active project directory, run the installed script:

```text
python /path/to/ue-blender/scripts/mcp_cli.py doctor --server blender
python /path/to/ue-blender/scripts/mcp_cli.py preflight blender
```

On Windows, `scripts/mcpctl.ps1` locates Python; set `MCP_CLI_PYTHON` if needed. On macOS/Linux use `python3` when appropriate. See the [command reference](skills/ue-blender/references/commands.md) for precedence, discovery, timing, and output semantics.

## Behavior And Limits

- Sequential calls, schema discovery, and explicit read/write intent.
- Separate verification after mutations and focused asset/file saves.
- Screenshots extracted to local files.
- Bounded read retries and write-outcome verification after lost responses.
- Host-specific guidance and staged asset transfers.

Intent is a label, not a sandbox. The client does not implement a cross-process lock, transactions, or editor-side cancellation. Follow the recovery instructions. Saved-file Blender background processing is a separate workflow; the `blender-batch` skill is optional, not a dependency.

## Validation

```text
python -m unittest discover -s tests -v
```

Tests use a fake local stdio server and temporary configurations, without connecting to editors. They exercise configuration precedence, single-host diagnostics, tool calls and errors, lost responses, timeouts, and binary output. Passing tests does not certify every editor/server version; use a read-only preflight against your installation.

Do not commit local MCP configurations, credentials, editor assets, or generated captures.

## License

Released under the [MIT License](LICENSE). External editors, MCP servers, and addons retain their own licenses. Include the license when redistributing the skill or its scripts.
