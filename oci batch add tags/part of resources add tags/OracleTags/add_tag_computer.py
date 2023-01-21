import oci
import traceback

from OracleTags import base_config, COMPARTMENT_ID, make_defined_tags, REGION_LIST


def update_computer_tags():
    for region in REGION_LIST:
        config = base_config(region)
        core_client = oci.core.ComputeClient(config)
        try:
            vls = core_client.list_instances(compartment_id=COMPARTMENT_ID, limit=1000)
        except:
            print(region, 'list_instances', traceback.format_exc())
            continue

        for v in vls.data:
            vid = v.id
            try:
                get_one_response = core_client.get_instance(instance_id=vid)
                one_details = get_one_response.data

                defined_tags = getattr(one_details, "defined_tags")
                freeform_tags = getattr(one_details, "freeform_tags")
                defined_tags = make_defined_tags(defined_tags)

                core_client.update_instance(
                    instance_id=vid,
                    update_instance_details=oci.core.models.UpdateInstanceDetails(
                        defined_tags=defined_tags,
                        freeform_tags=freeform_tags
                    )
                )
            except:
                print(region, vid, 'update_instance', traceback.format_exc())
                continue


if __name__ == '__main__':
    update_computer_tags()
