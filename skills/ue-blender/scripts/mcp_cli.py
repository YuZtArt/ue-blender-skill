#!/usr/bin/env python3
"""Small, dependency-free stdio MCP client for Unreal and Blender hosts."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import queue
import subprocess
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit("mcpctl requires Python 3.11 or newer") from exc


PROTOCOL_VERSION = "2025-03-26"
READ_PREFIXES = (
    "get_", "list_", "search_", "find_", "read_", "describe_", "compare_",
    "validate_", "analyze_", "audit_", "export_", "check_", "ping", "poll_",
)


class CliError(Exception):
    pass


class RpcTimeout(CliError):
    pass


@dataclass
class ServerConfig:
    name: str
    command: str
    args: list[str]
    env: dict[str, str]
    cwd: Path
    source: Path
    startup_timeout: float = 120.0


def _json_object(value: str, label: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise CliError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise CliError(f"{label} must be a JSON object")
    return parsed


def _nearest_project_config(start: Path) -> Path | None:
    current = start.resolve()
    for directory in (current, *current.parents):
        candidate = directory / ".mcp.json"
        if candidate.is_file():
            return candidate
    return None


def _codex_config() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    return Path(codex_home) / "config.toml" if codex_home else Path.home() / ".codex" / "config.toml"


def _parse_json_config(path: Path) -> dict[str, ServerConfig]:
    try:
        document = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CliError(f"cannot read MCP config {path}: {exc}") from exc
    if "mcpServers" in document:
        return _normalize_servers(document["mcpServers"], path)
    # OpenCode JSON, including the resolved output of `opencode debug config`.
    converted = {}
    for name, raw in document.get("mcp", {}).items():
        if not isinstance(raw, dict) or raw.get("type") != "local":
            continue
        command = raw.get("command", [])
        if not isinstance(command, list) or not command or not all(isinstance(x, str) for x in command):
            raise CliError(f"OpenCode server {name!r} has invalid command array")
        converted[name] = {"command": command[0], "args": command[1:],
                           "env": raw.get("environment", {}),
                           "enabled": raw.get("enabled", True)}
    return _normalize_servers(converted, path)


def _parse_toml_config(path: Path) -> dict[str, ServerConfig]:
    try:
        with path.open("rb") as handle:
            document = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise CliError(f"cannot read MCP config {path}: {exc}") from exc
    return _normalize_servers(document.get("mcp_servers", {}), path)


def _normalize_servers(raw_servers: Any, source: Path) -> dict[str, ServerConfig]:
    result: dict[str, ServerConfig] = {}
    if not isinstance(raw_servers, dict):
        return result
    for name, raw in raw_servers.items():
        if not isinstance(raw, dict) or raw.get("enabled") is False:
            continue
        command = raw.get("command")
        if not isinstance(command, str) or not command:
            continue
        args = raw.get("args", [])
        env = raw.get("env", {})
        if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
            raise CliError(f"server {name!r} in {source} has invalid args")
        if not isinstance(env, dict):
            raise CliError(f"server {name!r} in {source} has invalid env")
        result[str(name)] = ServerConfig(
            name=str(name), command=command, args=args,
            env={str(key): str(value) for key, value in env.items()},
            cwd=source.parent, source=source,
            startup_timeout=float(raw.get("startup_timeout_sec", 120)),
        )
    return result


def load_servers(explicit: str | None = None) -> tuple[dict[str, ServerConfig], Path | None]:
    configs: list[Path] = []
    global_config = _codex_config()
    if global_config.is_file():
        configs.append(global_config)
    project_config = _nearest_project_config(Path.cwd())
    if project_config and project_config not in configs:
        configs.append(project_config)
    if explicit:
        explicit_path = Path(explicit).expanduser().resolve()
        if not explicit_path.is_file():
            raise CliError(f"config file does not exist: {explicit_path}")
        configs.append(explicit_path)

    servers: dict[str, ServerConfig] = {}
    for path in configs:
        parsed = _parse_toml_config(path) if path.suffix.lower() == ".toml" else _parse_json_config(path)
        servers.update(parsed)
    return servers, project_config


class McpClient:
    def __init__(self, config: ServerConfig, startup_timeout: float | None = None):
        self.config = config
        self.startup_timeout = startup_timeout or config.startup_timeout
        self.process: subprocess.Popen[bytes] | None = None
        self.stdout_queue: queue.Queue[bytes | None] = queue.Queue()
        self.stderr_tail: deque[str] = deque(maxlen=20)
        self.next_id = 1

    def __enter__(self) -> "McpClient":
        command = self.config.command
        if Path(command).name.lower() in {"python", "python.exe", "python3", "python3.exe"}:
            command = sys.executable
        env = os.environ.copy()
        env.update(self.config.env)
        try:
            self.process = subprocess.Popen(
                [command, *self.config.args], cwd=self.config.cwd, env=env,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
        except OSError as exc:
            raise CliError(f"failed to start server {self.config.name!r}: {exc}") from exc
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()
        try:
            self._request(
                "initialize",
                {"protocolVersion": PROTOCOL_VERSION, "capabilities": {},
                 "clientInfo": {"name": "mcpctl", "version": "1.0.0"}},
                self.startup_timeout,
            )
            self._notify("notifications/initialized", {})
        except Exception:
            self.__exit__()
            raise
        return self

    def __exit__(self, *_: object) -> None:
        if not self.process:
            return
        if self.process.stdin:
            try:
                self.process.stdin.close()
            except OSError:
                pass
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)

    def _read_stdout(self) -> None:
        assert self.process and self.process.stdout
        for line in iter(self.process.stdout.readline, b""):
            self.stdout_queue.put(line)
        self.stdout_queue.put(None)

    def _read_stderr(self) -> None:
        assert self.process and self.process.stderr
        for line in iter(self.process.stderr.readline, b""):
            self.stderr_tail.append(line.decode("utf-8", errors="replace").rstrip())

    def _send(self, message: dict[str, Any]) -> None:
        assert self.process and self.process.stdin
        payload = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
        try:
            self.process.stdin.write(payload)
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise CliError(f"server {self.config.name!r} closed its input") from exc

    def _notify(self, method: str, params: dict[str, Any]) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def _request(self, method: str, params: dict[str, Any], timeout: float) -> Any:
        request_id = self.next_id
        self.next_id += 1
        self._send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RpcTimeout(f"{method} exceeded {timeout:g} seconds")
            try:
                line = self.stdout_queue.get(timeout=remaining)
            except queue.Empty as exc:
                raise RpcTimeout(f"{method} exceeded {timeout:g} seconds") from exc
            if line is None:
                detail = self.stderr_tail[-1] if self.stderr_tail else "no server diagnostic"
                raise CliError(f"server exited before replying: {detail}")
            try:
                message = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if message.get("id") != request_id:
                if "id" in message and "method" in message:
                    self._send({"jsonrpc": "2.0", "id": message["id"],
                                "error": {"code": -32601, "message": "Unsupported client method"}})
                continue
            if "error" in message:
                error = message["error"]
                raise CliError(f"MCP error {error.get('code')}: {error.get('message')}")
            return message.get("result")

    def list_tools(self, timeout: float) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            result = self._request("tools/list", {"cursor": cursor} if cursor else {}, timeout)
            tools.extend(result.get("tools", []))
            cursor = result.get("nextCursor")
            if not cursor:
                return tools

    def call_tool(self, name: str, arguments: dict[str, Any], timeout: float) -> Any:
        return self._request("tools/call", {"name": name, "arguments": arguments}, timeout)


def _resolve_server(servers: dict[str, ServerConfig], name: str) -> ServerConfig:
    if name not in servers:
        available = ", ".join(sorted(servers)) or "none"
        raise CliError(f"MCP server {name!r} is not configured; available: {available}")
    return servers[name]


def _plain_tool_name(server: str, name: str) -> str:
    prefix = f"mcp__{server}__"
    return name[len(prefix):] if name.startswith(prefix) else name


def _find_tool(tools: list[dict[str, Any]], server: str, requested: str) -> dict[str, Any]:
    plain = _plain_tool_name(server, requested)
    for tool in tools:
        if tool.get("name") == plain:
            return tool
    names = ", ".join(sorted(str(item.get("name")) for item in tools)[:20])
    raise CliError(f"tool {plain!r} was not advertised by {server!r}; first available tools: {names}")


def _infer_intent(tool: str, arguments: dict[str, Any]) -> str:
    candidate = str(arguments.get("action", "")) or tool
    if candidate.startswith(READ_PREFIXES) or candidate in {"monolith_status", "monolith_discover", "monolith_guide"}:
        return "read"
    return "write"


def _artifact_root(project_config: Path | None, requested: str | None) -> Path:
    if requested:
        return Path(requested).expanduser().resolve()
    if project_config:
        return project_config.parent / "Saved" / "McpCliArtifacts"
    return Path.cwd() / ".mcp-cli-artifacts"


def _materialize_binary(value: Any, root: Path, stem: str, counter: list[int]) -> Any:
    if isinstance(value, list):
        return [_materialize_binary(item, root, stem, counter) for item in value]
    if not isinstance(value, dict):
        return value
    block_type = value.get("type")
    data = value.get("data")
    if block_type in {"image", "audio", "blob"} and isinstance(data, str):
        try:
            decoded = base64.b64decode(data, validate=True)
        except ValueError:
            return {key: _materialize_binary(item, root, stem, counter) for key, item in value.items()}
        root.mkdir(parents=True, exist_ok=True)
        counter[0] += 1
        mime = str(value.get("mimeType", "application/octet-stream"))
        suffix = mimetypes.guess_extension(mime) or ".bin"
        path = root / f"{stem}-{int(time.time())}-{counter[0]}{suffix}"
        path.write_bytes(decoded)
        replacement = {key: item for key, item in value.items() if key != "data"}
        replacement.update({"saved_file": str(path), "bytes": len(decoded)})
        return replacement
    return {key: _materialize_binary(item, root, stem, counter) for key, item in value.items()}


def _emit(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _call(config: ServerConfig, server_name: str, tool_name: str,
          arguments: dict[str, Any], intent_option: str, user_prompt: str | None,
          timeout: float, startup_timeout: float | None,
          artifact_root: Path) -> tuple[dict[str, Any], int]:
    plain_name = _plain_tool_name(server_name, tool_name)
    intent = _infer_intent(plain_name, arguments) if intent_option == "auto" else intent_option
    started = time.monotonic()
    client = McpClient(config, startup_timeout)
    try:
        with client:
            tools = client.list_tools(timeout)
            tool = _find_tool(tools, server_name, plain_name)
            properties = tool.get("inputSchema", {}).get("properties", {})
            if user_prompt is not None and "user_prompt" in properties and "user_prompt" not in arguments:
                arguments["user_prompt"] = user_prompt
            result = client.call_tool(plain_name, arguments, timeout)
    except RpcTimeout as exc:
        elapsed = round((time.monotonic() - started) * 1000, 1)
        unknown = intent == "write"
        return ({"ok": False, "server": server_name, "tool": plain_name,
                 "intent": intent, "code": "timeout",
                 "outcome": "unknown" if unknown else "not_observed",
                 "elapsed_ms": elapsed, "error": str(exc),
                 "stderr_tail": list(client.stderr_tail)}, 4 if unknown else 3)
    except (CliError, OSError) as exc:
        return ({"ok": False, "server": server_name, "tool": plain_name,
                 "intent": intent, "code": "error",
                 "outcome": "unknown" if intent == "write" else "not_observed",
                 "error": str(exc), "stderr_tail": list(client.stderr_tail)}, 2)
    result = _materialize_binary(result, artifact_root, f"{server_name}-{plain_name}", [0])
    if isinstance(result, dict) and result.get("isError"):
        return ({"ok": False, "server": server_name, "tool": plain_name,
                 "intent": intent, "code": "tool_error",
                 "outcome": "unknown" if intent == "write" else "not_observed",
                 "result": result}, 2)
    return ({"ok": True, "server": server_name, "tool": plain_name,
             "intent": intent, "elapsed_ms": round((time.monotonic() - started) * 1000, 1),
             "result": result}, 0)


def _add_connection_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", help="additional JSON or TOML MCP config")
    parser.add_argument("--timeout", type=float, default=30.0, help="tool/list call timeout in seconds")
    parser.add_argument("--startup-timeout", type=float, help="server initialization timeout in seconds")


def _add_call_options(parser: argparse.ArgumentParser, params_name: str = "args") -> None:
    parser.add_argument(f"--{params_name}", default="{}", help="JSON object")
    parser.add_argument(f"--{params_name}-file", help="UTF-8 file containing a JSON object")
    parser.add_argument("--intent", choices=("auto", "read", "write"), default="auto")
    parser.add_argument("--user-prompt", help="original user request, passed only when supported")
    parser.add_argument("--output-dir", help="directory for binary result content")
    _add_connection_options(parser)


def _arguments_from(options: argparse.Namespace, name: str) -> dict[str, Any]:
    file_value = getattr(options, f"{name}_file", None)
    if file_value:
        try:
            raw = Path(file_value).read_text(encoding="utf-8-sig")
        except OSError as exc:
            raise CliError(f"cannot read {name} file {file_value}: {exc}") from exc
    else:
        raw = getattr(options, name)
    return _json_object(raw, name)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mcpctl", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("servers", help="show configured stdio MCP servers without starting them").add_argument("--config")
    doctor = sub.add_parser("doctor", help="validate commands and config without starting servers")
    doctor.add_argument("--config")
    doctor.add_argument("--server", choices=("unreal", "blender"), help="check only this required host")

    preflight = sub.add_parser("preflight", help="run a lightweight host check")
    preflight.add_argument("server", choices=("unreal", "blender"))
    preflight.add_argument("--user-prompt", default="MCP CLI preflight")
    _add_connection_options(preflight)

    tools = sub.add_parser("tools", help="list tools advertised by a server")
    tools.add_argument("server")
    tools.add_argument("--filter", default="")
    _add_connection_options(tools)

    schema = sub.add_parser("schema", help="show one advertised tool schema")
    schema.add_argument("server")
    schema.add_argument("tool")
    _add_connection_options(schema)

    call = sub.add_parser("call", help="call one MCP tool")
    call.add_argument("server")
    call.add_argument("tool")
    _add_call_options(call)

    ue = sub.add_parser("ue", help="call an Unreal <namespace>_query action")
    ue.add_argument("namespace")
    ue.add_argument("action")
    _add_call_options(ue, "params")

    blender = sub.add_parser("blender", help="call one Blender MCP tool")
    blender.add_argument("tool")
    _add_call_options(blender)
    return parser


def _which(command: str) -> str | None:
    from shutil import which
    return which(command)


def main(argv: list[str] | None = None) -> int:
    options = build_parser().parse_args(argv)
    try:
        servers, project_config = load_servers(options.config)
        if options.command in {"servers", "doctor"}:
            rows = []
            all_ok = True
            target_servers = {name: config for name, config in servers.items() if name in {"unreal", "blender"}}
            required = {options.server} if getattr(options, "server", None) else {"unreal", "blender"}
            if options.command == "doctor":
                target_servers = {name: config for name, config in target_servers.items() if name in required}
            for name, config in sorted(target_servers.items()):
                command = config.command
                if Path(command).name.lower() in {"python", "python.exe", "python3", "python3.exe"}:
                    command = sys.executable
                command_ok = Path(command).is_file() if Path(command).is_absolute() else bool(_which(command))
                all_ok = all_ok and command_ok
                rows.append({"name": name, "transport": "stdio", "command": command,
                             "command_ok": command_ok, "args": config.args,
                             "env_keys": sorted(config.env), "source": str(config.source)})
            all_ok = all_ok and required.issubset(target_servers)
            _emit({"ok": all_ok if options.command == "doctor" else True, "servers": rows})
            return 0 if options.command == "servers" or all_ok else 2

        server_name = options.server if hasattr(options, "server") else ("unreal" if options.command == "ue" else "blender")
        config = _resolve_server(servers, server_name)
        if options.command in {"tools", "schema"}:
            with McpClient(config, options.startup_timeout) as client:
                listed = client.list_tools(options.timeout)
            if options.command == "tools":
                needle = options.filter.casefold()
                selected = [item for item in listed if needle in
                            (str(item.get("name", "")) + " " + str(item.get("description", ""))).casefold()]
                _emit({"ok": True, "server": options.server, "count": len(selected), "tools": selected})
            else:
                _emit({"ok": True, "server": options.server,
                       "tool": _find_tool(listed, options.server, options.tool)})
            return 0

        if options.command == "preflight":
            tool = "monolith_status" if options.server == "unreal" else "get_scene_info"
            payload, code = _call(config, options.server, tool, {}, "read", options.user_prompt,
                                  options.timeout, options.startup_timeout, _artifact_root(project_config, None))
        elif options.command == "call":
            payload, code = _call(config, options.server, options.tool, _arguments_from(options, "args"),
                                  options.intent, options.user_prompt, options.timeout,
                                  options.startup_timeout, _artifact_root(project_config, options.output_dir))
        elif options.command == "ue":
            arguments = {"action": options.action, "params": _arguments_from(options, "params")}
            payload, code = _call(config, "unreal", f"{options.namespace}_query", arguments,
                                  options.intent, options.user_prompt, options.timeout,
                                  options.startup_timeout, _artifact_root(project_config, options.output_dir))
        else:
            payload, code = _call(config, "blender", options.tool, _arguments_from(options, "args"),
                                  options.intent, options.user_prompt, options.timeout,
                                  options.startup_timeout, _artifact_root(project_config, options.output_dir))
        _emit(payload)
        return code
    except KeyboardInterrupt:
        _emit({"ok": False, "code": "interrupted"})
        return 130
    except (CliError, OSError) as exc:
        _emit({"ok": False, "code": "error", "error": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
