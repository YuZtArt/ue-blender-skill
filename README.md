# Unreal 与 Blender MCP Skill

中文 | [English](README.en.md)

用于操作正在运行的 Unreal Engine 和 Blender 编辑器的统一 Codex／OpenCode skill。它合并了 `ue-blender-mcp-cli` 和 `reliable-ue-blender-mcp`：内置 stdio CLI 负责工具发现与调用，统一操作规范负责调用顺序、结果验证和超时恢复。

## 两个 Skill

| Skill | 用途 |
| --- | --- |
| `ue-blender` | 日常操作：检查编辑器、修改资产、截图、验证与超时恢复 |
| `ue-blender-setup` | 初始化：检查环境、安装所需组件、生成本机连接配置、验证连通性 |

初始化 skill 是由代理执行的安装与配置流程，不是包含 UE、Blender 或插件的离线一键安装包。只需要 UE 时，不会要求安装 Blender。

## OpenCode 安装

克隆仓库后，将两个文件夹复制到 OpenCode 的 skills 目录。标准 Windows 配置目录示例：

```powershell
git clone https://github.com/YuZtArt/ue-blender-skill.git
$skillParent = Join-Path $HOME '.config/opencode/skills'
New-Item -ItemType Directory -Force $skillParent | Out-Null
Copy-Item -Recurse ./ue-blender-skill/skills/ue-blender $skillParent
Copy-Item -Recurse ./ue-blender-skill/skills/ue-blender-setup $skillParent
opencode debug skill
```

自定义配置目录以 `opencode debug paths` 为准；macOS／Linux 可复制到 `~/.config/opencode/skills/`。更新时请先备份并替换旧文件夹，避免嵌套复制。

然后对 OpenCode 说：**“使用 ue-blender-setup，为当前项目初始化 Unreal MCP。”** 已配置的环境可直接说：**“使用 ue-blender 检查当前 Unreal 项目。”**

CLI 支持通过 `--config` 指定独立连接文件，也支持 OpenCode 的严格 JSON 本地 MCP 配置。JSONC、变量替换及多层配置需要先通过 OpenCode 解析，再提取所需 MCP 条目。详见 [OpenCode 兼容说明](skills/ue-blender/references/opencode.md)。不需要额外注册直接 MCP 工具。

本机验证：OpenCode 1.18.22 能发现 skill，CLI 已连接 Monolith 0.22.0／UE 5.8；Blender 桥接进程可启动，但验证时插件未连接，因此不宣称 Blender 端到端验证通过。

上游依赖：[Monolith](https://github.com/tumourlove/monolith) · [BlenderMCP](https://github.com/ahujasid/mcp-for-blender)。版本选择和安装要求见[初始化参考](skills/ue-blender-setup/references/providers.md)。

## 依赖与前置条件

| 依赖 | 用途与要求 |
| --- | --- |
| Python 3.11 或更新版本 | 运行内置 CLI，仅使用 Python 标准库 |
| Unreal Monolith／UEMCP | 操作 Unreal 编辑器，需要自行安装并配置对应 MCP 服务和编辑器插件 |
| BlenderMCP | 操作 Blender，需要自行安装并配置 MCP 服务和 Blender 插件 |
| Codex 或兼容代理 | 能读取 `SKILL.md` 并执行命令 |

**只需配置实际使用的应用，无需同时安装两个 MCP。** 使用时应启动对应编辑器并启用插件。CLI 的便捷命令使用 `unreal`、`blender` 作为 MCP 服务名称。

内置 CLI 仅支持 **stdio**。HTTP／SSE 配置需要代理环境中可用的直接 MCP 工具作为备用入口。本仓库不包含也不会自动安装编辑器、MCP 服务或插件。Unreal 便捷命令采用 Monolith 的命名空间／动作接口，其他实现应按实际公布的工具使用通用调用。

## 安装

以下是 Codex 安装方式。克隆仓库，将 `skills/ue-blender` 和 `skills/ue-blender-setup` 两个文件夹复制到个人 skills 目录。

Windows PowerShell：

```powershell
git clone https://github.com/YuZtArt/ue-blender-skill.git
$skillParent = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $HOME '.codex/skills' }
New-Item -ItemType Directory -Force $skillParent | Out-Null
Copy-Item -Recurse ./ue-blender-skill/skills/ue-blender $skillParent
Copy-Item -Recurse ./ue-blender-skill/skills/ue-blender-setup $skillParent
```

macOS／Linux：

```bash
git clone https://github.com/YuZtArt/ue-blender-skill.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R ue-blender-skill/skills/ue-blender ue-blender-skill/skills/ue-blender-setup "${CODEX_HOME:-$HOME/.codex}/skills/"
```

更新时，用新版替换已安装的 `ue-blender` 文件夹。如果安装过两个旧 skill，请在安装新版后，将旧文件夹移出活动 skills 目录保存，避免重复触发。新建代理会话以加载新版。

使用示例：

> 使用 $ue-blender 检查当前 Blender 场景，在导出到 Unreal 前验证模型比例。

## 配置与连接检查

可复用已有的 Codex `config.toml` 或项目 `.mcp.json`。服务命令应指向你实际安装的 MCP 桥接程序。以下仅演示 JSON 配置结构，其中的路径需要替换，不是可直接安装的 MCP 服务：

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

在当前项目目录运行已安装的脚本，将示例路径替换成实际位置：

```text
python /path/to/ue-blender/scripts/mcp_cli.py doctor --server blender
python /path/to/ue-blender/scripts/mcp_cli.py preflight blender
```

`doctor` 检查本地配置与启动命令，`preflight` 检查实际连接。检查 Unreal 时，将上述 `blender` 改为 `unreal`。

Windows 可使用 `scripts/mcpctl.ps1` 自动定位 Python，也可通过 `MCP_CLI_PYTHON` 指定解释器。macOS／Linux 按环境使用 `python3`。配置优先级、工具发现、超时参数和输出格式见[命令参考](skills/ue-blender/references/commands.md)。

## 功能与边界

- 按顺序调用编辑器，查询工具 schema，并明确标记读写意图。
- 修改后单独验证结果，只保存目标资产或文件。
- 将截图等二进制返回内容保存为本地文件。
- 限制读取重试次数，写入响应丢失后先核实状态再决定是否重试。
- 提供 Unreal、Blender 专属操作说明与分阶段资产传输流程。

读写意图是标签，不是执行沙箱。CLI 不提供跨进程锁、事务或编辑器端取消机制，操作时需遵循恢复说明。对已保存 Blender 文件进行后台批处理属于另一种工作流；`blender-batch` 是可选 skill，不是本 skill 的依赖。

## 验证

在仓库根目录运行：

```text
python -m unittest discover -s tests -v
```

测试使用本地模拟 stdio 服务和临时配置，不连接真实编辑器。覆盖配置优先级、单应用检查、工具调用与错误、响应丢失、超时及二进制输出。测试通过不代表兼容所有编辑器和 MCP 版本；请对自己的安装执行只读连接检查。

不要将本机 MCP 配置、凭据、编辑器资产或生成的截图提交到仓库。

## 许可证

本仓库采用 [MIT 许可证](LICENSE)。外部编辑器、MCP 服务和插件仍遵循各自的许可证。再分发此 skill 或脚本时，请保留许可证文本。
