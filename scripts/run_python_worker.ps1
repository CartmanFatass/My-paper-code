param(
    [Parameter(Mandatory = $true)]
    [string]$SpecPath
)

$ErrorActionPreference = "Stop"
$spec = Get-Content -Raw -LiteralPath $SpecPath | ConvertFrom-Json
$exitCode = 1

try {
    Set-Location -LiteralPath ([string]$spec.working_directory)
    $pythonArguments = @($spec.arguments | ForEach-Object { [string]$_ })
    & ([string]$spec.python_bin) @pythonArguments `
        1> ([string]$spec.stdout_path) `
        2> ([string]$spec.stderr_path)
    if ($null -eq $LASTEXITCODE) {
        throw "Python worker returned no exit code"
    }
    $exitCode = [int]$LASTEXITCODE
}
catch {
    $message = [string]$_.Exception.Message
    [System.IO.File]::AppendAllText(
        [string]$spec.stderr_path,
        "`nworker_wrapper_error=$message`n"
    )
    $exitCode = 1
}
finally {
    $exitCodePath = [string]$spec.exit_code_path
    [System.IO.File]::WriteAllText($exitCodePath, [string]$exitCode)
}

exit $exitCode
