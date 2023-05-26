

$key="Mi4wLGFwLXNpbmdhcG9yZS0xLG9jaWQxLnRlbmFuY3kub2MxLi5hYWFhYWFhYXJvN2FveDJmY2x1NHVydHBnc2JhY25ybWp2NDZlN240Znczc2Myd2JxMjRsN2R6ZjNrYmEsb2NpZDEubWFuYWdlbWVudGFnZW50aW5zdGFsbGtleS5vYzEuYXAtc2luZ2Fwb3JlLTEuYW1hYWFhYWFhazdnYnJpYTRzemFrdnNvN251a3pwcGZyMng2aDdyNGFmY2JxYmVkYXJ3ZHNydWVzdTNhLElmcDFGMFVMejNyWm9SZjNoZmpaMFk3Tk9wNFVXNGtNSlpwNWJINU8="

Set-ExecutionPolicy Unrestricted
$AgentDisplayName= "mgmt-agent"
$jreurl = "https://objectstorage.ap-seoul-1.oraclecloud.com/p/LxGPuXosZF1tKBNVEg9XbtFATs-QGH9o2r4ScidNZgkHRLG7Cd2xW9jIvtQBYK3h/n/sehubjapacprod/b/jim_bucket/o/jre-8u371-windows-x64.exe"
$JAVA_HOME="C:\Program Files\Java\jre-1.8"
$mgmt_agent="https://objectstorage.ap-seoul-1.oraclecloud.com/p/f47dhUnN5x-7GSM8oIbe0h9igiP57X7ZvMjl7kb1hWhUcgN0T6vBoBXnvPcIdK4I/n/sehubjapacprod/b/jim_bucket/o/oracle.mgmt_agent.230427.2233.Windows-x86_64.zip"
$tempDir1 = Join-Path -Path $env:TEMP  -ChildPath "ocitemporary"
if (-not (Test-Path $tempDir1)) {
    # Create the directory
    New-Item $tempDir1 -ItemType Directory
}
Invoke-WebRequest -Uri $jreurl -OutFile $tempDir1\jre-8u371-windows-x64.exe
Start-Process -FilePath $tempDir1\jre-8u371-windows-x64.exe -Wait



$currentPath = [Environment]::GetEnvironmentVariable("PATH")

# Add the new path to the end of the PATH
$currentPath += ";$JAVA_HOME\bin\"

# Set the new value of the PATH environment variable
[Environment]::SetEnvironmentVariable("PATH", $currentPath,"Machine")
[System.Environment]::SetEnvironmentVariable("JAVA_HOME",$JAVA_HOME, "Machine")


### edit rsp　AgentDisplayName = $AgentDisplayName
New-Item -Path . -Name mgmt_input.rsp  -ItemType file -Value "managementAgentInstallKey = $key
CredentialWalletPassword = Abcdefgh1#"



## expand agent
Invoke-WebRequest -Uri $mgmt_agent -OutFile $tempDir1\oracle.mgmt_agent.230427.2233.Windows-x86_64.zip
Expand-Archive -Path $tempDir1\oracle.mgmt_agent.230427.2233.Windows-x86_64.zip -DestinationPath $tempDir1

## install
$env:JAVA_HOME=$JAVA_HOME
cmd.exe /c $tempDir1\installer.bat  C:\Windows\system32\mgmt_input.rsp
 