[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$launcher = Join-Path $repo '.omp/browsermcp-direct/start_browsermcp_direct.ps1'
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
    throw 'Controller-direct BrowserMCP launcher is missing.'
}

$utf8 = [Text.UTF8Encoding]::new($false)
$root = Join-Path ([IO.Path]::GetTempPath()) ('hmasd-browsermcp-direct-' + [Guid]::NewGuid().ToString('N'))
try {
    [IO.Directory]::CreateDirectory($root) | Out-Null
    $source = Join-Path $root 'index.js'
    $output = Join-Path $root 'index.patched.js'
    $typeBlock = @(
        'var sender = (options = { timeoutMs: 3e4 }) => options;',
        'var context = (options = { timeoutMs: 3e4 }) => options;',
        'var type = {',
        '  handle: async (context, params) => {',
        '    const validatedParams = TypeTool.shape.arguments.parse(params);',
        '    await context.sendSocketMessage("browser_type", validatedParams);',
        '    const snapshot2 = await captureAriaSnapshot(context);',
        '    return {',
        '      content: [',
        '        {',
        '          type: "text",',
        '          text: `Typed "${validatedParams.text}" into "${validatedParams.element}"`',
        '        },',
        '        ...snapshot2.content',
        '      ]',
        '    };',
        '  }',
        '};'
    ) -join "`n"
    [IO.File]::WriteAllText($source, $typeBlock, $utf8)
    $sourceBefore = [IO.File]::ReadAllBytes($source)

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $launcher `
        -SourcePath $source -OutputPath $output -PatchOnly
    if ($LASTEXITCODE -ne 0) { throw "Launcher fixture patch failed with exit $LASTEXITCODE" }

    $patched = [IO.File]::ReadAllText($output, $utf8)
    if (($patched.Split([string[]]@('options = { timeoutMs: 12e4 }'), [StringSplitOptions]::None).Count - 1) -ne 2) {
        throw 'Patched launcher did not extend both WebSocket timeouts to 120 seconds.'
    }
    if ($patched.Contains('const snapshot2 = await captureAriaSnapshot(context);') -or
        $patched.Contains('...snapshot2.content')) {
        throw 'Patched type handler still performs an implicit post-action snapshot.'
    }
    if (-not $patched.Contains('postcondition snapshot required')) {
        throw 'Patched type handler does not require explicit postcondition reconciliation.'
    }
    if (-not ([Linq.Enumerable]::SequenceEqual($sourceBefore, [IO.File]::ReadAllBytes($source)))) {
        throw 'Launcher mutated the upstream source bundle.'
    }

    $drifted = Join-Path $root 'drifted.js'
    [IO.File]::WriteAllText($drifted, $typeBlock.Replace('options = { timeoutMs: 3e4 }', 'options = { timeoutMs: 4e4 }'), $utf8)
    $failedClosed = $false
    try {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $launcher `
            -SourcePath $drifted -OutputPath (Join-Path $root 'drifted.patched.js') -PatchOnly 2>$null
    } catch { $failedClosed = $true }
    if ($LASTEXITCODE -ne 0) { $failedClosed = $true }
    if (-not $failedClosed) { throw 'Launcher accepted an unknown upstream timeout shape.' }

    Write-Output 'BROWSERMCP_DIRECT_LAUNCHER_CONTRACT_OK timeout_ms=120000 implicit_type_snapshot=removed upstream_drift=blocked'
} finally {
    if (Test-Path -LiteralPath $root) { Remove-Item -LiteralPath $root -Recurse -Force }
}
