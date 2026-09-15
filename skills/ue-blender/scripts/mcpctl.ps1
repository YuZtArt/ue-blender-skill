[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $McpCliArgs
)

$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot 'mcp_cli.py'
$candidates = @()

if ($env:MCP_CLI_PYTHON) {
    $candidates += $env:MCP_CLI_PYTHON
}

$pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
if ($pythonCommand -and $pythonCommand.Source -notlike '*WindowsApps*') {
    $candidates += $pythonCommand.Source
}

$localPythonRoot = Join-Path $env:LOCALAPPDATA 'Programs\Python'
if (Test-Path -LiteralPath $localPythonRoot) {
    $candidates += Get-ChildItem -LiteralPath $localPythonRoot -Filter python.exe -Recurse -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending |
        ForEach-Object FullName
}

$python = $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $python) {
    throw 'Python 3.11+ was not found. Set MCP_CLI_PYTHON to a Python executable.'
}

& $python $scriptPath @McpCliArgs
exit $LASTEXITCODE
