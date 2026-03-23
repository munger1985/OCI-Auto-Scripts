# 查看当前配置
sudo oci-vnic-enhanced.sh -s

# 配置 VNIC（自动清理旧 macvlan + 支持 IPv6）
sudo oci-vnic-enhanced.sh -c

# 配置带 namespace
sudo oci-vnic-enhanced.sh -c -n

# 重置网络（清理所有虚拟网卡）
sudo oci-vnic-enhanced.sh --reset --clean-macvlan --clean-vlan

# 完全重置（包括重启 NetworkManager）
sudo oci-vnic-enhanced.sh --reset --clean-full
