variable "bootStrapShape" {
	default ="VM.Standard.E4.Flex"
}
variable "bootStrapMem" {
	default = "16"
}
variable "bootStrapOcpu" {
	default = "2"
}
variable "bootVolSize" {
	default = "111"
}
variable "bootVolVpu" {
	default = "10"
}
resource "oci_core_instance" "bootstrap" {
	agent_config {
		is_management_disabled = "false"
		is_monitoring_disabled = "false"
		plugins_config {
			desired_state = "DISABLED"
			name = "Vulnerability Scanning"
		}
		plugins_config {
			desired_state = "DISABLED"
			name = "Oracle Java Management Service"
		}
		plugins_config {
			desired_state = "DISABLED"
			name = "Oracle Autonomous Linux"
		}
		plugins_config {
			desired_state = "ENABLED"
			name = "OS Management Service Agent"
		}
		plugins_config {
			desired_state = "DISABLED"
			name = "Management Agent"
		}
		plugins_config {
			desired_state = "ENABLED"
			name = "Custom Logs Monitoring"
		}
		plugins_config {
			desired_state = "ENABLED"
			name = "Compute Instance Run Command"
		}
		plugins_config {
			desired_state = "ENABLED"
			name = "Compute Instance Monitoring"
		}
		plugins_config {
			desired_state = "DISABLED"
			name = "Block Volume Management"
		}
		plugins_config {
			desired_state = "DISABLED"
			name = "Bastion"
		}
	}
	availability_config {
		recovery_action = "RESTORE_INSTANCE"
	}
	availability_domain = var.availability_domain
	compartment_id = var.compartment_ocid
	create_vnic_details {
		assign_private_dns_record = "true"
		assign_public_ip = "true"
		private_ip = var.bootStrapIp
		subnet_id =  var.subnetId
	}
	display_name = "oc-bootstrap"
	instance_options {
		are_legacy_imds_endpoints_disabled = "false"
	}
	launch_options {
		network_type = "VFIO"
	}
	metadata = {
		"user_data" =  base64encode(data.template_file.bootstrapIgn.rendered) 
	}
	shape = var.bootStrapShape
	shape_config {
		memory_in_gbs = var.bootStrapMem
		ocpus = var.bootStrapOcpu
	}
	source_details {
		boot_volume_size_in_gbs = var.bootVolSize
		boot_volume_vpus_per_gb = var.bootVolVpu
		source_id = var.coreos_image_id
		source_type = "image"
	}
}
