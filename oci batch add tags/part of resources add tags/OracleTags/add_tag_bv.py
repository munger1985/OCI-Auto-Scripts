import oci
import traceback

from OracleTags import base_config, make_defined_tags, REGION_LIST, COMPARTMENT_ID


def update_boot_volume_tags():
    for region in REGION_LIST:
        core_client = oci.core.BlockstorageClient(base_config(region))
        try:
            vls = core_client.list_boot_volumes(compartment_id=COMPARTMENT_ID, limit=1000)
        except:
            print(region, 'list_boot_volumes', traceback.format_exc())
            continue

        for v in vls.data:
            vid = v.id
            try:
                get_volume_response = core_client.get_boot_volume(boot_volume_id=vid)
                volume_details = get_volume_response.data

                defined_tags = getattr(volume_details, "defined_tags")
                freeform_tags = getattr(volume_details, "freeform_tags")
                defined_tags = make_defined_tags(defined_tags)

                core_client.update_boot_volume(
                    boot_volume_id=vid,
                    update_boot_volume_details=oci.core.models.UpdateBootVolumeDetails(
                        defined_tags=defined_tags,
                        freeform_tags=freeform_tags
                    )
                )
            except:
                print(region, vid, 'update_boot_volume', traceback.format_exc())
                continue


def update_volume_tags():
    for region in REGION_LIST:
        print(region)
        core_client = oci.core.BlockstorageClient(base_config(region))
        try:
            vls = core_client.list_volumes(compartment_id=COMPARTMENT_ID, limit=1000)
        except:
            print(region, 'list_volumes', traceback.format_exc())
            continue

        for v in vls.data:
            vid = v.id
            try:
                get_volume_response = core_client.get_volume(volume_id=vid)
                volume_details = get_volume_response.data

                defined_tags = getattr(volume_details, "defined_tags")
                freeform_tags = getattr(volume_details, "freeform_tags")
                defined_tags = make_defined_tags(defined_tags)

                core_client.update_volume(
                    volume_id=vid,
                    update_volume_details=oci.core.models.UpdateVolumeDetails(
                        defined_tags=defined_tags,
                        freeform_tags=freeform_tags
                    )
                )
            except:
                print(region, vid, 'update_volume', traceback.format_exc())
                continue


if __name__ == '__main__':
    update_boot_volume_tags()
    update_volume_tags()
