param([Parameter(Mandatory=$true)][string] $Manifest, [Parameter(Mandatory=$true)][string] $Preflight, [string] $Requirements = 'docs/project/PROJECT_REQUIREMENTS.toml', [string] $Registry = 'docs/project/EXECUTION_BACKEND_REGISTRY.toml', [string] $ProjectMap = 'docs/project/PROJECT_MAP.md')
$ErrorActionPreference = 'Stop'
$python = 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe'
& $python -m tools.hmasd_control_plane.boundary_cli manifest $Manifest --preflight $Preflight --requirements $Requirements --registry $Registry --project-map $ProjectMap
exit $LASTEXITCODE
