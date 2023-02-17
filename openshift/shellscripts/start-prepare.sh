### paste pull secret here in the file name pullsecret.txt
rm -rf ~/newinstall
mkdir ~/newinstall
cp * ~/newinstall/
pushd ~/newinstall
ssh-keygen -t ed25519 -N '' -f sshkey
python pycon.py
pkill python

python -m http.server 8888 &


openshift-install create manifests --dir ./
openshift-install create ignition-configs --dir  ./
popd
pushd ../
#prepare terraform creds and run tf
pwd

terraform init
terraform apply --auto-approve
pushd bootstrap
pwd
sleep 5

terraform init
terraform apply --var-file=../terraform.tfvars  --auto-approve
popd
pushd master
terraform init
terraform apply --var-file=../terraform.tfvars  --auto-approve
popd
pushd worker

terraform init
terraform apply --var-file=../terraform.tfvars  --auto-approve
