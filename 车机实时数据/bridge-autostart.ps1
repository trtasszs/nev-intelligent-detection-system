# ============================================================
#  Silent bridge autostart  --  ROS(8770) + CAN(8780)
# ------------------------------------------------------------
#  Pure ASCII on purpose: the script derives its own directory
#  from $PSScriptRoot, so no non-ASCII path literal is needed
#  and no encoding/BOM problem can occur.
#
#  The listening check MUST filter on State = Listen.
#  Matching the bare port number also hits TIME_WAIT leftovers
#  from a previous run and falsely reports "already running".
# ============================================================

$DIR = $PSScriptRoot
$PYW = 'C:\Users\ASUS\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\pythonw.exe'
if (-not (Test-Path $PYW)) { $PYW = 'pythonw.exe' }

$bridges = @(
    @{ File = 'ros_bridge.py'; Port = 8770 },
    @{ File = 'can_bridge.py'; Port = 8780 }
)

foreach ($b in $bridges) {
    $script = Join-Path $DIR $b.File
    $port   = $b.Port

    $lis = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($lis) {
        Write-Host ('  [skip ] ' + $b.File + '  ' + $port + ' already listening')
        continue
    }
    if (-not (Test-Path $script)) {
        Write-Host ('  [error] missing ' + $script)
        continue
    }
    try {
        Start-Process -FilePath $PYW `
                      -ArgumentList $script, '--port', $port `
                      -WorkingDirectory $DIR `
                      -WindowStyle Hidden -ErrorAction Stop
        Write-Host ('  [start] ' + $b.File + '  ' + $port)
    } catch {
        Write-Host ('  [error] ' + $b.File + ' : ' + $_.Exception.Message)
    }
}
