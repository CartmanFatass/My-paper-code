param([Parameter(Mandatory=$true)][string] $InputJson)
$ErrorActionPreference = 'Stop'
$python = 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe'
& $python -m tools.hmasd_control_plane.boundary_cli runtime $InputJson
exit $LASTEXITCODE
