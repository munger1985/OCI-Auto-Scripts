data "oci_network_load_balancer_network_load_balancer" "api_network_load_balancer" {
  #Required
  network_load_balancer_id = oci_network_load_balancer_network_load_balancer.api_network_load_balancer.id
}
locals{
  masterIps=[var.master2Ip,var.master1Ip,var.master0Ip]
}

resource "oci_network_load_balancer_network_load_balancer" "api_network_load_balancer" {
  #Required
  compartment_id = var.compartment_ocid
  display_name   = "api-ocp-nlb"
  subnet_id      = var.subnetId
  #	defined_tags = {"Operations.CostCenter"= "42"}
  #	freeform_tags = {"Department"= "Finance"}
  is_preserve_source_destination = "false"
  is_private     = "false"
  lifecycle {
    postcondition {
      condition     =contains(local.masterIps, element(self.ip_addresses,0) )!=true
      error_message = "private ip should not be clashed"
    }
  }
  #	network_security_group_ids = var.network_load_balancer_network_security_group_ids
  #	nlb_ip_version = var.network_load_balancer_nlb_ip_version
  #	reserved_ips {
  #
  #		#Optional
  #		id = var.network_load_balancer_reserved_ips_id
  #	}
}

resource "oci_network_load_balancer_network_load_balancers_backend_sets_unified" "api_backend_set" {
  #Required
  health_checker {
    #Required
    protocol = "TCP"

    #Optional
    #		interval_in_millis = var.backend_set_health_checker_interval_in_millis
    port     = 6443
    #		request_data = var.backend_set_health_checker_request_data
    #		response_body_regex = var.backend_set_health_checker_response_body_regex
    #		response_data = var.backend_set_health_checker_response_data
    #		retries = var.backend_set_health_checker_retries
    #		return_code = var.backend_set_health_checker_return_code
    #		timeout_in_millis = var.backend_set_health_checker_timeout_in_millis
    url_path = "/"
  }
  name                     = "api_ocp_bs"
  network_load_balancer_id = oci_network_load_balancer_network_load_balancer.api_network_load_balancer.id
  policy                   = "FIVE_TUPLE"
  #Optional
  backends  {
    #Required
    port       = 0
    #Optional
    ip_address = var.bootStrapIp
  }
  backends {
    #Required
    port       = 0
    #Optional
    ip_address = var.master2Ip
  }
  backends {
    #Required
    port       = 0
    #Optional
    ip_address = var.master1Ip
  }
  backends {
    #Required
    port       = 0
    #Optional
    ip_address = var.master0Ip
  }
  #	ip_version = var.network_load_balancers_backend_sets_unified_ip_version
  is_preserve_source = "false"

}

resource "oci_network_load_balancer_listener" "api_nlb_listener" {
  #Required
  default_backend_set_name = oci_network_load_balancer_network_load_balancers_backend_sets_unified.api_backend_set.name
#  default_backend_set_name =  oci_network_load_balancer_backend_set.api_backend_set.name

  name                     = "api-ocp-listener"
  network_load_balancer_id = oci_network_load_balancer_network_load_balancer.api_network_load_balancer.id
  port                     = 0
  protocol                 = "TCP_AND_UDP"
  #Optional
  #	ip_version = var.listener_ip_version
}

# below are some other style, you can try if you like
#resource "oci_network_load_balancer_backend_set" "api_backend_set" {
#	#Required
#	health_checker {
#		#Required
#		protocol = "TCP"
#
#		#Optional
#		#		interval_in_millis = var.backend_set_health_checker_interval_in_millis
#		port = 6443
#		#		request_data = var.backend_set_health_checker_request_data
#		#		response_body_regex = var.backend_set_health_checker_response_body_regex
#		#		response_data = var.backend_set_health_checker_response_data
#		#		retries = var.backend_set_health_checker_retries
#		#		return_code = var.backend_set_health_checker_return_code
#		#		timeout_in_millis = var.backend_set_health_checker_timeout_in_millis
#		url_path ="/"
#	}
#	name = "api_ocp_beset"
#	network_load_balancer_id = oci_network_load_balancer_network_load_balancer.api_network_load_balancer.id
#	policy = "FIVE_TUPLE"
#
#}
#resource "oci_network_load_balancer_backend" "master0-be1" {
#	network_load_balancer_id = oci_network_load_balancer_network_load_balancer.api_network_load_balancer.id
#	backend_set_name         = oci_network_load_balancer_backend_set.api_backend_set.name
#	ip_address               = var.master0Ip
#	port                     = 0
#	is_backup                = false
#	is_drain                 = false
#	is_offline               = false
#	weight                   = 1
#}
#resource "oci_network_load_balancer_backend" "master1-be1" {
#	network_load_balancer_id = oci_network_load_balancer_network_load_balancer.api_network_load_balancer.id
#	backend_set_name         = oci_network_load_balancer_backend_set.api_backend_set.name
#	ip_address               = var.master1Ip
#	port                     = 0
#	is_backup                = false
#	is_drain                 = false
#	is_offline               = false
#	weight                   = 1
#}
#resource "oci_network_load_balancer_backend" "master2-be1" {
#	network_load_balancer_id = oci_network_load_balancer_network_load_balancer.api_network_load_balancer.id
#	backend_set_name         = oci_network_load_balancer_backend_set.api_backend_set.name
#	ip_address               = var.master2Ip
#	port                     = 0
#	is_backup                = false
#	is_drain                 = false
#	is_offline               = false
#	weight                   = 1
#}
#resource "oci_network_load_balancer_backend" "bootStrap-be1" {
#	network_load_balancer_id = oci_network_load_balancer_network_load_balancer.api_network_load_balancer.id
#	backend_set_name         = oci_network_load_balancer_backend_set.api_backend_set.name
#	ip_address               = var.bootStrapIp
#	port                     = 0
#	is_backup                = false
#	is_drain                 = false
#	is_offline               = false
#	weight                   = 1
#}
