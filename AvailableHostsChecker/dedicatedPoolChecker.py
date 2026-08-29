#!/usr/bin/env python3
"""
Gradio interface for checking available hosts in an OCI Dedicated Compute Host pool.
# jingsong.liu@oracle.com
This script uses a local OCI API key config (OCI CLI config file).
It counts compute hosts in lifecycle_state=AVAILABLE and instance_id=None
(free/unassigned hosts), groups counts by shape, and shows a table of hosts.

Run with:
    python3 oci_dedicated_hosts_gradio.py

Then open the provided URL in your browser.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import configparser
import os

import gradio as gr
import oci


REGIONS = [
    "us-ashburn-1", "us-phoenix-1", "us-sanjose-1",
    "eu-frankfurt-1", "eu-amsterdam-1", "eu-zurich-1",
    "ap-sydney-1", "ap-melbourne-1", "ap-osaka-1", "ap-seoul-1",
    "ap-jakarta-1", "ap-singapore-1", "me-jeddah-1", "me-dubai-1",
    "sa-saopaulo-1", "uk-london-1", "ca-toronto-1", "ca-montreal-1",
    "ap-kulai-1", "il-jerusalem-1", "uk-cardiff-1",
]


def list_compute_hosts(compartment_id: str, cfg: dict):
    compute = oci.core.ComputeClient(config=cfg)
    resp = oci.pagination.list_call_get_all_results(
        compute.list_compute_hosts,
        compartment_id=compartment_id,
    )
    return resp.data or []


def get_available_profiles():
    config_path = os.path.expanduser("~/.oci/config")
    if not os.path.exists(config_path):
        return ["DEFAULT"]

    config = configparser.ConfigParser()
    config.read(config_path)

    profiles = ["DEFAULT"]
    profiles.extend(section for section in config.sections() if section != "DEFAULT")
    return profiles


def build_hosts_table(hosts, region: str):
    rows = []
    for host in hosts:
        rows.append([
            getattr(host, "id", ""),
            getattr(host, "lifecycle_state", ""),
            region,
            getattr(host, "shape", ""),
        ])
    return rows


def check_hosts(profile, region, all_states):
    try:
        cfg = oci.config.from_file(profile_name=profile)
        cfg["region"] = region
    except Exception as exc:
        return (
            "Failed to load OCI config. Ensure you have an API key configured "
            f"and a valid OCI config file.\nError: {exc}",
            [],
        )

    tenancy_from_config = cfg.get("tenancy")
    if not tenancy_from_config:
        return "Could not determine tenancy OCID from config. Ensure config has 'tenancy='.", []

    try:
        hosts = list_compute_hosts(tenancy_from_config, cfg)
    except Exception as exc:
        return f"Failed to list compute hosts in {region}.\nError: {exc}", []

    by_id = {}
    for host in hosts:
        host_id = getattr(host, "id", None)
        if host_id:
            by_id[host_id] = host
    hosts = list(by_id.values())

    hosts_table = build_hosts_table(hosts, region)
    total_counts_by_shape = Counter(getattr(host, "shape", "UNKNOWN") for host in hosts)
    total_hosts = sum(total_counts_by_shape.values())

    if all_states:
        counts = defaultdict(Counter)
        for host in hosts:
            state = getattr(host, "lifecycle_state", "UNKNOWN")
            shape = getattr(host, "shape", "UNKNOWN")
            counts[state][shape] += 1

        output = ""
        for state in sorted(counts.keys()):
            output += f"State={state}\n"
            for shape, count in counts[state].most_common():
                shape_total = total_counts_by_shape.get(shape, 0)
                output += f"\t{shape}: {count} / total {shape_total}\n"

        return output.strip(), hosts_table

    available = []
    for host in hosts:
        state = getattr(host, "lifecycle_state", None)
        instance_id = getattr(host, "instance_id", None)
        if state == "AVAILABLE" and not instance_id:
            available.append(host)

    counts_by_shape = Counter(getattr(host, "shape", "UNKNOWN") for host in available)
    total = sum(counts_by_shape.values())

    output = (
        f"Total AVAILABLE (unassigned) hosts: {total}\n"
        f"Total hosts: {total_hosts}\n"
    )
    for shape, shape_total in total_counts_by_shape.most_common():
        available_count = counts_by_shape.get(shape, 0)
        output += f"{shape}: AVAILABLE {available_count} / total {shape_total}\n"

    return output.strip(), hosts_table


def query_baremetal_host(profile, region, host_id):
    if not host_id or not host_id.strip():
        return "Please enter a BareMetal host ID."

    try:
        cfg = oci.config.from_file(profile_name=profile)
        cfg["region"] = region
    except Exception as exc:
        return f"Failed to load OCI config.\nError: {exc}"

    try:
        compute = oci.core.ComputeClient(config=cfg)
        host = compute.get_compute_host(compute_host_id=host_id.strip()).data
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return f"Host not found: {host_id} in region {region}."
        return f"Service error ({e.status}): {e.message}"
    except Exception as exc:
        return f"Failed to query host.\nError: {exc}"

    details = []
    for attr in sorted(dir(host)):
        if attr.startswith("_"):
            continue
        try:
            val = getattr(host, attr)
            if callable(val):
                continue
            if isinstance(val, (list, dict)):
                val = str(val)
            details.append(f"{attr}: {val}")
        except Exception:
            pass

    return "\n".join(details)


def format_model_details(model):
    details = []
    for attr in sorted(dir(model)):
        if attr.startswith("_"):
            continue
        try:
            val = getattr(model, attr)
            if callable(val):
                continue
            if isinstance(val, (list, dict)):
                val = str(val)
            details.append(f"{attr}: {val}")
        except Exception:
            pass

    return "\n".join(details)


def query_baremetal_host_by_instance(profile, region, instance_id):
    if not instance_id or not instance_id.strip():
        return "Please enter an Instance OCID."

    instance_id = instance_id.strip()

    try:
        cfg = oci.config.from_file(profile_name=profile)
        cfg["region"] = region
    except Exception as exc:
        return f"Failed to load OCI config.\nError: {exc}"

    tenancy_from_config = cfg.get("tenancy")
    if not tenancy_from_config:
        return "Could not determine tenancy OCID from config. Ensure config has 'tenancy='."

    compute = oci.core.ComputeClient(config=cfg)

    instance_summary = ""
    try:
        instance = compute.get_instance(instance_id=instance_id).data
        instance_summary = (
            "Instance\n"
            f"id: {getattr(instance, 'id', '')}\n"
            f"display_name: {getattr(instance, 'display_name', '')}\n"
            f"shape: {getattr(instance, 'shape', '')}\n"
            f"lifecycle_state: {getattr(instance, 'lifecycle_state', '')}\n"
            f"availability_domain: {getattr(instance, 'availability_domain', '')}\n"
            f"fault_domain: {getattr(instance, 'fault_domain', '')}\n"
        )
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            instance_summary = (
                "Instance\n"
                f"id: {instance_id}\n"
                f"warning: Instance not found in region {region}, continuing to search compute hosts.\n"
            )
        else:
            instance_summary = (
                "Instance\n"
                f"id: {instance_id}\n"
                f"warning: Failed to query instance ({e.status}): {e.message}\n"
            )
    except Exception as exc:
        instance_summary = (
            "Instance\n"
            f"id: {instance_id}\n"
            f"warning: Failed to query instance: {exc}\n"
        )

    try:
        hosts = list_compute_hosts(tenancy_from_config, cfg)
    except oci.exceptions.ServiceError as e:
        return (
            f"{instance_summary}\n"
            f"Failed to list compute hosts in {region} ({e.status}): {e.message}"
        )
    except Exception as exc:
        return f"{instance_summary}\nFailed to list compute hosts in {region}.\nError: {exc}"

    matched_hosts = [host for host in hosts if getattr(host, "instance_id", None) == instance_id]

    if not matched_hosts:
        return (
            f"{instance_summary}\n"
            "BareMetal Host\n"
            "status: NOT_FOUND\n"
            "message: No compute host in this tenancy/region has instance_id equal to the provided Instance OCID.\n"
            "Please verify the region/profile and that this is a BareMetal instance assigned to a compute host."
        )

    output = [instance_summary.strip(), "BareMetal Host"]
    for idx, host in enumerate(matched_hosts, start=1):
        if len(matched_hosts) > 1:
            output.append(f"\nMatched host #{idx}")
        output.append(f"baremetal_host_id: {getattr(host, 'id', '')}")
        output.append(format_model_details(host))

    return "\n".join(output)


def create_interface():
    profiles = get_available_profiles()

    with gr.Blocks(title="OCI Dedicated Hosts Checker", theme=gr.themes.Glass()) as demo:
        gr.Markdown("# OCI Dedicated Pool Checker")
        gr.Markdown("Enter the details and click Submit to check available hosts.")

        profile = gr.Dropdown(
            choices=profiles,
            value="DEFAULT",
            label="OCI Config Profile",
            info="Select the profile from ~/.oci/config",
        )

        region = gr.Dropdown(
            choices=REGIONS,
            value="eu-frankfurt-1",
            label="Region",
            info="Select the OCI region to query.",
        )

        all_states = gr.Checkbox(
            label="Show counts for all lifecycle states",
            value=False,
        )

        submit_btn = gr.Button("Check Hosts", variant="primary")

        output = gr.Textbox(
            label="Results",
            lines=20,
            interactive=False,
        )

        hosts_table = gr.Dataframe(
            headers=["id", "lifecycle_status", "region", "shape"],
            datatype=["str", "str", "str", "str"],
            label="Compute Hosts",
            interactive=False,
            wrap=True,
        )

        submit_btn.click(
            fn=check_hosts,
            inputs=[profile, region, all_states],
            outputs=[output, hosts_table],
        )

        gr.Markdown("---")
        gr.Markdown("### Query a specific BareMetal host by ID")

        bm_host_id = gr.Textbox(
            label="BareMetal Host OCID",
            placeholder="ocid1.computehost.oc1...",
            lines=1,
        )

        bm_query_btn = gr.Button("Query Host Details", variant="secondary")

        bm_output = gr.Textbox(
            label="Host Details",
            lines=25,
            interactive=False,
        )

        bm_query_btn.click(
            fn=query_baremetal_host,
            inputs=[profile, region, bm_host_id],
            outputs=[bm_output],
        )

        gr.Markdown("---")
        gr.Markdown("### Query BareMetal host by Instance ID")

        instance_ocid = gr.Textbox(
            label="Instance OCID",
            placeholder="ocid1.instance.oc1...",
            lines=1,
        )

        instance_query_btn = gr.Button("Find BareMetal Host", variant="secondary")

        instance_query_output = gr.Textbox(
            label="BareMetal Host Lookup Result",
            lines=30,
            interactive=False,
        )

        instance_query_btn.click(
            fn=query_baremetal_host_by_instance,
            inputs=[profile, region, instance_ocid],
            outputs=[instance_query_output],
        )

    return demo


if __name__ == "__main__":
    demo = create_interface()
    demo.launch(share=False)
