#!/usr/bin/env python3
"""
Gradio interface for checking available hosts in OCI Dedicated Compute Host pool.

This script uses a local OCI API key config (OCI CLI config file).
It counts compute hosts in lifecycle_state=AVAILABLE and instance_id=None
(i.e., free/unassigned hosts) and groups counts by shape.

Run with: python3 oci_dedicated_hosts_gradio.py
Then open the provided URL in your browser.
"""

from __future__ import annotations

import gradio as gr
from collections import Counter, defaultdict

import oci
import os
import configparser

regions= [
                "us-ashburn-1", "us-phoenix-1", "us-sanjose-1",
                "eu-frankfurt-1", "eu-amsterdam-1", "eu-zurich-1",
                "ap-sydney-1", "ap-melbourne-1", "ap-osaka-1", "ap-seoul-1",
                "ap-jakarta-1", "ap-singapore-1", "me-jeddah-1", "me-dubai-1",
                "sa-saopaulo-1", "uk-london-1", "ca-toronto-1", "ca-montreal-1",
                "ap-kulai-1",   "il-jerusalem-1", "uk-cardiff-1",
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
    profiles = ["DEFAULT"] + list(config.sections())
    return profiles


def check_hosts(profile, region, all_states):
    # Configure OCI SDK to use local API key config.
    try:
        cfg = oci.config.from_file(profile_name=profile)
        # Force region
        cfg["region"] = region
    except Exception as e:
        return f"Failed to load OCI config. Ensure you have an API key configured and a valid OCI config file.\nError: {e}"

    tenancy_from_config = cfg.get("tenancy")
    if not tenancy_from_config:
        return "Could not determine tenancy OCID from config. Ensure config has 'tenancy='."

    # Fetch hosts
    hosts = []
    hosts.extend(list_compute_hosts(tenancy_from_config, cfg))

    # De-dup by host id
    by_id = {}
    for h in hosts:
        host_id = getattr(h, "id", None)
        if host_id:
            by_id[host_id] = h
    hosts = list(by_id.values())

    if all_states:
        counts = defaultdict(Counter)  # state -> Counter(shape)
        for h in hosts:
            state = getattr(h, "lifecycle_state", "UNKNOWN")
            shape = getattr(h, "shape", "UNKNOWN")
            counts[state][shape] += 1

        output = ""
        for state in sorted(counts.keys()):
            output += f"State={state}\n"
            for shape, c in counts[state].most_common():
                output += f" \t  {shape}: {c}\n"
        return output.strip()

    # Default: only AVAILABLE unassigned
    available = []
    for h in hosts:
        state = getattr(h, "lifecycle_state", None)
        instance_id = getattr(h, "instance_id", None)
        if state == "AVAILABLE" and not instance_id:
            available.append(h)

    c_by_shape = Counter(getattr(h, "shape", "UNKNOWN") for h in available)
    total = sum(c_by_shape.values())
    output = f"Total AVAILABLE (unassigned) hosts: {total}\n"
    for shape, c in c_by_shape.most_common():
        output += f"{shape}: {c}\n"
    return output.strip()


def create_interface():
    profiles = get_available_profiles()
    with gr.Blocks(title="OCI Dedicated Hosts Checker",theme=gr.themes.Glass()) as demo:
        gr.Markdown("# OCI Dedicated Pool Checker")
        gr.Markdown("Enter the details and click Submit to check available hosts.")

        profile = gr.Dropdown(
            choices=profiles,
            value="DEFAULT",
            label="OCI Config Profile",
            info="Select the profile from ~/.oci/config"
        )

        region = gr.Dropdown(
            choices=regions,
            value="ap-kulai-1",
            label="Region",
            info="Select the OCI region to query."
        )

        all_states = gr.Checkbox(
            label="Show counts for all lifecycle states",
            value=False
        )

        submit_btn = gr.Button("Check Hosts", variant="primary")

        output = gr.Textbox(
            label="Results",
            lines=20,
            interactive=False
        )

        submit_btn.click(
            fn=check_hosts,
            inputs=[profile, region, all_states],
            outputs=output
        )

    return demo


if __name__ == "__main__":
    demo = create_interface()
    demo.launch(share=False)
