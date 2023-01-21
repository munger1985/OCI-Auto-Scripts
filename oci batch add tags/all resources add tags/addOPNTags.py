import oci
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--compartment-id', type=str, help='compartment ocid', required=True)
parser.add_argument('-p', '--partner-id', type=str, help='partner id', required=True)
parser.add_argument('-o', '--opportunity-id', type=str, help='opportunity id', required=True)
parser.add_argument('-w', '--workload', type=str, help='workload', required=True)
parser.add_argument('-a', '--action', type=str, help='action types', default='create_only', choices=['create_only', 'create_and_tag'], required=True)
args = parser.parse_args()

config = oci.config.from_file()

identity_client = oci.identity.IdentityClient(config)

# Check if tag namespace OPN is exist in tenancy
tag_namespaces = identity_client.list_tag_namespaces(config['tenancy'], include_subcompartments=True).data
for tag_namespace in tag_namespaces:
	if "OPN" == tag_namespace.name:
		print('Tag namespace "OPN" is existing in tenancy, please delete it and retry.')
		raise SystemExit

# Create Tag Namespace
opn_tag_namespace_response = identity_client.create_tag_namespace(
oci.identity.models.CreateTagNamespaceDetails(
    compartment_id = args.compartment_id,
    name = "OPN",
    description = "OPN"
)
)
opn_tagnamespace_id = opn_tag_namespace_response.data.id
print('Tag namespace "OPN" has been created.')

# Create OPN Tag PartnerID
value_partner_id = oci.identity.models.EnumTagDefinitionValidator(
validator_type = "ENUM",
values = [args.partner_id]
)

opn_tag_partner_id_response = identity_client.create_tag(
opn_tagnamespace_id,
oci.identity.models.CreateTagDetails(
	name = "PartnerID",
	description = "PartnerID",
	validator = value_partner_id
	)
)
opn_tag_partner_id_id = opn_tag_partner_id_response.data.id
print('Tag key "PartnerID" has been created.')

# Create OPN Tag OpportunityID
value_opp_id = oci.identity.models.EnumTagDefinitionValidator(
validator_type = "ENUM",
values = [args.opportunity_id]
)

opn_tag_opp_id_response = identity_client.create_tag(
opn_tagnamespace_id, 
oci.identity.models.CreateTagDetails(
	name = "OpportunityID",
	description = "OpportunityID",
	validator = value_opp_id
	)
)
opn_tag_opp_id_id = opn_tag_opp_id_response.data.id
print('Tag key "OpportunityID" has been created.')

# Create OPN Tag Workload
value_workload = oci.identity.models.EnumTagDefinitionValidator(
validator_type = "ENUM",
values = [args.workload]
)

opn_tag_workload_response = identity_client.create_tag(
opn_tagnamespace_id, 
oci.identity.models.CreateTagDetails(
	name = "Workload",
	description = "Workload",
	validator = value_workload
	)
)
opn_tag_workload_id = opn_tag_workload_response.data.id
print('Tag key "Workload" has been created.')

# Set OPN tags as default tags in compartment
identity_client.create_tag_default(
oci.identity.models.CreateTagDefaultDetails(
	compartment_id = args.compartment_id,
	is_required = False,
	tag_definition_id = opn_tag_partner_id_id,
	value = args.partner_id
	)
)

identity_client.create_tag_default(
oci.identity.models.CreateTagDefaultDetails(
	compartment_id = args.compartment_id,
	is_required = False,
	tag_definition_id = opn_tag_opp_id_id,
	value = args.opportunity_id
	)
)

identity_client.create_tag_default(
oci.identity.models.CreateTagDefaultDetails(
	compartment_id = args.compartment_id,
	is_required = False,
	tag_definition_id = opn_tag_workload_id,
	value = args.workload
	)
)

compartment_name = identity_client.get_compartment(args.compartment_id).data.name
print('Default tags have been set for compartment {}.'.format(compartment_name))


if 'create_and_tag' == args.action:

	opn_tags = {
		"OPN": {
			"PartnerID": args.partner_id, 
			"OpportunityID": args.opportunity_id, 
			"Workload": args.workload
		}
	}

	def add_tags(opn_tags, obj_name, list_object, update_object, update_modal_obj, availability_domains=None, obj_namespace=""):

		print('Starting to tag for {} ...'.format(obj_name))

		# if AD generate ad names
		availability_domains_array = [ad.name for ad in availability_domains] if availability_domains else ['single']

		object_array = []
		valid_states = ["RUNNING", "ACTIVE", "AVAILABLE", "STOPPED"]
		for availability_domain in availability_domains_array:
			try:
				if availability_domains:
					object_array = oci.pagination.list_call_get_all_results(list_object, availability_domain=availability_domain, compartment_id=args.compartment_id).data
				elif obj_namespace:
					object_array = oci.pagination.list_call_get_all_results(list_object, obj_namespace, args.compartment_id, fields=['tags']).data
				else:
					object_array = oci.pagination.list_call_get_all_results(list_object, args.compartment_id).data
			except Exception as e:
				print('[ERROR]Failed to get resources list for {}.'.format(obj_name))
				print('[ERROR]The error is {}'.format(e))
				continue
			else:
				if len(object_array) == 0:
					print('    No resourses in {}.'.format(obj_name))
					continue

			for object_details in object_array:
				if not obj_namespace and obj_name != "Network CPEs":
					if object_details.lifecycle_state not in valid_states:
						continue

				# object id - diff between services
				object_details_name = str(object_details.name) if obj_namespace else str(object_details.display_name)
				obj_details_id = str(object_details.name) if obj_namespace else str(object_details.id)

				print('    resources_name = ', object_details_name)

				updating_tags = object_details.defined_tags
				updating_tags.update(opn_tags)

				try:
					if obj_namespace:
						update_object(obj_namespace, obj_details_id, update_modal_obj(defined_tags=updating_tags))
					elif obj_name == "Load Balancers":
						update_object(update_modal_obj(defined_tags=updating_tags), obj_details_id)
					else:
						update_object(obj_details_id, update_modal_obj(defined_tags=updating_tags))
				except Exception as e:
					print('[ERROR]Failed to add tags for {}.'.format(object_details_name))
					print('[ERROR]The error is {}'.format(e))
					continue

	regions = identity_client.list_region_subscriptions(config['tenancy']).data
	for region in regions:
		config.update({'region': region.region_name})
		print('Starting to tag resources in region {}:'.format(region.region_name))

		identity_client = oci.identity.IdentityClient(config)

		compute_client = oci.core.ComputeClient(config)
		blockstorage_client = oci.core.BlockstorageClient(config)
		network_client = oci.core.VirtualNetworkClient(config)
		loadbalancer_client = oci.load_balancer.LoadBalancerClient(config)
		network_loadbalancer_client = oci.network_load_balancer.NetworkLoadBalancerClient(config)
		database_client = oci.database.DatabaseClient(config)
		objectstorage_client = oci.object_storage.ObjectStorageClient(config)
		filestorage_client = oci.file_storage.FileStorageClient(config)
		mysql_client = oci.mysql.DbSystemClient(config)
		mysql_backup_client = oci.mysql.DbBackupsClient(config)

		# get availability_domains
		availability_domains = identity_client.list_availability_domains(config["tenancy"]).data

		# get namespace for object storage
		obj_namespace = objectstorage_client.get_namespace().data

		# Compute
		add_tags(opn_tags, "Instances", compute_client.list_instances, compute_client.update_instance, oci.core.models.UpdateInstanceDetails)

		# Block storage
		add_tags(opn_tags, "Boot Volumes", blockstorage_client.list_boot_volumes, blockstorage_client.update_boot_volume, oci.core.models.UpdateBootVolumeDetails, availability_domains)
		add_tags(opn_tags, "Boot Volumes Backups", blockstorage_client.list_boot_volume_backups, blockstorage_client.update_boot_volume_backup, oci.core.models.UpdateBootVolumeBackupDetails)
		add_tags(opn_tags, "Block Volumes", blockstorage_client.list_volumes, blockstorage_client.update_volume, oci.core.models.UpdateVolumeDetails, availability_domains)
		add_tags(opn_tags, "Block Volumes Backups", blockstorage_client.list_volume_backups, blockstorage_client.update_volume_backup, oci.core.models.UpdateVolumeBackupDetails)
		add_tags(opn_tags, "Volume Groups", blockstorage_client.list_volume_groups, blockstorage_client.update_volume_group, oci.core.models.UpdateVolumeGroupDetails)
		add_tags(opn_tags, "Volume Groups Backup", blockstorage_client.list_volume_group_backups, blockstorage_client.update_volume_group_backup, oci.core.models.UpdateVolumeGroupBackupDetails)

		# filestorage
		add_tags(opn_tags, "File Systems", filestorage_client.list_file_systems, filestorage_client.update_file_system, oci.file_storage.models.UpdateFileSystemDetails, availability_domains)
		add_tags(opn_tags, "Mount Targets", filestorage_client.list_mount_targets, filestorage_client.update_mount_target, oci.file_storage.models.UpdateMountTargetDetails, availability_domains)

		# Network
		add_tags(opn_tags, "Network VCNs", network_client.list_vcns, network_client.update_vcn, oci.core.models.UpdateVcnDetails)
		add_tags(opn_tags, "Network Subnets", network_client.list_subnets, network_client.update_subnet, oci.core.models.UpdateSubnetDetails)
		add_tags(opn_tags, "Network CPEs", network_client.list_cpes, network_client.update_cpe, oci.core.models.UpdateCpeDetails)
		add_tags(opn_tags, "Network DHCPs", network_client.list_dhcp_options, network_client.update_dhcp_options, oci.core.models.UpdateDhcpDetails)
		add_tags(opn_tags, "Network IGWs", network_client.list_internet_gateways, network_client.update_internet_gateway, oci.core.models.UpdateInternetGatewayDetails)
		add_tags(opn_tags, "Network IPSECs", network_client.list_ip_sec_connections, network_client.update_ip_sec_connection, oci.core.models.UpdateIPSecConnectionDetails)
		add_tags(opn_tags, "Network LPGs", network_client.list_local_peering_gateways, network_client.update_local_peering_gateway, oci.core.models.UpdateLocalPeeringGatewayDetails)
		add_tags(opn_tags, "Network NATGWs", network_client.list_nat_gateways, network_client.update_nat_gateway, oci.core.models.UpdateNatGatewayDetails)
		add_tags(opn_tags, "Network RPGs", network_client.list_remote_peering_connections, network_client.update_remote_peering_connection, oci.core.models.UpdateRemotePeeringConnectionDetails)
		add_tags(opn_tags, "Network Routes", network_client.list_route_tables, network_client.update_route_table, oci.core.models.UpdateRouteTableDetails)
		add_tags(opn_tags, "Network SLs", network_client.list_security_lists, network_client.update_security_list, oci.core.models.UpdateSecurityListDetails)
		add_tags(opn_tags, "Network SGWs", network_client.list_service_gateways, network_client.update_service_gateway, oci.core.models.UpdateServiceGatewayDetails)
		add_tags(opn_tags, "Network VCircuit", network_client.list_virtual_circuits, network_client.update_virtual_circuit, oci.core.models.UpdateVirtualCircuitDetails)

		# load balancer
		add_tags(opn_tags, "Load Balancers", loadbalancer_client.list_load_balancers, loadbalancer_client.update_load_balancer, oci.load_balancer.models.UpdateLoadBalancerDetails)
		add_tags(opn_tags, "Network Load Balancers", network_loadbalancer_client.list_network_load_balancers, network_loadbalancer_client.update_network_load_balancer, oci.network_load_balancer.models.UpdateNetworkLoadBalancerDetails)

		# Databases
		add_tags(opn_tags, "DB DB Systems", database_client.list_db_systems, database_client.update_db_system, oci.database.models.UpdateDbSystemDetails)
		add_tags(opn_tags, "DB Autonomous", database_client.list_autonomous_databases, database_client.update_autonomous_database, oci.database.models.UpdateAutonomousDatabaseDetails)

		# Object storage
		add_tags(opn_tags, "Object Storage Buckets", objectstorage_client.list_buckets, objectstorage_client.update_bucket, oci.object_storage.models.UpdateBucketDetails, obj_namespace=obj_namespace)

		# MySQL
		add_tags(opn_tags, "Mysql DB Systems", mysql_client.list_db_systems, mysql_client.update_db_system, oci.mysql.models.UpdateDbSystemDetails)
		add_tags(opn_tags, "Mysql DB Backups", mysql_backup_client.list_backups, mysql_backup_client.update_backup, oci.mysql.models.UpdateBackupDetails)

		print('Completed tagging resources in {}.\n'.format(region.region_name))

	print('OPN tags have been tagged for resources above. Please check if any error occurred, and tag them manually.')