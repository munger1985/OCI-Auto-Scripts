from typing import Dict, Optional, List
import requests
import oci
from oci.config import from_file
from oci.regions import REGIONS

from oci.resource_search.models import FreeTextSearchDetails
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain.prompts import PromptTemplate

auth_type = "INSTANCE_PRINCIPAL"
auth_type = "API_KEY"
GenAIEndpoint = "https://inference.generativeai.ap-osaka-1.oci.oraclecloud.com"
compartment_id = "ocid1.compartment.oc1..aaaaaaaau5q457a7teqkjce4oenoiz6bmc4g3s74a5543iqbm7xwplho44fq"
intentP="""
you are a helpful assistant, can help me find the matching region id to the city. only to return the region id, no other explanation.
the region ids are:
{regions},
the city is:
{city}
"""
llm = ChatOCIGenAI(
    model_id="cohere.command-a-03-2025",
    service_endpoint=GenAIEndpoint,
    compartment_id=compartment_id,
    auth_type=auth_type,
    model_kwargs={
        'max_tokens': 555,
        'temperature': 0.10,
    }
)
class OCIIPResourceFinder:
    def __init__(self, config_file: str = "~/.oci/config"):
        # 初始化 OCI 配置
        self.config = from_file(config_file)
        # 初始化 langchain 模型
        self.chat =llm

    def get_ip_location(self, ip: str) -> Optional[str]:
        """使用 ip-api.com 获取 IP 地址的国家代码"""
        try:
                response = requests.get(f"http://ip-api.com/json/{ip}?fields=city")
                if response.status_code == 200:
                    data = response.json()
                    return data.get('city')
                return None
        except Exception as e:
                print(f"Error getting IP location: {e}")
                return None

    def get_matching_regions(self, city: str) -> List[str]:
        """根据国家代码找到匹配的 OCI 区域"""
        promptTemplate=PromptTemplate(template=intentP, input_variables=["regions", "city"])
        chain =promptTemplate|self.chat
        response = chain.invoke({"regions":REGIONS, "city":city})
        return [response.content.strip()]

    def search_resources(self, ip: str) -> Dict:
        """根据 IP 地址搜索 OCI 资源"""
        try:
            # 获取 IP 地址的国家代码
            city = self.get_ip_location(ip)
            if not city:
                return {"error": "无法确定 IP 地址的位置"}

            # 获取匹配的区域
            matching_regions = self.get_matching_regions(city)
            # if not matching_regions:
            #     # 如果没有直接匹配，使用 LangChain 询问最佳区域
            #     prompt = f"给定国家代码 {city}，在以下 OCI 区域中选择最近的区域：{list(self.region_country_map.keys())}。只返回区域名称，不要其他解释。"
            #     response = self.chat([HumanMessage(content=prompt)])
            #     suggested_region = response.content.strip()
            #     matching_regions = [suggested_region] if suggested_region in self.region_country_map else []

            if not matching_regions:
                return {"error": "找不到匹配的 OCI 区域"}

            # 在匹配的区域中搜索资源
            results = {}
            for region in matching_regions:
                # 更新配置中的区域
                self.config["region"] = region
                # 初始化资源搜索客户端
                resource_search_client = oci.resource_search.ResourceSearchClient(self.config)

                search_details = FreeTextSearchDetails(text=f"{ip}")

                # Perform the search

                # 执行搜索
                try:
                    response = resource_search_client.search_resources(search_details=search_details)

                    results[region] = {
                        "total_items": len(response.data.items),
                        "items": [{
                            "id": item.identifier,
                            "type": item.resource_type,
                            "name": getattr(item, 'display_name', 'N/A')
                        } for item in response.data.items[:10]]  # 限制返回前10个结果
                    }
                except Exception as e:
                    results[region] = {"error": str(e)}

            return {
                "country_code": city,
                "matching_regions": matching_regions,
                "resources": results
            }

        except Exception as e:
            return {"error": str(e)}
import sys
# 使用示例
if __name__ == "__main__":
    finder = OCIIPResourceFinder()

    # Check if the IP address argument is provided
    if len(sys.argv) < 2:
        print("Usage: python smartIPFinder.py <IP_ADDRESS>")
        sys.exit(1)

    # Get the IP address from the command line
    ip_address = sys.argv[1]
    result = finder.search_resources(ip_address)
    print(result)
    instance_id = None
    lb_id=None
    for region, resource_data in result['resources'].items():
        print("*" * 33)
        for item in resource_data.get('items', []):
            if item.get('type') == 'Instance':
                instance_id = item.get('id')
                break  # Stop after finding the first match
            elif item.get('type') == "LoadBalancer":
                lb_id= item.get("id")
                break
    if instance_id:

        print("Instance ID:", instance_id)
        parts = instance_id.split('.')
        region = parts[3]  # 'ap-melbourne-1'

        print("Instance url:", "https://cloud.oracle.com/compute/instances/"+instance_id+"?region="+region)
    elif lb_id:
        print("LB id: ",lb_id)
