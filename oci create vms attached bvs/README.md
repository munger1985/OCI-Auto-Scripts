# Scenario 
Use this jar, and config file in your ~/.oci for authentication. for setting up this auth config file, refer to https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm or directly copy those in your cloud shell, you should have permission of creating vms, bvs to run the tool jar.
> we can create certain number of vms, with block volumes attached to them.
> we can delete those vms according to the free form tags.
> we can define different kinds of vm config in the conf.yml

# Usage
Just modify the conf.yml to adjust parameters of your own.

## Example cmd
### can check help
> java -jar solar.jar -h
### find out those vms to delete
>  java -jar solar.jar    --delete --compartment  ocid1.compartment.oc1..sdw3kkj4q --freeTagKey Auto --freeTagValue 1
### create those vms based on conf.yml
> java -jar solar.jar   