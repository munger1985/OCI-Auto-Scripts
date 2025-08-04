import oci
import gradio as gr
from oci.ai_document import AIServiceDocumentClient
from oci.object_storage import ObjectStorageClient
from oci.ai_document.models import AnalyzeDocumentDetails, DocumentFeature, InlineDocumentContent
import base64
import io

# OCI 配置
CONFIG_PROFILE = "DEFAULT"
config = oci.config.from_file("~/.oci/config", CONFIG_PROFILE)
COMPARTMENT_OCID = "ocid1.compartment.oc1..aaaaaaaau5q457a7teqkjce4oenoiz6bmc4g3s74a5543iqbm7xwplho44fq"  # 替换为您的compartment OCID
NAMESPACE_NAME = "sehubjapacprod"  # 替换为您的Object Storage命名空间
BUCKET_NAME = "velero"  # 替换为您的存储桶名称
config.update({"region": "ap-singapore-2"})
# 初始化OCI客户端
ai_client = AIServiceDocumentClient(config)
object_storage_client = ObjectStorageClient(config)

def ocr_image(image_path):
    try:
        # 将图像转换为base64编码

        with open(image_path, "rb") as image_file:
            base64_str  = base64.b64encode(image_file.read()).decode("utf-8")


        # 创建InlineDocumentContent
        document_content = InlineDocumentContent(data=base64_str )

        # 设置OCR功能
        features = DocumentFeature(feature_type="TEXT_EXTRACTION")

        # 配置分析请求
        analyze_document_details = AnalyzeDocumentDetails(
            compartment_id=COMPARTMENT_OCID,
            document=oci.ai_document.models.InlineDocumentDetails(
                source="INLINE",
                data=base64_str
               ),
            features=[features],
            language='zh',
            output_location=oci.ai_document.models.OutputLocation(
                namespace_name=NAMESPACE_NAME,
                bucket_name=BUCKET_NAME,
                prefix="ocr_results"
            ),
            document_type="OTHERS",
        )

        # 调用Document Understanding服务
        response = ai_client.analyze_document(analyze_document_details=analyze_document_details)
        result = response.data
        print(result)

        # 提取文本
        extracted_text = ""
        for page in result.pages:
            for line in page.lines:
                print(line.text)
                extracted_text+= line.text + "\n"

        return extracted_text
    except Exception as e:
        return f"错误: {str(e)}"





webui_title = "OCI document understanding text extraction"
with gr.Blocks( ) as demo:
    model_status =   gr.State("llava-mistral")
    gr.Markdown(webui_title)
    with gr.Tab('upload an image'):
        with gr.Row():
            with gr.Column(scale=8):
                pic =  gr.Image(type="filepath")
                lang = gr.Dropdown(
                    choices=[
                        ("Chinese", "zh"),
                        # Label: "Option A (Friendly Name)", Value: "internal_code_a"
                        ("English", "en"),
                        ("Japanese", "ja"),
                        # Label: "Option B (Another Name)", Value: "internal_code_b"
                        ("Option C", "internal_code_c")  # Label: "Option C", Value: "internal_code_c"
                    ],
                    label="Select a language",  # The label for the dropdown
                    value="en"  # Default selected value
                )
                btn = gr.Button(value="OCR")
                res = gr.TextArea(show_label=False, placeholder="answer")

                btn.click(ocr_image,   inputs= [pic],  outputs=  [ res],api_name="llava")

demo.queue()
demo.launch(server_name='0.0.0.0',
         server_port=8898,share=False)


