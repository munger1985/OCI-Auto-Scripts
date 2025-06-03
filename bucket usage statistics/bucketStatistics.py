import oci
import gradio as gr
REGION = None
def get_oci_config():
    config = oci.config.from_file()
    return config

def get_oci_regions():
    """获取所有可用OCI Region列表"""
    try:
        config = oci.config.from_file()
        identity_client = oci.identity.IdentityClient(config)
        response = identity_client.list_regions()

        return [region.name for region in response.data]
    except Exception as e:
        print(f"获取Region列表失败: {str(e)}")
        return []
def update_selected_region(selected_region):
    """更新全局region的回调函数"""
    global REGION
    REGION = selected_region

def get_compartments(identity_client,compartment_id):
    compartments = []
    response = identity_client.list_compartments(compartment_id)
    compartments.extend(response.data)
    for compartment in response.data:
        sub_compartments = get_compartments(identity_client, compartment.id)
        compartments.extend(sub_compartments)
    return compartments
def get_all_compartments( ):
    config = oci.config.from_file()
    identity_client = oci.identity.IdentityClient(config)
    tenancy_id = config["tenancy"]
    compartments = []

    response = identity_client.list_compartments(tenancy_id)
    compartments.extend(response.data)
    for compartment in response.data:
        sub_compartments = get_compartments(identity_client, compartment.id)
        compartments.extend(sub_compartments)

    compartmentIdNameTuples = [(compartment.id, compartment.name) for compartment in compartments]
    compartmentNameList= [ compartment.name for compartment in compartments]
    return compartmentIdNameTuples, compartmentNameList

def get_buckets(compartmentId):
    config = get_oci_config()
    config.update({"region":REGION})
    object_storage = oci.object_storage.ObjectStorageClient(config)
    namespace = object_storage.get_namespace().data
    list_buckets_response = object_storage.list_buckets(namespace_name=namespace,compartment_id=compartmentId)
    return [bucket.name for bucket in list_buckets_response.data]


def get_directories(bucket_name):
    config = get_oci_config()
    object_storage = oci.object_storage.ObjectStorageClient(config)
    namespace = object_storage.get_namespace().data
    directories = set()
    next_start_with = None
    while True:
        list_objects_response = object_storage.list_objects(
            namespace_name=namespace,
            bucket_name=bucket_name,
            delimiter="/",
            start=next_start_with
        )
        for prefix in list_objects_response.data.prefixes:
            directories.add(prefix)
        next_start_with = list_objects_response.data.next_start_with
        if not next_start_with:
            break
    directories.add("")
    return sorted(directories)


def count_objects_and_get_size(bucket_name, prefix):
    config = get_oci_config()
    config.update({"region":REGION})
    object_storage = oci.object_storage.ObjectStorageClient(config)
    namespace = object_storage.get_namespace().data

    total_size = 0
    object_count = 0
    next_start_with = None
    while True:
        list_objects_response = object_storage.list_objects(
            namespace_name=namespace,
            bucket_name=bucket_name,
            prefix=prefix,
            start=next_start_with,
            fields="name,size"
        )
        for obj in list_objects_response.data.objects:
            if obj.size is not None:
                total_size += obj.size
                object_count += 1
                print('counting',prefix, total_size)
        next_start_with = list_objects_response.data.next_start_with
        if not next_start_with:
            break

    return object_count, total_size


def convert_size(size, unit):
    if unit == "MiB":
        return size / (1024 ** 2)
    elif unit == "GiB":
        return size / (1024 ** 3)
    return size


def display_stats(bucket_name, directory, unit):
    count, size = count_objects_and_get_size(bucket_name, directory)
    converted_size = convert_size(size, unit)
    return f"count: {count}, size: {converted_size:.2f} {unit}"


def update_directories(bucket_name):
    directories = get_directories(bucket_name)
    return gr.Dropdown(choices=directories, label="folders")
def update_buckets( region , compartment_name):
    update_selected_region( region  )
    compartment_id = next((id for id, name in compartmentIdNameTuples if name == compartment_name), None)
    buckets = get_buckets(  compartment_id)
    return gr.update(choices=buckets)


compartmentIdNameTuples, compartmentNameList = get_all_compartments()

if __name__ == "__main__":
    with gr.Blocks(theme=gr.themes.Glass()) as demo:

        gr.Markdown("OCI bucket statistics")

        regions = get_oci_regions()
        current_region = oci.config.from_file().get("region", regions[0] if regions else "")
        update_selected_region(current_region)

        # 创建下拉框组件
        region_dropdown = gr.Dropdown(
            choices=regions,
            value=current_region,
            label="Select OCI Region",
            interactive=True
        )

        compartment_dropdown = gr.Dropdown(choices=compartmentNameList, label="select compartment")

        bucket_dropdown = gr.Dropdown(choices=[], label="buckets")
        # 新增获取目录按钮
        # get_dir_button = gr.Button("get folders")
        # directory_dropdown = gr.Dropdown(label="select folder", choices=[])
        directory_dropdown = gr.Textbox(label="folder / prefix")
        unit_dropdown = gr.Dropdown(choices=["Byte", "MiB", "GiB"], value="Byte", label="select unit")
        btn = gr.Button("statistics")
        result_output = gr.Textbox(label="result")
        region_dropdown.change(
            fn=update_buckets,
            inputs=[region_dropdown,compartment_dropdown],
            outputs=bucket_dropdown
        )
        compartment_dropdown.change(
            fn=update_buckets,
            inputs=[region_dropdown, compartment_dropdown],
            outputs=bucket_dropdown
        )
        # 修改为点击获取目录按钮触发更新目录操作
        # get_dir_button.click(
        #     fn=update_directories,
        #     inputs=bucket_dropdown,
        #     outputs=directory_dropdown
        # )
        btn.click(
            fn=display_stats,
            inputs=[bucket_dropdown, directory_dropdown, unit_dropdown],
            outputs=result_output
        )

    demo.launch()
