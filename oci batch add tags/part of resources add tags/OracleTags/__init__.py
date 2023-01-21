import os
from oci.config import from_file

"""
TODO:
1. 修改config文件
2. 修改key文件
3. 修改COMPARTMENT_ID, PARTNER_ID...等数据
4. 建议print换成logger, 将异常信息保存到文件中, 之后需要重试
"""

REGION_LIST = [
    "sa-santiago-1",
    "il-jerusalem-1",
    "sa-vinhedo-1",
    "me-jeddah-1",
    "af-johannesburg-1",
    "eu-milan-1",
    "ap-seoul-1",
    "ap-tokyo-1",
    "ap-singapore-1",
    "ap-chuncheon-1",
    "eu-stockholm-1",
    "eu-frankfurt-1",
    "sa-saopaulo-1",
    "eu-marseille-1",
    "us-phoenix-1",
    "uk-london-1",
    "us-sanjose-1",
    "us-ashburn-1",
    "ap-sydney-1",
    "ca-toronto-1",
    "me-dubai-1",
    "ap-mumbai-1",
    "eu-madrid-1"
]

COMPARTMENT_ID = '...'
PARTNER_ID = '...'
OPPORTUNITY_ID = '...'
WORKLOAD = '...'


def base_config(region):
    config_path = os.path.abspath('./config')
    key_path = os.path.abspath('./key')

    config = from_file(file_location=config_path)
    config.update({'key_file': key_path, 'region': region})

    return config


def make_defined_tags(defined_tags):
    """
    添加标签属性
    """
    defined_tags.setdefault('OPN', {})
    defined_tags['OPN']['PartnerID'] = PARTNER_ID
    defined_tags['OPN']['OpportunityID'] = OPPORTUNITY_ID
    defined_tags['OPN']['Workload'] = WORKLOAD
    return defined_tags
