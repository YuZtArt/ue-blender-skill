# CLI Reference

Requires Python 3.11+ with no third-party packages. Resolve this skill's installed directory and run commands from the active project directory.

```powershell
$skillRoot = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills/ue-blender' } else { Join-Path $HOME '.codex/skills/ue-blender' }
$mcpctl = Join-Path $skillRoot 'scripts/mcpctl.ps1'
& $mcpctl doctor --server unreal
& $mcpctl preflight unreal
& $mcpctl tools unreal
& $mcpctl schema unreal monolith_discover
```

Alternatively use `python /path/to/ue-blender/scripts/mcp_cli.py` with the same arguments. On macOS/Linux use `python3` if appropriate. The PowerShell wrapper targets Windows; `MCP_CLI_PYTHON` selects its interpreter.

## Configuration

Whole server definitions are merged in this order, with later definitions winning:

1. `$CODEX_HOME/config.toml`, or `~/.codex/config.toml`.
2. The nearest `.mcp.json` from the working directory upward.
3. `--config PATH`, if supplied (JSON or TOML).

Only enabled stdio entries with `command` are loaded; HTTP/SSE is unsupported. Convenience commands use names `unreal` and `blender`; generic `call`, `tools`, and `schema` accept other names. The child server starts in the config file's directory. Use absolute paths where needed. No shell expansion or `${VAR}` interpolation is implemented. Environment is inherited with configured `env` overlaid. Generic `python`/`python3` commands resolve to the CLI's own interpreter; use an absolute Python path for a server's dedicated environment.

`servers` and `doctor` do not start servers. `doctor --server blender` checks only Blender; bare `doctor` expects both hosts. It checks the launch command, not connectivity or addon installation. `preflight` calls `monolith_status` for Unreal or `get_scene_info` for Blender. If absent, discover another small read-only tool for your server version.

## Calls

```powershell
& $mcpctl servers
& $mcpctl doctor --server blender
& $mcpctl preflight blender
& $mcpctl tools blender --filter scene
& $mcpctl schema blender get_scene_info
& $mcpctl call unreal monolith_status --intent read
& $mcpctl blender get_scene_info --intent read --user-prompt 'Inspect the current scene'
& $mcpctl call blender execute_blender_code --args-file ./mcp-args.json --intent write --user-prompt 'The original request'
```

For discovered domain actions, `ue NAMESPACE ACTION --params-file FILE` calls `NAMESPACE_query` with `action` and `params`. Use `call SERVER TOOL --args-file FILE` for other tools, including `monolith_discover`.

`--args` and `--params` also accept inline JSON objects. Prefer UTF-8 JSON files for code or complex quoting. Plain and qualified tool names are accepted. Arguments are not locally schema-validated; inspect the advertised schema first.

Always pass explicit intent. `auto` is a name heuristic and cannot identify code side effects. `--user-prompt` fills `user_prompt` only when advertised and not already provided.

## Timing And Output

`--timeout SECONDS` defaults to 30 per protocol request, not per whole invocation. Initialization defaults to 120 seconds or `startup_timeout_sec`; override with `--startup-timeout`. Listing pages and cleanup can add time. There are no automatic retries.

Output is JSON. Tool results with `isError` return `ok: false` and exit 2. A successful envelope still requires inspection of nested content and target state. MCP sampling, elicitation, and resource methods are not implemented; unsupported server requests get method-not-found.

Binary image/audio/blob blocks are saved and replaced with `saved_file` and `bytes`. `--output-dir` overrides the destination. Otherwise the nearest project config selects `Saved/McpCliArtifacts`, or the working directory receives `.mcp-cli-artifacts`.

| Exit | Meaning |
| --- | --- |
| 0 | Tool/protocol success; verify the requested result |
| 2 | Configuration, protocol, or tool error; writes may have partially applied |
| 3 | Read timeout; result not observed |
| 4 | Write timeout; outcome unknown |
| 130 | Interrupted; verify any in-flight write before retrying |

Error diagnostics may contain server stderr. Environment values are omitted from `doctor`, but arguments and diagnostics can contain sensitive data. Inspect local outputs before sharing them.
