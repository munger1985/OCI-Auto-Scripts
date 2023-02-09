// This is an automatically generated code sample. 
// To make this code sample work in your Oracle Cloud tenancy, 
// please replace the values for any parameters whose current values do not fit
// your use case (such as resource IDs, strings containing ‘EXAMPLE’ or ‘unique_id’, and 
// boolean, number, and enum parameters with values not fitting your use case).

using System;
using System.Threading.Tasks;
using Oci.OnsService;
using Oci.Common;
using Oci.Common.Auth;

namespace Oci.Sdk.DotNet.Example.Ons
{
    public class PublishMessageExample
    {
        public static async Task MainNotification()
        {
            // Create a request and dependent object(s).
            var messageDetails = new Oci.OnsService.Models.MessageDetails
            {
                Title = "EXAMPLE-title-Value2",
                Body = "EXAMPLE-body-Value2"
            };
            var publishMessageRequest = new Oci.OnsService.Requests.PublishMessageRequest
            {
                TopicId = "ocid1.onstopic.oc1.ap-seoul-1.aaaaaaaa5vy7i6hu2mwyia3xh5kpjjn44sua64r7urg3pkbhnuu2z6g3isfa",
                MessageDetails = messageDetails,
                OpcRequestId = "UPHAGJD36WJMQZCXNCKE<unique_ID>",
                MessageType = Oci.OnsService.Requests.PublishMessageRequest.MessageTypeEnum.RawText
            };

            // Create a default authentication provider that uses the DEFAULT
            // profile in the configuration file.
            // Refer to <see href="https://docs.cloud.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm#SDK_and_CLI_Configuration_File>the public documentation</see> on how to prepare a configuration file. 
            var provider = new ConfigFileAuthenticationDetailsProvider("DEFAULT");
            try
            {
                // Create a service client and send the request.
                using (var client = new NotificationDataPlaneClient(provider, new ClientConfiguration()))
                {
                    var response = await client.PublishMessage(publishMessageRequest);
                    // Retrieve value from the response.
                    var messageIdValue = response.PublishResult.MessageId;
                }
            }
            catch (Exception e)
            {
                Console.WriteLine($"PublishMessage Failed with {e.Message}");
                throw e;
            }
        }

    }
}
