package s3sdkoci;

import org.junit.jupiter.api.BeforeEach;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.core.ResponseBytes;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.core.sync.ResponseTransformer;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.S3Configuration;
import software.amazon.awssdk.services.s3.model.*;
import software.amazon.awssdk.services.s3.presigner.S3Presigner;
import software.amazon.awssdk.services.s3.presigner.model.GetObjectPresignRequest;
import software.amazon.awssdk.services.s3.presigner.model.PresignedGetObjectRequest;
import software.amazon.awssdk.services.s3.presigner.model.PresignedPutObjectRequest;
import software.amazon.awssdk.services.s3.presigner.model.PresignedUploadPartRequest;
import software.amazon.awssdk.services.s3.presigner.model.PutObjectPresignRequest;
import software.amazon.awssdk.services.s3.presigner.model.UploadPartPresignRequest;

import java.util.Arrays;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.*;

import org.junit.jupiter.api.Test;
import software.amazon.awssdk.utils.BinaryUtils;
import software.amazon.awssdk.utils.Md5Utils;

import javax.xml.stream.XMLOutputFactory;
import javax.xml.stream.XMLStreamException;
import javax.xml.stream.XMLStreamWriter;

import static org.junit.jupiter.api.Assertions.*;

public class S3SdkTest {
    S3Client s3;
    String bucketName = "velero";
    String objectKey = "1.mp4";
    String filePath = "/Users/luka/Downloads/1.mp4";
    String smallFilePath = "/Users/luka/Downloads/Oracle_Document.pdf";
    String deleteObject = "8.terraform-modules.pdf";
    String headObject = "thumb.xml";
    String UploadPartPresignedUrl_key = "test_part_upload.pptx";
    String UploadPartPresignedUrl_path = "/Users/luka/Downloads/test_part_upload.pptx";
    String regionStr = "ap-singapore-1";

    @BeforeEach
    public void init() {
        String endpoint = "https://sehubjapacprod.compat.objectstorage.ap-singapore-1.oraclecloud.com";
        String accessKey = "AKAK";
        String secretKey = "SKSK+60yq4IneE=";


        s3 = S3Client.builder()
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
    }

    @Test
    /**
     * say we have 1.mp4 and test.txt in the bucket, we want to delete them both.
     */
    void testBatchDelete() throws Exception {
        List<String> keysToDelete = Arrays.asList("1.mp4", "test.txt");


        List<String> failedKeys=new ArrayList<>();
        ExecutorService executor = Executors.newFixedThreadPool(keysToDelete.size());
        List<Future<?>> futures = new ArrayList<>();
        for (String key : keysToDelete) {
            futures.add(executor.submit(() -> {
                try{
                 DeleteObjectRequest deleteRequest = DeleteObjectRequest.builder()
                        .bucket(bucketName)
                        .key(key)
                        .build();
                s3.deleteObject(deleteRequest);}
                catch (Exception e) {
                    failedKeys.add(key);
                    System.out.println("Error deleting " + key);
                    throw e;
                }

            }));
        }
    // Wait for all tasks to complete
        for (Future<?> future : futures) {
            future.get();
        }

        executor.shutdown(); // 停止接受新任务
        try {
            if (!executor.awaitTermination(600, TimeUnit.SECONDS)) {
                executor.shutdownNow(); // 超时后强制终止
            }
        } catch (InterruptedException e) {
            executor.shutdownNow();
        }
        System.out.println("failed objects to delete: "+failedKeys);

    }


    @Test
    void testCreateMultipartUpload() throws IOException {

        // 1. 初始化分段上传
        CreateMultipartUploadRequest createRequest = CreateMultipartUploadRequest.builder()
                .bucket(bucketName)
                .key(objectKey)
                .build();

        CreateMultipartUploadResponse createResponse = s3.createMultipartUpload(createRequest);
        String uploadId = createResponse.uploadId();
        System.out.println("Upload ID: " + uploadId);

        // 2. 上传分段
        File file = new File(filePath);
        long fileSize = file.length();
        long partSize = 1 * 1024 * 1024; // 5MB每段
        int partCount = (int) (fileSize / partSize);
        if (fileSize % partSize != 0) {
            partCount++;
        }

        List<UploadPartResponse> uploadResponses = new ArrayList<>();
        try (FileInputStream fis = new FileInputStream(file)) {
            for (int i = 1; i <= partCount; i++) {
                long startPos = (i - 1) * partSize;
                long curPartSize = Math.min(partSize, fileSize - startPos);
                byte[] partBytes = new byte[(int) curPartSize];
                fis.read(partBytes);

                UploadPartRequest uploadRequest = UploadPartRequest.builder()
                        .bucket(bucketName)
                        .key(objectKey)
                        .uploadId(uploadId)
                        .partNumber(i)
                        .contentLength(curPartSize)
                        .build();

                UploadPartResponse uploadResponse = s3.uploadPart(
                        uploadRequest,
                        RequestBody.fromBytes(partBytes)
                );
                uploadResponses.add(uploadResponse);
                System.out.println("Part " + i + " uploaded, ETag: " + uploadResponse.eTag());
            }
        }

        // 3. 完成分段上传
        List<CompletedPart> parts = new ArrayList<>();
        for (int i = 0; i < uploadResponses.size(); i++) {
            parts.add(CompletedPart.builder()
                    .partNumber(i + 1)
                    .eTag(uploadResponses.get(i).eTag())
                    .build());
        }

        // 完成分段上传时需要这样使用
        CompletedMultipartUpload completedMultipartUpload = CompletedMultipartUpload.builder()
                .parts(parts)
                .build();

        CompleteMultipartUploadRequest completeRequest = CompleteMultipartUploadRequest.builder()
                .bucket(bucketName)
                .key(objectKey)
                .uploadId(uploadId)
                .multipartUpload(completedMultipartUpload)
                .build();

        CompleteMultipartUploadResponse completeResponse = s3.completeMultipartUpload(completeRequest);

    }


    @Test
    /**
     *  test listing multipartupload before and after aborting multipart upload
     */
    void testAbortMultipartUpload() {

        String newObjName = "abort/"+objectKey;
        CreateMultipartUploadRequest createRequest = CreateMultipartUploadRequest.builder()
                .bucket(bucketName)
                .key(newObjName)
                .build();

        CreateMultipartUploadResponse createResponse = s3.createMultipartUpload(createRequest);
        String uploadId = createResponse.uploadId();
        System.out.println("Upload ID: " + uploadId);

        // 2. 上传分段
        File file = new File(filePath);
        long fileSize = file.length();
        long partSize = 1 * 1024 * 1024; // 5MB每段
        int partCount = (int) (fileSize / partSize);
        if (fileSize % partSize != 0) {
            partCount++;
        }

        List<UploadPartResponse> uploadResponses = new ArrayList<>();
        try (FileInputStream fis = new FileInputStream(file)) {
            for (int i = 1; i <= partCount; i++) {
                long startPos = (i - 1) * partSize;
                long curPartSize = Math.min(partSize, fileSize - startPos);
                byte[] partBytes = new byte[(int) curPartSize];
                fis.read(partBytes);

                UploadPartRequest uploadRequest = UploadPartRequest.builder()
                        .bucket(bucketName)
                        .key(newObjName)
                        .uploadId(uploadId)
                        .partNumber(i)
                        .contentLength(curPartSize)
                        .build();

                UploadPartResponse uploadResponse = s3.uploadPart(
                        uploadRequest,
                        RequestBody.fromBytes(partBytes)
                );
                uploadResponses.add(uploadResponse);
                System.out.println("Part " + i + " uploaded, ETag: " + uploadResponse.eTag());
                break;
            }
        } catch (FileNotFoundException e) {
            throw new RuntimeException(e);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }



        ListMultipartUploadsRequest request = ListMultipartUploadsRequest.builder()
                .bucket(bucketName)
                .prefix("abort/")
                .maxUploads(100) // 限制返回的最大数量
                .build();
        ListMultipartUploadsResponse response = s3.listMultipartUploads(request);
        for (MultipartUpload upload : response.uploads()) {
            System.out.println("Upload: " + upload.key() + ", UploadId: " + upload.uploadId());
            AbortMultipartUploadRequest abortRequest = AbortMultipartUploadRequest.builder()
                    .bucket(bucketName)
                    .key(newObjName)
                    .uploadId(upload.uploadId())
                    .build();
            s3.abortMultipartUpload(abortRequest);
        }


        ListMultipartUploadsResponse response2 = s3.listMultipartUploads(request);
        assertEquals(0, response2.uploads().size());

    }

    @Test
    void testPutObject(){
        PutObjectResponse response = s3.putObject(
                PutObjectRequest.builder()
                .bucket(bucketName)
                .key("Oracle_Document.pdf_by_putObject")
                .contentType("text/plain") // 显式设置 MIME 类型
                .build(),
                RequestBody.fromFile(Paths.get(smallFilePath))
            );

            System.out.println("上传成功! ETag: " + response.eTag());

    }
    @Test
    void testListObjects() {
        ListObjectsV2Response response = s3.listObjectsV2(ListObjectsV2Request.builder()
                .bucket(bucketName)
                        .prefix("ff")
                .delimiter("/")  ///  split common prefix for objects
                .build());
        System.out.println("Bucket objects");
        response.contents().forEach(obj -> System.out.println(" - " + obj.key()));
        System.out.println("Bucket prefixes:");

        for (CommonPrefix prefix : response.commonPrefixes()) {
            System.out.println(" - " + prefix.prefix());
        }
    }

    @Test
    void TestDeleteObject() {
        s3.deleteObject(DeleteObjectRequest.builder()
                .bucket(bucketName)
                .key(deleteObject)
                .build());
        System.out.println("删除成功: " + deleteObject);
    }

    @Test
    void testGetObject() {
        ResponseBytes<GetObjectResponse> objectBytes = s3.getObject(
                GetObjectRequest.builder()
                        .bucket(bucketName)
                        .key(headObject)
                        .build(),
                ResponseTransformer.toBytes()
        );
        String content = objectBytes.asUtf8String();
        System.out.println("文件下载完成: ");
    }

    @Test
    void testHeadObject(){
        // 获取对象元数据
        HeadObjectResponse headResponse = s3.headObject(
            HeadObjectRequest.builder()
                .bucket(bucketName)
                .key(headObject)
                .build()
        );

        // 提取元数据
        long fileSize = headResponse.contentLength(); // 文件大小（字节）
        Instant lastModified = headResponse.lastModified(); // 最后修改时间
        String eTag = headResponse.eTag(); // 文件的ETag（哈希值）
        String contentType = headResponse.contentType(); // MIME类型（如text/plain）

        System.out.println("文件元数据:");
        System.out.println(" - 大小: " + fileSize + " bytes");
        System.out.println(" - 最后修改时间: " + lastModified);
        System.out.println(" - ETag: " + eTag);
        System.out.println(" - Content-Type: " + contentType);
    }

    @Test
    void testGenerateGetPresignedUrl() {
        S3Presigner presigner = S3Presigner.builder()
                .endpointOverride(s3.serviceClientConfiguration().endpointOverride().orElse(null))
                .credentialsProvider(s3.serviceClientConfiguration().credentialsProvider())
                .region(s3.serviceClientConfiguration().region())
                .serviceConfiguration(S3Configuration.builder().pathStyleAccessEnabled(true).build())
                .build();

        PresignedGetObjectRequest presignedRequest = presigner.presignGetObject(
                GetObjectPresignRequest.builder()
                        .signatureDuration(Duration.ofMinutes(10))  
                        .getObjectRequest(GetObjectRequest.builder()
                                .bucket(bucketName)
                                .key("apache-tomcat.zip")
                                .build())
                        .build());

        presigner.close();
        System.out.println("OCI 预签名下载URL: " + presignedRequest.url().toString());
    }        

    @Test
    void testGeneratePutPresignedUrl() {
        S3Presigner presigner = S3Presigner.builder()
                .endpointOverride(s3.serviceClientConfiguration().endpointOverride().orElse(null))
                .credentialsProvider(s3.serviceClientConfiguration().credentialsProvider())
                .region(s3.serviceClientConfiguration().region())
                .serviceConfiguration(S3Configuration.builder().pathStyleAccessEnabled(true).build())
                .build();

        PresignedPutObjectRequest presignedRequest = presigner.presignPutObject(
            PutObjectPresignRequest.builder()
                .signatureDuration(Duration.ofMinutes(15))
                .putObjectRequest(PutObjectRequest.builder()
                    .bucket(bucketName)
                    .key("Oracle_Document.pdf_by_presignPutObject")
                    .contentType("application/octet-stream") // 强制二进制流类型
                    .build())
                .build());

        String presignedUrl = presignedRequest.url().toString();
        System.out.println("OCI 预签名上传URL: \n" + presignedUrl);

        Path file = Paths.get(smallFilePath);
        try {
            File file1 = file.toFile();
            URL url = new URL(presignedUrl);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            
            // 配置请求
            conn.setRequestMethod("PUT");
            conn.setDoOutput(true);
            conn.setRequestProperty("Content-Type", "application/octet-stream");
            
            // 上传文件流
            try (FileInputStream fis = new FileInputStream(file1);
                 OutputStream os = conn.getOutputStream()) {
                byte[] buffer = new byte[8192];
                int bytesRead;
                while ((bytesRead = fis.read(buffer)) != -1) {
                    os.write(buffer, 0, bytesRead);
                }
            }
            // 获取响应状态码
            int statusCode = conn.getResponseCode();
            System.out.println("上传状态码: " + statusCode); // 成功返回 200
        } catch (Exception e) {
            e.printStackTrace();
        }

        //验证上传本地文件（需安装 curl）curl -X PUT --upload-file "localfile.txt" -H "Content-Type: application/octet-stream" url
        presigner.close();
    }

    @Test
    void testGenerateUploadPartPresignedUrl(){
        String object_key = UploadPartPresignedUrl_key;
        try {
            // 1. 初始化分片上传
            String uploadId = initMultipartUpload(s3, bucketName, object_key);
            System.out.println("Upload ID: " + uploadId);

            // 2. 生成分片预签名URL
            int partNumber = 1;
            String presignedUrl = generatePartPresignedUrl(
                s3, 
                bucketName, 
                object_key, 
                uploadId, 
                partNumber, 
                1, // 有效期1小时
                TimeUnit.HOURS
            );
            System.out.println("Part " + partNumber + " Presigned URL: \n" + presignedUrl);

            // 3. 实际上传分片并获取真实ETag
            String eTag = uploadPartAndGetETag(presignedUrl);
            System.out.println("Part " + partNumber + " ETag: " + eTag);

            // 4. 验证分片是否上传成功
            if (verifyPartUpload(s3, bucketName, object_key, uploadId, partNumber, eTag)) {
                // 5. 完成分片上传
                List<CompletedPart> completedParts = new ArrayList<>();
                completedParts.add(CompletedPart.builder()
                    .partNumber(partNumber)
                    .eTag(eTag)
                    .build());

                completeMultipartUpload(s3, bucketName, object_key, uploadId, completedParts);
            } else {
                System.err.println("分片验证失败，请检查上传情况");
            }
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            s3.close();
        }
    }

    private static String initMultipartUpload(S3Client s3Client, String bucket, String key) {
        CreateMultipartUploadRequest request = CreateMultipartUploadRequest.builder()
            .bucket(bucket)
            .key(key)
            .build();
        return s3Client.createMultipartUpload(request).uploadId();
    }

    private static String generatePartPresignedUrl(
            S3Client s3Client, String bucket, String key, 
            String uploadId, int partNumber, 
            long expiry, TimeUnit timeUnit) {
        
        S3Presigner presigner = S3Presigner.builder()
            .endpointOverride(s3Client.serviceClientConfiguration().endpointOverride().orElse(null))
            .credentialsProvider(s3Client.serviceClientConfiguration().credentialsProvider())
            .region(s3Client.serviceClientConfiguration().region())
            .serviceConfiguration(S3Configuration.builder().pathStyleAccessEnabled(true).build())
            .build();

        UploadPartRequest uploadPartRequest = UploadPartRequest.builder()
            .bucket(bucket)
            .key(key)
            .uploadId(uploadId)
            .partNumber(partNumber)
            .build();

        PresignedUploadPartRequest presignedRequest = presigner.presignUploadPart(
            UploadPartPresignRequest.builder()
                .signatureDuration(Duration.ofHours(expiry))
                .uploadPartRequest(uploadPartRequest)
                .build());

        presigner.close();
        return presignedRequest.url().toString();
    }

    private String uploadPartAndGetETag(String presignedUrl) {
        String filePath = UploadPartPresignedUrl_path;
        Path file = Paths.get(filePath);
        
        try {
            URL url = new URL(presignedUrl);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            
            // 配置请求
            conn.setRequestMethod("PUT");
            conn.setDoOutput(true);
            conn.setRequestProperty("Content-Type", "application/octet-stream");
            
            // 上传文件流
            try (FileInputStream fis = new FileInputStream(file.toFile());
                 OutputStream os = conn.getOutputStream()) {
                byte[] buffer = new byte[8192];
                int bytesRead;
                while ((bytesRead = fis.read(buffer)) != -1) {
                    os.write(buffer, 0, bytesRead);
                }
            }
            
            // 获取响应状态码和ETag
            int statusCode = conn.getResponseCode();
            String eTag = conn.getHeaderField("ETag");
            
            if (statusCode == 200 && eTag != null) {
                // 移除ETag中的双引号
                return eTag.replace("\"", "");
            } else {
                throw new RuntimeException("上传失败，状态码: " + statusCode);
            }
        } catch (Exception e) {
            throw new RuntimeException("分片上传失败", e);
        }
    }

    private static boolean verifyPartUpload(S3Client s3Client, String bucket, String key, 
                                         String uploadId, int partNumber, String expectedETag) {
        try {
            ListPartsRequest listRequest = ListPartsRequest.builder()
                .bucket(bucket)
                .key(key)
                .uploadId(uploadId)
                .build();

            List<Part> parts = s3Client.listParts(listRequest).parts();
            for (Part part : parts) {
                if (part.partNumber() == partNumber) {
                    String actualETag = part.eTag().replace("\"", "");
                    if (actualETag.equals(expectedETag)) {
                        System.out.println("分片验证成功");
                        return true;
                    } else {
                        System.err.println("ETag不匹配，预期: " + expectedETag + "，实际: " + actualETag);
                        return false;
                    }
                }
            }
            System.err.println("未找到指定分片");
            return false;
        } catch (Exception e) {
            System.err.println("验证分片时出错: " + e.getMessage());
            return false;
        }
    }

    private static void completeMultipartUpload(
            S3Client s3Client, String bucket, String key, 
            String uploadId, List<CompletedPart> parts) {
        
        try {
            CompletedMultipartUpload completedUpload = CompletedMultipartUpload.builder()
                .parts(parts)
                .build();

            CompleteMultipartUploadRequest completeRequest = CompleteMultipartUploadRequest.builder()
                .bucket(bucket)
                .key(key)
                .uploadId(uploadId)
                .multipartUpload(completedUpload)
                .build();

            CompleteMultipartUploadResponse response = s3Client.completeMultipartUpload(completeRequest);
            System.out.println("分片上传完成！对象ETag: " + response.eTag());
        } catch (S3Exception e) {
            System.err.println("完成分片上传失败: " + e.awsErrorDetails().errorMessage());
            throw e;
        }
    }
}
