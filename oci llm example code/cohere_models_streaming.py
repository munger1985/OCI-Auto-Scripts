
import oci

compartment_id = "ocid1.compartment.oc1..aaaaaaaau5q457a7teqkjce4oenoiz6bmc4g3s74a5543iqbm7xwplho44fq"
CONFIG_PROFILE = "DEFAULT"
config = oci.config.from_file('~/.oci/config', CONFIG_PROFILE)
model_id="cohere.command-a-03-2025"

region = 'us-chicago-1'
# Service endpoint
endpoint = f"https://inference.generativeai.{region}.oci.oraclecloud.com"

generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(config=config, service_endpoint=endpoint, retry_strategy=oci.retry.NoneRetryStrategy(), timeout=(10,240))
chat_detail = oci.generative_ai_inference.models.ChatDetails()

chat_request = oci.generative_ai_inference.models.CohereChatRequest()
chat_request.message = "hi hello, how are you"
chat_request.max_tokens = 600
chat_request.temperature = 1

chat_request.frequency_penalty = 0

chat_request.top_p = 0.75

chat_request.top_k = 0


chat_request.is_stream = True





chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id=model_id)
chat_detail.chat_request = chat_request
chat_detail.compartment_id = compartment_id

chat_response = generative_ai_inference_client.chat(chat_detail)

# Print result
print("**************************Chat Result**************************")
print(vars(chat_response))


import json

for event in chat_response.data.events():
    output = json.loads(event.data)
    if output.get('text') is not None:
        import time
        time.sleep(0.3)
        print(output.get('text'), end='', flush=True)

