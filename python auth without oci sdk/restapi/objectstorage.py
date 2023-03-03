import sys
import requests, json
import datetime, time
from signer import Signer

auth = Signer(
    tenancy='ocid1.tenancy.oc1..aaaaaaaav4l377b6cxuwehvjbzbxe7nkea4ltkgb6haa7fhuymhjvzoctq2q',
    user='ocid1.user.oc1..aaaaaaaab44jcrtczf6kmf5lckbaqvjlnqq7dsj4lr7xhmnjqftjjgkv42na',
    fingerprint='6b:f4:8c:e3:7c:01:07:95:93:a4:df:ff:7b:ef:38:68',
    private_key_file_location='oci_api_key.pem'
)

endpoint = 'https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/frqeqsp3vdci/b'

body = {
    'name': 'Bob_test_1',
    'compartmentId': 'ocid1.tenancy.oc1..aaaaaaaav4l377b6cxuwehvjbzbxe7nkea4ltkgb6haa7fhuymhjvzoctq2q'
}


response = requests.post(endpoint, json=body, auth=auth)
response.raise_for_status()

if response.status_code != 200:
    print ('Request Failed !')
    exit(1)

print(response.text)
