[CmdletBinding()]
param(
    [string]$SourcePath,
    [string]$OutputPath,
    [switch]$PatchOnly
)

$ErrorActionPreference = 'Stop'
$utf8 = [Text.UTF8Encoding]::new($false, $true)

function Resolve-UpstreamBundle {
    if (-not [string]::IsNullOrWhiteSpace($SourcePath)) {
        return (Resolve-Path -LiteralPath $SourcePath).Path
    }

    $cacheRoot = Join-Path $env:LOCALAPPDATA 'npm-cache/_npx'
    $candidates = @(Get-ChildItem -LiteralPath $cacheRoot -Directory -ErrorAction Stop | ForEach-Object {
        Join-Path $_.FullName 'node_modules/@browsermcp/mcp/dist/index.js'
    } | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf })

    $matches = @($candidates | Where-Object {
        $packagePath = Join-Path (Split-Path (Split-Path $_ -Parent) -Parent) 'package.json'
        if (-not (Test-Path -LiteralPath $packagePath -PathType Leaf)) { return $false }
        try { (Get-Content -LiteralPath $packagePath -Raw | ConvertFrom-Json).version -eq '0.1.3' }
        catch { $false }
    })
    if ($matches.Count -ne 1) {
        throw "Expected exactly one cached @browsermcp/mcp 0.1.3 bundle, found $($matches.Count)."
    }
    return (Resolve-Path -LiteralPath $matches[0]).Path
}

$source = Resolve-UpstreamBundle
$sourceBytes = [IO.File]::ReadAllBytes($source)
if ($sourceBytes.Length -ge 3 -and $sourceBytes[0] -eq 0xef -and $sourceBytes[1] -eq 0xbb -and $sourceBytes[2] -eq 0xbf) {
    throw 'Upstream BrowserMCP bundle must be UTF-8 without BOM.'
}
$bundle = $utf8.GetString($sourceBytes).Replace("`r`n", "`n").Replace("`r", "`n")

$timeoutOld = 'options = { timeoutMs: 3e4 }'
if (($bundle.Split([string[]]@($timeoutOld), [StringSplitOptions]::None).Count - 1) -ne 2) {
    throw 'BrowserMCP timeout anchor count changed; refusing to patch unknown upstream code.'
}
$bundle = $bundle.Replace($timeoutOld, 'options = { timeoutMs: 12e4 }')

$typeOld = @(
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
    '    };'
) -join "`n"
$typeNew = @(
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
if (($bundle.Split([string[]]@($typeOld), [StringSplitOptions]::None).Count - 1) -ne 1) {
    throw 'BrowserMCP type-handler anchor changed; refusing to patch unknown upstream code.'
}
$bundle = $bundle.Replace($typeOld, $typeNew)

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path (Split-Path $source -Parent) 'index.hmasd-direct.js'
}
$output = [IO.Path]::GetFullPath($OutputPath)
[IO.File]::WriteAllText($output, $bundle, $utf8)

if ($PatchOnly) { exit 0 }
& node.exe $output
exit $LASTEXITCODE
