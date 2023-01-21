locals {
	ApiNlbIP_Private=element( data.oci_network_load_balancer_network_load_balancer.api_network_load_balancer.ip_addresses,1).ip_address
#	ApiLbIp=element(oci_load_balancer_load_balancer.apilb.ip_address_details, 0).ip_address
	iPEnd=element(split(".", local.ApiNlbIP_Private ),3)
	AppsNlbIP_Public=element( data.oci_network_load_balancer_network_load_balancer.apps_network_load_balancer.ip_addresses,0).ip_address
	ApiNlbIP_Public=element( data.oci_network_load_balancer_network_load_balancer.api_network_load_balancer.ip_addresses,0).ip_address


}
resource "oci_dns_zone" "ocp_zone" {
	#Required
	compartment_id = var.compartment_ocid
	name = var.zone_name
	zone_type = "PRIMARY"
	scope = var.zone_scope
	view_id = var.dns_view_id
}

##there seems a bug, i can not create them all in one rrset
resource "oci_dns_rrset" "api_rr" {
	#Required
	domain = "api.c4.${oci_dns_zone.ocp_zone.name}"
	rtype = var.rrset_rtype
	zone_name_or_id = oci_dns_zone.ocp_zone.id
	scope           = var.zone_scope
	#Optional
	compartment_id = var.compartment_ocid
	items {
		#Required
		domain = "api.c4.${oci_dns_zone.ocp_zone.name}"
		rdata = local.ApiNlbIP_Public
		rtype  = "A"
		ttl    = 3600
	}
	view_id         = var.dns_view_id
}
resource "oci_dns_rrset" "apiint_rr" {
	#Required
	domain = "api-int.c4.${oci_dns_zone.ocp_zone.name}"
	rtype = var.rrset_rtype
	zone_name_or_id = oci_dns_zone.ocp_zone.id
	scope           = var.zone_scope
	#Optional
	compartment_id = var.compartment_ocid
	items {
		#Required
		domain = "api-int.c4.${oci_dns_zone.ocp_zone.name}"
		rdata = local.ApiNlbIP_Public
		rtype  = "A"
		ttl    = 3600
	}
	view_id         = var.dns_view_id
}
resource "oci_dns_rrset" "generic_rr" {
	#Required
	domain = "*.apps.c4.${oci_dns_zone.ocp_zone.name}"

	rtype = var.rrset_rtype
	zone_name_or_id = oci_dns_zone.ocp_zone.id
	scope           = var.zone_scope
	#Optional
	compartment_id = var.compartment_ocid
	items {
		#Required
		domain = "*.apps.c4.${oci_dns_zone.ocp_zone.name}"

		rdata = local.AppsNlbIP_Public
		rtype  = "A"
		ttl    = 3600
	}
	view_id         = var.dns_view_id
}
resource "oci_dns_rrset" "bootstrap_rr" {
	#Required
	domain = "bootstrap.c4.${oci_dns_zone.ocp_zone.name}"
	rtype = var.rrset_rtype
	zone_name_or_id = oci_dns_zone.ocp_zone.id
	scope           = var.zone_scope
	#Optional
	compartment_id = var.compartment_ocid
	items {
		#Required
		domain = "bootstrap.c4.${oci_dns_zone.ocp_zone.name}"
		rdata = var.bootStrapIp
		rtype  = "A"
		ttl    = 3600
	}
	view_id         = var.dns_view_id
}
resource "oci_dns_rrset" "master0" {
	#Required
	domain = "master0.c4.${oci_dns_zone.ocp_zone.name}"
	rtype = var.rrset_rtype
	zone_name_or_id = oci_dns_zone.ocp_zone.id
	scope           = var.zone_scope
	#Optional
	compartment_id = var.compartment_ocid
	items {
		#Required
		domain = "master0.c4.${oci_dns_zone.ocp_zone.name}"
		rdata = var.master0Ip
		rtype  = "A"
		ttl    = 3600
	}
	view_id         = var.dns_view_id
}
resource "oci_dns_rrset" "master1" {
	#Required
	domain = "master1.c4.${oci_dns_zone.ocp_zone.name}"
	rtype = var.rrset_rtype
	zone_name_or_id = oci_dns_zone.ocp_zone.id
	scope           = var.zone_scope
	#Optional
	compartment_id = var.compartment_ocid
	items {
		#Required
		domain = "master1.c4.${oci_dns_zone.ocp_zone.name}"
		rdata = var.master1Ip
		rtype  = "A"
		ttl    = 3600
	}
	view_id         = var.dns_view_id
}
resource "oci_dns_rrset" "master2" {
	#Required
	domain = "master2.c4.${oci_dns_zone.ocp_zone.name}"
	rtype = var.rrset_rtype
	zone_name_or_id = oci_dns_zone.ocp_zone.id
	scope           = var.zone_scope
	#Optional
	compartment_id = var.compartment_ocid
	items {
		#Required
		domain = "master2.c4.${oci_dns_zone.ocp_zone.name}"
		rdata = var.master2Ip
		rtype  = "A"
		ttl    = 3600
	}
	view_id         = var.dns_view_id
}

resource "oci_dns_rrset" "worker0" {
	#Required
	domain = "worker0.c4.${oci_dns_zone.ocp_zone.name}"
	rtype = var.rrset_rtype
	zone_name_or_id = oci_dns_zone.ocp_zone.id
	scope           = var.zone_scope
	#Optional
	compartment_id = var.compartment_ocid
	items {
		#Required
		domain = "worker0.c4.${oci_dns_zone.ocp_zone.name}"
		rdata = var.worker0Ip
		rtype  = "A"
		ttl    = 3600
	}
	view_id         = var.dns_view_id
}

resource "oci_dns_rrset" "worker1" {
	#Required
	domain = "worker1.c4.${oci_dns_zone.ocp_zone.name}"
	rtype = var.rrset_rtype
	zone_name_or_id = oci_dns_zone.ocp_zone.id
	scope           = var.zone_scope
	#Optional
	compartment_id = var.compartment_ocid
	items {
		#Required
		domain = "worker1.c4.${oci_dns_zone.ocp_zone.name}"
		rdata = var.worker1Ip
		rtype  = "A"
		ttl    = 3600
	}
	view_id         = var.dns_view_id
}
#resource "oci_dns_view" "test_view" {
#	compartment_id = var.compartment_ocid
#	scope          = "PRIVATE"
#}
#
resource "oci_dns_zone" "test_zone_ptr" {
	#Required
	compartment_id = var.compartment_ocid
	name = var.zone_name_ptr
	zone_type = "PRIMARY"
	scope = var.zone_scope
	view_id = var.dns_view_id
	#Optional
	#	defined_tags = var.zone_defined_tags
	#	external_masters {
	#		#Required
	#		address = var.zone_external_masters_address
	#
	#		#Optional
	#		port = var.zone_external_masters_port
	#		tsig_key_id = oci_dns_tsig_key.test_tsig_key.id
	#	}
	#	freeform_tags = var.zone_freeform_tags
}


resource "oci_dns_rrset" "worker0_ptr" {
	#Required
	domain = "${element(split(".",var.worker0Ip),3)}.${oci_dns_zone.test_zone_ptr.name}"
	rtype = "PTR"
	zone_name_or_id = oci_dns_zone.test_zone_ptr.id
	scope           = var.zone_scope
	#Optional
	compartment_id = var.compartment_ocid
	items {
		#Required
		domain = "${element(split(".",var.worker0Ip),3)}.${oci_dns_zone.test_zone_ptr.name}"

		rdata = "worker0.c4.${oci_dns_zone.ocp_zone.name}"
		rtype  = "PTR"
		ttl    = 3600
	}
	view_id         = var.dns_view_id
}
resource "oci_dns_rrset" "worker1_ptr" {
	#Required
	domain = "${element(split(".",var.worker1Ip),3)}.${oci_dns_zone.test_zone_ptr.name}"
	rtype = "PTR"
	zone_name_or_id = oci_dns_zone.test_zone_ptr.id
	scope           = var.zone_scope
	#Optional
	compartment_id = var.compartment_ocid
	items {
		#Required
		domain = "${element(split(".",var.worker1Ip),3)}.${oci_dns_zone.test_zone_ptr.name}"

		rdata = "worker1.c4.${oci_dns_zone.ocp_zone.name}"
		rtype  = "PTR"
		ttl    = 3600
	}
	view_id         = var.dns_view_id
}




resource "oci_dns_rrset" "api_ptr" {
	#Required
	domain = "${local.iPEnd}.${oci_dns_zone.test_zone_ptr.name}"
	rtype = "PTR"
	zone_name_or_id = oci_dns_zone.test_zone_ptr.id
	scope           = var.zone_scope
	#Optional
	compartment_id = var.compartment_ocid
	items {
		#Required
		domain = "${local.iPEnd}.${oci_dns_zone.test_zone_ptr.name}"


		rdata = "api.c4.${oci_dns_zone.ocp_zone.name}"
		rtype  = "PTR"
		ttl    = 3600
	}
	items {
		#Required
		domain = "${local.iPEnd}.${oci_dns_zone.test_zone_ptr.name}"


		rdata = "api-int.c4.${oci_dns_zone.ocp_zone.name}"
		rtype  = "PTR"
		ttl    = 3600
	}
	view_id         = var.dns_view_id
}
#resource "oci_dns_rrset" "apiint_ptr" {
#	#Required
#	domain = "${local.iPEnd}.${oci_dns_zone.test_zone_ptr.name}"
#	rtype = "PTR"
#	zone_name_or_id = oci_dns_zone.test_zone_ptr.id
#	scope           = var.zone_scope
#	#Optional
#	compartment_id = var.compartment_ocid
#	items {
#		#Required
#		domain = "${local.iPEnd}.${oci_dns_zone.test_zone_ptr.name}"
#
#
#		rdata = "api-int.c4.${oci_dns_zone.ocp_zone.name}"
#		rtype  = "PTR"
#		ttl    = 3600
#	}
#	view_id         = var.dns_view_id
#}
resource "oci_dns_rrset" "bs_ptr" {
	#Required
	domain = "${element(split(".",var.bootStrapIp),3)}.${oci_dns_zone.test_zone_ptr.name}"
	rtype = "PTR"
	zone_name_or_id = oci_dns_zone.test_zone_ptr.id
	scope           = var.zone_scope
	#Optional
	compartment_id = var.compartment_ocid
	items {
		#Required
		domain = "${element(split(".",var.bootStrapIp),3)}.${oci_dns_zone.test_zone_ptr.name}"


		rdata = "bootstrap.c4.${oci_dns_zone.ocp_zone.name}"
		rtype  = "PTR"
		ttl    = 3600
	}
	view_id         = var.dns_view_id
}
resource "oci_dns_rrset" "master0_ptr" {
	#Required
	domain = "${element(split(".",var.master0Ip),3)}.${oci_dns_zone.test_zone_ptr.name}"
	rtype = "PTR"
	zone_name_or_id = oci_dns_zone.test_zone_ptr.id
	scope           = var.zone_scope
	#Optional
	compartment_id = var.compartment_ocid
	items {
		#Required
		domain = "${element(split(".",var.master0Ip),3)}.${oci_dns_zone.test_zone_ptr.name}"


		rdata = "master0.c4.${oci_dns_zone.ocp_zone.name}"
		rtype  = "PTR"
		ttl    = 3600
	}
	view_id         = var.dns_view_id
}
resource "oci_dns_rrset" "master1_ptr" {
	#Required
	domain = "${element(split(".",var.master1Ip),3)}.${oci_dns_zone.test_zone_ptr.name}"
	rtype = "PTR"
	zone_name_or_id = oci_dns_zone.test_zone_ptr.id
	scope           = var.zone_scope
	#Optional
	compartment_id = var.compartment_ocid
	items {
		#Required
		domain = "${element(split(".",var.master1Ip),3)}.${oci_dns_zone.test_zone_ptr.name}"


		rdata = "master1.c4.${oci_dns_zone.ocp_zone.name}"
		rtype  = "PTR"
		ttl    = 3600
	}
	view_id         = var.dns_view_id
}
resource "oci_dns_rrset" "master2_ptr" {
	#Required
	domain = "${element(split(".",var.master2Ip),3)}.${oci_dns_zone.test_zone_ptr.name}"
	rtype = "PTR"
	zone_name_or_id = oci_dns_zone.test_zone_ptr.id
	scope           = var.zone_scope
	#Optional
	compartment_id = var.compartment_ocid
	items {
		#Required
		domain = "${element(split(".",var.master2Ip),3)}.${oci_dns_zone.test_zone_ptr.name}"


		rdata = "master2.c4.${oci_dns_zone.ocp_zone.name}"
		rtype  = "PTR"
		ttl    = 3600
	}
	view_id         = var.dns_view_id
}
#data "oci_dns_view" "test_view" {
#	#Required
#	view_id = oci_dns_view.test_view.id
#	scope = "PRIVATE"
#}
#data "oci_dns_records" "test_records" {
#	#Required
##	oci_dns_rrset=
#	zone_name_or_id = oci_dns_zone_name_or.test_zone_name_or.id
#
#	#Optional
#	compartment_id = var.compartment_ocid
#	domain = var.record_domain
#	domain_contains = var.record_domain_contains
#	rtype = var.record_rtype
#	scope = var.record_scope
#	view_id = oci_dns_view.test_view.id
##	zone_version = var.record_zone_version
#}

#data "oci_dns_rrset" "test_rrset" {
#	#Required
#	domain = var.rrset_domain
#	rtype = var.rrset_rtype
#	zone_name_or_id = oci_dns_zone.oc_zone.id
#
#	#Optional
#	compartment_id = var.compartment_ocid
##	scope = var.rrset_scope
#	view_id = oci_dns_view.test_view.id
#}
#data "oci_dns_view" "vcn_view" {
#	#Required
#	view_id = oci_dns_view.test_view.id
#	scope = "PRIVATE"
#}