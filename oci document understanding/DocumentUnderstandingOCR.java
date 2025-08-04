package du;

import com.oracle.bmc.Region;
import com.oracle.bmc.aidocument.AIServiceDocumentClient;
import com.oracle.bmc.aidocument.model.*;
import com.oracle.bmc.aidocument.requests.AnalyzeDocumentRequest;
import com.oracle.bmc.aidocument.responses.AnalyzeDocumentResponse;
import com.oracle.bmc.auth.ConfigFileAuthenticationDetailsProvider;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

public class DuTest {
    @Test
    public void testOcrBucketFile() throws IOException {

        // 1. the file location in your bucket
        String ns = "sehubjapacprod";
        String bucket = "velero";
        String outputPrefix = "output";
        String objectName = "pp.png";


        ConfigFileAuthenticationDetailsProvider provider =
                new ConfigFileAuthenticationDetailsProvider("~/.oci/config", "DEFAULT");

        // 2. 创建客户端
        AIServiceDocumentClient client =      AIServiceDocumentClient.builder().build(provider);
        client.setRegion(Region.AP_CHUNCHEON_1);
        // 3. 读取图片并Base64编码
        ArrayList<DocumentFeature> featureArrayList = new ArrayList<>();
//        new DocumentFeature().
        featureArrayList.add(new DocumentTextExtractionFeature(false) );
        // 4. 构建请求
        AnalyzeDocumentRequest request = AnalyzeDocumentRequest.builder()
                .analyzeDocumentDetails(
                        AnalyzeDocumentDetails.builder()
                                .features(featureArrayList)
                                .document(ObjectStorageDocumentDetails.builder()
                                        .namespaceName(ns)
                                        .bucketName(bucket)
                                        .objectName(objectName).build())
                                .language("zh") // 指定中文
                                .build()
                )
                .build();

        // 5. 调用API
        AnalyzeDocumentResponse response = client.analyzeDocument(request);
        AnalyzeDocumentResult analyzeDocumentResult = response.getAnalyzeDocumentResult();

        List<Page> pages = analyzeDocumentResult.getPages();

        for (Page page : pages) {
            // 遍历每一页的所有行
            List<Line> lines = page.getLines();
            if (lines != null) {
                for (Line line : lines) {
                    System.out.println(line.getText());

                }
            }
        }

    }

    /**
     // inline document, dont need to upload to bucket
     *
     * @throws IOException
     */
    @Test
    public void testOcrInlineDocument() throws IOException {

        String filePath="C:\\Users\\qq\\Desktop\\pp.png";

        ConfigFileAuthenticationDetailsProvider provider  =
                new ConfigFileAuthenticationDetailsProvider("~/.oci/config", "DEFAULT");
        AIServiceDocumentClient client =      AIServiceDocumentClient.builder().build(provider);
        client.setRegion(Region.AP_CHUNCHEON_1);

        ArrayList<DocumentFeature> featureArrayList = new ArrayList<>();
        featureArrayList.add(
                DocumentTextExtractionFeature.builder().generateSearchablePdf(false)
                        // If the boolean was for a specific property (e.g., isOcrEnabled or similar), set it here.
                        // Consult the SDK docs for exact properties; 'false' is assumed to map to a flag like this:
                        .build()
        );
        byte[] fileBytes = Files.readAllBytes(Paths.get(filePath));


        AnalyzeDocumentRequest  request = AnalyzeDocumentRequest.builder()
                .analyzeDocumentDetails(
                        AnalyzeDocumentDetails.builder()
                                .features(featureArrayList)
                                .document(InlineDocumentDetails.builder().data(fileBytes).build())
                                .language("zh") // 指定中文
                                .build()
                )
                .build();

        AnalyzeDocumentResponse response = client.analyzeDocument(request);

      AnalyzeDocumentResult  analyzeDocumentResult = response.getAnalyzeDocumentResult();

        List<Page> pages   = analyzeDocumentResult.getPages();

        for (Page page : pages) {
            // 遍历每一页的所有行
            List<Line> lines = page.getLines();
            if (lines != null) {
                for (Line line : lines) {
                    System.out.println(line.getText());

                }
            }
        }
    }



}
