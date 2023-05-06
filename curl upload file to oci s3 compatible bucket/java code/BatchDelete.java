package com.example.demo;

/**
 * Copyright 2018-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * This file is licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License. A copy of
 * the License is located at
 *
 * http://aws.amazon.com/apache2.0/
 *
 * This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
 * CONDITIONS OF ANY KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations under the License.
 */

// snippet-sourcedescription:[UploadObject.java demonstrates how to perform a basic object upload using Amazon S3.]
// snippet-service:[s3]
// snippet-keyword:[Java]
// snippet-sourcesyntax:[java]
// snippet-keyword:[Amazon S3]
// snippet-keyword:[Code Sample]
// snippet-keyword:[PUT Object]
// snippet-sourcetype:[full-example]
// snippet-sourcedate:[2019-01-28]
// snippet-sourceauthor:[AWS]
// snippet-start:[s3.java.upload_object.complete]

import com.amazonaws.AmazonServiceException;
import com.amazonaws.ClientConfiguration;
import com.amazonaws.Protocol;
import com.amazonaws.SdkClientException;
import com.amazonaws.auth.*;
import com.amazonaws.client.builder.AwsClientBuilder;
import com.amazonaws.regions.Regions;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3Client;
import com.amazonaws.services.s3.AmazonS3ClientBuilder;
import com.amazonaws.services.s3.S3ClientOptions;
import com.amazonaws.services.s3.model.ObjectMetadata;
import com.amazonaws.services.s3.model.PutObjectRequest;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.util.Properties;

public class UploadObject {


    public static void mm( ) throws IOException {
        // if use env vars, AWS_ACCESS_KEY_ID=xxx, AWS_SECRET_ACCESS_KEY=xxx
//        Properties p =
//                new Properties(System.getProperties());
//        p.setProperty("aws.accessKeyId","5");
//        p.setProperty("aws.secretAccessKey", "5+60yq4IneE=");
//        System.setProperties(p);
//        BasicAWSCredentials awsCreds = new BasicAWSCredentials
//                ("5",
//                        "5+60yq4IneE=");
        Regions clientRegion = Regions.DEFAULT_REGION;
        String bucketName = "velero";
        String stringObjKeyName = "stryml";
        String fileObjKeyName = "application.yml";
        String fileName = "./d.yml";
        AwsClientBuilder.EndpointConfiguration endpointConfiguration = new AwsClientBuilder.EndpointConfiguration("sehubjapacprod.compat.objectstorage.ap-singapore-1.oraclecloud.com", "ap-singapore-1");
        try {
            //This code expects that you have AWS credentials set up per:
            // https://docs.aws.amazon.com/sdk-for-java/v1/developer-guide/setup-credentials.html

            ClientConfiguration clienConfig=new ClientConfiguration();
            clienConfig.setProtocol(Protocol.HTTPS);
            AmazonS3ClientBuilder preb  =  AmazonS3ClientBuilder.standard(). withEndpointConfiguration(endpointConfiguration)
                    .withCredentials(new EnvironmentVariableCredentialsProvider())
//                    .withCredentials (new AWSStaticCredentialsProvider(awsCreds))
                    .withPathStyleAccessEnabled(true);
//            preb.setClientConfiguration(clienConfig);
            AmazonS3 s3Client = preb
                    .build();

                    List<DeleteObjectsRequest.KeyVersion> keysAndVersions = new ArrayList<>();
                    keysAndVersions.add(new DeleteObjectsRequest.KeyVersion("stryml"));
                    keysAndVersions.add(new DeleteObjectsRequest.KeyVersion("my-object-2", "version-id-2"));ersion("stryml2"));
                    DeleteObjectsRequest deleteObjectsRequest = new DeleteObjectsRequest(bucketName)
                            .withKeys(keysAndVersions);
        
        // Delete the objects using the deleteObjects method
                    DeleteObjectsResult deleteObjectsResult = s3Client.deleteObjects(deleteObjectsRequest);
        
//            request.setMetadata(metadata);
//            s1=System.currentTimeMillis();
//            s3Client.putObject(request);
//            s2=System.currentTimeMillis();
//            System.out.println("takes "+(s2-s1));
        } catch (AmazonServiceException e) {
            // The call was transmitted successfully, but Amazon S3 couldn't process
            // it, so it returned an error response.
            e.printStackTrace();
        } catch (SdkClientException e) {
            // Amazon S3 couldn't be contacted for a response, or the client
            // couldn't parse the response from Amazon S3.
            e.printStackTrace();
        }
    }
}