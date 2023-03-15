local function str2bytes(str)
    local bytes = {}
    for i = 1, #str do
        bytes[i] = string.byte(str, i)
    end

    return #bytes
end

local function auth()
    local tenancy = "ocid1.tenancy.oc1..aaaaaaaav4l377b6cxuwehvjbzbxe7nkea4ltkgb6haa7fhuymhjvzoctq2q"
    local user = "ocid1.user.oc1..aaaaaaaab44jcrtczf6kmf5lckbaqvjlnqq7dsj4lr7xhmnjqftjjgkv42na"
    local fingerprint = "6b:f4:8c:e3:7c:01:07:95:93:a4:df:ff:7b:ef:38:68"

    local rsa_priv_key = [[-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCdAfDQr1mJi++J
SrkYEUEhr6wFRRjS7FBrPEq3JnHEUbNf24kNWliLjHn83qp5co/XGrghJhvjNJ5P
g2JDhX8iA13CZ5NGZIbVpHOjshQnl6AxmdNFWhk2AMoCfgcDprHuOqQc9l1ZEQEC
3Hb2EPPPmGtuN6rkwrok3YZ6SJ0QfM3f7OLHxCKVh2nbVPUj4FCOn9+G5rh5tUja
2vv1NqLooHUu9v4jTgq1oK73hqtSd8pdZW5GFvz1HQpLy5QTBnCu5rFoq3ZAFESx
ZtLjHvGfn/NAymly5MAf7zSX/W7Or1jSMxFsBIfz29sFwUZye1qEzmYGKazWgbRb
cxAsNi5nAgMBAAECggEAAhlTO7UNisdnS5XfsJSzbAjvY3fijXnGLSkzcLDu8zmc
ekr79dcwtfvrgy7GYSuWozSkTuSRK/f/g5qnoZ0FhPOHMC6JAJvhqmzfQ+7WcQsO
g7p5f+xk1DhMJbcYsEop+64CGu2uNxLQknqsEtWewPlmD/q8ApLvLorXTo3O9Ept
RQCWwwkDPU0vOgHp7LgGkCsunu8FMn9jGHJ666lO1pE9LxzujbX9wRp/V69MY5j2
OP0wpcx1gqgEhwonlpjs4Janl/YI+MOsmRQfEnp6r6eW7si6Mhgt4Gy2QPJxjPav
Q7MG/RKtuQG+4f9NVaS5wXIZ4Lkgg9QAw5mY2z9/3QKBgQDV7uPnE+Bw2xZ4r1+q
84XT8QRRB3Laye65dgZkXtgiPYffazvt45CK5jrwWN5RbcxuEdcTAzFG4JGjs9+9
SYywprWJ3bod1FHt7otO1IFOCcuh1R3WKt82xgphIeKup/T223Ik/dW4LKObmC82
El7TJgm6pLMFP66M3oGGjX8ynQKBgQC74X4ZIvvGpZsmRI1dH0KwCpTVwNmIjCiU
RUA//35aMLnjYR1qdiqW8U8rs87ICluWYyUwH6uT9PG2scwOclWGZwPGnE/SSMVi
dWxxkFYn0Hd1BavUcd7LQpUkn/+Dptf7JrFx3auJEV0cYHVE3mECUktXN21m1ram
5d6AdgQj0wKBgFwOjSE9a2IE1Lmf9ZHRcrAN0Wawxtqg9En4IK4GJgkt4w7fzQ0D
1IoAojIUe64cilB++saipAy0y9beqxN/17uYMRwfPlxhpdO1x1pnlTCohGiiFVG4
Zw7hz0uW0j2H5qBnM8n5NIMpKknlBcPFyeogPyWCg8ppacoSYTguISL9AoGACe45
RArdU/qc4MDu1+U3GSb2BvZSiS0fV/bxFnDitNGugZ44d9AXIDNRA/ZVD628eY50
AL8ryn4/6HAtYPYaHyiCwpSwg2TlSfb67GW8qA4UwlKyamA6bnPufikW0FaZQ+Uf
q+0TjAMm8MEIccNvTTgcU1fSqITg0qGDyTZzsZECgYBXShsu4iJrWQ2TUZP2D3Ma
pQbeRgnjM2udAfMmkeHlGxWK7CyBQpVeU8qtH1egaHhFciHLJGQNnDziCouBB7Nv
dj8kSjhViqKxTRyYmB4uK5dGQrrw0ZgvYZ0r9qOgIOEfWHfBXAjltXwIleULD2Wv
KDExvUOUDdzysnqrraRsgw==
-----END PRIVATE KEY-----]]


    local apiKeyId = string.format("%s/%s/%s",tenancy, user, fingerprint)
    local host= ngx.var.hostname
    local method = ngx.var.request_method
    local path = ngx.unescape_uri(ngx.var.uri)


    local currentDate = ngx.http_time(ngx.time())
    ngx.req.set_header("date", currentDate)
    ngx.req.set_header("host", host)


    local hostHeader = string.format('host: %s', host)
    local dateHeader = string.format('date: %s', currentDate)
    local requestTargetHeader = string.format('(request-target): %s %s', string.lower(method), path)
    ngx.req.set_header("(request-target)", requestTargetHeader);
    local signingStringArray = {
        requestTargetHeader,
        dateHeader,
        hostHeader
    }

    local headersToSign = {
        "(request-target)",
        "date",
        "host"
    }
    local methodsThatRequireExtraHeaders = "POST|PUT|PATCH"



    local objectStorageSpecial = false
    if ((method == "PUT") and ((string.find(path,"/n/") == 1) and ((string.find(path,"/o/")~=nil or string.find(path,"/u/")~=nil)))) then
        objectStorageSpecial = true
    end

    if (string.find(methodsThatRequireExtraHeaders, method) ~= nil and objectStorageSpecial == false) then
        ngx.req.read_body()
        local body = ngx.var.request_body
        if (body == nil) then
            body = ""
        end

        local bodyLength = tostring(str2bytes(body))
        local contentLengthHeader = string.format("content-length: %s", bodyLength)
        local contentTypeHeader = "content-type: application/json"

        ngx.req.set_header("content-length" ,bodyLength)
        ngx.req.set_header("content-type", "application/json")

        local resty_sha256 = require "resty.sha256"
        local str = require "resty.string"
        local sha256 = resty_sha256:new()
        sha256:update(body)
        local digest = sha256:final()
        local base64EncodedBodyHash = ngx.encode_base64(digest)

        local contentSha256Header = string.format("x-content-sha256: %s",base64EncodedBodyHash)
        ngx.req.set_header("x-content-sha256", base64EncodedBodyHash)

        table.insert(signingStringArray, contentSha256Header)
        table.insert(signingStringArray, contentTypeHeader)
        table.insert(signingStringArray, contentLengthHeader)

        table.insert(headersToSign, "x-content-sha256")
        table.insert(headersToSign, "content-type")
        table.insert(headersToSign, "content-length")

    end

    local headers = table.concat(headersToSign, " ")
    local signingString = table.concat(signingStringArray,"\n")

    local resty_rsa = require "resty.rsa"
    local str = require "resty.string"
    local algorithm = "RSA-SHA256"
    local priv, err = resty_rsa:new({ private_key = rsa_priv_key, algorithm = algorithm})
    if not priv then
        ngx.say("new rsa err: ", err)
        return
    end

    local sig, err = priv:sign(signingString)
    if not sig then
        ngx.say("failed to sign:", err)
        return
    end

    local base64EncodedSignature = ngx.encode_base64(sig)

    local authorization = string.format('Signature version="1",keyId="%s",algorithm="rsa-sha256",headers="%s",signature="%s"',apiKeyId, headers, base64EncodedSignature)

    ngx.req.set_header("Authorization", authorization)

    ngx.log(authorization)

    ngx.exec("@oci_os")

end

-- main
res = auth()

if res then
    ngx.exit(res)
end