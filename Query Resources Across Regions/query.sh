EMAIL=$1
echo "[" > list.json
for REGION in {eu-marseille-1,eu-milan-1,ap-singapore-1,ap-osaka-1,ap-tokyo-1,eu-amsterdam-1,me-jeddah-1,ap-singapore-1,af-johannesburg-1,ap-seoul-1,ap-chuncheon-1,eu-stockholm-1,eu-zurich-1,me-abudhabi-1,me-dubai-1,uk-london-1,uk-cardiff-1,us-ashburn-1,us-phoenix-1,us-sanjose-1,ap-sydney-1,ap-melbourne-1,sa-saopaulo-1,sa-vinhedo-1,ca-montreal-1,ca-toronto-1,sa-santiago-1,eu-frankfurt-1,ap-hyderabad-1,ap-mumbai-1,il-jerusalem-1}; 
do 
  echo "search "$REGION" start"; 
  echo "[{\"regoin\":\"$REGION\"}," >> list.json
  QUERY_TEXT='query all resources where (definedTags.namespace = "default_tags" && definedTags.key = "CreatedBy" && definedTags.value = "'$EMAIL'")'
  oci search resource structured-search --query-text "$QUERY_TEXT" --query 'data.[items[*]]' --region=$REGION >> list.json
  
  echo "search "$REGION" complete"; 
  echo "]" >> list.json
  echo "," >> list.json
done;
echo "[]" >> list.json
echo "]" >> list.json
mv list.json $2

#用法 ./query.sh 用户名 另存为文件名
#示例 ./query.sh oracleidentitycloudservice/wenbin.chen@oracle.com  wenbin.chen.json
#json to excel  https://jsongrid.com/json-grid