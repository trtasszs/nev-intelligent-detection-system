Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$targetPid = 17528
$root = [System.Windows.Automation.AutomationElement]::RootElement
$cond = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::ProcessIdProperty, $targetPid)
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)

$done = $false
foreach ($w in $wins) {
    if ($w.Current.ClassName -ne 'QMessageBox') { continue }
    Write-Output ("dialog found: " + $w.Current.Name)
    $btnCond = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
        [System.Windows.Automation.ControlType]::Button)
    $btns = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, $btnCond)
    foreach ($b in $btns) {
        if ($b.Current.Name -eq 'OK') {
            $pat = $b.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
            $pat.Invoke()
            Write-Output "invoked OK"
            $done = $true
        }
    }
}
if (-not $done) { Write-Output "no OK button invoked" }
Start-Sleep -Milliseconds 800

# report the windows again
$wins2 = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)
Write-Output ("windows now: " + $wins2.Count)
foreach ($w in $wins2) { Write-Output ("  [" + $w.Current.Name + "] " + $w.Current.ClassName) }
