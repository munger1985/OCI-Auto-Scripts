resource "oci_network_load_balancer_network_load_balancer" "apps_network_load_balancer" {
  #Required
  compartment_id                 = var.compartment_ocid
  display_name                   = "apps-ocp-nlb"
  subnet_id                      = var.subnetId
  is_private                     = "false"
  is_preserve_source_destination = "false"
  lifecycle {
    postcondition {
      condition     =contains(local.masterIps, element(self.ip_addresses,0) )!=true
      error_message = "private ip should not be clashed"
    }
  }
}
data "oci_network_load_balancer_network_load_balancer" "apps_network_load_balancer" {
  #Required
  network_load_balancer_id = oci_network_load_balancer_network_load_balancer.apps_network_load_balancer.id

}

resource "oci_network_load_balancer_listener" "apps_nlb_listener" {
  #Required
  default_backend_set_name = oci_network_load_balancer_network_load_balancers_backend_sets_unified.apps_backend_set.name
#  default_backend_set_name =  oci_network_load_balancer_backend_set.apps_backend_set.name
  name                     = "apps-ocp-listener"
  network_load_balancer_id = oci_network_load_balancer_network_load_balancer.apps_network_load_balancer.id
  port                     = 0
  protocol                 = "TCP_AND_UDP"
  #Optional
  #	ip_version = var.listener_ip_version
}

resource "oci_network_load_balancer_network_load_balancers_backend_sets_unified" "apps_backend_set" {
  #Required
  health_checker {
    protocol = "TCP"
    port     = 22
    url_path = "/"
  }
  name                     = "apps_ocp_bs"
  network_load_balancer_id = oci_network_load_balancer_network_load_balancer.apps_network_load_balancer.id
  policy                   = "FIVE_TUPLE"
  #Optional
  backends {
    port       = 0
    ip_address = var.worker1Ip
  }
  backends {
    port       = 0
    ip_address = var.worker0Ip
  }
  backends {
    port       = 0
    ip_address = var.master0Ip
  }
  backends {
    port       = 0
    ip_address = var.master1Ip
  }
  backends {
    port       = 0
    ip_address = var.master2Ip
  }

	is_preserve_source = "false"

}
# some other style
#resource "oci_network_load_balancer_backend_set" "apps_backend_set" {
#	#Required
#	health_checker {
#		#Required
#		protocol = "TCP"
#
#		#Optional
##		interval_in_millis = var.backend_set_health_checker_interval_in_millis
#		port = 22
##		request_data = var.backend_set_health_checker_request_data
##		response_body_regex = var.backend_set_health_checker_response_body_regex
##		response_data = var.backend_set_health_checker_response_data
##		retries = var.backend_set_health_checker_retries
##		return_code = var.backend_set_health_checker_return_code
##		timeout_in_millis = var.backend_set_health_checker_timeout_in_millis
#		url_path ="/"
#	}
#	name = "apps_ocp_beset"
#	network_load_balancer_id = oci_network_load_balancer_network_load_balancer.apps_network_load_balancer.id
#	policy = "FIVE_TUPLE"
#	#Optional
##	ip_version = var.backend_set_ip_version
#	is_preserve_source = "false"
#}
#resource "oci_network_load_balancer_backend" "worker0-be1" {
#	network_load_balancer_id = oci_network_load_balancer_network_load_balancer.apps_network_load_balancer.id
#	backend_set_name         = oci_network_load_balancer_backend_set.apps_backend_set.name
#	ip_address               = var.worker0Ip
#	port                     = 0
#	is_backup                = false
#	is_drain                 = false
#	is_offline               = false
#	weight                   = 1
#}
#resource "oci_network_load_balancer_backend" "worker1-be1" {
#	network_load_balancer_id = oci_network_load_balancer_network_load_balancer.apps_network_load_balancer.id
#	backend_set_name         = oci_network_load_balancer_backend_set.apps_backend_set.name
#	ip_address               = var.worker1Ip
#	port                     = 0
#	is_backup                = false
#	is_drain                 = false
#	is_offline               = false
#	weight                   = 1
#}
