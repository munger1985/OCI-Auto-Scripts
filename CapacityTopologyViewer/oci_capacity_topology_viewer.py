#!/usr/bin/env python3
"""
OCI Capacity Topology Viewer

功能：
1. 自动列出 OCI Frankfurt region (默认 eu-frankfurt-1) 下的 Capacity Topology ID。
2. 选定一个 topology id 后，抓取该 topology 下的 HPC Island、Network Block、Local Block、BareMetal Host / Instance 信息。
3. 生成一个单文件 HTML 页面，用拓扑图显示关系：

       Capacity Topology -> HPC Island -> Network Block -> Local Block -> BareMetal Host/Instance

   点击 BareMetal 节点时：
       - 如果该节点有 instance，显示 instance id
       - 如果没有 instance，显示 BareMetal host id

依赖：
    pip install oci

常用命令：
    # 列出 Frankfurt 下所有 topology id
    python oci_capacity_topology_viewer.py --profile yellow --list

    # 指定 topology id 生成 HTML
    python oci_capacity_topology_viewer.py --profile yellow --topology-id <ocid1.computecapacitytopology...>

    # 如果 topology 不在 tenancy/root compartment，指定 compartment
    python oci_capacity_topology_viewer.py --profile yellow --compartment-id <compartment_ocid> --list

    # 也可以用序号选择。先 list 后输入序号，或直接：
    python oci_capacity_topology_viewer.py --profile yellow --select 1
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable

import oci


DEFAULT_PROFILE = "yellow"
DEFAULT_REGION = "eu-frankfurt-1"
DEFAULT_OUTPUT_HTML = r"c:\Users\qq\Desktop\ppppf\oci_capacity_topology_frankfurt.html"


def configure_console_encoding() -> None:
    """Avoid UnicodeEncodeError on Windows consoles using non-UTF-8 code pages."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def load_config(config_file: str | None, profile: str, region: str) -> dict[str, Any]:
    if config_file:
        config = oci.config.from_file(file_location=os.path.expanduser(config_file), profile_name=profile)
    else:
        config = oci.config.from_file(profile_name=profile)

    config["region"] = region
    if not config.get("tenancy"):
        raise ValueError("OCI config 中没有 tenancy OCID。请检查 ~/.oci/config。")
    return config


def collection_items(collection_or_list: Any) -> list[Any]:
    """OCI list APIs for this feature return collection objects with .items."""
    if collection_or_list is None:
        return []
    if isinstance(collection_or_list, list):
        return collection_or_list
    return list(getattr(collection_or_list, "items", []) or [])


def to_plain_dict(value: Any) -> Any:
    """Convert OCI model/datetime/list/dict values into JSON-serializable objects."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (list, tuple, set)):
        return [to_plain_dict(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_plain_dict(val) for key, val in value.items()}

    swagger_types = getattr(value, "swagger_types", None)
    if swagger_types:
        return {field: to_plain_dict(getattr(value, field, None)) for field in swagger_types.keys()}

    return str(value)


def short_id(ocid: str | None, prefix_chars: int = 18, suffix_chars: int = 8) -> str:
    if not ocid:
        return "N/A"
    if len(ocid) <= prefix_chars + suffix_chars + 3:
        return ocid
    return f"{ocid[:prefix_chars]}...{ocid[-suffix_chars:]}"


def safe_getattr(obj: Any, attr: str, default: Any = "") -> Any:
    value = getattr(obj, attr, default)
    return default if value is None else value


def list_capacity_topologies(
    compute_client: oci.core.ComputeClient,
    compartment_id: str,
    availability_domain: str | None = None,
) -> list[Any]:
    kwargs: dict[str, Any] = {
        "compartment_id": compartment_id,
        "sort_by": "DISPLAYNAME",
        "sort_order": "ASC",
    }
    if availability_domain:
        kwargs["availability_domain"] = availability_domain

    response = oci.pagination.list_call_get_all_results(
        compute_client.list_compute_capacity_topologies,
        **kwargs,
    )
    return collection_items(response.data)


def print_topology_table(topologies: list[Any]) -> None:
    if not topologies:
        print("没有找到 Compute Capacity Topology。")
        return

    print(f"找到 {len(topologies)} 个 Compute Capacity Topology：")
    print("-" * 140)
    print(f"{'#':<4} {'DISPLAY_NAME':<32} {'STATE':<10} {'AVAILABILITY_DOMAIN':<28} {'TOPOLOGY_ID'}")
    print("-" * 140)
    for idx, topology in enumerate(topologies, start=1):
        print(
            f"{idx:<4} "
            f"{str(safe_getattr(topology, 'display_name'))[:31]:<32} "
            f"{str(safe_getattr(topology, 'lifecycle_state'))[:9]:<10} "
            f"{str(safe_getattr(topology, 'availability_domain'))[:27]:<28} "
            f"{safe_getattr(topology, 'id')}"
        )
    print("-" * 140)


def choose_topology_id(topologies: list[Any], selected_index: int | None) -> str:
    if not topologies:
        raise ValueError("没有可选择的 topology。")

    if selected_index is not None:
        if selected_index < 1 or selected_index > len(topologies):
            raise ValueError(f"--select 必须在 1 到 {len(topologies)} 之间。")
        return safe_getattr(topologies[selected_index - 1], "id")

    while True:
        raw = input("请输入要生成 HTML 的 topology 序号，或直接粘贴 topology OCID：").strip()
        if not raw:
            continue
        if raw.isdigit():
            index = int(raw)
            if 1 <= index <= len(topologies):
                return safe_getattr(topologies[index - 1], "id")
            print(f"序号无效，请输入 1 到 {len(topologies)}。")
            continue
        return raw


def list_topology_children(
    compute_client: oci.core.ComputeClient,
    topology_id: str,
    compartment_id: str | None,
    availability_domain: str | None,
) -> tuple[list[Any], list[Any], list[Any]]:
    common_kwargs: dict[str, Any] = {"compute_capacity_topology_id": topology_id}
    if compartment_id:
        common_kwargs["compartment_id"] = compartment_id
    if availability_domain:
        common_kwargs["availability_domain"] = availability_domain

    hpc_resp = oci.pagination.list_call_get_all_results(
        compute_client.list_compute_capacity_topology_compute_hpc_islands,
        **common_kwargs,
    )
    network_resp = oci.pagination.list_call_get_all_results(
        compute_client.list_compute_capacity_topology_compute_network_blocks,
        **common_kwargs,
    )
    host_resp = oci.pagination.list_call_get_all_results(
        compute_client.list_compute_capacity_topology_compute_bare_metal_hosts,
        **common_kwargs,
    )

    return collection_items(hpc_resp.data), collection_items(network_resp.data), collection_items(host_resp.data)


def node_id(kind: str, raw_id: str) -> str:
    return f"{kind}:{raw_id}"


def add_node(nodes: dict[str, dict[str, Any]], node: dict[str, Any]) -> None:
    nodes[node["id"]] = node


def add_edge(edges: list[dict[str, str]], source: str, target: str, label: str) -> None:
    if source and target and source != target:
        edges.append({"source": source, "target": target, "label": label})


def build_graph_data(
    region: str,
    compartment_id: str,
    topology: Any,
    hpc_islands: list[Any],
    network_blocks: list[Any],
    hosts: list[Any],
) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []

    topology_ocid = safe_getattr(topology, "id")
    topology_node_id = node_id("topology", topology_ocid)
    add_node(
        nodes,
        {
            "id": topology_node_id,
            "kind": "topology",
            "label": safe_getattr(topology, "display_name") or "Capacity Topology",
            "subtitle": short_id(topology_ocid),
            "ocid": topology_ocid,
            "details": {
                "type": "Capacity Topology",
                "topology_id": topology_ocid,
                "display_name": safe_getattr(topology, "display_name"),
                "lifecycle_state": safe_getattr(topology, "lifecycle_state"),
                "availability_domain": safe_getattr(topology, "availability_domain"),
                "compartment_id": safe_getattr(topology, "compartment_id"),
                "time_created": to_plain_dict(safe_getattr(topology, "time_created", None)),
                "time_updated": to_plain_dict(safe_getattr(topology, "time_updated", None)),
            },
        },
    )

    hpc_ids = {safe_getattr(item, "id") for item in hpc_islands if safe_getattr(item, "id")}
    network_ids = {safe_getattr(item, "id") for item in network_blocks if safe_getattr(item, "id")}

    for hpc in hpc_islands:
        hpc_id = safe_getattr(hpc, "id")
        if not hpc_id:
            continue
        hpc_node_id = node_id("hpc", hpc_id)
        add_node(
            nodes,
            {
                "id": hpc_node_id,
                "kind": "hpc",
                "label": "HPC Island",
                "subtitle": short_id(hpc_id),
                "ocid": hpc_id,
                "details": {
                    "type": "HPC Island",
                    "hpc_island_id": hpc_id,
                    "total_bare_metal_host_count": safe_getattr(hpc, "total_compute_bare_metal_host_count", 0),
                    "lifecycle_state": safe_getattr(hpc, "lifecycle_state"),
                    "time_created": to_plain_dict(safe_getattr(hpc, "time_created", None)),
                    "time_updated": to_plain_dict(safe_getattr(hpc, "time_updated", None)),
                },
            },
        )
        add_edge(edges, topology_node_id, hpc_node_id, "contains")

    for network in network_blocks:
        network_id = safe_getattr(network, "id")
        if not network_id:
            continue
        network_node_id = node_id("network", network_id)
        hpc_id = safe_getattr(network, "compute_hpc_island_id")
        add_node(
            nodes,
            {
                "id": network_node_id,
                "kind": "network",
                "label": "Network Block",
                "subtitle": short_id(network_id),
                "ocid": network_id,
                "details": {
                    "type": "Network Block",
                    "network_block_id": network_id,
                    "hpc_island_id": hpc_id,
                    "total_bare_metal_host_count": safe_getattr(network, "total_compute_bare_metal_host_count", 0),
                    "lifecycle_state": safe_getattr(network, "lifecycle_state"),
                    "time_created": to_plain_dict(safe_getattr(network, "time_created", None)),
                    "time_updated": to_plain_dict(safe_getattr(network, "time_updated", None)),
                },
            },
        )
        if hpc_id and hpc_id in hpc_ids:
            add_edge(edges, node_id("hpc", hpc_id), network_node_id, "contains")
        else:
            add_edge(edges, topology_node_id, network_node_id, "contains")

    local_block_to_hosts: dict[str, list[Any]] = defaultdict(list)
    for host in hosts:
        local_block_id = safe_getattr(host, "compute_local_block_id") or "UNKNOWN_LOCAL_BLOCK"
        local_block_to_hosts[local_block_id].append(host)

    for local_block_id, block_hosts in sorted(local_block_to_hosts.items()):
        local_node_id = node_id("local", local_block_id)
        network_id = ""
        hpc_id = ""
        for host in block_hosts:
            network_id = network_id or safe_getattr(host, "compute_network_block_id")
            hpc_id = hpc_id or safe_getattr(host, "compute_hpc_island_id")

        add_node(
            nodes,
            {
                "id": local_node_id,
                "kind": "local",
                "label": "Local Block" if local_block_id != "UNKNOWN_LOCAL_BLOCK" else "Local Block Unknown",
                "subtitle": short_id(local_block_id),
                "ocid": local_block_id,
                "details": {
                    "type": "Local Block",
                    "local_block_id": local_block_id,
                    "network_block_id": network_id,
                    "hpc_island_id": hpc_id,
                    "bare_metal_host_count": len(block_hosts),
                },
            },
        )
        if network_id and network_id in network_ids:
            add_edge(edges, node_id("network", network_id), local_node_id, "contains")
        elif hpc_id and hpc_id in hpc_ids:
            add_edge(edges, node_id("hpc", hpc_id), local_node_id, "contains")
        else:
            add_edge(edges, topology_node_id, local_node_id, "contains")

        for host in block_hosts:
            host_id = safe_getattr(host, "id")
            if not host_id:
                continue
            instance_id = safe_getattr(host, "instance_id")
            host_node_id = node_id("host", host_id)
            node_label = "Instance" if instance_id else "BareMetal Host"
            node_subtitle = short_id(instance_id or host_id)
            click_value = instance_id or host_id
            click_value_label = "Instance ID" if instance_id else "BareMetal Host ID"
            add_node(
                nodes,
                {
                    "id": host_node_id,
                    "kind": "host_occupied" if instance_id else "host_empty",
                    "label": node_label,
                    "subtitle": node_subtitle,
                    "ocid": host_id,
                    "clickValueLabel": click_value_label,
                    "clickValue": click_value,
                    "details": {
                        "type": node_label,
                        "click_result": f"{click_value_label}: {click_value}",
                        "instance_id": instance_id,
                        "bare_metal_host_id": host_id,
                        "instance_shape": safe_getattr(host, "instance_shape"),
                        "local_block_id": safe_getattr(host, "compute_local_block_id"),
                        "network_block_id": safe_getattr(host, "compute_network_block_id"),
                        "hpc_island_id": safe_getattr(host, "compute_hpc_island_id"),
                        "lifecycle_state": safe_getattr(host, "lifecycle_state"),
                        "lifecycle_details": safe_getattr(host, "lifecycle_details"),
                        "time_created": to_plain_dict(safe_getattr(host, "time_created", None)),
                        "time_updated": to_plain_dict(safe_getattr(host, "time_updated", None)),
                    },
                },
            )
            add_edge(edges, local_node_id, host_node_id, "contains")

    summary = {
        "region": region,
        "compartment_id": compartment_id,
        "topology_id": topology_ocid,
        "topology_display_name": safe_getattr(topology, "display_name"),
        "availability_domain": safe_getattr(topology, "availability_domain"),
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "hpc_island_count": len(hpc_islands),
        "network_block_count": len(network_blocks),
        "local_block_count": len(local_block_to_hosts),
        "bare_metal_host_count": len(hosts),
        "occupied_host_count": sum(1 for host in hosts if safe_getattr(host, "instance_id")),
        "empty_host_count": sum(1 for host in hosts if not safe_getattr(host, "instance_id")),
    }

    return {
        "summary": summary,
        "nodes": list(nodes.values()),
        "edges": edges,
        "raw": {
            "topology": to_plain_dict(topology),
            "hpc_islands": to_plain_dict(hpc_islands),
            "network_blocks": to_plain_dict(network_blocks),
            "bare_metal_hosts": to_plain_dict(hosts),
        },
    }


def html_template(graph_data: dict[str, Any]) -> str:
    data_json = json.dumps(graph_data, ensure_ascii=False, indent=2)
    # <script> is a raw-text element. Do not use html.escape() here; escape only
    # sequences that could prematurely close the script tag or be interpreted as
    # HTML-sensitive characters when embedded in the document.
    data_json_for_script = (
        data_json
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    summary = graph_data["summary"]
    title = f"OCI Capacity Topology - {summary.get('region')}"
    escaped_title = html.escape(title)

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escaped_title}</title>
  <style>
    :root {{
      --bg: #0f172a;
      --panel: #111827;
      --panel2: #1f2937;
      --text: #e5e7eb;
      --muted: #9ca3af;
      --line: #64748b;
      --accent: #38bdf8;
      --topology: #a78bfa;
      --hpc: #22c55e;
      --network: #06b6d4;
      --local: #f59e0b;
      --occupied: #ef4444;
      --empty: #94a3b8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", Arial, "Microsoft YaHei", sans-serif;
      background: linear-gradient(135deg, #020617, #111827 55%, #1e293b);
      color: var(--text);
      overflow: hidden;
    }}
    header {{
      height: 76px;
      padding: 14px 18px;
      border-bottom: 1px solid rgba(148, 163, 184, .25);
      background: rgba(15, 23, 42, .92);
      backdrop-filter: blur(8px);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}
    h1 {{ margin: 0 0 6px 0; font-size: 19px; font-weight: 650; }}
    .sub {{ color: var(--muted); font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 74vw; }}
    .stats {{ display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }}
    .chip {{
      border: 1px solid rgba(148, 163, 184, .3);
      background: rgba(31, 41, 55, .75);
      border-radius: 999px;
      padding: 5px 9px;
      font-size: 12px;
      color: #d1d5db;
    }}
    #layout {{ display: grid; grid-template-columns: 1fr 380px; height: calc(100vh - 76px); }}
    #graphWrap {{ position: relative; min-width: 0; }}
    #graph {{ width: 100%; height: 100%; display: block; cursor: grab; touch-action: none; }}
    #graph.panning {{ cursor: grabbing; }}
    #toolbar {{
      position: absolute; top: 14px; left: 14px; z-index: 3;
      display: flex; gap: 8px; flex-wrap: wrap;
      max-width: calc(100% - 28px);
    }}
    input, button {{
      border-radius: 10px;
      border: 1px solid rgba(148, 163, 184, .35);
      background: rgba(15, 23, 42, .88);
      color: var(--text);
      padding: 9px 10px;
      outline: none;
    }}
    input {{ width: 360px; max-width: 52vw; }}
    button {{ cursor: pointer; }}
    button:hover {{ border-color: var(--accent); color: white; }}
    #zoomLevel {{
      border-radius: 10px;
      border: 1px solid rgba(148, 163, 184, .35);
      background: rgba(15, 23, 42, .88);
      color: #cbd5e1;
      padding: 9px 10px;
      font-size: 12px;
      min-width: 76px;
      text-align: center;
    }}
    aside {{
      border-left: 1px solid rgba(148, 163, 184, .25);
      background: rgba(17, 24, 39, .92);
      overflow: auto;
      padding: 16px;
    }}
    .legend {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 16px; }}
    .legendItem {{ font-size: 12px; color: #d1d5db; display: flex; align-items: center; gap: 7px; }}
    .dot {{ width: 13px; height: 13px; border-radius: 50%; display: inline-block; }}
    .card {{
      border: 1px solid rgba(148, 163, 184, .22);
      background: rgba(31, 41, 55, .72);
      border-radius: 14px;
      padding: 14px;
      margin-bottom: 14px;
    }}
    .card h2 {{ margin: 0 0 10px 0; font-size: 16px; }}
    .kv {{ margin: 8px 0; font-size: 12px; }}
    .k {{ color: var(--muted); display: block; margin-bottom: 3px; }}
    .v {{
      color: #f8fafc;
      word-break: break-all;
      font-family: Consolas, "Courier New", monospace;
      line-height: 1.35;
    }}
    .primaryValue {{
      border: 1px solid rgba(56, 189, 248, .45);
      background: rgba(8, 47, 73, .8);
      color: #e0f2fe;
      padding: 10px;
      border-radius: 10px;
      margin-bottom: 12px;
      word-break: break-all;
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      line-height: 1.4;
    }}
    .node circle {{ stroke: rgba(255,255,255,.78); stroke-width: 1.5px; filter: drop-shadow(0 6px 8px rgba(0,0,0,.35)); }}
    .node text {{ pointer-events: none; fill: #f8fafc; font-size: 11px; paint-order: stroke; stroke: rgba(2, 6, 23, .85); stroke-width: 3px; stroke-linejoin: round; }}
    .node .subtitle {{ fill: #cbd5e1; font-size: 9px; }}
    .node {{ cursor: pointer; }}
    .node.dim {{ opacity: .16; }}
    .node.highlight circle {{ stroke: #fef08a; stroke-width: 4px; }}
    .edge {{ stroke: rgba(148, 163, 184, .45); stroke-width: 1.4px; }}
    .edge.highlight {{ stroke: #fef08a; stroke-width: 2.6px; }}
    .edge.dim {{ opacity: .12; }}
    .edgeLabel {{ fill: var(--muted); font-size: 9px; pointer-events: none; }}
    @media (max-width: 980px) {{
      body {{ overflow: auto; }}
      header {{ height: auto; align-items: flex-start; flex-direction: column; }}
      #layout {{ grid-template-columns: 1fr; height: auto; }}
      #graphWrap {{ height: 68vh; }}
      aside {{ border-left: 0; border-top: 1px solid rgba(148, 163, 184, .25); }}
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>{escaped_title}</h1>
      <div class="sub">Topology ID: {html.escape(str(summary.get('topology_id', '')))} | AD: {html.escape(str(summary.get('availability_domain', '')))} | Generated: {html.escape(str(summary.get('generated_at', '')))}</div>
    </div>
    <div class="stats">
      <span class="chip">HPC {summary.get('hpc_island_count')}</span>
      <span class="chip">Network {summary.get('network_block_count')}</span>
      <span class="chip">Local {summary.get('local_block_count')}</span>
      <span class="chip">BM Hosts {summary.get('bare_metal_host_count')}</span>
      <span class="chip">Instances {summary.get('occupied_host_count')}</span>
      <span class="chip">Empty {summary.get('empty_host_count')}</span>
    </div>
  </header>
  <div id="layout">
    <main id="graphWrap">
      <div id="toolbar">
        <input id="search" placeholder="搜索 OCID / Instance / Host / Block / Island..." />
        <button id="zoomInBtn">放大</button>
        <button id="zoomOutBtn">缩小</button>
        <button id="fitViewBtn">适配</button>
        <span id="zoomLevel">100%</span>
        <button id="fitBtn">重新布局</button>
        <button id="clearBtn">清除高亮</button>
      </div>
      <svg id="graph" role="img" aria-label="OCI topology graph"></svg>
    </main>
    <aside>
      <div class="card">
        <h2>图例</h2>
        <div class="legend">
          <div class="legendItem"><span class="dot" style="background:var(--topology)"></span>Capacity Topology</div>
          <div class="legendItem"><span class="dot" style="background:var(--hpc)"></span>HPC Island</div>
          <div class="legendItem"><span class="dot" style="background:var(--network)"></span>Network Block</div>
          <div class="legendItem"><span class="dot" style="background:var(--local)"></span>Local Block</div>
          <div class="legendItem"><span class="dot" style="background:var(--occupied)"></span>Instance</div>
          <div class="legendItem"><span class="dot" style="background:var(--empty)"></span>Empty BM Host</div>
        </div>
      </div>
      <div class="card" id="details">
        <h2>节点详情</h2>
        <p style="color: var(--muted); font-size: 13px; line-height:1.5">点击任意节点查看详情。点击 Instance/BareMetal 节点时会优先显示 Instance ID；没有 Instance 时显示 BareMetal Host ID。</p>
      </div>
      <div class="card">
        <h2>Topology 摘要</h2>
        <div id="summary"></div>
      </div>
    </aside>
  </div>
  <script id="topology-data" type="application/json">{data_json_for_script}</script>
  <script>
    const graphData = JSON.parse(document.getElementById('topology-data').textContent);
    const svg = document.getElementById('graph');
    const details = document.getElementById('details');
    const summaryEl = document.getElementById('summary');
    const search = document.getElementById('search');
    const zoomLevel = document.getElementById('zoomLevel');
    const color = {{
      topology: getCss('--topology'), hpc: getCss('--hpc'), network: getCss('--network'),
      local: getCss('--local'), host_occupied: getCss('--occupied'), host_empty: getCss('--empty')
    }};
    const radius = {{ topology: 24, hpc: 19, network: 17, local: 15, host_occupied: 12, host_empty: 11 }};
    let nodes = graphData.nodes.map((d, i) => ({{...d, x: 80 + (i % 12) * 85, y: 120 + Math.floor(i / 12) * 70, vx: 0, vy: 0}}));
    let nodeById = new Map(nodes.map(n => [n.id, n]));
    let edges = graphData.edges.map(e => ({{...e, sourceNode: nodeById.get(e.source), targetNode: nodeById.get(e.target)}})).filter(e => e.sourceNode && e.targetNode);
    let selectedNode = null;
    let tickTimer = null;
    let graphRoot = null;
    let viewport = {{x: 0, y: 0, scale: 1}};
    const MIN_ZOOM = 0.01;
    const MAX_ZOOM = 12;

    function getCss(name) {{ return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }}
    function esc(s) {{ return String(s ?? '').replace(/[&<>"']/g, m => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}}[m])); }}
    function shortText(s, max = 28) {{ s = String(s ?? ''); return s.length > max ? s.slice(0, Math.floor(max * .62)) + '...' + s.slice(-8) : s; }}
    function svgEl(tag, attrs = {{}}) {{
      const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
      for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
      return el;
    }}

    function clamp(value, min, max) {{ return Math.max(min, Math.min(max, value)); }}
    function applyViewport() {{
      if (graphRoot) graphRoot.setAttribute('transform', `translate(${{viewport.x}},${{viewport.y}}) scale(${{viewport.scale}})`);
      zoomLevel.textContent = `${{Math.round(viewport.scale * 100)}}%`;
    }}
    function screenToWorld(clientX, clientY) {{
      const rect = svg.getBoundingClientRect();
      return {{
        x: (clientX - rect.left - viewport.x) / viewport.scale,
        y: (clientY - rect.top - viewport.y) / viewport.scale,
      }};
    }}
    function zoomAt(clientX, clientY, factor) {{
      const rect = svg.getBoundingClientRect();
      const sx = clientX - rect.left;
      const sy = clientY - rect.top;
      const before = screenToWorld(clientX, clientY);
      viewport.scale = clamp(viewport.scale * factor, MIN_ZOOM, MAX_ZOOM);
      viewport.x = sx - before.x * viewport.scale;
      viewport.y = sy - before.y * viewport.scale;
      applyViewport();
    }}
    function graphBounds() {{
      if (!nodes.length) return {{minX: 0, minY: 0, maxX: 1, maxY: 1}};
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      for (const n of nodes) {{
        const r = (radius[n.kind] || 12) + 42;
        minX = Math.min(minX, n.x - r); minY = Math.min(minY, n.y - r);
        maxX = Math.max(maxX, n.x + r); maxY = Math.max(maxY, n.y + r);
      }}
      return {{minX, minY, maxX, maxY}};
    }}
    function graphCanvasSize() {{
      const rect = svg.getBoundingClientRect();
      const counts = {{topology: 0, hpc: 0, network: 0, local: 0, host_occupied: 0, host_empty: 0}};
      for (const n of nodes) counts[n.kind] = (counts[n.kind] || 0) + 1;
      const hostCount = (counts.host_occupied || 0) + (counts.host_empty || 0);
      const maxLaneCount = Math.max(...Object.values(counts), hostCount, 1);
      return {{
        width: Math.max(rect.width * 1.8, 1600),
        height: Math.max(rect.height * 1.5, maxLaneCount * 46 + 220),
      }};
    }}
    function fitToView(padding = 70) {{
      const rect = svg.getBoundingClientRect();
      const b = graphBounds();
      const bw = Math.max(1, b.maxX - b.minX);
      const bh = Math.max(1, b.maxY - b.minY);
      const sx = (rect.width - padding * 2) / bw;
      const sy = (rect.height - padding * 2) / bh;
      viewport.scale = clamp(Math.min(sx, sy), MIN_ZOOM, MAX_ZOOM);
      viewport.x = (rect.width - bw * viewport.scale) / 2 - b.minX * viewport.scale;
      viewport.y = (rect.height - bh * viewport.scale) / 2 - b.minY * viewport.scale;
      applyViewport();
    }}
    function resetZoom() {{ viewport = {{x: 0, y: 0, scale: 1}}; applyViewport(); }}

    function renderSummary() {{
      summaryEl.innerHTML = Object.entries(graphData.summary).map(([k, v]) => `<div class="kv"><span class="k">${{esc(k)}}</span><div class="v">${{esc(v)}}</div></div>`).join('');
    }}

    function initPositions() {{
      const canvas = graphCanvasSize();
      const w = canvas.width, h = canvas.height;
      const levels = {{topology: 0, hpc: 1, network: 2, local: 3, host_occupied: 4, host_empty: 4}};
      const grouped = {{}};
      for (const n of nodes) (grouped[n.kind] ||= []).push(n);
      for (const n of nodes) {{
        const level = levels[n.kind] ?? 4;
        let group = grouped[n.kind] || [n];
        if (n.kind === 'host_occupied' || n.kind === 'host_empty') {{
          group = [...(grouped.host_occupied || []), ...(grouped.host_empty || [])];
        }}
        const idx = Math.max(0, group.indexOf(n));
        const yGap = h / (group.length + 1);
        n.x = 120 + level * ((w - 240) / 4);
        n.y = Math.max(70, Math.min(h - 50, yGap * (idx + 1)));
        n.vx = n.vy = 0;
      }}
    }}

    function render() {{
      svg.innerHTML = '';
      const defs = svgEl('defs');
      defs.innerHTML = `<marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="rgba(148,163,184,.65)" /></marker>`;
      svg.appendChild(defs);
      graphRoot = svgEl('g', {{id: 'graphRoot'}});
      const edgeGroup = svgEl('g', {{id: 'edges'}});
      const labelGroup = svgEl('g', {{id: 'edgeLabels'}});
      const nodeGroup = svgEl('g', {{id: 'nodes'}});
      graphRoot.appendChild(edgeGroup); graphRoot.appendChild(labelGroup); graphRoot.appendChild(nodeGroup);
      svg.appendChild(graphRoot);

      for (const e of edges) {{
        e.line = svgEl('line', {{class: 'edge', 'marker-end': 'url(#arrow)'}});
        edgeGroup.appendChild(e.line);
        e.text = svgEl('text', {{class: 'edgeLabel'}});
        e.text.textContent = e.label || '';
        labelGroup.appendChild(e.text);
      }}
      for (const n of nodes) {{
        const g = svgEl('g', {{class: 'node', 'data-id': n.id}});
        n.g = g;
        const c = svgEl('circle', {{r: radius[n.kind] || 12, fill: color[n.kind] || '#999'}});
        const t1 = svgEl('text', {{'text-anchor': 'middle', y: -2}});
        t1.textContent = shortText(n.label, 24);
        const t2 = svgEl('text', {{'text-anchor': 'middle', y: 12, class: 'subtitle'}});
        t2.textContent = shortText(n.subtitle, 32);
        g.appendChild(c); g.appendChild(t1); g.appendChild(t2);
        g.addEventListener('click', ev => {{ ev.stopPropagation(); selectNode(n); }});
        nodeGroup.appendChild(g);
      }}
      applyViewport();
      updateSvg();
    }}

    function updateSvg() {{
      for (const e of edges) {{
        const sx = e.sourceNode.x, sy = e.sourceNode.y, tx = e.targetNode.x, ty = e.targetNode.y;
        const dx = tx - sx, dy = ty - sy, len = Math.hypot(dx, dy) || 1;
        const tr = radius[e.targetNode.kind] || 12;
        e.line.setAttribute('x1', sx); e.line.setAttribute('y1', sy);
        e.line.setAttribute('x2', tx - dx / len * (tr + 3)); e.line.setAttribute('y2', ty - dy / len * (tr + 3));
        e.text.setAttribute('x', (sx + tx) / 2); e.text.setAttribute('y', (sy + ty) / 2 - 4);
      }}
      for (const n of nodes) n.g.setAttribute('transform', `translate(${{n.x}},${{n.y}})`);
    }}

    function simulate(iterations = 260) {{
      if (tickTimer) clearInterval(tickTimer);
      let i = 0;
      tickTimer = setInterval(() => {{
        tick(); updateSvg();
        if (++i >= iterations) {{
          clearInterval(tickTimer);
          fitToView();
        }}
      }}, 16);
    }}

    function enablePanZoom() {{
      svg.addEventListener('wheel', ev => {{
        ev.preventDefault();
        const factor = ev.deltaY < 0 ? 1.16 : 1 / 1.16;
        zoomAt(ev.clientX, ev.clientY, factor);
      }}, {{passive: false}});

      let panning = false;
      let lastX = 0;
      let lastY = 0;
      svg.addEventListener('pointerdown', ev => {{
        if (ev.target.closest && ev.target.closest('.node')) return;
        panning = true;
        lastX = ev.clientX;
        lastY = ev.clientY;
        svg.classList.add('panning');
        svg.setPointerCapture(ev.pointerId);
      }});
      svg.addEventListener('pointermove', ev => {{
        if (!panning) return;
        viewport.x += ev.clientX - lastX;
        viewport.y += ev.clientY - lastY;
        lastX = ev.clientX;
        lastY = ev.clientY;
        applyViewport();
      }});
      function stopPan(ev) {{
        if (!panning) return;
        panning = false;
        svg.classList.remove('panning');
        try {{ svg.releasePointerCapture(ev.pointerId); }} catch (_) {{}}
      }}
      svg.addEventListener('pointerup', stopPan);
      svg.addEventListener('pointercancel', stopPan);
      svg.addEventListener('pointerleave', stopPan);
    }}

    function tick() {{
      const canvas = graphCanvasSize();
      const w = canvas.width, h = canvas.height;
      const levels = {{topology: 0, hpc: 1, network: 2, local: 3, host_occupied: 4, host_empty: 4}};
      for (let i = 0; i < nodes.length; i++) {{
        for (let j = i + 1; j < nodes.length; j++) {{
          const a = nodes[i], b = nodes[j];
          let dx = b.x - a.x, dy = b.y - a.y, dist2 = dx*dx + dy*dy || 1;
          const force = Math.min(1800 / dist2, 2.5);
          const d = Math.sqrt(dist2);
          a.vx -= dx / d * force; a.vy -= dy / d * force;
          b.vx += dx / d * force; b.vy += dy / d * force;
        }}
      }}
      for (const e of edges) {{
        const a = e.sourceNode, b = e.targetNode;
        const dx = b.x - a.x, dy = b.y - a.y, dist = Math.hypot(dx, dy) || 1;
        const target = 125;
        const force = (dist - target) * 0.008;
        a.vx += dx / dist * force; a.vy += dy / dist * force;
        b.vx -= dx / dist * force; b.vy -= dy / dist * force;
      }}
      for (const n of nodes) {{
        const targetX = 120 + (levels[n.kind] ?? 4) * ((w - 240) / 4);
        n.vx += (targetX - n.x) * 0.012;
        n.vy += (h / 2 - n.y) * 0.0015;
        n.vx *= 0.86; n.vy *= 0.86;
        n.x = Math.max(45, Math.min(w - 45, n.x + n.vx));
        n.y = Math.max(45, Math.min(h - 45, n.y + n.vy));
      }}
    }}

    function connectedIds(n) {{
      const ids = new Set([n.id]);
      for (const e of edges) if (e.source === n.id || e.target === n.id) {{ ids.add(e.source); ids.add(e.target); }}
      return ids;
    }}

    function selectNode(n) {{
      selectedNode = n;
      const ids = connectedIds(n);
      for (const node of nodes) node.g.setAttribute('class', 'node ' + (ids.has(node.id) ? 'highlight' : 'dim'));
      for (const e of edges) {{
        e.line.setAttribute('class', 'edge ' + ((e.source === n.id || e.target === n.id) ? 'highlight' : 'dim'));
        e.text.setAttribute('class', 'edgeLabel ' + ((e.source === n.id || e.target === n.id) ? 'highlight' : 'dim'));
      }}
      const primary = n.clickValue ? `<div class="primaryValue"><b>${{esc(n.clickValueLabel)}}:</b><br>${{esc(n.clickValue)}}</div>` : '';
      details.innerHTML = `<h2>${{esc(n.label)}}</h2>${{primary}}` + Object.entries(n.details || {{}}).map(([k, v]) => `<div class="kv"><span class="k">${{esc(k)}}</span><div class="v">${{esc(v)}}</div></div>`).join('');
    }}

    function clearHighlight() {{
      selectedNode = null;
      for (const node of nodes) node.g.setAttribute('class', 'node');
      for (const e of edges) {{ e.line.setAttribute('class', 'edge'); e.text.setAttribute('class', 'edgeLabel'); }}
    }}

    function applySearch() {{
      const q = search.value.trim().toLowerCase();
      if (!q) {{ clearHighlight(); return; }}
      const matches = nodes.filter(n => JSON.stringify(n).toLowerCase().includes(q));
      const ids = new Set(matches.map(n => n.id));
      for (const node of nodes) node.g.setAttribute('class', 'node ' + (ids.has(node.id) ? 'highlight' : 'dim'));
      for (const e of edges) {{
        const hit = ids.has(e.source) || ids.has(e.target);
        e.line.setAttribute('class', 'edge ' + (hit ? 'highlight' : 'dim'));
        e.text.setAttribute('class', 'edgeLabel ' + (hit ? 'highlight' : 'dim'));
      }}
      details.innerHTML = `<h2>搜索结果</h2><p style="color:var(--muted)">匹配 ${{matches.length}} 个节点</p>` + matches.slice(0, 50).map(n => `<div class="kv"><span class="k">${{esc(n.label)}} / ${{esc(n.kind)}}</span><div class="v">${{esc(n.clickValue || n.ocid || n.id)}}</div></div>`).join('');
    }}

    search.addEventListener('input', applySearch);
    document.getElementById('zoomInBtn').addEventListener('click', () => {{
      const rect = svg.getBoundingClientRect();
      zoomAt(rect.left + rect.width / 2, rect.top + rect.height / 2, 1.28);
    }});
    document.getElementById('zoomOutBtn').addEventListener('click', () => {{
      const rect = svg.getBoundingClientRect();
      zoomAt(rect.left + rect.width / 2, rect.top + rect.height / 2, 1 / 1.28);
    }});
    document.getElementById('fitViewBtn').addEventListener('click', () => fitToView());
    document.getElementById('fitBtn').addEventListener('click', () => {{ initPositions(); simulate(); }});
    document.getElementById('clearBtn').addEventListener('click', () => {{ search.value = ''; clearHighlight(); }});
    svg.addEventListener('click', clearHighlight);
    window.addEventListener('resize', () => {{ initPositions(); simulate(120); }});

    renderSummary();
    initPositions();
    render();
    enablePanZoom();
    fitToView();
    simulate();
  </script>
</body>
</html>
"""


def write_html(graph_data: dict[str, Any], output_html: str) -> None:
    output_path = os.path.abspath(os.path.expanduser(output_html))
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as file_obj:
        file_obj.write(html_template(graph_data))
    print(f"HTML 已生成: {output_path}")


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List OCI Capacity Topology IDs and generate an interactive HTML topology graph.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config-file", default=None, help="OCI config file path. None means SDK default ~/.oci/config.")
    parser.add_argument("--profile", default=DEFAULT_PROFILE, help="OCI config profile name.")
    parser.add_argument("--region", default=DEFAULT_REGION, help="OCI region, Frankfurt is eu-frankfurt-1.")
    parser.add_argument("--compartment-id", default=None, help="Compartment OCID. Default uses tenancy/root compartment from OCI config.")
    parser.add_argument("--availability-domain", default=None, help="Optional AD filter, for example xxxx:EU-FRANKFURT-1-AD-1.")
    parser.add_argument("--list", action="store_true", help="Only list topology IDs and exit.")
    parser.add_argument("--topology-id", default=None, help="Topology OCID to render.")
    parser.add_argument("--select", type=int, default=None, help="Select topology by 1-based index from list result.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_HTML, help="Output HTML file path.")
    parser.add_argument("--open", action="store_true", help="Open generated HTML with default browser after writing it.")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    configure_console_encoding()
    args = parse_args(argv)

    try:
        config = load_config(args.config_file, args.profile, args.region)
    except Exception as exc:
        print(f"加载 OCI config 失败: {exc}", file=sys.stderr)
        return 2

    compartment_id = args.compartment_id or config["tenancy"]
    compute_client = oci.core.ComputeClient(config=config)

    print(f"Region: {args.region}")
    print(f"Compartment: {compartment_id}")

    topology_id = args.topology_id
    topologies: list[Any] = []

    if args.list or args.select is not None or not topology_id:
        try:
            topologies = list_capacity_topologies(
                compute_client=compute_client,
                compartment_id=compartment_id,
                availability_domain=args.availability_domain,
            )
        except oci.exceptions.ServiceError as exc:
            print(f"列出 Capacity Topology 失败: HTTP {exc.status} {exc.message}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"列出 Capacity Topology 失败: {exc}", file=sys.stderr)
            return 1

        print_topology_table(topologies)
        if args.list:
            return 0

        try:
            topology_id = choose_topology_id(topologies, args.select)
        except Exception as exc:
            print(f"选择 topology 失败: {exc}", file=sys.stderr)
            return 2

    if not topology_id:
        print("没有 topology id。请使用 --topology-id，或不加 --list 交互选择。", file=sys.stderr)
        return 2

    print(f"正在读取 topology: {topology_id}")
    try:
        topology = compute_client.get_compute_capacity_topology(topology_id).data
        # 如果用户没有显式传 AD，优先用 topology 自身 AD 缩小子资源查询范围。
        child_availability_domain = args.availability_domain or safe_getattr(topology, "availability_domain") or None
        hpc_islands, network_blocks, hosts = list_topology_children(
            compute_client=compute_client,
            topology_id=topology_id,
            compartment_id=compartment_id,
            availability_domain=child_availability_domain,
        )
    except oci.exceptions.ServiceError as exc:
        print(f"读取 topology 子资源失败: HTTP {exc.status} {exc.message}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"读取 topology 子资源失败: {exc}", file=sys.stderr)
        return 1

    print(
        "读取完成: "
        f"HPC Islands={len(hpc_islands)}, "
        f"Network Blocks={len(network_blocks)}, "
        f"BareMetal Hosts={len(hosts)}, "
        f"Instances={sum(1 for host in hosts if safe_getattr(host, 'instance_id'))}"
    )

    graph_data = build_graph_data(
        region=args.region,
        compartment_id=compartment_id,
        topology=topology,
        hpc_islands=hpc_islands,
        network_blocks=network_blocks,
        hosts=hosts,
    )
    write_html(graph_data, args.output)

    if args.open:
        try:
            os.startfile(os.path.abspath(os.path.expanduser(args.output)))  # type: ignore[attr-defined]
        except Exception as exc:
            print(f"打开 HTML 失败，请手工打开。原因: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
