# intro

Here are some code for reference to search IP resource on OCI

## globalIPFinder is search all your region ip from OCI, will take longer time but it would not miss the required IP. 

### usage

input your compartmentID and target IP you wanna search, and run the file

## singleFileSmartFinder.py

it uses llm and ip-api to get the possible region of the ip, and search the result, faster but required llm on OCI

### usage

input compartmentID in python file, and use ip as command line arguments, when you run it will prompt you need to run python  singleFileSmartFinder.py   <IP address>.


# auth

globalIPFinder  uses ~/.oci/config 

singleFileSmartFinder.py uses instance principal which requires allow dynamic-group <xxxx> to manage generative-ai-family in tenancy

