# Scenario 
This page demonstrate how to search OCI resources created by someone (or any other pattern) across all regions.  

You could use this script (or variants ) on differnt scenarios , such as:

> 1. When someone leave the organization, we need to review the assets created by him/her, to decide if need to keep, reuse, transfer or clean up
> 2. When lots of resource are created by accidently or by hacker, you could list those resource and review before take futhure action.

# Usage
Just modify the conf.yml to adjust parameters of your own.

## Example cmd
###用法 ./query.sh 用户名 另存为文件名
> ./query.sh 'oracleidentitycloudservice/wenbin.chen@oracle.com'  wenbin.chen.json
###json to excel  https://jsongrid.com/json-grid
