# cloud account auth
variable "region" {  default="ap-sydney-1"  }
variable "tenancy_ocid" {default="ocid1.tenancy.oc1..aaaaaaaaro7aox2fclu4urtpgsbacnrmjv46e7n4fw3sc2wbq24l7dzf3kba"} 
variable "user_ocid" {}
variable "private_key_path" {
  default = "key.pem"
}
variable "fingerprint" {}
variable "deployHost" {
  default = ""
}
variable "compartment_ocid" {}
variable "coreos_image_id" {}
variable "zone_name" {default = "js.s"}
variable "zone_name_ptr" {}
variable "subnetId" {}
variable "rrset_domain" {
  default = "js.s"
}
variable "zone_scope" {
  default = "PRIVATE"
}
variable "dns_view_id" {
  default = ""
}

variable "rrset_items_ttl" {
  default = "3600"
}
variable "rrset_rtype" {
  default = "A"
}
variable "availability_domain" {
  default = ""
}
variable "master2Ip" {
  default = ""
}
variable "master1Ip" {
  default = ""
}
variable "master0Ip" {
  default = ""
}

variable "bootStrapIp" {
  default = ""
}
variable "worker0Ip" {
  default = ""
}
variable "worker1Ip" {
  default = ""
}