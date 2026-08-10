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
                output += f"\t{shape}: {count}\n"

        return output.strip(), hosts_table

    available = []
    for host in hosts:
        state = getattr(host, "lifecycle_state", None)
        instance_id = getattr(host, "instance_id", None)
        if state == "AVAILABLE" and not instance_id:
            available.append(host)

    counts_by_shape = Counter(getattr(host, "shape", "UNKNOWN") for host in available)
    total = sum(counts_by_shape.values())

    output = f"Total AVAILABLE (unassigned) hosts: {total}\n"
    for shape, count in counts_by_shape.most_common():
        output += f"{shape}: {count}\n"

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
            value="ap-kulai-1",
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

    return demo


if __name__ == "__main__":
    demo = create_interface()
    demo.launch(share=False)
