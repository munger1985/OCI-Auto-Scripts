import oci
import traceback

from OracleTags import base_config, COMPARTMENT_ID, make_defined_tags, REGION_LIST


def update_vncs():
    for region in REGION_LIST:
        core_client = oci.core.VirtualNetworkClient(base_config(region))
        try:
            vls = core_client.list_vcns(compartment_id=COMPARTMENT_ID)
        except:
            print(region, 'list_vcns', traceback.format_exc())
            continue

        for v in vls.data:
            vid = v.id
            try:
                one_response = core_client.get_vcn(vcn_id=vid)
                one_detail = one_response.data

                defined_tags = getattr(one_detail, "defined_tags")
                freeform_tags = getattr(one_detail, "freeform_tags")
                defined_tags = make_defined_tags(defined_tags)

                core_client.update_vcn(
                    vcn_id=vid,
                    update_vcn_details=oci.core.models.UpdateVcnDetails(
                        defined_tags=defined_tags,
                        freeform_tags=freeform_tags
                    )
                )
            except:
                print(region, vid, 'update_vcn', traceback.format_exc())
                continue


def update_subnet():
    for region in REGION_LIST:
        core_client = oci.core.VirtualNetworkClient(base_config(region))
        try:
            vls = core_client.list_subnets(compartment_id=COMPARTMENT_ID)
        except:
            print(region, 'list_subnets', traceback.format_exc())
            continue

        for v in vls.data:
            vid = v.id
            try:
                one_response = core_client.get_subnet(subnet_id=vid)
                one_detail = one_response.data

                defined_tags = getattr(one_detail, "defined_tags")
                freeform_tags = getattr(one_detail, "freeform_tags")
                defined_tags = make_defined_tags(defined_tags)

                core_client.update_subnet(
                    subnet_id=vid,
                    update_subnet_details=oci.core.models.UpdateSubnetDetails(
                        defined_tags=defined_tags,
                        freeform_tags=freeform_tags
                    )
                )
            except:
                print(region, vid, 'update_subnet', traceback.format_exc())
                continue


def update_igw():
    for region in REGION_LIST:
        core_client = oci.core.VirtualNetworkClient(base_config(region))
        try:
            vls = core_client.list_internet_gateways(compartment_id=COMPARTMENT_ID)
        except:
            print(region, 'list_internet_gateways', traceback.format_exc())
            continue

        for v in vls.data:
            vid = v.id
            try:
                one_response = core_client.get_internet_gateway(ig_id=vid)
                one_detail = one_response.data

                defined_tags = getattr(one_detail, "defined_tags")
                freeform_tags = getattr(one_detail, "freeform_tags")
                defined_tags = make_defined_tags(defined_tags)

                core_client.update_internet_gateway(
                    ig_id=vid,
                    update_internet_gateway_details=oci.core.models.UpdateInternetGatewayDetails(
                        defined_tags=defined_tags,
                        freeform_tags=freeform_tags
                    )
                )
            except:
                print(region, vid, 'update_internet_gateway', traceback.format_exc())
                continue


def update_ngw():
    for region in REGION_LIST:
        core_client = oci.core.VirtualNetworkClient(base_config(region))
        try:
            vls = core_client.list_nat_gateways(compartment_id=COMPARTMENT_ID)
        except:
            print(region, 'list_nat_gateways', traceback.format_exc())
            continue

        for v in vls.data:
            vid = v.id
            try:
                one_response = core_client.get_nat_gateway(nat_gateway_id=vid)
                one_detail = one_response.data

                defined_tags = getattr(one_detail, "defined_tags")
                freeform_tags = getattr(one_detail, "freeform_tags")
                defined_tags = make_defined_tags(defined_tags)

                core_client.update_nat_gateway(
                    nat_gateway_id=vid,
                    update_nat_gateway_details=oci.core.models.UpdateNatGatewayDetails(
                        defined_tags=defined_tags,
                        freeform_tags=freeform_tags
                    )
                )
            except:
                print(region, vid, 'update_nat_gateway', traceback.format_exc())
                continue


def update_vnic():
    for region in REGION_LIST:
        compute_client = oci.core.ComputeClient(base_config(region))
        core_client = oci.core.VirtualNetworkClient(base_config(region))
        try:
            vls = compute_client.list_vnic_attachments(compartment_id=COMPARTMENT_ID, limit=1000)
        except:
            print(region, 'list_vnic_attachments', traceback.format_exc())
            continue

        for v in vls.data:
            vid = v.vnic_id
            try:
                one_response = core_client.get_vnic(vnic_id=vid)
                one_detail = one_response.data

                defined_tags = getattr(one_detail, "defined_tags")
                freeform_tags = getattr(one_detail, "freeform_tags")
                defined_tags = make_defined_tags(defined_tags)

                core_client.update_vnic(
                    vnic_id=vid,
                    update_vnic_details=oci.core.models.UpdateVnicDetails(
                        defined_tags=defined_tags,
                        freeform_tags=freeform_tags
                    )
                )
            except:
                print(region, vid, 'update_vnic', traceback.format_exc())
                continue


if __name__ == '__main__':
    update_vncs()
    update_subnet()
    update_igw()
    update_ngw()
    update_vnic()
