# MCP Providers

## Unreal: Monolith

- Repository: https://github.com/tumourlove/monolith
- Releases: https://github.com/tumourlove/monolith/releases
- Installation: https://github.com/tumourlove/monolith/wiki/Installation

The inspected upstream instructions describe project installation under `Plugins/Monolith`, with release binaries tied to the UE engine version, and source builds for supported versions. Confirm current support before installation. Do not assume any installed UE version is supported.

Use the shipped native stdio proxy when available for the platform, or the documented Python fallback. The CLI cannot directly connect to the editor's HTTP endpoint: the stdio proxy bridges it. Inspect the selected release's files and documentation for the actual executable/script path and connection settings. The bundled CLI's shorthand expects Monolith namespace/action tools; other UEMCP implementations may need generic calls and a different lightweight check.

Locally verified: Monolith 0.22.0 on UE 5.8, using the Python proxy. This is evidence from one installation, not a guarantee for all releases.

## Blender: BlenderMCP

- Repository: https://github.com/ahujasid/mcp-for-blender
- Legacy repository URL redirects here: https://github.com/ahujasid/blender-mcp

Follow the current upstream README for the Blender addon and stdio server package. Both are required: starting a server process alone does not connect the addon. Check Python/uv requirements, supported Blender versions, and actual host/port settings before generating configuration. Do not enable optional paid generation integrations for a basic setup.

The inspected local launch used `uvx --python 3.11 blender-mcp`; treat this as a local example, not a pinned installation instruction. Its bridge launched but its addon was disconnected during validation.

## Client Skill Discovery

- OpenCode skill documentation: https://opencode.ai/docs/skills/
- OpenCode MCP documentation: https://opencode.ai/docs/mcp-servers/

Use the installed client's diagnostic commands to confirm actual config paths and discovery. The companion skill's OpenCode reference documents the supported strict JSON mapping and the dedicated configuration option.
