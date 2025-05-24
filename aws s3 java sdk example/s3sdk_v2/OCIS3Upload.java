package realtimeSpeech;

import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.S3Configuration;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.model.PutObjectResponse;

import java.io.IOException;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.UUID;

public class OCIS3Upload {
    public static void main(String[] args) throws IOException {
        // OCI 兼容 S3 的 endpoint，例如：https://<namespace>.compat.objectstorage.<region>.oraclecloud.com
        String endpoint = "https://sehubjapacprod.compat.objectstorage.ap-singapore-1.oraclecloud.com";
        String accessKey = "frgsdsd";
        String secretKey = "fgr+60yq4IneE=";
        String bucketName = "velero";
        String objectKey = "test.txt";
        String filePath = "C:\\c.cc";
        String regionStr = "ap-singapore-1";

        S3Client s3 = S3Client.builder()
                .endpointOverride(URI.create(endpoint))
                .region(Region.of(regionStr))
                .credentialsProvider(StaticCredentialsProvider.create(
                        AwsBasicCredentials.create(accessKey, secretKey)))
                .forcePathStyle(true)
                .serviceConfiguration(
                        S3Configuration.builder()
                                .checksumValidationEnabled(false)
                                .build())
                                .build();

        PutObjectRequest putObjectRequest = PutObjectRequest.builder()
                .bucket(bucketName)
                .key(objectKey)
                .build();

 ///// / write string to the file directly
        PutObjectResponse response = s3.putObject(
                putObjectRequest,
                RequestBody.fromString("write str to it ") // 直接从内存上传
        );


////   write local file to the bucket
        PutObjectRequest putObjectRequest2 = PutObjectRequest.builder()
                .bucket(bucketName)
                .key(objectKey)
                .build();
        PutObjectResponse response2 = s3.putObject(putObjectRequest2, Paths.get(filePath));

////    write bytearray to the bucket
        byte[] imageBytes = Files.readAllBytes(Paths.get("C:\\a.png"));
        PutObjectResponse response3 = s3.putObject(
                putObjectRequest,
                RequestBody.fromBytes(imageBytes) // Upload byte array directly
        );


    }
}