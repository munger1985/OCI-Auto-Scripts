#!/usr/bin/env bash
# Copyright (c) 2018, Oracle and/or its affiliates.
# The Universal Permissive License (UPL), Version 1.0
#
# Oracle OCI Virtual Cloud Networks IP configuration script
# Enhanced Version: Fixed interface name length (max 15 chars)
#
# 2026-03-23 FIX: MACVLAN name max 15 chars (IFNAMSIZ limit)

declare -r THIS=$(basename "$0")
declare -r MD_URL='http://169.254.169.254/opc/v1/vnics/'
declare -r NA='-'
declare -r RTS_FILE='/etc/iproute2/rt_tables'
declare -ir RT_ID_MIN=10
declare -ir RT_ID_MAX=255
declare -r RT_FORMAT_BM='ort${nic}vl${vltag}'
declare -r RT_FORMAT_VM='ort${nic}'
declare -r DEF_NS_FORMAT_BM='ons${nic}vl${vltag}'
declare -r DEF_NS_FORMAT_VM='ons${nic}'

# 🔧 FIX: 短接口名称（最多 15 字符）
declare -r MACVLAN_FORMAT='mv${vltag}'           # 如：mv2361 (6 字符) ✅
declare -r VLAN_FORMAT='v${vltag}'               # 如：v2361 (5 字符) ✅

declare -ir MTU=9000
declare -r ADD='ADD'
declare -r DELETE='DELETE'
declare -r YES='YES'
declare -r CURL=$(which curl)
declare -r IP=$(which ip)
declare -r SSHD=$(which sshd)
declare -r MODPROBE=$(which modprobe)
declare -r OS_RELEASE='/etc/os-release'

# IPv6 支持
declare -a MD_IPV6_ADDRS
declare -a MD_IPV6_PREFIXES
declare -a MD_IPV6_GATEWAYS
declare ENABLE_IPV6=''

# 重置模式
declare CLEAN_MODE=''
declare CLEAN_MACVLAN=''
declare CLEAN_VLAN=''
declare CLEAN_FULL=''

if [ -f "$OS_RELEASE" ]; then
    declare -r OS_ID=$(grep -ws ID $OS_RELEASE | cut -f 2 -d '=' | tr -d '"' | tr '[:upper:]' '[:lower:]')
    declare -r OS_VERSION=$(grep -ws VERSION_ID $OS_RELEASE | cut -f 2 -d '=' | tr -d '"')
else
    declare -r OS_RELEASE_alt='/etc/redhat-release'
    if [ -f "$OS_RELEASE_alt" ]; then
        declare -r OS_ID=$(cat $OS_RELEASE_alt|cut -f 1 -d ' ' | tr '[:upper:]' '[:lower:]')
        declare -r OS_VERSION=$(cat $OS_RELEASE_alt | cut -f 3 -d ' ')
    fi
fi

if [ -n "$OS_VERSION" ]; then
    declare -r OS_MAJ_VERSION=$(echo $OS_VERSION | cut -f 1 -d '.')
fi

declare -r SYS_CLASS_NET='/sys/class/net'
declare -A VIRTUAL_IFACES
declare IS_VM=''
declare -a MACS
declare -A MD_I_BY_MAC
declare -a MD_MACS
declare -a MD_ADDRS
declare -a MD_VLTAGS
declare -a MD_SCIDRS
declare -a MD_SPREFIXS
declare -a MD_SBITSS
declare -a MD_VIRTRTS
declare -a MD_VNICS
declare -a MD_NIC_IS
declare -a MD_CONFIGS
declare -A DUP_ADDRS
declare -A DUP_SADDRS
declare -A IP_I_BY_MAC
declare -a IP_MACS
declare -a IP_NSS
declare -a IP_IFACES
declare -a IP_ADDRS
declare -a IP_SADDRS
declare -a IP_SBITSS
declare -a IP_VIRTRTS
declare -a IP_STATES
declare -a IP_VLANS
declare -a IP_VLTAGS
declare -a IP_SECADS
declare -a IP_SRCS
declare -a IP_NIC_IS
declare -a IP_CONFIGS
declare -a NIC_IP_IS
declare -A NIC_I_BY_PHYS_IP_I
declare QUIET=''
declare DEBUG=''
declare START_SSHD=''
declare USE_NS=''
declare NS_FORMAT=''
declare -a SEC_ADDRS
declare -a SEC_VNICS
declare -r IFACE_AWK_SCRIPT='/tmp/oci_vcn_iface.awk'

# ============================================================================
# AWK 脚本（更新以匹配新命名格式）
# ============================================================================
cat >$IFACE_AWK_SCRIPT <<'EOF'
function prtiface(mac, iface, addr, sbits, state, vlan, vltag, secad) {
    if (iface != "") printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n", mac, iface, addr, sbits, state, vlan, vltag, secad
}
BEGIN { iface = ""; addr = "-" }
/^[0-9]/ {
    if (addr == "-") prtiface(mac, iface, addr, sbits, state, vlan, vltag, secad)
    addr = "-"
    sbits = "-"
    state = "-"
    macvlan = "-"
    vlan = "-"
    vltag = "-"
    secad = "-"
    if ($0 ~ /BROADCAST/ && $0 !~ /UNKNOWN/ && $0 !~ /NO-CARRIER/ && $0 !~ /master /) {
        i = index($2, "@")
        if (1 < i) {
            j = index($2, ".")
            if (j < i) {
                macvlan = substr($2, 1, i - 1)
                iface = substr($2, i + 1, length($2) - i - 1)
                addr = ""
            } else {
                vlan = substr($2, 1, i - 1)
                iface = substr($2, i + 1, j - i - 1)
                vltag = substr($2, j + 1, length($2) - j - 1)
            }
        } else {
            i = index($2, ":")
            if (i <= 1) { print "cannot find interface name"; exit 1 }
            iface = substr($2, 1, i - 1)
        }
        if ($0 ~ /LOWER_UP/) state = "UP"
        else state = "DOWN"
    } else iface = ""
    next
}
/ link\/ether / { mac = tolower($2) }
/ inet [0-9]/ {
    i = index($2, "/")
    if (i <= 1) { print "cannot find interface inet address"; exit 1 }
    if (addr != "-") secad = "YES"
    addr = substr($2, 0, i - 1)
    sbits = substr($2, i + 1, length($2) - i)
    prtiface(mac, iface, addr, sbits, state, vlan, vltag, secad)
}
END { if (addr == "-") prtiface(mac, iface, addr, sbits, state, vlan, vltag, secad) }
EOF

# ============================================================================
# 错误处理函数
# ============================================================================
oci_vcn_err() { echo "Error: $1" >&2; exit 1; }
oci_vcn_warn() { echo "Warning: $1" >&2; }
oci_vcn_info() { [ -n "$QUIET" ] || echo "Info: $1" >&2; }
oci_vcn_debug() { [ -z "$DEBUG" ] || echo "Debug: $1" >&2; }

# ============================================================================
# 清理已存在的接口
# ============================================================================
oci_vcn_cleanup_macvlan() {
    local iface=$1
    local vltag=$2
    local macvlan=$(oci_vcn_macvlan_name $iface $vltag)
    local vlan=$(oci_vcn_vlan_name $iface $vltag)

    if $IP link show "$vlan" &>/dev/null; then
        oci_vcn_debug "cleanup: delete existing $vlan"
        $IP link delete "$vlan" 2>/dev/null || true
    fi

    if $IP link show "$macvlan" &>/dev/null; then
        oci_vcn_debug "cleanup: delete existing $macvlan"
        $IP link delete "$macvlan" 2>/dev/null || true
    fi
}

oci_vcn_cleanup_all_virtual() {
    oci_vcn_info "清理所有 macvlan/vlan 虚拟网卡..."

    local vlan_count=0
    for iface in $($IP -o link show type vlan 2>/dev/null | awk -F': ' '{print $2}' | cut -d'@' -f1); do
        $IP link delete "$iface" 2>/dev/null && vlan_count=$((vlan_count + 1)) || true
    done

    local macvlan_count=0
    for iface in $($IP -o link show type macvlan 2>/dev/null | awk -F': ' '{print $2}' | cut -d'@' -f1); do
        $IP link delete "$iface" 2>/dev/null && macvlan_count=$((macvlan_count + 1)) || true
    done

    oci_vcn_info "已删除 $vlan_count 个 vlan, $macvlan_count 个 macvlan"
}

# ============================================================================
# IPv6 支持
# ============================================================================
oci_vcn_md_read_ipv6() {
    local -r tmpfile=$(mktemp /tmp/oci_vcn_md_ipv6.XXXXX)
    $CURL -s $MD_URL | tr , '\n' >"$tmpfile" || oci_vcn_err "cannot read metadata"

    MD_IPV6_ADDRS=($(grep -w "ipv6" "$tmpfile" | cut -f 4 -d '"' 2>/dev/null)) || true
    MD_IPV6_GATEWAYS=($(grep -w "ipv6SubnetGateway" "$tmpfile" | cut -f 4 -d '"' 2>/dev/null)) || true

    local s
    for s in $(grep -w "ipv6SubnetCidrBlock" "$tmpfile" | cut -f 4 -d '"' 2>/dev/null); do
        MD_IPV6_PREFIXES+=(${s})
    done

    rm "$tmpfile"
    [ ${#MD_IPV6_ADDRS[@]} -gt 0 ] && ENABLE_IPV6='t'
}

oci_vcn_ipv6_addr_add_iface() {
    local -ir md_i=$1
    local -ir ip_i=$2
    local -r ns=$3
    local iface="${IP_IFACES[$ip_i]}"
    local -r addr="${MD_IPV6_ADDRS[$md_i]}"
    local -r prefix="${MD_IPV6_PREFIXES[$md_i]:-64}"
    local -r gateway="${MD_IPV6_GATEWAYS[$md_i]}"

    local -r vltag="${MD_VLTAGS[$md_i]}"
    local vlan=''
    [ -z "$IS_VM" ] && [ $vltag -ne 0 ] && vlan=$(oci_vcn_vlan_name $iface $vltag)
    local -r dev="${vlan:-$iface}"

    local nscmd=''
    [ -n "$ns" ] && nscmd="netns exec $ns $IP"

    $IP $nscmd link set dev $dev up 2>/dev/null || true
    $IP $nscmd -6 addr add $addr/$prefix dev $dev 2>/dev/null || oci_vcn_warn "cannot add IPv6 $addr/$prefix"

    [ -n "$gateway" ] && [ $md_i -eq 0 ] && $IP $nscmd -6 route add default via $gateway dev $dev metric 100 2>/dev/null || true
    oci_vcn_info "added IPv6 $addr/$prefix on $dev"
}

# ============================================================================
# 读取虚拟接口
# ============================================================================
oci_vcn_virtual_ifaces_read() {
    VIRTUAL_IFACES=()
    for iface in $(ls $SYS_CLASS_NET); do
        ls -l $SYS_CLASS_NET/$iface | grep -wq virtual && VIRTUAL_IFACES[$iface]='t'
    done
}

# ============================================================================
# 读取元数据
# ============================================================================
oci_vcn_md_read() {
    local -r tmpfile=$(mktemp /tmp/oci_vcn_md.XXXXX)
    $CURL -s $MD_URL | tr , '\n' >"$tmpfile" || oci_vcn_err "cannot read metadata"

    MD_MACS=($(grep -w macAddr "$tmpfile" | cut -f 4 -d '"')) || exit $?
    for i in $(seq 0 $((${#MD_MACS[@]} - 1))); do MD_MACS[$i]="${MD_MACS[$i],,}"; done

    MD_ADDRS=($(grep -w privateIp "$tmpfile" | cut -f 4 -d '"'))
    MD_VLTAGS=($(grep -w vlanTag "$tmpfile" | cut -f 2 -d ':' | tr -d ' '))
    MD_VIRTRTS=($(grep -w virtualRouterIp "$tmpfile" | cut -f 4 -d '"'))

    for s in $(grep -w subnetCidrBlock "$tmpfile" | cut -f 4 -d '"'); do
        MD_SCIDRS+=(${s})
        MD_SPREFIXS+=(${s%/*})
        MD_SBITSS+=(${s#*/})
    done

    MD_VNICS=($(grep -w vnicId "$tmpfile" | cut -f 4 -d '"'))
    MD_NIC_IS=($(grep -w nicIndex "$tmpfile" | cut -f 2 -d ':' | tr -d ' '))

    [ ${#MD_MACS[@]} -eq ${#MD_ADDRS[@]} ] || oci_vcn_err "invalid metadata: MAC/IP mismatch"
    [ ${#MD_MACS[@]} -eq ${#MD_VLTAGS[@]} ] || oci_vcn_err "invalid metadata: MAC/VLAN mismatch"
    [ ${#MD_MACS[@]} -eq ${#MD_VIRTRTS[@]} ] || oci_vcn_err "invalid metadata: MAC/virt router mismatch"
    [ ${#MD_MACS[@]} -eq ${#MD_SPREFIXS[@]} ] || oci_vcn_err "invalid metadata: MAC/subnet mismatch"
    [ ${#MD_MACS[@]} -eq ${#MD_VNICS[@]} ] || oci_vcn_err "invalid metadata: MAC/VNIC mismatch"

    for i in $(seq 0 $((${#MD_MACS[@]} - 1))); do
        [[ ${MD_ADDRS[$i]} =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || oci_vcn_err "invalid IP: ${MD_ADDRS[$i]}"
        [[ ${MD_VLTAGS[$i]} =~ ^[0-9]+$ ]] || oci_vcn_err "invalid VLAN tag: ${MD_VLTAGS[$i]}"
        [[ ${MD_VIRTRTS[$i]} =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || oci_vcn_err "invalid virt router: ${MD_VIRTRTS[$i]}"
        [[ ${MD_SPREFIXS[$i]} =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || oci_vcn_err "invalid subnet: ${MD_SPREFIXS[$i]}"
    done

    [ ${#MD_NIC_IS[@]} -eq 0 ] && IS_VM='t' && oci_vcn_virtual_ifaces_read

    for i in "${!MD_MACS[@]}"; do MD_I_BY_MAC[${MD_MACS[$i]}]=$i; done
    rm "$tmpfile"

    local -A addrs=()
    for addr in "${MD_ADDRS[@]}"; do
        [ -n "${addrs[$addr]}" ] && DUP_ADDRS[$addr]='t'
        addrs[$addr]='t'
    done

    local -A saddrs=()
    for addr in "${MD_SPREFIXS[@]}"; do
        [ -n "${saddrs[$addr]}" ] && DUP_SADDRS[$addr]='t'
        saddrs[$addr]='t'
    done

    oci_vcn_md_read_ipv6
}

# ============================================================================
# 路由表函数
# ============================================================================
oci_vcn_ip_route_table_name() {
    local -ir nic=$1 vltag=$2
    local format="$RT_FORMAT_VM"
    [ -n "$IS_VM" ] || format="$RT_FORMAT_BM"
    eval echo "$format"
}

oci_vcn_ip_route_table_name_ip_i() {
    local -ir ip_i=$1
    oci_vcn_ip_route_table_name ${IP_NIC_IS[$ip_i]} ${IP_VLTAGS[$ip_i]}
}

oci_vcn_ip_route_table_exists() {
    grep -qsw $1 $RTS_FILE && echo "$1"
}

oci_vcn_ip_route_table_find_unused_id() {
    local lines; mapfile -t lines < <(cat $RTS_FILE | grep -E '^[0-9]' | tr '\t' ' ' | tr -s ' ' ' ')
    local -A rt_by_id
    for line in "${lines[@]}"; do
        local -a pair=($line)
        rt_by_id[${pair[0]}]=${pair[1]}
    done
    for i in $(seq $RT_ID_MIN $RT_ID_MAX); do
        [ -z "${rt_by_id[$i]}" ] && echo $i && return
    done
    oci_vcn_err "cannot find unused route table id"
}

oci_vcn_ip_route_table_create() {
    local -ir nic_i=$1 vltag=$2
    local -r skip_if_exists=$3
    local -r rt_name=$(oci_vcn_ip_route_table_name $nic_i $vltag)
    local rt_exists=$(oci_vcn_ip_route_table_exists $rt_name)

    if [ -n "$rt_exists" ]; then
        [ -n "$skip_if_exists" ] && return
        oci_vcn_warn "route table $rt_name exists, reusing"
    else
        local -i rt_id=$(oci_vcn_ip_route_table_find_unused_id)
        echo "$rt_id    $rt_name" >> $RTS_FILE
    fi
    echo "$rt_name"
}

oci_vcn_ip_route_table_del() {
    local -r rt_name=$1
    grep -qsw $rt_name $RTS_FILE || return
    local -r tmpfile=$(mktemp /tmp/oci_vcn_rt_tables.XXXXX)
    cp -p $RTS_FILE "$tmpfile"
    grep -vw $rt_name $RTS_FILE > "$tmpfile"
    mv "$tmpfile" $RTS_FILE
    echo 't'
}

# ============================================================================
# 路由配置
# ============================================================================
oci_vcn_ip_routing_add() {
    local -ir md_i=$1 nic_i=$2
    local -r iface=$3 ns=$4 skip_if_exists=$5
    local -ir vltag="${MD_VLTAGS[$md_i]}"
    local -r addr="${MD_ADDRS[$md_i]}"
    local -r sprefix="${MD_SPREFIXS[$md_i]}"
    local -r virtrt="${MD_VIRTRTS[$md_i]}"
    local -r scidr="${MD_SCIDRS[$md_i]}"

    if [ -n "$ns" ]; then
        $IP netns exec $ns $IP route add default via $virtrt || oci_vcn_err "cannot add namespace default route"
        oci_vcn_info "added namespace $ns default route to $virtrt"
    else
        [ -n "${DUP_ADDRS[$addr]}" ] && oci_vcn_warn "duplicate IP $addr, skipping source route" && return
        local -r rt_name=$(oci_vcn_ip_route_table_create $nic_i $vltag $skip_if_exists)
        [ -n "$rt_name" ] || return
        $IP route add default via $virtrt dev $iface table $rt_name
        $IP route add $scidr dev $iface table $rt_name
        $IP rule add from $addr lookup $rt_name || oci_vcn_err "cannot add rule from $addr"
        oci_vcn_info "added rule from $addr lookup $rt_name"
    fi
}

oci_vcn_ip_routing_del() {
    local -ir ip_i=$1
    local -r ns="${IP_NSS[$ip_i]#$NA}"
    [ -n "$ns" ] && return
    local -r rt_name=$(oci_vcn_ip_route_table_name_ip_i $ip_i)
    while $IP rule del lookup $rt_name 2>/dev/null; do true; done
    oci_vcn_ip_route_table_del $rt_name >/dev/null
}

oci_vcn_ip_routing_sec_addr_add() {
    local -ir iface_ip_i=$1
    local -r addr=$2
    local -r ns="${IP_NSS[$iface_ip_i]#$NA}"
    [ -z "$ns" ] && [ $iface_ip_i -ne 0 ] && {
        local -r rt_name=$(oci_vcn_ip_route_table_name_ip_i $iface_ip_i)
        $IP rule add from $addr lookup $rt_name
        oci_vcn_info "added rule from secondary $addr"
    }
}

oci_vcn_ip_routing_sec_addr_del() {
    local -ir ip_i=$1
    local -r addr=$2
    local -r ns="${IP_NSS[$ip_i]#$NA}"
    [ -z "$ns" ] && [ $ip_i -ne 0 ] && $IP rule del from $addr 2>/dev/null
}

oci_vcn_ip_routes_read() {
    local -ir ip_i=$1
    local -r ns="${IP_NSS[$ip_i]#$NA}"
    local -r iface="${IP_IFACES[$ip_i]}"
    local nscmd='' virtrt="$NA"

    [ -n "$ns" ] && nscmd="netns exec $ns $IP" || {
        local -r rt_name=$(oci_vcn_ip_route_table_name_ip_i $ip_i)
        if $IP rule | grep -qsw $rt_name; then
            local -a def_entry=($($IP route show table $rt_name | grep -sw ^default))
            [ -n "${def_entry[2]}" ] && virtrt="${def_entry[2]}" || oci_vcn_ip_routing_del $ip_i
        fi
    }

    local sprefix="$NA" sbits="$NA" src="$NA"
    mapfile -t routes < <($IP $nscmd route | grep -w $iface)
    for line in "${routes[@]}"; do
        local -a route=($line)
        [ "${route[0]}" = 'default' ] && virtrt="${route[2]}"
        [[ "${route[0]#169.}" = "${route[0]}" ]] && {
            sprefix=${route[0]%/*}; sbits=${route[0]#*/}
            [ "$sprefix" = "$sbits" ] && { sprefix="$NA"; sbits="$NA"; }
        }
    done
    IP_VIRTRTS[$ip_i]="$virtrt"
    IP_SADDRS[$ip_i]="$sprefix"
    IP_SBITSS[$ip_i]="$sbits"
    IP_SRCS[$ip_i]="$src"
}

oci_vcn_macvlan_name() { eval echo "$MACVLAN_FORMAT"; }
oci_vcn_vlan_name() { eval echo "$VLAN_FORMAT"; }

oci_vcn_ip_ns_name() {
    local -ir nic=$1 vltag=$2
    [ -n "$USE_NS" ] && [ -z "$NS_FORMAT" ] && {
        [ -n "$IS_VM" ] && NS_FORMAT="$DEF_NS_FORMAT_VM" || NS_FORMAT="$DEF_NS_FORMAT_BM"
    }
    eval echo "$NS_FORMAT"
}

oci_vcn_ip_ns_svcs_stop() {
    local -r ns=$1
    local pids=$($IP netns pids $ns)
    [ -n "$pids" ] && kill -TERM $pids
}

oci_vcn_ip_ns_svcs_start() {
    local -r ns=$1
    [ -n "$START_SSHD" ] && $IP netns exec $ns $SSHD
}

oci_vcn_ip_ns_del() {
    local -r ns=$1
    $IP netns del $ns
    oci_vcn_info "deleted namespace $ns"
}

oci_vcn_ip_ns_create() {
    local -ir nic_i=$1 vltag=$2
    $MODPROBE 8021q || oci_vcn_err "failed to load 8021q"
    local ns=$(oci_vcn_ip_ns_name $nic_i $vltag)
    $IP netns add $ns || oci_vcn_err "cannot create namespace $ns"
    oci_vcn_info "created namespace $ns"
    echo "$ns"
}

# ============================================================================
# IP 地址配置（核心修复）
# ============================================================================
oci_vcn_ip_addr_add_iface() {
    local -ir md_i=$1 ip_i=$2
    local -r ns=$3
    local iface="${IP_IFACES[$ip_i]}"
    local -r physns="${IP_NSS[$ip_i]#$NA}"
    local -r mac="${MD_MACS[$md_i]}"
    local -ir vltag="${MD_VLTAGS[$md_i]}"
    local -r addr="${MD_ADDRS[$md_i]}"
    local -r sbits="${MD_SBITSS[$md_i]}"
    local vlan=''

    local macvlan=''
    if [ -z "$IS_VM" ] && [ $vltag -ne 0 ]; then
        local physnscmd=''
        [ -n "$physns" ] && physnscmd="netns exec $physns $IP"

        # 🔧 清理旧接口
        oci_vcn_cleanup_macvlan "$iface" "$vltag"

        # 🔧 创建 macvlan（短名称）
        macvlan=$(oci_vcn_macvlan_name $iface $vltag)
        $IP $physnscmd link add link $iface name $macvlan address $mac type macvlan \
            || oci_vcn_err "cannot create MAC VLAN $macvlan for MAC $mac"

        [ -n "$physns" ] && $IP $physnscmd link set $macvlan netns 1

        # 🔧 创建 VLAN（短名称）
        vlan=$(oci_vcn_vlan_name $iface $vltag)
        $IP link add link $macvlan name $vlan type vlan id $vltag \
            || oci_vcn_err "cannot create VLAN $vlan on $macvlan"
    fi

    local nscmd=''
    local -r dev="${vlan:-$iface}"
    if [ -n "$ns" ]; then
        nscmd="netns exec $ns $IP"
        [ -n "$macvlan" ] && $IP link set dev $macvlan netns $ns
        $IP link set dev $dev netns $ns
    fi

    $IP $nscmd addr add $addr/$sbits dev $dev || oci_vcn_err "cannot add IP $addr/$sbits on $dev"

    if [ -n "$macvlan" ]; then
        $IP $nscmd link set dev $macvlan mtu $MTU up
        $IP $nscmd link set dev $vlan mtu $MTU up
    else
        $IP $nscmd link set dev $iface mtu $MTU up
    fi

    oci_vcn_info "added IP $addr on $dev with MTU $MTU"

    # IPv6
    [ -n "$ENABLE_IPV6" ] && [ -n "${MD_IPV6_ADDRS[$md_i]}" ] && oci_vcn_ipv6_addr_add_iface $md_i $ip_i $ns

    echo "$dev"
}

oci_vcn_ip_addr_del_iface() {
    local -ir ip_i=$1
    local -r iface="${IP_IFACES[$ip_i]}"
    local -r ns="${IP_NSS[$ip_i]#$NA}"
    local -r vlan="${IP_VLANS[$ip_i]#$NA}"
    local -r secad="${IP_SECADS[$ip_i]#$NA}"
    local nscmd=''
    [ -n "$ns" ] && nscmd="netns exec $ns $IP"

    if [ "$secad" != "$YES" ] && [ -n "$vlan" ]; then
        local -ir vltag="${IP_VLTAGS[$ip_i]}"
        local macvlan=$(oci_vcn_macvlan_name $iface $vltag)
        $IP $nscmd link del link $vlan dev $macvlan
        oci_vcn_info "removed VLAN $vlan"
    else
        local -r addr="${IP_ADDRS[$ip_i]#$NA}"
        local -r dev="${vlan:-$iface}"
        local bits="${IP_SBITSS[$ip_i]#$NA}"
        [ "$secad" != "$YES" ] || bits=32
        $IP $nscmd addr del $addr/$bits dev $dev
        oci_vcn_info "removed IP $addr from $dev"
    fi
}

oci_vcn_ip_addr_add() {
    local -ir md_i=$1
    local -r mac="${MD_MACS[$md_i]}"
    local -r addr="${MD_ADDRS[$md_i]}"
    local iface='' ip_i=0 nic_i vltag

    if [ -z "$IS_VM" ]; then
        nic_i=${MD_NIC_IS[$md_i]}
        [ $nic_i -lt ${#NIC_IP_IS[@]} ] || oci_vcn_err "cannot find interface for NIC $nic_i"
        ip_i=${NIC_IP_IS[$nic_i]}
        iface="${IP_IFACES[$ip_i]}"
        vltag=${MD_VLTAGS[$md_i]}
    else
        local found=''
        for ip_mac in "${IP_MACS[@]}"; do
            [ "$ip_mac" = "$mac" ] && { found='t'; break; }
            ip_i+=1
        done
        [ -n "$found" ] || oci_vcn_err "cannot find interface for MAC $mac"
        iface="${IP_IFACES[$ip_i]}"
        nic_i=${IP_NIC_IS[$ip_i]}
        vltag=0
    fi

    [ "${IP_STATES[$ip_i]}" != "UP" ] && $IP link set dev $iface up

    local ns=''
    if [ -n "$USE_NS" ]; then
        ns=$(oci_vcn_ip_ns_create $nic_i $vltag)
        [ $vltag -ne 0 ] || IP_NSS[$ip_i]="$ns"
    fi

    local dev=$(oci_vcn_ip_addr_add_iface $md_i $ip_i $ns)
    oci_vcn_ip_routing_add $md_i $nic_i $dev $ns
    [ -n "$ns" ] && { sleep 1; oci_vcn_ip_ns_svcs_start $ns; }
}

oci_vcn_ip_sec_addr_add() {
    local -ir iface_ip_i=$1
    local -r addr=$2
    local -r iface="${IP_IFACES[$iface_ip_i]}"
    local -r vlan="${IP_VLANS[$iface_ip_i]#$NA}"
    local -r dev="${vlan:-$iface}"
    local -r ns="${IP_NSS[$iface_ip_i]#$NA}"
    local nscmd='' nsinfo=''

    oci_vcn_ip_routing_sec_addr_add $iface_ip_i $addr
    [ -n "$ns" ] && { nscmd="netns exec $ns $IP"; nsinfo=" in namespace $ns"; }

    oci_vcn_info "adding secondary IP $addr to $dev$nsinfo"
    $IP $nscmd addr add $addr/32 dev $dev || oci_vcn_err "cannot add secondary IP $addr"
}

oci_vcn_ip_sec_addr_del() {
    local -ir ip_i=$1
    local -r deconfig_all=$2
    local -r addr=${IP_ADDRS[$ip_i]}
    local -r iface=${IP_IFACES[$ip_i]}
    local -r vlan="${IP_VLANS[$ip_i]#$NA}"
    local -r dev="${vlan:-$iface}"
    local -r ns="${IP_NSS[$ip_i]#$NA}"
    local nscmd='' nsinfo=''

    [ "${IP_SECADS[$ip_i]}" = "$YES" ] || oci_vcn_err "not a secondary IP: $addr"

    if [ -z "$deconfig_all" ] || ([ -z "$vlan" ] && [ -z "$ns" ]); then
        [ -z "$deconfig_all" ] && [ -n "$ns" ] && { nscmd="netns exec $ns $IP"; nsinfo=" in namespace $ns"; }
        oci_vcn_info "removing secondary IP $addr from $dev$nsinfo"
        $IP $nscmd addr del $addr/32 dev $dev
    fi
    oci_vcn_ip_routing_sec_addr_del $ip_i $addr
}

oci_vcn_sec_addr_is_provisioned() {
    local -r find_addr=$1 find_vnic=$2
    for i in $(seq 0 $((${#SEC_ADDRS[@]} - 1))); do
        [ "$find_addr" = "${SEC_ADDRS[$i]}" ] && [ "$find_vnic" = "${SEC_VNICS[$i]}" ] && echo 't' && return
    done
}

oci_vcn_ip_addr_del() {
    local -ir ip_i=$1
    local -r ns="${IP_NSS[$ip_i]#$NA}"
    local -r secad="${IP_SECADS[$ip_i]#$NA}"
    [ $ip_i -ne 0 ] || oci_vcn_err "cannot remove primary VNIC"

    [ "$secad" != "$YES" ] && {
        [ -n "$ns" ] && oci_vcn_ip_ns_svcs_stop $ns
        oci_vcn_ip_routing_del $ip_i
    }
    oci_vcn_ip_addr_del_iface $ip_i
    [ "$secad" != "$YES" ] && [ -n "$ns" ] && { oci_vcn_ip_ns_del $ns; sleep 1; }
}

oci_vcn_ip_ifaces_read() {
    local -r ns="$1"
    local nscmd=''
    [ -n "$ns" ] && nscmd="netns exec $ns $IP"

    mapfile -t iface_datas < <($IP $nscmd addr show | awk -f $IFACE_AWK_SCRIPT)
    [ ${#iface_datas[@]} -eq 0 ] && {
        [ -n "$ns" ] || oci_vcn_err "cannot locate interfaces"
        $IP netns del $ns
        oci_vcn_warn "deleted empty namespace $ns"
        return
    }

    local -r nsna="${ns:-$NA}"
    local -i ip_i=${#IP_MACS[@]}
    for line in "${iface_datas[@]}"; do
        local -a iface_data=($line)
        local iface="${iface_data[1]}"
        if [ -z "$IS_VM" ] || [ -z "${VIRTUAL_IFACES[$iface]}" ]; then
            IP_MACS+=("${iface_data[0]}")
            IP_NSS+=("$nsna")
            IP_IFACES+=("$iface")
            IP_ADDRS+=("${iface_data[2]}")
            IP_SBITSS+=("${iface_data[3]}")
            IP_STATES+=("${iface_data[4]}")
            IP_VLANS+=("${iface_data[5]}")
            IP_VLTAGS+=("${iface_data[6]}")
            IP_SECADS+=("${iface_data[7]}")
            [ "${iface_data[7]}" = "$YES" ] || IP_I_BY_MAC["${iface_data[0]}"]=$ip_i
            ip_i+=1
        fi
    done
}

oci_vcn_ip_read() {
    IP_I_BY_MAC=(); IP_MACS=(); IP_NSS=(); IP_IFACES=(); IP_ADDRS=()
    IP_SADDRS=(); IP_SBITSS=(); IP_VIRTRTS=(); IP_STATES=()
    IP_VLANS=(); IP_VLTAGS=(); IP_SECADS=(); IP_SRCS=()
    IP_NIC_IS=(); NIC_IP_IS=(); NIC_I_BY_PHYS_IP_I=()

    oci_vcn_ip_ifaces_read
    mapfile -t nss < <($IP netns 2>/dev/null)
    for ns in "${nss[@]}"; do oci_vcn_ip_ifaces_read $ns; done

    for ip_i in $(seq 0 $((${#IP_MACS[@]} - 1))); do
        [ -n "${IP_VLTAGS[$ip_i]#$NA}" ] || IP_VLTAGS[$ip_i]=0
        oci_vcn_ip_routes_read $ip_i
    done

    local -r tmpfile=$(mktemp /tmp/oci_vcn_ifaces.XXXXX)
    local -A ip_i_by_phys_iface
    for ip_i in $(seq 0 $((${#IP_MACS[@]} - 1))); do
        if [ ${IP_VLTAGS[$ip_i]} -eq 0 ] && [ "${IP_SECADS[$ip_i]}" != "$YES" ]; then
            ip_i_by_phys_iface[${IP_IFACES[$ip_i]}]=$ip_i
            echo "${IP_IFACES[$ip_i]}" >> "$tmpfile"
        fi
        NIC_I_BY_PHYS_IP_I[$ip_i]=-1
    done

    local -i nic_i=0
    for iface in $(cat "$tmpfile" | awk '{ match($1, /[0-9]+/); print substr($1, RSTART, RLENGTH), $1 }' | sort -n | cut -f 2 -d ' '); do
        local ip_i=${ip_i_by_phys_iface[$iface]}
        NIC_IP_IS+=($ip_i)
        NIC_I_BY_PHYS_IP_I[$ip_i]=$nic_i
        nic_i+=1
    done
    rm "$tmpfile"

    for ip_i in $(seq 0 $((${#IP_MACS[@]} - 1))); do
        IP_NIC_IS[$ip_i]=${NIC_I_BY_PHYS_IP_I[${ip_i_by_phys_iface[${IP_IFACES[$ip_i]}]}]}
    done

    if [ ${#MD_NIC_IS[@]} -eq 0 ] && [ ${#NIC_IP_IS[@]} -eq 1 ] && ([ ${#IP_MACS[@]} -gt 1 ] || [ ${#MD_MACS[@]} -gt 1 ]); then
        for md_i in $(seq 0 $((${#MD_MACS[@]} - 1))); do MD_NIC_IS+=(0); done
        oci_vcn_info "legacy BM instance detected"
        IS_VM=''
    fi
}

oci_vcn_read() {
    [ -n "$IP" ] || oci_vcn_err "cannot find ip command"
    local -i attempt
    for attempt in 1 2; do
        MACS=("${MD_MACS[@]}")
        oci_vcn_ip_read
        MD_CONFIGS=()
        local -i md_i=0
        for mac in "${MD_MACS[@]}"; do
            MD_CONFIGS[$md_i]="$NA"
            local -i ip_i=${IP_I_BY_MAC[$mac]:--1}
            [ $ip_i -lt 0 ] && MD_CONFIGS[$md_i]="$ADD" || {
                local addr="${IP_ADDRS[$ip_i]#$NA}"
                [ -z "$addr" ] && MD_CONFIGS[$md_i]="$ADD"
            }
            md_i+=1
        done

        local -i ip_i=0
        IP_CONFIGS=()
        local retry='' warn_ifaces=''
        local -A new_macs=()
        for mac in "${IP_MACS[@]}"; do
            IP_CONFIGS[$ip_i]="$NA"
            local addr="${IP_ADDRS[$ip_i]#$NA}"
            local -i md_i=${MD_I_BY_MAC[$mac]:--1}
            if [ $md_i -lt 0 ]; then
                local iface="${IP_IFACES[$ip_i]}"
                [ -n "$addr" ] && IP_CONFIGS[$ip_i]="$DELETE" || {
                    [ -z "$IS_VM" ] && [ ${IP_VLTAGS[$ip_i]} -ne 0 ] && {
                        IP_CONFIGS[$ip_i]="$DELETE"
                        warn_ifaces="$warn_ifaces $iface"
                    }
                }
                [ -z "$IS_VM" ] || {
                    ([ $attempt -eq 1 ] && [ "${IP_STATES[$ip_i]}" = 'DOWN' ]) || oci_vcn_err "interface $iface MAC $mac no metadata"
                    $IP link set dev $iface up
                    retry='t'
                }
                [ -z "${new_macs[$mac]}" ] && { new_macs[$mac]='t'; MACS+=("$mac"); }
            elif [ "${IP_SECADS[$ip_i]}" = "$YES" ]; then
                local is_prov=$(oci_vcn_sec_addr_is_provisioned $addr "${MD_VNICS[$md_i]}")
                [ -z "$is_prov" ] && IP_CONFIGS[$ip_i]="$DELETE"
            fi
            ip_i+=1
        done
        [ -n "$retry" ] || break
    done
    [ -n "$warn_ifaces" ] && oci_vcn_warn "no VNIC, interfaces marked for delete:$warn_ifaces"
}

oci_vcn_config_or_deconfig_sec_addrs() {
    local -r do_config="$1"
    local found=''
    for i in $(seq 0 $((${#SEC_ADDRS[@]} - 1))); do
        local addr=${SEC_ADDRS[$i]} vnic=${SEC_VNICS[$i]} mac=''
        for md_i in $(seq 0 $((${#MD_MACS[@]} - 1))); do
            [ "$vnic" = "${MD_VNICS[$md_i]}" ] && { mac="${MD_MACS[$md_i]}"; break; }
        done
        [ -n "$mac" ] || oci_vcn_err "cannot find VNIC for secondary IP $addr"

        local -i iface_ip_i=-1 already_config=''
        for ip_i in $(seq 0 $((${#IP_MACS[@]} - 1))); do
            [ "$mac" = "${IP_MACS[$ip_i]}" ] && {
                [ $iface_ip_i -ge 0 ] || iface_ip_i=$ip_i
                [ "$addr" = "${IP_ADDRS[$ip_i]}" ] && { already_config='t'; break; }
            }
        done
        [ $iface_ip_i -ge 0 ] || oci_vcn_err "cannot find interface for secondary IP $addr"

        if [ -n "$do_config" ] && [ -z "$already_config" ]; then
            oci_vcn_ip_sec_addr_add $iface_ip_i $addr
            found='t'
        elif [ -z "$do_config" ] && [ -n "$already_config" ]; then
            oci_vcn_ip_sec_addr_del $ip_i
            found='t'
        fi
    done
    echo "$found"
}

oci_vcn_config() {
    local found=''
    for md_i in $(seq 0 $((${#MD_CONFIGS[@]} - 1))); do
        local config="${MD_CONFIGS[$md_i]#$NA}"
        [ "$config" = "$ADD" ] && {
            oci_vcn_info "adding IP config for VNIC MAC ${MD_MACS[$md_i]}"
            oci_vcn_ip_addr_add $md_i
            found='t'
        }
    done

    local del_vmac=''
    for ip_i in $(seq 0 $((${#IP_CONFIGS[@]} - 1))); do
        local config="${IP_CONFIGS[$ip_i]#$NA}"
        if [ "$config" = "$DELETE" ]; then
            local mac="${IP_MACS[$ip_i]}"
            local secad="${IP_SECADS[$ip_i]#$NA}"
            if [ "$secad" != "$YES" ] || [ "$del_vmac" != "$mac" ]; then
                oci_vcn_info "removing IP config from MAC $mac"
                oci_vcn_ip_addr_del $ip_i
                found='t'
                [ "${IP_VLTAGS[$ip_i]}" -eq 0 ] || del_vmac=$mac
            fi
        fi
    done

    local sec_addrs_found=''
    if [ ${#SEC_ADDRS[@]} -gt 0 ]; then
        [ -n "$found" ] && { sleep 2; oci_vcn_read; }
        sec_addrs_found=$(oci_vcn_config_or_deconfig_sec_addrs 't')
    fi
    [ -n "$found" ] || [ -n "$sec_addrs_found" ] || oci_vcn_info "no changes, configuration up-to-date"
}

oci_vcn_deconfig_all() {
    local -i ip_i=0 found=''
    for mac in "${IP_MACS[@]}"; do
        local addr="${IP_ADDRS[$ip_i]#$NA}"
        if [ -n "$addr" ]; then
            if [ "${IP_SECADS[$ip_i]}" != "$YES" ]; then
                if [ $ip_i -gt 0 ]; then
                    local -i md_i=${MD_I_BY_MAC[$mac]:--1}
                    local vnicmsg=''
                    [ $md_i -ge 0 ] && vnicmsg=" with id ${MD_VNICS[$md_i]}"
                    oci_vcn_info "removing IP config $addr for VNIC MAC $mac$vnicmsg"
                    oci_vcn_ip_addr_del $ip_i
                    found='t'
                fi
            else
                oci_vcn_ip_sec_addr_del $ip_i 't'
                found='t'
            fi
        fi
        ip_i+=1
    done
    [ -z "$found" ] && oci_vcn_info "no changes, no IP configuration to delete"
}

# ============================================================================
# 重置功能
# ============================================================================
oci_vcn_reset() {
    echo "🔄 Oracle OCI VCN 网络重置"
    echo "══════════════════════════════════════════════════════════════"

    [ -n "$CLEAN_MACVLAN" ] || [ -n "$CLEAN_VLAN" ] && oci_vcn_cleanup_all_virtual
    oci_vcn_deconfig_all

    [ -n "$CLEAN_FULL" ] && {
        echo -e "\n🔄 重启 NetworkManager..."
        systemctl restart NetworkManager 2>/dev/null || true
        sleep 3
    }

    echo -e "\n📊 验证:"
    $IP -br link show | grep -E "macvlan|vlan" || echo "   ✅ 无虚拟网卡"
    echo -e "\n✅ 重置完成！"
}

oci_vcn_show() {
    local -r fmt="%-6s %-15s %-15s %-5s %-15s %-10s %-3s %-10s %-5s %-11s %-5s %-17s %s\n"
    printf "$fmt" CONFIG ADDR SPREFIX SBITS VIRTRT NS IND IFACE VLTAG VLAN STATE MAC VNIC
    for mac in "${MACS[@]}"; do
        local config="$NA" addr="$NA" nic_i="$NA" vltag="$NA"
        local sprefix="$NA" sbits="$NA" virtrt="$NA" ns="$NA"
        local iface="$NA" vlan="$NA" state="$NA" vnic="$NA"

        local -i md_i=${MD_I_BY_MAC[$mac]:--1}
        [ $md_i -ge 0 ] && {
            config="${MD_CONFIGS[$md_i]}"
            nic_i="${MD_NIC_IS[$md_i]:-$NA}"
            addr="${MD_ADDRS[$md_i]}"
            [ -n "$IS_VM" ] || vltag="${MD_VLTAGS[$md_i]}"
            sprefix="${MD_SPREFIXS[$md_i]}"
            sbits="${MD_SBITSS[$md_i]}"
            virtrt="${MD_VIRTRTS[$md_i]}"
            vnic="${MD_VNICS[$md_i]}"
        }

        local -i ip_i=${IP_I_BY_MAC[$mac]:--1}
        if [ $ip_i -ge 0 ]; then
            local -i pri_ip_i=$ip_i
            while true; do
                local secad="${IP_SECADS[$ip_i]#$NA}"
                [ $pri_ip_i -eq $ip_i ] || [ -n "$secad" ] || break
                vlan="${IP_VLANS[$ip_i]:-$NA}"
                iface="${IP_IFACES[$ip_i]}"
                ns="${IP_NSS[$ip_i]}"
                state="${IP_STATES[$ip_i]}"
                local cfg="${IP_CONFIGS[$ip_i]#$NA}"
                [ -z "$cfg" ] || config="$cfg"
                [ $md_i -lt 0 ] && {
                    addr="${IP_ADDRS[$ip_i]}"
                    sbits="${IP_SBITSS[$ip_i]}"
                    virtrt="${IP_VIRTRTS[$ip_i]}"
                    [ -n "$IS_VM" ] || vltag="${IP_VLTAGS[$ip_i]}"
                }
                [ -n "$secad" ] && addr="${IP_ADDRS[$ip_i]}"
                [ -z "$secad" ] && printf "$fmt" "$config" "$addr" "$sprefix" "$sbits" "$virtrt" "$ns" "$nic_i" "$iface" "$vltag" "$vlan" "$state" "$mac" "$vnic"
                ip_i+=1
            done
        else
            printf "$fmt" "$config" "$addr" "$sprefix" "$sbits" "$virtrt" "$ns" "$nic_i" "$iface" "$vltag" "$vlan" "$state" "$mac" "$vnic"
        fi
    done

    [ -n "$ENABLE_IPV6" ] && [ ${#MD_IPV6_ADDRS[@]} -gt 0 ] && {
        echo -e "\nIPv6 Configuration:"
        printf "%-15s %-40s %-40s\n" "VNIC" "IPv6 Address" "IPv6 Gateway"
        for i in $(seq 0 $((${#MD_IPV6_ADDRS[@]} - 1))); do
            printf "%-15s %-40s %-40s\n" "${MD_VNICS[$i]}" "${MD_IPV6_ADDRS[$i]}" "${MD_IPV6_GATEWAYS[$i]:-N/A}"
        done
    }
}

oci_vcn_help() {
    cat <<EOF
NAME
$THIS -- Oracle OCI VCN IP configuration script (Enhanced)

SYNOPSIS
$THIS [-s] [-e <IP> <VNIC>]
$THIS -c [-q] [-s] [-n [<format>] [-r]] [-e <IP> <VNIC> [-e ...]]
$THIS -d [-q] [-s] [-e <IP> <VNIC>]
$THIS --reset [--clean-macvlan] [--clean-vlan] [--clean-full]

OPTIONS
-c          Configure VNICs
-d          Deconfigure all VNICs (except primary)
-e <IP> <VNIC>  Secondary IP to configure/deconfigure
--reset     Reset network configuration
--clean-macvlan  Clean all macvlan interfaces
--clean-vlan     Clean all vlan interfaces
--clean-full     Full reset with NetworkManager restart
-n [<format>]   Use namespace
-r          Start sshd in namespace
-q          Quiet mode
-s          Show configuration
-v          Verbose mode
-h          Show help

EXAMPLES
$THIS -c                      # Configure VNICs
$THIS --reset --clean-macvlan # Reset and clean macvlan
EOF
}

# ============================================================================
# 主程序
# ============================================================================
declare show='' config='' deconfig=''
declare os_ver="$OS_ID-$OS_VERSION"
declare os_maj_ver="$OS_ID-$OS_MAJ_VERSION"

while [ $# -ge 1 ]; do
    declare opt="$1"; shift
    case $opt in
        -c) config='t';;
        -d) deconfig='t';;
        --reset) CLEAN_MODE='t';;
        --clean-macvlan) CLEAN_MACVLAN='t';;
        --clean-vlan) CLEAN_VLAN='t';;
        --clean-full) CLEAN_FULL='t';;
        -e) [ $# -lt 2 ] && oci_vcn_err "secondary IP requires <IP> <VNIC>"
            SEC_ADDRS+=($1); shift; SEC_VNICS+=($1); shift;;
        -n) [ "$os_maj_ver" = "ol-6" ] || [ "$os_maj_ver" = "centos-6" ] && oci_vcn_err "namespaces not supported on $os_ver"
            [ $# -ge 1 ] && ! [[ "$1" =~ ^\- ]] && { [ -z "$1" ] || NS_FORMAT="$1"; shift; }
            USE_NS='t';;
        -r) START_SSHD='t'; [ -n "$SSHD" ] || oci_vcn_err "missing sshd";;
        -s) show='t';;
        -h) oci_vcn_help; exit 0;;
        -q) [ -n "$DEBUG" ] && oci_vcn_err "cannot specify quiet with verbose"; QUIET='t';;
        -v) [ -n "$QUIET" ] && oci_vcn_err "cannot specify verbose with quiet"; DEBUG='t';;
        -*) oci_vcn_err "unknown option $opt";;
    esac
done

[ -z "$START_SSHD" ] || [ -n "$USE_NS" ] || oci_vcn_err "cannot start sshd without namespace"
[ $EUID -eq 0 ] || oci_vcn_err "must be run as root"

[ -n "$CLEAN_MODE" ] && { oci_vcn_md_read; oci_vcn_reset; exit 0; }

oci_vcn_md_read
oci_vcn_read

if [ -n "$config" ]; then
    [ -z "$deconfig" ] || oci_vcn_err "conflicting options"
    oci_vcn_config
    [ -z "$show" ] || oci_vcn_read
elif [ -n "$deconfig" ]; then
    if [ ${#SEC_ADDRS[@]} -gt 0 ]; then oci_vcn_config_or_deconfig_sec_addrs
    else oci_vcn_deconfig_all; fi
    [ -z "$show" ] || oci_vcn_read
else
    show='t'
fi

[ -z "$show" ] || oci_vcn_show
