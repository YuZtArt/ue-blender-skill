---
name: ue-blender
description: Operate live Unreal Engine through Monolith/UEMCP and Blender through BlenderMCP using a bundled CLI, focused verification, and safe timeout recovery. Use for editor inspection, asset or scene changes, screenshots, and Unreal-Blender asset transfer; file-only Blender background jobs are a separate workflow.
---

# Unreal And Blender MCP

Use the bundled `scripts/mcp_cli.py` (Python 3.11+) or Windows wrapper `scripts/mcpctl.ps1` for Unreal and Blender MCP requests. Resolve scripts relative to this skill and run them from the active project directory. No separately installed skill is required.

Read [references/commands.md](references/commands.md) for configuration, commands, and output semantics. If Python or a supported stdio server is unavailable, state the concrete gap before using an exposed direct MCP tool. Apply the same call and recovery rules to that fallback; do not switch transports merely to repeat a stalled write.

## Agent Compatibility

In OpenCode, read [references/opencode.md](references/opencode.md) before the first command. Resolve scripts from the directory of the loaded skill, not from Codex's personal directory. The same skill works in both clients; no direct MCP registration is needed when using the CLI. For first-time setup or missing dependencies, use the companion `ue-blender-setup` skill if installed.

If setup created a dedicated `ue-blender.mcp.json` in the client configuration directory, pass its absolute path with `--config` on every command, in either client. Otherwise use the existing configuration discovery rules.

## Workflow

1. Run `doctor --server unreal` or `doctor --server blender` for each needed host, then preflight hosts separately. Only required hosts need to be configured.
2. Inspect the advertised tool schema before a new operation. For Unreal, inspect `<namespace>_query` and discover the selected action's schema with `monolith_discover`; inspect that discovery tool's schema first. Never invent action parameters.
3. Keep one GUI-host request in flight across both applications. Do not parallelize calls or hide unrelated operations inside a batch.
4. Announce the intended asset or scene change. Pass explicit `--intent read` for inspection and `--intent write` for mutations, including saves and exports. This flag labels recovery behavior; it does not enforce read-only execution.
5. Keep code execution to one phase per call: inspect, calculate, mutate, save, or verify. Return a compact checkpoint. Pass the user's original request through `--user-prompt` when the Blender tool supports it.
6. Verify each change with a separate focused read or capture. Save only the intended package or Blender file when saving is in scope. Inspect returned screenshot files with an available image viewer.

CLI completion is not proof of the requested visual or behavioral result. Inspect tool content and evaluated state. Report changed assets, verification, and any uncertain operation at handoff.

## Timeouts And Recovery

The default timeout is 30 seconds per protocol request; initialization has a separate timeout. Announce inherently long operations and choose an appropriate timeout. Give meaningful updates around 30-second stalled-call checkpoints, identifying the active operation and its intent.

If the outer runner returns a session identifier, poll that session. Never launch the same command again while it is active. Read [references/recovery.md](references/recovery.md) when a call stalls or fails.

A write timeout or lost response has an unknown outcome. Do not retry until a read proves whether the change happened. A timed-out read can be retried once, with a smaller scope, after a successful lightweight preflight. Stop issuing work to a host after two failed preflights; report the last confirmed state. Do not restart the editor or addon without authorization.

## Host And Transfer Guidance

Read [references/hosts.md](references/hosts.md) for substantial scene changes, long operations, or transfers between Blender and Unreal. Targeted queries and saves are preferred; use bulk operations when the actual task requires them.

For deterministic processing of saved Blender files, background Blender CLI may be more suitable. Use `blender-batch` if installed, or a file-based workflow; this skill does not require it. Background execution cannot inspect the current editor's unsaved scene.
