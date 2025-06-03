# This is an automatically generated code sample.
# To make this code sample work in your Oracle Cloud tenancy,
# please replace the values for any parameters whose current values do not fit
# your use case (such as resource IDs, strings containing ‘EXAMPLE’ or ‘unique_id’, and
# boolean, number, and enum parameters with values not fitting your use case).
from email.policy import default

import oci

# Create a default config using DEFAULT profile in default location
# Refer to
# https://docs.cloud.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm#SDK_and_CLI_Configuration_File
# for more info
config = oci.config.from_file()
region="us-phoenix-1"
region="EU-FRANKFURT-1"
region="US-ASHBURN-1"
region="eu-paris-1"

config.update({"region": region})
tenancy_shorts='bxtG'
# Initialize service client with default config file
core_client = oci.core.ComputeClient(config)
# bxtG:
compartment_id='ocid1.compartment.oc1..aaaaaaaau5q457a7teqkjce4oenoiz6bmc4g3s74a5543iqbm7xwplho44fq'
compartment_id='ocid1.compartment.oc1..aaaaaaaapzb3jds7nb5it4t5aoq2ytpyalfm7hidjashb7jmbgz3qboeuugq'

# shape='BM.GPU.A100-v2.8'
# shape='VM.Standard.E4.Flex'
# Send the request to service, some parameters are not required, see API
# doc for more info
# shapeList = [
# 'BM.GPU.A100-v2.8',
# 'VM.GPU.A10.1',
# "VM.Standard.E4.Flex",
# "VM.Standard.E5.Flex",
#
# ]


identity_client = oci.identity.IdentityClient(config)
list_regions_response = identity_client.list_regions()
regions = list_regions_response.data
regionNames= [item.name for item in regions]
def checkReport(shape, region, AD):

    config.update({"region": region})

    # region_api_parameter = region[:-2]

    core_client = oci.core.ComputeClient(config)
    # availability_domain = f"{tenancy_shorts}:{region_api_parameter}-AD-{AD_NO}"
    # shape to lower case
    if 'flex' in shape.lower():
        create_compute_capacity_report_response = core_client.create_compute_capacity_report(
            create_compute_capacity_report_details=oci.core.models.CreateComputeCapacityReportDetails(
                compartment_id=compartment_id,
                availability_domain=AD,
                shape_availabilities=[
                    oci.core.models.CreateCapacityReportShapeAvailabilityDetails(
                        instance_shape=shape,
                        instance_shape_config=oci.core.models.CapacityReportInstanceShapeConfig(
                            ocpus=1.0,
                            memory_in_gbs=16.0)
                    )
                ]
            ),
             )
    else:
        create_compute_capacity_report_response = core_client.create_compute_capacity_report(
            create_compute_capacity_report_details=oci.core.models.CreateComputeCapacityReportDetails(
                compartment_id=compartment_id,
                availability_domain=AD,
                shape_availabilities=[
                    oci.core.models.CreateCapacityReportShapeAvailabilityDetails(
                        instance_shape=shape,
                    )
                ]
            ),
        )

    return create_compute_capacity_report_response.data

import gradio as gr
# def listShape(region):
#     config['region'] = region
#     shapeClient = oci.core.ComputeClient(config=config)
#
#     # Fetch and sort available shapes in the region
#     shapes_in_home_region = shapeClient.list_shapes(compartment_id).data
#
#     shapeList = [shape.shape for shape in shapes_in_home_region]
#     return gr.update(choices=shapeList ,value=shapeList[0])

def listAdAndShape(region):
    config['region'] = region

    identity_client = oci.identity.IdentityClient(config)

    availability_domains = oci.pagination.list_call_get_all_results(
        identity_client.list_availability_domains,
        compartment_id
    ).data
    AD_Names = [item.name for item in availability_domains]
    print(AD_Names)

    shapeClient = oci.core.ComputeClient(config=config)

    shapes_in_home_region = shapeClient.list_shapes(compartment_id).data

    shapeList = [shape.shape for shape in shapes_in_home_region]
    return gr.update(choices=shapeList ,value=shapeList[0]) , gr.update(choices=AD_Names ,value=AD_Names[0])

with gr.Blocks(theme=gr.themes.Glass()) as demo:
    region  =gr.Dropdown(regionNames, label="Regions", info="select your subscribed region")
    shape = gr.Dropdown( interactive =True, choices=  [], label="Shape"   )
    # shapeGr = gr.Dropdown( choices=  shapeList, label="Shape2" ,value=["VM.Standard.E5.Flex"] )
    ad = gr.Radio([],  interactive =True, label="AD" )
    button = gr.Button("Check Report")
    text=gr.Textbox(label="Report")
    button.click(checkReport,[shape, region,ad],[ text])
    region.select(listAdAndShape, [region], [shape, ad], show_progress='minimal')
#

if __name__ == "__main__":
    demo.launch()
