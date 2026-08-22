param([Parameter(Mandatory=$true)][string] $Result, [Parameter(Mandatory=$true)][string] $Assignment, [string] $Requirements = 'docs/project/PROJECT_REQUIREMENTS.toml')
$ErrorActionPreference = 'Stop'
$python = 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe'
& $python -m tools.hmasd_control_plane.boundary_cli incident $Result --assignment $Assignment --requirements $Requirements
exit $LASTEXITCODE
