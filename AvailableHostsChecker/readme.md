# 配置

API KEY用于调用API，肯定要实现配置好，由于租户很多，所以可以每个租户配成一个profile

类似

\[DEFAULT\]

user=ocid1.user.ocqifj4ezwlddm6sksc2zaftslo75ja

fingerprint=_2b_:b7:_7d_:_6d_:fd3a:c4:_3e_:0*5*:38:48

tenancy=ocid1.tenancy.oc1..aaaaaaaaadc4cg5aidblsi4la

region=us-ashburn-1

key*file=C:\\\_Users\\df\\.oci\\dm*

\[APP\]

user=ocid1.user.oc1..aaaaaaaf3u4hb5ck75ga

fingerprint=50:71:c2:b7:_6b_:ff:ef:_1b_:13:c6:_5d_

tenancy=ocid1.tenancy.oc1..aaaaaaaa4fgdtsjpw4jpf6gpjhmkye6mgm5a

region=us-ashburn-1

key*file=C:\\\_Users\\df\\.oci\\apfo.pem*

\[UPP\]

user=ocid1.user.oc1..fhtetejm4c7epnjwgz7yzsrpg6pkq

fingerprint=_2c_:76:_2a_:93:59:17:_2d_:_4f_:f6:_1c_:33

tenancy=ocid1.tenancy.oc1..aaaaftybhiws2k537vfpvqsq

region=ap-osaka-1

key*file=C:\\\_Users\\df\\.oci\\ff\\key.pem*

每个租户可能存在多个region都有专有池，所以把需要用到的region填在工具的代码里

```
pip install gradio oci
```

# 运行

```
python dedicatedPoolChecker.py 
```

 

OCCUPIED是已经开成实例的数目

AVAILABLE就是此刻可以开出来的数目
