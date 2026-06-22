import oci
import sys

# Load config (from ~/.oci/config or instance principals)
config = oci.config.from_file()  # or oci.config.validate_config(your_dict)
config.update({"region": "ap-singapore-1"})
# Create Virtual Network Client
virtual_network = oci.core.VirtualNetworkClient(config)
'''
how to get this privateIP ocid, just make sure this ip checked 'skip src/dst check' as this will be taken as a hop, then use 
  search bar in console to search it from 'view all' which will direct you to resource explorer, then use 
'''
privateIPID='ocid1.privateip.oc1.ap-singapore-1.abzwsljrbcfsu6nc2tb2uovhu6r7atdro3csxqtucxox5bbdmdmcrqtym3pa'


def clear_all_route_rules(route_table_id: str):
    """
    清空路由表中的所有路由规则
    """
    try:
        # 准备清空规则（传入空列表）
        update_details = oci.core.models.UpdateRouteTableDetails(
            route_rules=[]  # ← 清空所有规则的关键
        )

        response = virtual_network.update_route_table(
            rt_id=route_table_id,
            update_route_table_details=update_details
        )

        print("🎉 路由表所有规则已成功清空！")
        print(f"Route Table OCID: {route_table_id}")
        print(f"当前规则数量: {len(response.data.route_rules)}")

        return response.data

    except oci.exceptions.ServiceError as e:
        print(f"❌ 清空失败: {e}")
        if e.status == 409:
            print("提示：默认路由表可能无法完全清空，或有其他限制。")
        sys.exit(1)

def add_route_via_private_ip(
        route_table_id: str,
        destination_cidr: str,
        next_hop_id: str,
        description: str = None
):
    """使用 IP 地址作为下一跳添加路由规则"""

    # 1. 把 IP 转成 OCID

    # 2. 获取当前路由规则
    rt = virtual_network.get_route_table(route_table_id).data
    current_rules = rt.route_rules or []
    
    # 3. 创建新规则
    new_rule = oci.core.models.RouteRule(
        destination=destination_cidr,
        destination_type="CIDR_BLOCK",
        network_entity_id=next_hop_id,  # 必须是 OCID
        description=description or f"Via {next_hop_id}"
    )
    
    # 4. 检查是否存在相同目的地的规则
    rule_exists = False
    updated_rules = []
    for rule in current_rules:
        if rule.destination == destination_cidr:
            # 如果存在，用新规则替换旧规则
            updated_rules.append(new_rule)
            rule_exists = True
            print(f"⚠️  检测到已存在的目标: {destination_cidr}，正在覆盖...")
        else:
            # 保留其他规则
            updated_rules.append(rule)
    
    # 如果不存在，添加新规则
    if not rule_exists:
        updated_rules.append(new_rule)
        print(f"✅ 添加新的路由规则: {destination_cidr}")
    else:
        print(f"🔄 已覆盖现有路由规则: {destination_cidr}")

    # 5. 更新路由表
    update_details = oci.core.models.UpdateRouteTableDetails(route_rules=updated_rules)

    response = virtual_network.update_route_table(
        rt_id=route_table_id,
        update_route_table_details=update_details
    )

    print("🎉 路由规则添加成功！")
    print(f"目标: {destination_cidr}")
    return response.data


# ====================== 使用示例 ======================
if __name__ == '__main__':


    route_table_id = "ocid1.routetable.oc1.ap-singapore-1.aaaaaaaazbb7wf4bbhshjh5vbxodmgzfflmct52ig3py4jdehkopv5tgvxcq"  # 你的路由表 OCID

    # if you wanna clear all rules, uncomment it
    # clear_all_route_rules(route_table_id)

    add_route_via_private_ip(
        route_table_id=route_table_id,
        destination_cidr="22.0.0.0/22",  # 默认路由示例
        next_hop_id=privateIPID,  # ← 直接使用 IP 地址
        description="Default route via firewall"
    )
