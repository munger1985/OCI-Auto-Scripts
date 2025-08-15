from typing import Dict, Optional, List
from langchain.schema import HumanMessage
import requests
import oci
from oci.config import from_file
from oci.regions import REGIONS

from oci.resource_search.models import FreeTextSearchDetails
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain.prompts import PromptTemplate
class OCIIPResourceFinder:
    def __init__(self, config_file: str = "~/.oci/config"):
        # 初始化 OCI 配置
        self.config = from_file(config_file)
        # 初始化 langchain 模型
        # OCI 区域到国家的映射
        # self.region_country_map = {
        #     "ap-sydney-1": "AU",     # 澳大利亚
        #     "ap-melbourne-1": "AU",  # 澳大利亚
        #     "ap-tokyo-1": "JP",      # 日本
        #     "ap-osaka-1": "JP",      # 日本
        #     "ap-seoul-1": "KR",      # 韩国
        #     "ap-chuncheon-1": "KR",  # 韩国
        #     "ap-singapore-1": "SG",  # 新加坡
        #     "eu-frankfurt-1": "DE",  # 德国
        #     "eu-amsterdam-1": "NL",  # 荷兰
        #     "eu-zurich-1": "CH",     # 瑞士
        #     "uk-london-1": "GB",     # 英国
        #     "uk-cardiff-1": "GB",    # 英国
        #     "us-ashburn-1": "US",    # 美国
        #     "us-phoenix-1": "US",    # 美国
        #     "sa-saopaulo-1": "BR",   # 巴西
        #     "me-dubai-1": "AE",      # 阿联酋
        #     "me-jeddah-1": "SA"      # 沙特阿拉伯
        # }

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


    def search_resources(self, ip: str) -> Dict:
        """根据 IP 地址搜索 OCI 资源"""
        try:
            # 获取 IP 地址的国家代码
            # city = self.get_ip_location(ip)
            # if not city:
            #     return {"error": "无法确定 IP 地址的位置"}

            # 获取匹配的区域
            matching_regions = REGIONS
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
                    if  results[region]["total_items"] > 0:
                        break;
                except Exception as e:
                    results[region] = {"error": str(e)}

            return {
                "resources": results
            }

        except Exception as e:
            return {"error": str(e)}

# 使用示例
if __name__ == "__main__":
    finder = OCIIPResourceFinder()
    # result = finder.search_resources("146.235.213.22")
    result = finder.search_resources("138.2.109.80")
    print(result)
    instance_id ,lb_id = None,None
    for region, resource_data in result['resources'].items():
        for item in resource_data.get('items', []):
            print("ip type: ",item.get('type'))
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
