# Scenario 
This page demonstrate how to search OCI resources created by someone (or any other pattern) across all regions.  

You could use this script (or variants ) on differnt scenarios , such as:

> 1. When someone leave the organization, we need to review the assets created by him/her, to decide if need to keep, reuse, transfer or clean up
> 2. When lots of resource are created by accidently or by hacker, you could list those resource and review before take futhure action.

# Usage
Just modify the conf.yml to adjust parameters of your own.

## Example cmd
### can check help
> java -jar solar.jar -h
### find out those vms to delete
>  java -jar solar.jar    --delete --compartment  ocid1.compartment.oc1..sdw3kkj4q --freeTagKey Auto --freeTagValue 1
### create those vms based on conf.yml
> java -jar solar.jar   
