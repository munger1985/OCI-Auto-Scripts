#!/bin/bash
#### just configure this script and bash this script for a particular vnic
echo "check ip via metadata svc " 

curl --fail -H "Authorization: Bearer Oracle"   -L0 http://169.254.169.254/opc/v2/vnics


set -e

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo "请使用 root 用户执行此脚本 (sudo)"
    exit 1
fi

# 参数解析
NIC=eth1
TABLE_ID=200

GATEWAY=10.0.3.1
subnetCidrBlock=10.0.3.0/24
privateIp=10.0.3.69
NETMASK="$(echo "$subnetCidrBlock" | cut -d'/' -f2)"

# 1. 配置 IP 地址并启用网卡
echo "==> 为网卡 $NIC 配置 IP $privateIp$NETMASK"
ip addr add "$privateIp/$NETMASK" dev $NIC 2>/dev/null || echo "IP 可能已存在，忽略错误"
ip link set $NIC up

# 2. 在 /etc/iproute2/rt_tables 中定义自定义路由表
TABLE_NAME="table_$NIC"
if ! grep -q "^$TABLE_ID[[:space:]]*$TABLE_NAME" /etc/iproute2/rt_tables; then
    echo "==> 添加路由表定义: $TABLE_ID $TABLE_NAME"
    echo "$TABLE_ID     $TABLE_NAME" >> /etc/iproute2/rt_tables
else
    echo "==> 路由表 $TABLE_NAME 已存在，跳过添加"
fi

# 3. 在自定义路由表中添加路由规则
echo "==> 配置自定义路由表 $TABLE_NAME"
# 清空该表旧内容（避免重复）
ip route flush table $TABLE_NAME 2>/dev/null || true
# 添加直连子网路由，并指定源 IP
ip route add $subnetCidrBlock dev $NIC src $privateIp table $TABLE_NAME
# 添加默认路由
ip route add default via $GATEWAY dev $NIC table $TABLE_NAME

# 4. 添加策略路由规则：源 IP 为 10.0.3.69 的流量使用上述自定义表
echo "==> 添加策略路由规则: from $privateIp/32 lookup $TABLE_NAME"
# 删除可能存在的旧规则（避免重复）
ip rule del from $privateIp/32 table $TABLE_NAME 2>/dev/null || true
ip rule add from $privateIp/32 table $TABLE_NAME

# 5. 完成提示
echo "✅ 配置完成！"
echo "测试命令: ping -I $privateIp 1.1.1.1"
echo "当前路由表 $TABLE_NAME 内容："
ip route show table $TABLE_NAME
