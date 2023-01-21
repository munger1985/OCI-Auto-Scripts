# Scenario
we can use this to automatically deploy openshift on oci vms without manually adding vms and configure sth.
# Prepare a VCN and subnet
make sure in that subnet there is security list which enable the access from the same subnet cidr
e.g. 10.0.0.0/24	All Protocols ingress, egress
> we recommend using a public subnet in a VCN, easy for access.

# Special
if you want to try lbaas instead of nlb, you can try lbaas.tf.baba

# Prerequisite
upload the basic coreos image to OCI, and use this ID in future terraform;
this image can be downloaded from https://mirror.openshift.com/pub/openshift-v4/x86_64/dependencies/rhcos/4.11/4.11.9/ or using

```
openshift-install coreos print-stream-json |grep qcow2 
```

to get urls

make an oracle linux in the same subnet, which can be used to run scripts and work like a client


download terraform

```
wget https://releases.hashicorp.com/terraform/1.3.6/terraform_1.3.6_linux_amd64.zip
```


download openshift install bins,

```
wget https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/stable/openshift-install-linux.tar.gz
wget https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/stable/openshift-client-linux.tar.gz
```



unzip and put them in ~/bin,
```
sudo yum install git -y
git clone https://github.com/munger1985/OCI-Auto-Scripts.git
```

prepare terraform OCI apikey as key.pem put in the root of repo;


enter shellscript folder;


put pullsecret in the folder shellscripts, you can use mine, but not guarantee it won't expire

# Run installation
```
sh start-prepare.sh 
```
wait for it finished, use the command in use.sh to check and play after
