# Scenario 
This page demonstrate how to search OCI resources created by someone (or any other pattern) across all regions.  

You could use this script (or variants ) on differnt scenarios , such as:

> 1. When someone leave the organization, we need to review the assets created by him/her, to decide if need to keep, reuse, transfer or clean up
> 2. When lots of resource are created by accidently or by hacker, you could list those resource and review before take futhure action.

# Usage
Just modify the region list on query.sh to meet your requirements.

## Example cmd
### usage ./query.sh <username> <output file name>
> ./query.sh 'oracleidentitycloudservice/usera@oraclecorp.com'  user1.output.json
###json to excel  https://jsongrid.com/json-grid
