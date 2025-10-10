import gradio as gr

import  json

from langchain_community.chat_models import ChatOCIGenAI
from langchain_core.prompts import PromptTemplate





bucket= 'speech'

import oci
from oci.ai_speech import AIServiceSpeechClientCompositeOperations

# Create a default config using DEFAULT profile in default location
# Refer to
# https://docs.cloud.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm#SDK_and_CLI_Configuration_File
# for more info
compartment_id = "ocid1.compartment.oc1..aaaaaaaau5q457a7teqkjce4oenoiz6bmc4g3s74a5543iqbm7xwplho44fq"
namespace = 'sehubjapacprod'
bucket = "speech"
audioName= "Bluebird.wav"
region = 'ap-singapore-1'
# Initialize service client with default config file


config = oci.config.from_file()
config.update({'region':region})
# Initialize service client with default config file
# ai_language_client = oci.ai_language.AIServiceLanguageClient(config={}, signer=signer)
ai_language_client = oci.ai_language.AIServiceLanguageClient(config = config)
ai_speech_client = oci.ai_speech.AIServiceSpeechClient(config=config)
object_storage_client = oci.object_storage.ObjectStorageClient(config)

endpoint = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"

generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(config=config,
                                                                                         service_endpoint=endpoint,
                                                                                         retry_strategy=oci.retry.NoneRetryStrategy(),
                                                                                         timeout=(10, 240))


auth_type = 'API_KEY'

chat = ChatOCIGenAI(
    model_id="cohere.command-latest",
    service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
    compartment_id=compartment_id,
    auth_type=auth_type,
    model_kwargs={"temperature": 0.7, "max_tokens": 4000},
)

def ociSpeech(bucket, objectName ,lang):
    '''

    Args:
        bucket:  name of bucket
        objectName:  name in bucket

    Returns:

    '''

    aiServiceSpeechClientCompositeOperations=AIServiceSpeechClientCompositeOperations(client=ai_speech_client)
    waiter_result =  aiServiceSpeechClientCompositeOperations.create_transcription_job_and_wait_for_state(
        create_transcription_job_details=oci.ai_speech.models.CreateTranscriptionJobDetails(
            compartment_id=compartment_id,
            input_location=oci.ai_speech.models.ObjectListInlineInputLocation(
                location_type="OBJECT_LIST_INLINE_INPUT_LOCATION",
                object_locations=[oci.ai_speech.models.ObjectLocation(
                    namespace_name=namespace,
                    bucket_name=bucket,
                    object_names=[objectName])]),
            output_location=oci.ai_speech.models.OutputLocation(
                namespace_name=namespace,
                bucket_name=bucket,
                prefix="out"),
            display_name="speechJob-displayName-Value",
            description="EXAMPLE-description-Value",
            additional_transcription_formats=[],
            model_details=oci.ai_speech.models.TranscriptionModelDetails(
                model_type="WHISPER_MEDIUM",
                domain="GENERIC",
                language_code=lang,
                # zh en
                transcription_settings=oci.ai_speech.models.TranscriptionSettings(
                    diarization=oci.ai_speech.models.Diarization(
                        is_diarization_enabled=False,
                        # number_of_speakers=2
                    ))),
            normalization=oci.ai_speech.models.TranscriptionNormalization(
                is_punctuation_enabled=True,
                # filters=[
                #     oci.ai_speech.models.ProfanityTranscriptionFilter(
                #         type="PROFANITY",
                #         mode="TAG")]
            ),
        ),wait_for_states=['SUCCEEDED','FAILED']
    )
    if waiter_result.data.lifecycle_state == "SUCCEEDED":
        outputPrefix= waiter_result.data.output_location.prefix
        objectName=namespace+"_"+bucket+'_'+ objectName+'.json'
        objectName = outputPrefix+ objectName


        # 设置桶名和对象名

        # 获取对象
        response = object_storage_client.get_object(namespace, bucket, objectName)

        # 读取对象内容
        file_content = response.data.text
        jsonData = json.loads(file_content)
        textData = jsonData['transcriptions'][0]['transcription']
        # print(textData)
        return textData
    else:
        return "FAILED ASR"



def oci_genai_sum(text_to_summarize):
    # Service endpoint
    SummaryP='''
    Summarize blow dialogue. Your summary should be concise, capturing the main ideas and key points without including unnecessary details. Aim to retain the original meaning and context of the text.
    {question}
    '''
    promptSummary = PromptTemplate(input_variables=["question"], template=SummaryP)

    llmchain =promptSummary |chat
    resp = llmchain.invoke({'question': text_to_summarize})
    return resp.content


# Send the request to service, some parameters are not required, see API
# doc for more info

def getSentiment(text):
    SummaryP = '''
 Using the same language of the dialogue, analyze the sentiment of the blow dialogue. Identify the emotions and attitudes expressed by each speaker, and indicate whether the overall sentiment is positive, negative, or neutral. Provide a brief explanation for your analysis, 

The dialogue to be analyzed is :
       {question}
       '''
    promptSentiment = PromptTemplate(input_variables=["question"], template=SummaryP)

    llmchain = promptSentiment|chat
    resp = llmchain.invoke({'question': text})
    return resp.content




# 接口创建函数
# fn设置处理函数，inputs设置输入接口组件，outputs设置输出接口组件
# fn,inputs,outputs都是必填函数
import os

def get_filename_from_path(path):
    return os.path.basename(path)

def upload_file_to_object_storage(file, bucket_name, object_name):
    with open(file,'rb') as f:
        obj = object_storage_client.put_object(namespace, bucket_name, object_name, f)
    print(obj.headers)


from stopwatch import Stopwatch

stopwatch = Stopwatch()
def asr(file,lang):
    print(file)
    # filename=file.name
    filename =get_filename_from_path(file)
    stopwatch.start()

    upload_file_to_object_storage(file,bucket, filename)
    stopwatch.stop()
    print('upload oss',stopwatch.duration)
    stopwatch.start()
    if lang=='中文':
        lang='zh'
    elif lang=='english':
        lang='en'
    text = ociSpeech(bucket,filename,lang)
    stopwatch.stop()
    print('speech ',stopwatch.duration)

    return text


with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column(scale=5):
            file = gr.File(label="Audio file / 对话音频", height=33)
        with gr.Column(scale=2):
            lang = gr.Radio(choices=["english", "中文"], label="language ASR " )
            # upload_button = gr.UploadButton("Click to Upload an audio clip", file_types=["audio"],
            #                                 file_count="single"  )

        with gr.Column(scale=5):
            audio = gr.Audio(label='recording / 录音', scale=5, sources=["microphone"], show_download_button=True,
                             type='filepath')
    with gr.Row():
        with gr.Column(scale=5):
            transcribedText = gr.Textbox(label="Transcribed Text / 识别的文字")
            summarize = gr.Button("Summarize / 对话总结")
            summaryText = gr.Textbox(label="Summary / 总结摘要")

            sentiment = gr.Button("Sentiment Analysis / 情绪分析")
            file.upload(asr, [file,lang], transcribedText, show_progress=True)
            audio.change(asr, [audio,lang], transcribedText)

            # max = gr.Number(label="summary token limits")

            # label = gr.Label(num_top_classes=4, label="Sentiment Analysis")
            sentiText = gr.Textbox(label="Sentiment / 情绪")

            transcribedText.change(oci_genai_sum, [transcribedText], summaryText)
            summaryText.change(getSentiment, summaryText, sentiText)
            summarize.click(oci_genai_sum, show_progress=True,
                            inputs=[transcribedText], outputs=summaryText)
            sentiment.click(getSentiment, show_progress=True,
                            inputs=[summaryText], outputs=[sentiText])

demo.launch()

# demo = gr.Interface(fn=sum, inputs="text", outputs="text")
# demo.launch(ssl_verify=False, server_name="0.0.0.0", server_port=8899, ssl_keyfile="privkey.pem",
#             ssl_certfile="fullchain.pem")
