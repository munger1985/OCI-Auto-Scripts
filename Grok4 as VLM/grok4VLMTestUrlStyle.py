import oci
import base64

compartment_id = "ocid1.compartment.oc1..aaaaaaaau5q457a7teqkjce4oenoiz6bmc4g3s74a5543iqbm7xwplho44fq"
CONFIG_PROFILE = "DEFAULT"
config = oci.config.from_file('~/.oci/config', CONFIG_PROFILE)

# Service endpoint
endpoint = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"

generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(config=config,
                                                                                         service_endpoint=endpoint,
                                                                                         retry_strategy=oci.retry.NoneRetryStrategy(),
                                                                                         timeout=(10, 240))

ModelID = "xai.grok-4"

prompt = """
You are a vision-based text extractor. Given an image, output ONLY a single JSON string containing all most-likely VINs (Vehicle Identification Numbers) found in the image. Follow these rules:

1. Output exactly one JSON in the format:
   {"vins":[{"vin":"<VIN1>","confidence":0.95}, {"vin":"<VIN2>","confidence":0.72}]}

2. Only include candidates that are 17 characters after normalization, uppercase, and do NOT contain letters I, O, Q. If none found, output {"vins":[]}.

3. Confidence must be a float between 0.00 and 1.00 (two decimals). Compute confidence from OCR character confidence, character plausibility, checksum/position cues if available, and visual clarity. Sort candidates by descending confidence. Limit output to top 5.

4. You may apply conservative OCR-corrections (e.g., ambiguous '1' vs 'I', '0' vs 'O') but only output corrected VINs that meet the 17-char/no-I/O/Q rule and with reduced confidence reflecting the correction.


"""

prompt='describe this picture'

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_message(query, image_path):
    content1 = oci.generative_ai_inference.models.TextContent()
    content1.text = query
    content2 = oci.generative_ai_inference.models.ImageContent()
    image_url = oci.generative_ai_inference.models.ImageUrl()
    image_url.url =image_path
    content2.image_url = image_url
    message = oci.generative_ai_inference.models.UserMessage()
    message.content = [content1, content2]

    return message


def get_chat_request(query, image_path):
    chat_request = oci.generative_ai_inference.models.GenericChatRequest()
    # chat_request.preamble_override = "you always answer in a one stanza poem."
    chat_request.messages = [get_message(query, image_path)]
    chat_request.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
    # chat_request.num_generations = 1
    chat_request.is_stream = False
    chat_request.max_tokens = 600
    chat_request.temperature = 0.75
    chat_request.top_p = 1

    return chat_request


def get_chat_detail(llm_request):
    chat_detail = oci.generative_ai_inference.models.ChatDetails()
    chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id=ModelID)
    chat_detail.compartment_id = compartment_id
    chat_detail.chat_request = llm_request

    return chat_detail


### input your query and image file path below
llm_request = get_chat_request(prompt, r"https://raw.githubusercontent.com/open-mmlab/mmdeploy/main/demo/resources/det.jpg")
chat_detail = get_chat_detail(llm_request)
chat_response = generative_ai_inference_client.chat(chat_detail)
print(vars(chat_response))
print("text for the image: ", chat_response.data.chat_response.choices[0].message.content[0].text)
