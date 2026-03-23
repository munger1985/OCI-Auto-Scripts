# 查看当前配置
sudo secondary_vnic_all_configure.sh  -s

# 配置 VNIC（自动清理旧 macvlan + 支持 IPv6）
sudo secondary_vnic_all_configure.sh  -c

# 配置带 namespace
sudo secondary_vnic_all_configure.sh -c -n

# 重置网络（清理所有虚拟网卡）
sudo secondary_vnic_all_configure.sh --reset --clean-macvlan --clean-vlan

# 完全重置（包括重启 NetworkManager）
sudo secondary_vnic_all_configure.sh --reset --clean-full
