  use it with caution
  pushd ../master
  terraform destroy --var-file=../terraform.tfvars  --auto-approve
  pushd ../worker
  terraform destroy --var-file=../terraform.tfvars  --auto-approve
  pushd ../bootstrap
  terraform destroy --var-file=../terraform.tfvars  --auto-approve
  pushd ../
  terraform destroy --auto-approve

