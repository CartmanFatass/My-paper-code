param(
    [Parameter(Position=0)] [ValidateSet('validate','render','show')] [string] $Action = 'validate',
    [string] $Id,
    [string] $Path = 'docs/project/PROJECT_REQUIREMENTS.toml'
)
$ErrorActionPreference = 'Stop'
$python = 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe'
$args = @('-m','tools.hmasd_control_plane.boundary_cli','requirements',$Action,'--path',$Path)
if ($Id) { $args += @('--id',$Id) }
& $python @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
