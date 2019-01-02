If (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))
{
  New-WinEvent -ProviderName "Microsoft-Windows-PowerShell" -Id 45090 -Payload @("Script needs to RunAs Adminstrator")
}
# https://docs.microsoft.com/azure/service-fabric/service-fabric-cluster-standalone-deployment-preparation#environment-setup
Install-WindowsFeature -Name Windows-Defender

$servicefabric_exe = "Fabric.exe","FabricHost.exe","FabricInstallerService.exe","FabricSetup.exe","FabricDeployer.exe","ImageBuilder.exe","FabricGateway.exe","FabricDCA.exe","FabricFAS.exe","FabricUOS.exe","FabricRM.exe","FileStoreService.exe"
# $_.ProcessName +.exe
for ($i = 0; $i -lt $servicefabric_exe.Length; $i++)
{
  Add-MpPreference -ExclusionProcess $servicefabric_exe[$i]
}

$servicefabric_storage = "C:\Program Files\Microsoft Service Fabric","D:\SvcFab","D:\SvcFab\Log"
# Storage Path
for ($i = 0; $i -lt $servicefabric_storage.Length; $i++)
{
  Add-MpPreference -ExclusionPath $servicefabric_storage[$i]
}
