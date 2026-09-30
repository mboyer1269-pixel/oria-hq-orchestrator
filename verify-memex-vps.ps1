param(
    [Parameter(Mandatory)][string]$SourceRoot,
    [Parameter(Mandatory)][string]$SshTarget,
    [Parameter(Mandatory)][string]$IdentityFile
)
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path -LiteralPath $SourceRoot).Path
if (!(Test-Path -LiteralPath (Join-Path $source 'src/mcp/server.ts'))) { throw 'Expected Memex Core source tree' }
if ($SshTarget -notmatch '^[a-zA-Z0-9_.-]+@[a-zA-Z0-9_.-]+$') { throw 'Invalid SSH target' }
$runName = 'memex-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
$outputRoot = Join-Path $PSScriptRoot '.validation'
$runPath = Join-Path $outputRoot $runName
New-Item -ItemType Directory -Path $runPath -Force | Out-Null
$archive = Join-Path $runPath 'source.tgz'
# Explicit allowlist: no real data, .env, credentials, node_modules, or Git history.
& tar -czf $archive -C $source package.json package-lock.json src tests fixtures configs/mcp/claude-code.local.example.json configs/mcp/claude-desktop.local.example.json configs/mcp/cursor.local.example.json
if ($LASTEXITCODE -ne 0) { throw 'Source archive failed' }
$digest = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash
$remotePath = '/opt/oria-validation/' + $runName
$sshOptions = @('-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-i',$IdentityFile)
& ssh @sshOptions $SshTarget "mkdir -p $remotePath"
if ($LASTEXITCODE -ne 0) { throw 'Remote directory creation failed' }
& scp @sshOptions $archive "${SshTarget}:$remotePath/source.tgz"
if ($LASTEXITCODE -ne 0) { throw 'Source transfer failed' }
$remoteCommand = "docker run --rm --cpus 2 --memory 2g --pids-limit 256 --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --mount type=bind,src=$remotePath,target=/input,readonly node:22-slim sh -c 'mkdir /tmp/work && tar -xzf /input/source.tgz -C /tmp/work && cd /tmp/work && node --version && npm ci --no-audit --no-fund && npm run check && npm test'"
& ssh @sshOptions $SshTarget $remoteCommand 2>&1 | Tee-Object -FilePath (Join-Path $runPath 'linux-validation.log')
$validationExit = $LASTEXITCODE
[ordered]@{ sourceArchiveSha256=$digest; checkedAt=(Get-Date).ToUniversalTime().ToString('o'); exitCode=$validationExit; remoteDirectory=$remotePath; scope='isolated synthetic Linux validation; no ports; no provider calls' } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runPath 'result.json')
if ($validationExit -ne 0) { throw "Linux validation failed (exit $validationExit); see $runPath" }
Write-Output "Linux validation passed; evidence: $runPath"
