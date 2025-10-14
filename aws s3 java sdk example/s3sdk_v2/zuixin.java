package com.demo;

import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.S3Configuration;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.presigner.S3Presigner;
import software.amazon.awssdk.services.s3.presigner.model.GetObjectPresignRequest;
import software.amazon.awssdk.services.s3.presigner.model.PresignedGetObjectRequest;

import java.net.URI;
import java.time.Duration;

//TIP To <b>Run</b> code, press <shortcut actionId="Run"/> or
// click the <icon src="AllIcons.Actions.Execute"/> icon in the gutter.

// if using the latest version s3 sdk , 
public class zuixin {
    public static void main(String[] args) {
        // OCI S3 兼容配置
        String endpoint = "https://axdnvp7.compat.objectstorage.ap-singapore-1.oraclecloud.com";
        String accessKey = "7a014aeddd2b199f49e";
        String secretKey = "XGYdfydDv4hsgc=";
        String regionStr = "ap-singapore-1";
        String bucketName = "bucket-20251010-1009";

        // 0. 创建 S3Client（适配 OCI）
        S3Client s3Client = S3Client.builder()
                .endpointOverride(URI.create(endpoint))  // OCI S3 兼容端点
                .serviceConfiguration(
                        S3Configuration.builder()
                                .pathStyleAccessEnabled(true) // 关键：强制使用 Path Style
                                .build())
                .credentialsProvider(StaticCredentialsProvider.create(
                        AwsBasicCredentials.create(accessKey, secretKey)))
                .region(Region.of(regionStr))  // 任意值（OCI 会忽略，但 SDK 要求必填）
                .build();

        // 1. 生成下载预签名 URL
        generateGetPresignedUrl(s3Client, bucketName);

        s3Client.close();
    }

    // 生成下载预签名URL 有效期10分钟
    private static void generateGetPresignedUrl(S3Client s3Client, String bucket) {
        S3Presigner presigner = S3Presigner.builder()
                .endpointOverride(s3Client.serviceClientConfiguration().endpointOverride().orElse(null))
                .credentialsProvider(s3Client.serviceClientConfiguration().credentialsProvider())
                .region(s3Client.serviceClientConfiguration().region())
                .serviceConfiguration(S3Configuration.builder().pathStyleAccessEnabled(true).build())
                .build();

        PresignedGetObjectRequest presignedRequest = presigner.presignGetObject(
                GetObjectPresignRequest.builder()
                        .signatureDuration(Duration.ofMinutes(10))
                        .getObjectRequest(GetObjectRequest.builder()
                                .bucket(bucket)
                                .key("1.mp4")
                                .build())
                        .build());

        presigner.close();
        System.out.println("OCI 预签名下载URL: " + presignedRequest.url().toString());
    }
}
