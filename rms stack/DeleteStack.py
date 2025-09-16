import oci

# Create a default config using DEFAULT profile in default location
# Refer to
# https://docs.cloud.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm#SDK_and_CLI_Configuration_File
# for more info
config = oci.config.from_file()
config.update({"region": "ap-melbourne-1"})

stack_id='ocid1.ormstack.oc1.ap-melbourne-1.amaaaaaaak7gbriam2kfn3gd5ewctu5lf33rzkjyxl3jzjgprm6lx4qvco7a'

# Initialize service client with default config file
resource_manager_client = oci.resource_manager.ResourceManagerClient(config)


# Send the request to service, some parameters are not required, see API
# doc for more info
delete_stack_response = resource_manager_client.delete_stack(
    stack_id=stack_id,
    # opc_request_id="MRR3IHYREMXDHWXIWC0R<unique_ID>",
    # if_match="EXAMPLE-ifMatch-Value"
)

# Get the data from response
print(delete_stack_response.headers)