---
name: ue-blender-setup
description: Initialize or repair the local Unreal/Blender MCP environment for Codex or OpenCode. Detect dependencies, install the ue-blender companion skill, configure selected MCP bridges, and verify editor connectivity. Use for a new machine, missing configuration, or migration between agent clients.
---

# Unreal And Blender Setup

Set up only the applications and agent client the user needs. This is an agent-guided setup workflow, not a bundled editor installer. The companion `ue-blender` supplies the CLI and ongoing operation rules.

## Inspect The Environment

Determine the target client, project path, required host(s), operating system, Python version, and installed editor/plugin versions. Infer from the request and local evidence; ask only for missing choices that determine the installation. Do not require Blender for Unreal-only work.

Locate this repository's sibling `ue-blender` folder, an existing installation, or the published repository at https://github.com/YuZtArt/ue-blender-skill. Read its SKILL.md. Python 3.11+ is required for the client. Reuse existing Python and MCP installations when suitable.

For OpenCode, use `opencode --version`, `opencode debug paths`, and `opencode debug skill`. Inspect only relevant MCP settings; resolved client config may contain provider credentials. For Codex, locate the configured personal skills directory and MCP configuration. Do not print secrets.

## Install Missing Components

Read [references/providers.md](references/providers.md) for upstream sources and host-specific prerequisites. Read the selected upstream's current installation instructions before choosing versions, downloads, package commands, or environment variables. Do not install an arbitrary similarly named UEMCP package.

Under the user's setup authorization, install missing components needed for the selected host. Match precompiled Unreal plugins to the engine version; if a source build is necessary, check the required compiler and SDK and explain the dependency before starting a substantial build. Do not overwrite an existing plugin or close a running editor without checking its state and the user's scope. Preserve unsaved scenes. When interactive plugin activation is required, give the exact remaining step and continue independent configuration work.

## Install Skills And Configure Connections

Install `ue-blender` alongside this setup skill in the selected client's skill directory. Include each skill's license. Back up any existing files before replacement; keep backups outside active skill discovery directories.

For OpenCode, use the config directory reported by `opencode debug paths`, with `skills/ue-blender` and `skills/ue-blender-setup`. For Codex, use `$CODEX_HOME/skills`, falling back to `~/.codex/skills`.

Prefer a dedicated local `ue-blender.mcp.json` in the client's configuration directory; use absolute server executable/script paths. Reuse verified existing server definitions rather than reconstructing them. Include only selected hosts under `mcpServers`, named `unreal` and/or `blender`, with `command`, `args`, and `env`. Preserve unrelated entries when updating an existing file, and back it up first. Do not put credentials or machine paths in the shareable skill/repository.

An OpenCode local MCP entry maps `command[0]` to command, the remaining array to args, and `environment` to env; preserve enabled state. For JSONC and layered configuration, extract only selected resolved entries from `opencode debug config`. Do not register duplicate direct MCP services unless the user wants that mode.

Use the real interpreter required by each server; dependencies in a virtual environment require that environment's absolute interpreter path. The CLI starts servers in the configuration file's directory, so resolve relative paths before copying existing configurations.

## Verify And Hand Off

Use the companion CLI with `--config` pointing to the dedicated file for every check. Run `doctor --server HOST`, then `preflight HOST`, one host at a time. Follow the companion skill's bounded timeout/recovery rules. Doctor verifies configuration, not connectivity.

Inspect result content even if `ok` is true. Connection-error text means the host is not ready. Confirm the returned Unreal project or Blender scene matches the intended target. Do not perform scene mutations as an installation test. In OpenCode, confirm both skills appear in `opencode debug skill`.

Report installed components and versions, skill/config paths, per-host connection results, and any required restart or addon activation. Give a copyable command using the actual installed paths and explicit config. Never claim the setup is ready for a host whose preflight did not succeed.
