# data "template_file" "bastion_config" {
#   template = file("config.bastion")
#   vars = {
#     key = tls_private_key.ssh.private_key_pem
#   }
# }

#data "template_file" "bootstrapIgn" {
#  template = file("bootstrap.ign")
#}
#


variable "deployHost" {
  default = ""
}
data "template_file" "workerIgn" {
  template = file("worker.ign")
  vars = {
    deployHost = "${var.deployHost}"
  }
}
#
#
#data "template_file" "masterIgn" {
#  template = file("master.ign")
#}


