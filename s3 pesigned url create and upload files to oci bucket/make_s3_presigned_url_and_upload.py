import requests

import argparse
import logging
import boto3
from botocore.exceptions import ClientError
import requests

logger = logging.getLogger(__name__)


def generate_presigned_url(s3_client, client_method, method_parameters, expires_in):
    """
    Generate a presigned Amazon S3 URL that can be used to perform an action.

    :param s3_client: A Boto3 Amazon S3 client.
    :param client_method: The name of the client method that the URL performs.
    :param method_parameters: The parameters of the specified client method.
    :param expires_in: The number of seconds the presigned URL is valid for.
    :return: The presigned URL.
    """
    try:
        url = s3_client.generate_presigned_url(
            ClientMethod=client_method,
            Params=method_parameters,
            ExpiresIn=expires_in
        )
        logger.info("Got presigned URL: %s", url)
    except ClientError:
        logger.exception(
            "Couldn't get a presigned URL for client method '%s'.", client_method)
        raise
    return url


# Create a Boto3 S3 client with your credentials and endpoint
s3_client = boto3.client(
    's3',
    aws_access_key_id='asd',
    aws_secret_access_key='asdasd+60yq4IneE=',
    endpoint_url='https://sehubjapacprod.compat.objectstorage.AP-SINGAPORE-1.oraclecloud.com',
    region_name=   'ap-singapore-1'
)

client_action =  'put_object'
# client_action =  'get_object'
url = generate_presigned_url(
s3_client, client_action, {'Bucket': 'velero', 'Key': 'w.txt'}, 360000)
print(url)

# Define the URL to which you want to send the PUT request
# url = 'https://sehubjapacprod.compat.objectstorage.ap-singapore-1.oraclecloud.com/velero/w2?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=aab8501fa89616424ac7d7123ea8958c1ee8253a%2F20231013%2Fap-singapore-1%2Fs3%2Faws4_request&X-Amz-Date=20231013T075853Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=a2444fdf2e14259f521a02510f1b68b335a324c1811242bd3629d8c9bb3181bf'  # Replace with your actual URL

# Define the file you want to upload
file_path = 'w.txt'  # Replace with the actual path to your file

# Open and read the file
with open(file_path, 'rb') as file:
    # Create a dictionary containing the file data
    files = {'file': (file_path, file)}
    object_text = file.read()
    # Send a PUT request with the file attached
    url =url.replace("https://sehubjapacprod.compat.objectstorage.AP-SINGAPORE-1.oraclecloud.com","http://t.tina.lol")

    response = requests.put(url, data=object_text)
    print('tina',url)
    # response = requests.put(url, files=files)

# Check the response
if response.status_code == 200:
    print("File successfully uploaded.")
else:
    print(f"Failed to upload file. Status code: {response.status_code}")
    print(response.text)  # Print the response content for more details if needed
