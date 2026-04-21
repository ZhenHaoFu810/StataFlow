#Requires -Version 5.1
# Thin wrapper: delegates to export_open_source.py for cross-platform reliability.
param(
    [switch]$DryRun,
    [switch]$Force,
    [string]$TargetRoot = ''
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot  = Resolve-Path (Join-Path $ScriptDir '..\..') | Select-Object -ExpandProperty Path
$PyScript  = Join-Path $RepoRoot 'scripts\release\export_open_source.py'

$argsList = @($PyScript)
if ($DryRun)   { $argsList += '--dry-run' }
if ($Force)    { $argsList += '--force' }
if ($TargetRoot) { $argsList += '--target-root'; $argsList += $TargetRoot }

& python @argsList
