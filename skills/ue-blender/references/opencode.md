# OpenCode

Install this folder under `~/.config/opencode/skills/ue-blender`, or the config directory reported by `opencode debug paths`. For a project-local installation use `.opencode/skills/ue-blender`. Check discovery with `opencode debug skill`. Ask OpenCode to load the `ue-blender` skill; Codex's dollar invocation syntax is not required.

Resolve `scripts/mcp_cli.py` from the loaded skill's directory and run it through the available shell. On Windows the bundled `mcpctl.ps1` is also available.

## Connection Configuration

Use an explicit `--config ABSOLUTE_PATH` on every command in OpenCode. Prefer a dedicated `ue-blender.mcp.json` in OpenCode's config directory when present. This file uses `mcpServers` with `command`, `args`, and `env`; the setup skill can create it without touching provider credentials or unrelated MCP entries.

Alternatively, the CLI accepts strict OpenCode JSON with `mcp` entries of `type: local`, command arrays, `environment`, and `enabled`. It does not auto-discover OpenCode configs, parse JSONC, perform OpenCode variable substitution, or merge OpenCode's project layers. Remote entries are unsupported. For JSONC or layered configuration, use `opencode debug config` and extract only the relevant resolved `mcp` entries to a private strict JSON file, without printing or publishing the full resolved configuration. Check that environment substitutions are resolved before use.

Example OpenCode JSON shape (replace paths before use):

```json
{"mcp":{"unreal":{"type":"local","command":["/absolute/path/to/monolith_proxy"],"enabled":true}}}
```

Commands from the active project directory:

```text
python /installed/ue-blender/scripts/mcp_cli.py doctor --server unreal --config /private/ue-blender.mcp.json
python /installed/ue-blender/scripts/mcp_cli.py preflight unreal --config /private/ue-blender.mcp.json
```

Use names `unreal` and `blender` for convenience commands. Generic commands accept other server names. The explicit file overrides matching discovered Codex/project definitions. A local CLI bridge is sufficient; duplicating it as a direct OpenCode MCP service is optional.

## Verified Scope

OpenCode 1.18.22 on Windows discovered the skill. The CLI reached a live Monolith 0.22.0 host. Blender's bridge launched, but its addon was disconnected; end-to-end Blender operation was not verified. A response can contain an error in text while `isError` is false: always inspect content and do not report a successful connection from the envelope alone.
