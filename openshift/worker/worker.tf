variable "bootVolumeSize" {
	default = "111"
}
variable "bootVolVpu" {
	default = "10"
}
resource "oci_core_instance" "worker0" {
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
		private_ip = var.worker0Ip
		subnet_id = var.subnetId
	}
	display_name = "worker0"
	instance_options {
		are_legacy_imds_endpoints_disabled = "false"
	}
	launch_options {
		network_type = "VFIO"
	}
	metadata = {
		"user_data" =  base64encode(data.template_file.workerIgn.rendered)

	}
	shape = var.workerShape
	shape_config {
		memory_in_gbs = var.workerMem
		ocpus = var.workerOcpu
	}
	source_details {
		boot_volume_size_in_gbs = var.bootVolumeSize
		boot_volume_vpus_per_gb = var.bootVolVpu
		source_id =  var.coreos_image_id
		source_type = "image"
	}
}


variable "workerShape" {
	default = "VM.Standard.E4.Flex"
}
variable "workerMem" {
	default = "16"
}
variable "workerOcpu" {
	default = "2"
}
resource "oci_core_instance" "worker1" {
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
		private_ip = var.worker1Ip
		subnet_id = var.subnetId
	}
	display_name = "worker1"
	instance_options {
		are_legacy_imds_endpoints_disabled = "false"
	}
	launch_options {
		network_type = "VFIO"
	}
	metadata = {
		"user_data" =  base64encode(data.template_file.workerIgn.rendered)
	}
	shape = var.workerShape
	shape_config {
		memory_in_gbs = var.workerMem
		ocpus = var.workerOcpu
	}
	source_details {
		boot_volume_size_in_gbs = var.bootVolumeSize
		boot_volume_vpus_per_gb = var.bootVolVpu
		source_id = var.coreos_image_id
		source_type = "image"
	}
}


