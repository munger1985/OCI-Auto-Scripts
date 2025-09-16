import oci
import base64

config = oci.config.from_file()
compartment_id = 'ocid1.compartment.oc1..aaaaaaaau5q457a7teqkjce4oenoiz6bmc4g3s74a5543iqbm7xwplho44fq'

config.update({"region": "ap-melbourne-1"})
stack_name= "EXAMPLE-displayName-Value"

zip_file_path = "oci-hpc-master.zip"  # Replace with actual path
working_directory="oci-hpc-master"   # Optional: Path within ZIP to Terraform files


# Initialize service client with default config file
resource_manager_client = oci.resource_manager.ResourceManagerClient(config)

# Path to your local Terraform ZIP file

# Read and base64 encode the ZIP file
with open(zip_file_path, "rb") as zip_file:
    zip_content = zip_file.read()
    base64_encoded_zip = base64.b64encode(zip_content).decode('utf-8')

# Send the request to service, some parameters are not required, see API doc for more info
create_stack_response = resource_manager_client.create_stack(
    create_stack_details=oci.resource_manager.models.CreateStackDetails(
        compartment_id=compartment_id,
        config_source=oci.resource_manager.models.CreateZipUploadConfigSourceDetails(
            config_source_type="ZIP_UPLOAD",
            zip_file_base64_encoded=base64_encoded_zip,
            working_directory=working_directory
        ),
        display_name=stack_name,
        description="EXAMPLE-description-Value",
        # custom_terraform_provider=oci.resource_manager.models.CustomTerraformProvider(
        #     region="EXAMPLE-region-Value",
        #     namespace="EXAMPLE-namespace-Value",
        #     bucket_name="EXAMPLE-bucketName-Value"),
        # variables={
        #     'EXAMPLE_KEY_odKuD': 'EXAMPLE_VALUE_TgrqNGs8XHRWhMl8DX3f'},
        # terraform_version="EXAMPLE-terraformVersion-Value",
        freeform_tags={
            'EXAMPLE_KEY_IML9E': 'EXAMPLE_VALUE_AzecUD9982DNrclffCkB'},
        # defined_tags={
        #     'EXAMPLE_KEY_FeI1P': {
        #         'EXAMPLE_KEY_XMbGt': 'EXAMPLE--Value'}}
    ),
)

# Get the data from response
print(create_stack_response.data)