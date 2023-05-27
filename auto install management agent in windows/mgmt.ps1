

$key="dBnc2JhY25ybWp2NDZlN240Znczc2dFuYWdlbWVudGFnZWdW1hdMThsMU1kMV9sd9oRWdnNjZRUU4="



$AgentDisplayName= "mgmt-agent"
$jreurl = "https://objectstorage.ap-seoul-1.oraclecloud.com/p/LxGPuXosZF1tKBNVEg9XbtFATs-QGH9o2r4ScidNZgkHRLG7Cd2xW9jIvtQBYK3h/n/sehubjapacprod/b/jim_bucket/o/jre-8u371-windows-x64.exe"
$JAVA_HOME="C:\Program Files\Java\jre-1.8"
$mgmt_agent="https://objectstorage.ap-seoul-1.oraclecloud.com/p/f47dhUnN5x-7GSM8oIbe0h9igiP57X7ZvMjl7kb1hWhUcgN0T6vBoBXnvPcIdK4I/n/sehubjapacprod/b/jim_bucket/o/oracle.mgmt_agent.230427.2233.Windows-x86_64.zip"

$tempDir1 = Join-Path -Path $env:TEMP  -ChildPath "ocitemporary"

if (Test-Path "C:\Oracle\mgmt_agent"){
Start-Process -FilePath C:\Oracle\mgmt_agent\uninstaller.bat    -Wait
Remove-Item  -Path  C:\Oracle\mgmt_agent  -Recurse -Force
}
 
if (Test-Path $tempDir1) {

    sc.exe delete "Oracle Management Agent"
    # Delete the directory
    Remove-Item  -Path  $tempDir1  -Recurse -Force
    # Remove-Item $tempDir1
    # Remove-Item  C:\Oracle\mgmt_agent\  -Recurse -Force
}
 

if (-not (Test-Path $tempDir1)) {
    # Create the directory
    New-Item $tempDir1 -ItemType Directory
}
Invoke-WebRequest -Uri $jreurl -OutFile $tempDir1\jre-8u371-windows-x64.exe
Start-Process -FilePath $tempDir1\jre-8u371-windows-x64.exe /s  -Wait


$currentPath = [Environment]::GetEnvironmentVariable("PATH")

# Add the new path to the end of the PATH
$currentPath += ";$JAVA_HOME\bin\"

# Set the new value of the PATH environment variable
[System.Environment]::SetEnvironmentVariable("JAVA_HOME",$JAVA_HOME, "Machine")
if ($env:Path -like "*$JAVA_HOME\bin*") {
    Write-Host "Java bin already is in the path"
}else {
    [Environment]::SetEnvironmentVariable("PATH", $currentPath,"Machine")

}


### edit rsp　AgentDisplayName = $AgentDisplayName
 

New-Item -Path  $tempDir1 -Name mgmt_input.rsp  -ItemType file -Value "managementAgentInstallKey = $key
CredentialWalletPassword = Abcdefgh1#"

## install agent
Invoke-WebRequest -Uri $mgmt_agent -OutFile $tempDir1\oracle.mgmt_agent.230427.2233.Windows-x86_64.zip
Expand-Archive -Path $tempDir1\oracle.mgmt_agent.230427.2233.Windows-x86_64.zip -DestinationPath $tempDir1

 
$env:JAVA_HOME=$JAVA_HOME
cmd.exe /c $tempDir1\installer.bat  $tempDir1\mgmt_input.rsp
 