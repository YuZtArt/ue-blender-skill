# Unreal And Blender MCP Skill

[中文](README.md) | English

A single Codex skill for live Unreal Engine and Blender editors. It merges `ue-blender-mcp-cli` and `reliable-ue-blender-mcp`: a bundled stdio CLI handles discovery and calls; unified instructions handle sequencing, verification, and uncertain outcomes.

## Skills And OpenCode

- `ue-blender`: ongoing live-editor operations, verification, and recovery.
- `ue-blender-setup`: agent-guided dependency installation, local connection configuration, and read-only validation. It does not bundle editors or promise unattended plugin installation.

For OpenCode, copy both folders from `skills/` into `~/.config/opencode/skills/` (or the config directory reported by `opencode debug paths`). Verify discovery with `opencode debug skill`, then ask: "Use ue-blender-setup to initialize Unreal MCP for this project."

The CLI accepts explicit dedicated connection files and strict OpenCode JSON local MCP entries. JSONC, variable substitution, and layered settings require a resolved export containing only the relevant MCP entries. See [OpenCode instructions](skills/ue-blender/references/opencode.md).

Verified locally: skill discovery on OpenCode 1.18.22, and a live Monolith 0.22.0 / UE 5.8 read. The Blender bridge launched but its addon was disconnected; Blender end-to-end operation remains unverified.

Upstreams: [Monolith](https://github.com/tumourlove/monolith), [BlenderMCP](https://github.com/ahujasid/mcp-for-blender). See [setup providers](skills/ue-blender-setup/references/providers.md) for version and installation guidance.

## Requirements

- Python 3.11+ for the CLI, using only the standard library.
- Unreal Monolith/UEMCP and/or BlenderMCP installed and configured separately, with the relevant editor and addon running.
- A stdio MCP server named `unreal` or `blender`. Only the host you use is required. HTTP/SSE configurations require an available direct MCP fallback.
- Codex or another agent able to load `SKILL.md` and execute commands.

This repository does not install editors, MCP servers, or addons. Unreal convenience commands assume Monolith's namespace/action API; generic calls use advertised tools.

## Install

For Codex, clone the repository and copy both `skills/ue-blender` and `skills/ue-blender-setup` into your personal skills directory.

Windows PowerShell:

```powershell
git clone https://github.com/YuZtArt/ue-blender-skill.git
$skillParent = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $HOME '.codex/skills' }
New-Item -ItemType Directory -Force $skillParent | Out-Null
Copy-Item -Recurse ./ue-blender-skill/skills/ue-blender $skillParent
Copy-Item -Recurse ./ue-blender-skill/skills/ue-blender-setup $skillParent
```

macOS/Linux:

```bash
git clone https://github.com/YuZtArt/ue-blender-skill.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R ue-blender-skill/skills/ue-blender ue-blender-skill/skills/ue-blender-setup "${CODEX_HOME:-$HOME/.codex}/skills/"
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
