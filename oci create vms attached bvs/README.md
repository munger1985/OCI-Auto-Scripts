# Scenario 
Use this jar, and config file in your ~/.oci for authentication. for setting up this auth config file, refer to https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm or directly copy those in your cloud shell, you should have permission of creating vms, bvs to run the tool jar.
> we can create certain number of vms
> we can delete those vms to save money, start them up with exisiting bvs where data resides, so that we can resume.
> we can create certain number of vms with corresponding count of bvs which can hold the data.

# Usage
Just modify the application.yml to adjust parameters of your own.

## Example cmd
### create 3 new vms without bvs
> java -jar solar.jar -p  -c 3  
###  find out those vms to delete
> java -jar solar.jar --delete  
### find out count of bvs, create the same number of vms and attached bvs
> java -jar solar.jar  -o 
### create 3 new vms with 3 new bvs.
> java -jar solar.jar -n -c 3 
