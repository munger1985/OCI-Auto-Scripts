 ## check progress
 openshift-install --dir ~/newinstall    wait-for install-complete   --log-level=info
 ###output the info for login and console url

 export KUBECONFIG=/home/opc/newinstall/auth/kubeconfig


 oc get csr -o go-template='{{range .items}}{{if not .status}}{{.metadata.name}}{{"\n"}}{{end}}{{end}}' |
xargs --no-run-if-empty oc adm certificate approve

 oc get node

 #verify image registry， check if pods are running, if not please refer to https://docs.okd.io/4.11/registry/configuring_registry_storage/configuring-registry-storage-baremetal.html
  oc get pod -n openshift-image-registry

oc new-app rails-postgresql-example
oc get po
