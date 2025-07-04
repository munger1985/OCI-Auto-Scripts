package s3sdkoci;

import org.junit.jupiter.api.BeforeEach;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.core.ResponseBytes;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.S3Configuration;
import software.amazon.awssdk.services.s3.model.*;

import java.io.*;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.*;

import org.junit.jupiter.api.Test;
import software.amazon.awssdk.utils.BinaryUtils;
import software.amazon.awssdk.utils.Md5Utils;

import javax.xml.stream.XMLOutputFactory;
import javax.xml.stream.XMLStreamException;
import javax.xml.stream.XMLStreamWriter;

import static org.junit.jupiter.api.Assertions.*;
public class S3SdkTestAll {
    S3Client s3;
    String bucketName = "velero";
    String objectKey = "1.mp4";
    String filePath = "C:\\1.mp4";
    String regionStr = "ap-singapore-1";
@BeforeEach
public   void init() {

    String endpoint = "https://sehubjapacprod.compat.objectstorage.ap-singapore-1.oraclecloud.com";
    String accessKey = "aab8501fa89616424ac7d7123ea8958c1ee8253a";
    String secretKey = "ugZQuW0svq15dwjtiABULNvwme2Xmgj9W+60yq4IneE=";


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

    private String buildDeleteXml(List<ObjectIdentifier> objects) {
        try {
            StringWriter stringWriter = new StringWriter();
            XMLOutputFactory outputFactory = XMLOutputFactory.newInstance();
            outputFactory.setProperty(XMLOutputFactory.IS_REPAIRING_NAMESPACES, true);

            XMLStreamWriter writer = outputFactory.createXMLStreamWriter(stringWriter);

            writer.writeStartDocument("1.0");
            writer.writeStartElement("Delete");

            for (ObjectIdentifier object : objects) {
                writer.writeStartElement("Object");
                writer.writeStartElement("Key");
                writer.writeCharacters(object.key());
                writer.writeEndElement(); // Key
                writer.writeEndElement(); // Object
            }

            writer.writeEndElement(); // Delete
            writer.writeEndDocument();
            writer.close();

            return stringWriter.toString();
        } catch (XMLStreamException e) {
            throw new RuntimeException("Error generating XML for batch delete", e);
        }
    }
    private String calculateContentMd5(String content) {
        byte[] md5 = Md5Utils.computeMD5Hash(content.getBytes(StandardCharsets.UTF_8));
        return BinaryUtils.toBase64(md5);
    }
    @Test
    /**
     * say we have 1.mp4 and test.txt in the bucket, we want to delete them both.
     */
    void testBatchDelete() throws Exception {
        List<String> keysToDelete = List.of("1.mp4", "test.txt");


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

    public static void main(String[] args) throws IOException {
        // OCI 兼容 S3 的 endpoint，例如：https://<namespace>.compat.objectstorage.<region>.oraclecloud.com
        String endpoint = "https://sehubjapacprod.compat.objectstorage.ap-singapore-1.oraclecloud.com";
        String accessKey = "aab8501fa89616424ac7d7123ea8958c1ee8253a";
        String secretKey = "ugZQuW0svq15dwjtiABULNvwme2Xmgj9W+60yq4IneE=";
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


/////  write file to the bucket
        PutObjectRequest putObjectRequest2 = PutObjectRequest.builder()
                .bucket(bucketName)
                .key(objectKey)
                .build();
        PutObjectResponse response2 = s3.putObject(putObjectRequest2, Paths.get(filePath));

/////   write bytearray to the bucket
//        byte[] imageBytes = Files.readAllBytes(Paths.get("C:\\a.png"));
//        PutObjectResponse response3 = s3.putObject(
//                putObjectRequest,
//                RequestBody.fromBytes(imageBytes) // Upload byte array directly
//        );
/////        System.out.println("上传完成，ETag: " + response.eTag());

/////   download as bytearray
        GetObjectRequest getObjectRequest = GetObjectRequest.builder()
                .bucket(bucketName)
                .key("test.txt")
                .build();

        // 下载为字节数组
        ResponseBytes<GetObjectResponse> objectBytes = s3.getObjectAsBytes(getObjectRequest);
        byte[] data = objectBytes.asByteArray();

        String text = new String(data, java.nio.charset.StandardCharsets.UTF_8);
        System.out.println("file content "+text);

//////  download as a file
        GetObjectRequest getObjectRequest3 = GetObjectRequest.builder()
                .bucket(bucketName)
                .key("test.txt")
                .build();
        String downloadPath = "C:\\Users\\qq\\Downloads\\test.txt";
        s3.getObject(getObjectRequest3, Paths.get(downloadPath));

    }
}
