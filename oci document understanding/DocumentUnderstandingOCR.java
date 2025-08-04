import com.oracle.bmc.aidocument.AIServiceDocumentClient;
import com.oracle.bmc.aidocument.model.*;
import com.oracle.bmc.aidocument.requests.AnalyzeDocumentRequest;
import com.oracle.bmc.aidocument.responses.AnalyzeDocumentResponse;
import com.oracle.bmc.auth.ConfigFileAuthenticationDetailsProvider;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class DocumentUnderstandingOCR {
    public static void main(String[] args) throws IOException {
        // 1. 认证
        String ns = "sehubjapacprod";
        String bucket = "velero";
        String outputPrefix = "output";
        String objectName = "pp.png";


        ConfigFileAuthenticationDetailsProvider provider =
                new ConfigFileAuthenticationDetailsProvider("~/.oci/config", "DEFAULT");

        // 2. 创建客户端
        AIServiceDocumentClient client =      AIServiceDocumentClient.builder().build(provider);
        // 3. 读取图片并Base64编码
        ArrayList<DocumentFeature> arrayList = new ArrayList<>();
//        new DocumentFeature().
        arrayList.add(new DocumentTextExtractionFeature(false) );
        // 4. 构建请求
        AnalyzeDocumentRequest request = AnalyzeDocumentRequest.builder()
                .analyzeDocumentDetails(
                        AnalyzeDocumentDetails.builder()
                                .features(arrayList)
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


        // 6. 输出识别结果
//        for (DetectedTextBlock block : response.getAnalyzeDocumentResult().getPages()) {
//            System.out.println("识别到的文本: " + block.getText());
//        }

        // 7. 关闭客户端
        client.close();
    }
}
