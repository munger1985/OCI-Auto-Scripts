
import oci

config = oci.config.from_file()

resource_manager_client = oci.resource_manager.ResourceManagerClient(config)

stack_id='ocid1.ormstack.oc1.ap-melbourne-1.amaaaaaaak7gbriam2kfn3gd5ewctu5lf33rzkjyxl3jzjgprm6lx4qvco7a'
job_name='apply a job'
# Load configuration from default location (~/.oci/config)
config.update({"region": "ap-melbourne-1"})



# Create a default config using DEFAULT profile in default location
# Refer to https://docs.cloud.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm#SDK_and_CLI_Configuration_File

# Initialize service client with default config file
resource_manager_client = oci.resource_manager.ResourceManagerClient(config)

# Replace with your stack OCID

# Create job details for APPLY operation
# For APPLY, specify job_operation_details as CreateApplyJobOperationDetails
create_job_details = oci.resource_manager.models.CreateJobDetails(
    stack_id=stack_id,
    display_name=job_name,
    operation="APPLY",  # This is the string value for APPLY operation
    job_operation_details=oci.resource_manager.models.CreateApplyJobOperationDetails(
        execution_plan_strategy="AUTO_APPROVED",  # Options: 'AUTO_APPROVED', 'FROM_PLAN_JOB_ID', etc.
        is_provider_upgrade_required=False,  # Optional
        terraform_advanced_options=oci.resource_manager.models.TerraformAdvancedOptions(
            is_refresh_required=False,
            parallelism=10,
            detailed_log_level="INFO"  # Options: 'ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE'
        )
    ),
    # apply_job_plan_resolution=oci.resource_manager.models.ApplyJobPlanResolution(
    #     is_use_latest_job_id=True,  # Use latest plan job if true
    #     is_auto_approved=True  # Auto-approve if needed
    #     # plan_job_id="ocid1.test.oc1..<unique_ID>EXAMPLE-planJobId-Value"  # Uncomment and set if using 'FROM_PLAN_JOB_ID'
    # ),
    freeform_tags={
        'EXAMPLE_KEY': 'EXAMPLE_VALUE'
    },
)

# Create the job
# Optional: Add opc_request_id and opc_retry_token for idempotency if needed
create_job_response = resource_manager_client.create_job(
    create_job_details=create_job_details,
    opc_request_id="EXAMPLE-OPC-REQUEST-ID",
    # opc_retry_token="EXAMPLE-OPC-RETRY-TOKEN"
)

job = create_job_response.data
job_id = job.id
print(f"Created APPLY job with ID: {job_id}")
import  time
# Poll for job completion
while True:
    job_details = resource_manager_client.get_job(job_id=job_id).data
    print(f"Job state: {job_details.lifecycle_state}")
    if job_details.lifecycle_state in ['SUCCEEDED', 'FAILED', 'CANCELED']:
        break
    time.sleep(30)  # Poll every 30 seconds

# Get execution results
if job_details.lifecycle_state == 'SUCCEEDED':
    # Get job logs (Note: This retrieves up to 20 log entries; use list_job_logs for pagination if needed)
    logs_response = resource_manager_client.get_job_logs(job_id=job_id, limit=100)  # Adjust limit as needed
    print("Job Logs:")
    for log in logs_response.data:
        print(log.message)

    # Get Terraform outputs
    outputs_response = resource_manager_client.list_job_outputs(job_id=job_id)
    print("Terraform Outputs:")
    for output in outputs_response.data:
        print(f"{output.name}: {output.value}")
else:
    print(f"Job failed or was canceled. State: {job_details.lifecycle_state}. Check logs for details.")

# Get the full job data
print(job_details)