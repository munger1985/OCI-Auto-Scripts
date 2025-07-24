 
import oci
import base64
compartment_id = "ocid1.compartment.oc1..aaaaaaaau5q457a7teqkjce4oenoiz6bmc4g3s74a5543iqbm7xwplho44fq"
CONFIG_PROFILE = "DEFAULT"
config = oci.config.from_file('~/.oci/config', CONFIG_PROFILE)

# Service endpoint
endpoint = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"

generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(config=config, service_endpoint=endpoint, retry_strategy=oci.retry.NoneRetryStrategy(), timeout=(10,240))
chat_detail = oci.generative_ai_inference.models.ChatDetails()

content = oci.generative_ai_inference.models.TextContent()
content.text = "introduce yourself"
message = oci.generative_ai_inference.models.Message()
message.role = "USER"
message.content = [content]
ModelID = "xai.grok-4"
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def get_message(query,image_path):
        content1 = oci.generative_ai_inference.models.TextContent()
        content1.text = query
        content2 = oci.generative_ai_inference.models.ImageContent()
        image_url = oci.generative_ai_inference.models.ImageUrl()
        image_url.url = f"data:image/jpeg;base64,{encode_image(image_path)}"
        content2.image_url = image_url
        message = oci.generative_ai_inference.models.UserMessage()
        message.content = [content1,content2] 

        return message


def get_chat_request(query,image_path):
        chat_request = oci.generative_ai_inference.models.GenericChatRequest()
        #chat_request.preamble_override = "you always answer in a one stanza poem."
        #chat_request.message = get_message()
        chat_request.messages = [get_message(query,image_path)]
        chat_request.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
        chat_request.num_generations = 1
        chat_request.is_stream = False 
        chat_request.max_tokens = 500
        chat_request.temperature = 0.75
        chat_request.top_p = 0.7

        return chat_request

def get_chat_detail (llm_request):
        chat_detail = oci.generative_ai_inference.models.ChatDetails()
        chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id=ModelID)
        chat_detail.compartment_id = compartment_id
        chat_detail.chat_request = llm_request

        return chat_detail

### input your query and image file path below
llm_request=get_chat_request("tell me about the picture",r"bbg.jpg")
chat_detail= get_chat_detail(llm_request)
chat_response = generative_ai_inference_client.chat(chat_detail)
print(vars(chat_response))
print("text for the image: ", chat_response.data.chat_response.choices[0].message.content[0].text)
