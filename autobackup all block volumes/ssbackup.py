# use streamlit to list all volumes in a oci compartment
import oci
config = oci.config.from_file()
from oci.identity import IdentityClient
config['region']='us-sanjose-1'
config['region']='ap-melbourne-1'
block_storage_client = oci.core.BlockstorageClient(config)
identity_client = IdentityClient(config)
volume_ocid =  'ocid1.bootvolume.oc1.us-sanjose-1.abzwuljr2zf6vjljicbca6jqqxedj7t35x67sxl5jnscm2wwwku53qcc6xtq'
policy_name_to_id = { }
import streamlit as st 

if "selected_volumes" not in st.session_state:
    st.session_state.selected_volumes = []


@st.cache_data
def get_region_backup_policy(  ):
    print('get policy')
    # Get all backup policies and find the "Bronze" policy
    policies = oci.pagination.list_call_get_all_results(
        block_storage_client.list_volume_backup_policies
    ).data
    policy_id = None
    for policy in policies:
        # if policy.display_name == "bronze":
            policy_id = policy.id
            policy_name_to_id[policy.display_name]=policy_id
            # break
    if policy_id is None:
        print("Error: 'Bronze' policy not found")
    return policy_name_to_id
         

policy_name_to_id= get_region_backup_policy()
tenancy_id = config["tenancy"]
policy_names =policy_name_to_id.keys()

# @st.cache_data(ignore_args=["identity_client"])
def get_compartments(identity_client,compartment_id):
    compartments = []
    response = identity_client.list_compartments(compartment_id)
    compartments.extend(response.data)
    for compartment in response.data:
        sub_compartments = get_compartments(identity_client, compartment.id)
        compartments.extend(sub_compartments)
    return compartments
@st.cache_data
def get_compartments_all():
    print('get comp all ' )
    compartments = []
    response = identity_client.list_compartments(tenancy_id)
    compartments.extend(response.data)
    for compartment in response.data:
        sub_compartments = get_compartments(identity_client, compartment.id)
        compartments.extend(sub_compartments)
    return compartments
# Sidebar: Compartment selection
compartments =  get_compartments_all( )
st.sidebar.header("Select Compartment")
compartment_dict = {c.name: c.id for c in compartments}
selected_compartment_name = st.sidebar.selectbox("Compartment", list(compartment_dict.keys()))
selected_compartment_id = compartment_dict[selected_compartment_name]

# Fetch volumes in the selected compartment
@st.cache_data
def list_volumes_in_compartment(compartment_id):
    print('list vol')
    st.session_state.selected_volumes=[]

    volumes = block_storage_client.list_volumes(compartment_id= compartment_id).data
    boot_volumes = block_storage_client.list_boot_volumes(compartment_id= compartment_id).data
    all_v=volumes+boot_volumes
    volume_names = [v.display_name for v in all_v]
    return all_v,volume_names
volumes,volume_names = list_volumes_in_compartment( compartment_id= selected_compartment_id)
# for volume in volumes:
#     policy_id = get_volume_policy(blockstorage_client, volume.id)
#     if policy_id in policy_name_to_id.values():
#         policy_name = next(name for name, pid in policy_name_to_id.items() if pid == policy_id)
#         policy_assignments[volume.display_name] = policy_name
#     else:
#         policy_assignments[volume.display_name] = None

# Filter to keep only volumes with a backup policy


# Fetch backup policies from the root compartment
root_compartment_id = tenancy_id
# backup_policies = block_storage_client.list_volume_backup_policies(compartment_id=root_compartment_id).data
# print(12333,backup_policies)
# policy_names = [p.display_name for p in backup_policies if p.display_name in ["bronze", "silver", "gold"]]
# policy_name_to_id = {p.display_name: p.id for p in backup_policies if p.display_name in ["bronze", "silver", "gold"]}
# Function to get the backup policy for a volume
@st.cache_data
def get_volume_policy( volume_id):
    try:
        print('get vol policy')
        assignment = block_storage_client.get_volume_backup_policy_asset_assignment(asset_id=volume_id).data
        if assignment:
            return assignment[0].policy_id
        return None
    except oci.exceptions.ServiceError:
        return None

# Determine policy assignments for each volume
policy_assignments = {}
for volume in volumes:
    policy_id = get_volume_policy(  volume.id)
    if policy_id in policy_name_to_id.values():
        policy_name = next(name for name, pid in policy_name_to_id.items() if pid == policy_id)
        policy_assignments[volume.display_name] = policy_name
    else:
        policy_assignments[volume.display_name] = None
volume_names = [name for name in volume_names if policy_assignments[name] is   None]
volume_name_to_id = {v.display_name: v.id for v in volumes}
# Categorize volumes by policy
gold_volumes = [name for name, policy in policy_assignments.items() if policy == "gold"]
silver_volumes = [name for name, policy in policy_assignments.items() if policy == "silver"]
bronze_volumes = [name for name, policy in policy_assignments.items() if policy == "bronze"]

# Display layout with two main columns
col1, col2 = st.columns([3, 1])  # Left column wider for multiselect, right for button and policy display

# Left column: Multiselect for volumes
with col1:
    st.header(f"Volumes in {selected_compartment_name}")
    if volume_names:
         st.session_state.selected_volumes = st.multiselect("Select volumes to assign policy", volume_names,default=st.session_state.selected_volumes )
      

    else:
        st.write("No volumes in this compartment")
        selected_volumes = []
    if st.button("Double Click：Select all"):
                st.session_state.selected_volumes = volume_names
                print(st.session_state.selected_volumes)
# Right column: Policy selection and Assign button
with col2:
    st.header("Policy Assignment")
    if policy_names:
        selected_policy = st.radio("Select backup policy", policy_names)
        if st.button("Assign Policy"):
            print(st.session_state.selected_volumes,123234)
            if st.session_state.selected_volumes:
                selected_ocids = [volume_name_to_id[name] for name in st.session_state.selected_volumes]
                selected_policy_id = policy_name_to_id[selected_policy]
                for ocid in selected_ocids:
                    # Remove existing policy assignments
                    assignments = block_storage_client.get_volume_backup_policy_asset_assignment(ocid).data
                    for assignment in assignments:
                        block_storage_client.delete_volume_backup_policy_assignment(assignment.id)
                    # Assign new policy
                    assignment_details = oci.core.models.CreateVolumeBackupPolicyAssignmentDetails(
                        asset_id=ocid,
                        policy_id=selected_policy_id
                    )
                    block_storage_client.create_volume_backup_policy_assignment(assignment_details)
                st.success(f"Assigned {selected_policy} policy to selected volumes")
                        # 清除所有数据缓存
                list_volumes_in_compartment.clear()
                get_volume_policy.clear()
                # 或仅清除特定函数缓存：load_data.clear()
            else:
                st.warning("Please select at least one volume")
    else:
        st.write("No backup policies available")

# Display current policy assignments below
st.header("Volumes with Backup Policies")
col3, col4, col5 = st.columns(3)
with col3:
    st.subheader("Gold")
    if gold_volumes:
        for vol in gold_volumes:
            st.write(vol)
    else:
        st.write("None")
with col4:
    st.subheader("Silver")
    if silver_volumes:
        for vol in silver_volumes:
            st.write(vol)
    else:
        st.write("None")
with col5:
    st.subheader("Bronze")
    if bronze_volumes:
        for vol in bronze_volumes:
            st.write(vol)
    else:
        st.write("None")

        
def assign_backup_policy(block_storage_client, volume_ocid, policy_id):
    assignments = block_storage_client.get_volume_backup_policy_asset_assignment(
            volume_ocid
        ).data
    if assignments:
        for assignment in assignments:
            pass
    else:
        assignment_details = oci.core.models.CreateVolumeBackupPolicyAssignmentDetails(
            asset_id=volume_ocid,
            policy_id=policy_id
        )
        response = block_storage_client.create_volume_backup_policy_assignment(
            assignment_details
        )
        print(f"Successfully assigned 'Bronze' policy to volume: {response.data.id}")

# assign_backup_policy(block_storage_client, volume_ocid, policy_id)