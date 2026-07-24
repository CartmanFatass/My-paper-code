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
    $clickBlock = @(
        'var click = {',
        '  schema: {',
        '    name: ClickTool.shape.name.value,',
        '    description: ClickTool.shape.description.value,',
        '    inputSchema: zodToJsonSchema3(ClickTool.shape.arguments)',
        '  },',
        '  handle: async (context, params) => {',
        '    const validatedParams = ClickTool.shape.arguments.parse(params);',
        '    await context.sendSocketMessage("browser_click", validatedParams);',
        '    const snapshot2 = await captureAriaSnapshot(context);',
        '    return {',
        '      content: [',
        '        {',
        '          type: "text",',
        '          text: `Clicked "${validatedParams.element}"`',
        '        },',
        '        ...snapshot2.content',
        '      ]',
        '    };',
        '  }',
        '};'
    ) -join "`n"
    $hoverBlock = @(
        'var hover = {',
        '  schema: {',
        '    name: HoverTool.shape.name.value,',
        '    description: HoverTool.shape.description.value,',
        '    inputSchema: zodToJsonSchema3(HoverTool.shape.arguments)',
        '  },',
        '  handle: async (context, params) => {',
        '    const validatedParams = HoverTool.shape.arguments.parse(params);',
        '    await context.sendSocketMessage("browser_hover", validatedParams);',
        '    const snapshot2 = await captureAriaSnapshot(context);',
        '    return {',
        '      content: [',
        '        {',
        '          type: "text",',
        '          text: `Hovered over "${validatedParams.element}"`',
        '        },',
        '        ...snapshot2.content',
        '      ]',
        '    };',
        '  }',
        '};'
    ) -join "`n"
    $typeBlock = @(
        'var type = {',
        '  schema: {',
        '    name: TypeTool.shape.name.value,',
        '    description: TypeTool.shape.description.value,',
        '    inputSchema: zodToJsonSchema3(TypeTool.shape.arguments)',
        '  },',
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
    $fixture = @(
        'var sender = (options = { timeoutMs: 3e4 }) => options;',
        'var context = (options = { timeoutMs: 3e4 }) => options;',
        $clickBlock,
        $hoverBlock,
        $typeBlock
    ) -join "`n"
    [IO.File]::WriteAllText($source, $fixture, $utf8)
    $sourceBefore = [IO.File]::ReadAllBytes($source)

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $launcher `
        -SourcePath $source -OutputPath $output -PatchOnly
    if ($LASTEXITCODE -ne 0) { throw "Launcher fixture patch failed with exit $LASTEXITCODE" }

    $patched = [IO.File]::ReadAllText($output, $utf8)
    if (($patched.Split([string[]]@('options = { timeoutMs: 12e4 }'), [StringSplitOptions]::None).Count - 1) -ne 2) {
        throw 'Patched launcher did not extend both WebSocket timeouts to 120 seconds.'
    }
    $patchedClick = @(
        '    await context.sendSocketMessage("browser_click", validatedParams);',
        '    return {',
        '      content: [',
        '        {',
        '          type: "text",',
        '          text: `Clicked "${validatedParams.element}"; postcondition snapshot required`',
        '        }',
        '      ]',
        '    };'
    ) -join "`n"
    if (-not $patched.Contains($patchedClick)) {
        throw 'Patched click handler does not retain the action and require explicit postcondition snapshot reconciliation.'
    }
    $patchedHover = @(
        '    await context.sendSocketMessage("browser_hover", validatedParams);',
        '    return {',
        '      content: [',
        '        {',
        '          type: "text",',
        '          text: `Hovered over "${validatedParams.element}"; postcondition snapshot required`',
        '        }',
        '      ]',
        '    };'
    ) -join "`n"
    if (-not $patched.Contains($patchedHover)) {
        throw 'Patched hover handler does not retain the action and require explicit postcondition snapshot reconciliation.'
    }
    $patchedType = @(
        '    await context.sendSocketMessage("browser_type", validatedParams);',
        '    return {',
        '      content: [',
        '        {',
        '          type: "text",',
        '          text: `Typed "${validatedParams.text}" into "${validatedParams.element}"; postcondition snapshot required`',
        '        }',
        '      ]',
        '    };'
    ) -join "`n"
    if (-not $patched.Contains($patchedType)) {
        throw 'Patched type handler does not retain the action and require explicit postcondition snapshot reconciliation.'
    }
    if ($patched.Contains('const snapshot2 = await captureAriaSnapshot(context);') -or
        $patched.Contains('...snapshot2.content')) {
        throw 'A patched action handler still performs an implicit post-action snapshot.'
    }
    if (($patched.Split([string[]]@('postcondition snapshot required'), [StringSplitOptions]::None).Count - 1) -ne 3) {
        throw 'Patched click, hover, and type handlers do not each advertise explicit postcondition reconciliation.'
    }
    if (-not ([Linq.Enumerable]::SequenceEqual($sourceBefore, [IO.File]::ReadAllBytes($source)))) {
        throw 'Launcher mutated the upstream source bundle.'
    }
    $samePathFailedClosed = $false
    try {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $launcher `
            -SourcePath $source -OutputPath $source -PatchOnly 2>$null
    } catch { $samePathFailedClosed = $true }
    if ($LASTEXITCODE -ne 0) { $samePathFailedClosed = $true }
    if (-not $samePathFailedClosed) { throw 'Launcher allowed patched output to overwrite the upstream source bundle.' }
    if (-not ([Linq.Enumerable]::SequenceEqual($sourceBefore, [IO.File]::ReadAllBytes($source)))) {
        throw 'Rejected same-path output mutated the upstream source bundle.'
    }


    $driftedTimeout = Join-Path $root 'drifted-timeout.js'
    [IO.File]::WriteAllText($driftedTimeout, $fixture.Replace('options = { timeoutMs: 3e4 }', 'options = { timeoutMs: 4e4 }'), $utf8)
    $timeoutFailedClosed = $false
    try {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $launcher `
            -SourcePath $driftedTimeout -OutputPath (Join-Path $root 'drifted-timeout.patched.js') -PatchOnly 2>$null
    } catch { $timeoutFailedClosed = $true }
    if ($LASTEXITCODE -ne 0) { $timeoutFailedClosed = $true }
    if (-not $timeoutFailedClosed) { throw 'Launcher accepted an unknown upstream timeout shape.' }

    $driftedClick = Join-Path $root 'drifted-click.js'
    [IO.File]::WriteAllText($driftedClick, $fixture.Replace('text: `Clicked "${validatedParams.element}"`', 'text: `Activated "${validatedParams.element}"`'), $utf8)
    $clickFailedClosed = $false
    try {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $launcher `
            -SourcePath $driftedClick -OutputPath (Join-Path $root 'drifted-click.patched.js') -PatchOnly 2>$null
    } catch { $clickFailedClosed = $true }
    if ($LASTEXITCODE -ne 0) { $clickFailedClosed = $true }
    if (-not $clickFailedClosed) { throw 'Launcher accepted an unknown upstream click-handler shape.' }

    $driftedHover = Join-Path $root 'drifted-hover.js'
    [IO.File]::WriteAllText($driftedHover, $fixture.Replace('text: `Hovered over "${validatedParams.element}"`', 'text: `Hovered "${validatedParams.element}"`'), $utf8)
    $hoverFailedClosed = $false
    try {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $launcher `
            -SourcePath $driftedHover -OutputPath (Join-Path $root 'drifted-hover.patched.js') -PatchOnly 2>$null
    } catch { $hoverFailedClosed = $true }
    if ($LASTEXITCODE -ne 0) { $hoverFailedClosed = $true }
    if (-not $hoverFailedClosed) { throw 'Launcher accepted an unknown upstream hover-handler shape.' }
    $driftedType = Join-Path $root 'drifted-type.js'
    [IO.File]::WriteAllText($driftedType, $fixture.Replace('text: `Typed "${validatedParams.text}" into "${validatedParams.element}"`', 'text: `Entered "${validatedParams.text}" into "${validatedParams.element}"`'), $utf8)
    $typeFailedClosed = $false
    try {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $launcher `
            -SourcePath $driftedType -OutputPath (Join-Path $root 'drifted-type.patched.js') -PatchOnly 2>$null
    } catch { $typeFailedClosed = $true }
    if ($LASTEXITCODE -ne 0) { $typeFailedClosed = $true }
    if (-not $typeFailedClosed) { throw 'Launcher accepted an unknown upstream type-handler shape.' }


    Write-Output 'BROWSERMCP_DIRECT_LAUNCHER_CONTRACT_OK timeout_ms=120000 implicit_click_snapshot=removed implicit_hover_snapshot=removed implicit_type_snapshot=removed same_path=blocked upstream_drift=blocked'
} finally {
    if (Test-Path -LiteralPath $root) { Remove-Item -LiteralPath $root -Recurse -Force }
}
