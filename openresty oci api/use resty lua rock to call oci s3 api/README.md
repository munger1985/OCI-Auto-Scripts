# https://opm.openresty.org/package/rtokarev/lua-resty-aws-signature/

but we need to modify some code

  ``` require("resty.aws-signature").s3_set_headers(ngx.var.s3_host, ngx.var.uri)
  ```
   ==>  

   ```
       require("resty.aws-signature").s3_set_headers(ngx.var.s3_host, ngx.var.uri,'ap-singapore-1')
       ```
vi  /usr/local/openresty/site/lualib/resty/aws-signature.lua

```
function _M.aws_set_headers(host, uri, region,creds)
  if not creds or not creds.access_key or not creds.secret_key then
    creds = get_credentials()
  end
  local timestamp = tonumber(ngx.time())
 
 service='s3'
  local auth = get_authorization(creds, timestamp, region, service, host, uri)

  ngx.req.set_header('Authorization', auth)
  ngx.req.set_header('Host', host)
  ngx.req.set_header('x-amz-date', get_iso8601_basic(timestamp))
end
```
you can now run resty to test