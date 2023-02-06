#!/bin/bash
HOST_INFO=host.info
for IP in $(awk '/^[^#]/{print $1}' $HOST_INFO);do
 USER=$(awk -v ip=$IP 'ip==$1{print $2}' $HOST_INFO)
 PORT=$(awk -v ip=$IP 'ip==$1{print $3}' $HOST_INFO)
 PRIKEY=$(awk -v ip=$IP 'ip==$1{print $4}' $HOST_INFO)
 DISK_SIZE=$(awk -v ip=$IP 'ip==$1{print $5}' $HOST_INFO)

 echo "####################################################"
 echo $USER@$IP:$PORT
 
 ssh -i $PRIKEY -o "StrictHostKeyChecking no" -p $PORT $USER@$IP << EOF
  sudo pvcreate /dev/sdb
  sudo vgcreate datavg /dev/sdb
  sudo lvcreate -n datalv datavg -L ${DISK_SIZE}
  sudo mkfs.xfs /dev/datavg/datalv
  sudo echo "/dev/datavg/datalv /data xfs defaults,nofail 0 0" | sudo tee -a /etc/fstab
  sudo mkdir /data
  sudo mount /dev/datavg/datalv /data
  df -h | grep datalv
EOF

 echo "####################################################"
done