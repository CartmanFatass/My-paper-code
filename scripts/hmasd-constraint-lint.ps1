param([string] $Root = '.')
$ErrorActionPreference = 'Stop'
$python = 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe'
& $python -m tools.hmasd_control_plane.boundary_cli lint --root $Root
exit $LASTEXITCODE
