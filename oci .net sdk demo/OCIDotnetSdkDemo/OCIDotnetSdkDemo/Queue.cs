using Oci.Common.Auth;
using Oci.Common;
using Oci.QueueService;
using System;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;
using System.Runtime.CompilerServices;

namespace Oci.Examples
{
    class ListQueuesExample
    {
        public static async Task mm()
        {
            // Create a request and dependent object(s).
            var listQueuesRequest = new Oci.QueueService.Requests.ListQueuesRequest
            {
                CompartmentId = "ocid1.compartment.oc1..aaaaaaaahr7aicqtodxmcfor6pbqn3hvsngpftozyxzqw36gj4kh3w3kkj4q",
                //LifecycleState = Oci.QueueService.Models.Queue.LifecycleStateEnum.Failed,
                //DisplayName = "EXAMPLE-displayName-Value",
                //Id = "ocid1.test.oc1..<unique_ID>EXAMPLE-id-Value",
                //Limit = 573,
                //Page = "EXAMPLE-page-Value",
                //SortOrder = Oci.QueueService.Models.SortOrder.Asc,
                //SortBy = Oci.QueueService.Requests.ListQueuesRequest.SortByEnum.TimeCreated,
                OpcRequestId = "A8DORQXDPX8ZB0ZSS0YZ<unique_ID>"
            };

            // Create a default authentication provider that uses the DEFAULT
            // profile in the configuration file.
            // Refer to <see href="https://docs.cloud.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm#SDK_and_CLI_Configuration_File>the public documentation</see> on how to prepare a configuration file. 
            var provider = new ConfigFileAuthenticationDetailsProvider("DEFAULT");
            try
            {
                // Create a service client and send the request.
                using (var client = new QueueAdminClient(provider, new ClientConfiguration()))
                {
                    var response = await client.ListQueues(listQueuesRequest);
                    // Retrieve value from the response.
                    var itemsValue = response.QueueCollection.Items;
                }
            }
            catch (Exception e)
            {
                Console.WriteLine($"ListQueues Failed with {e.Message}");
                throw e;
            }
        }

    }
   public class PutMessagesExample

    {
        public static async Task mm()
        {
            // Create a request and dependent object(s).
            var putMessagesDetails = new Oci.QueueService.Models.PutMessagesDetails
            {
                Messages = new List<Oci.QueueService.Models.PutMessagesDetailsEntry>
                {
                    new Oci.QueueService.Models.PutMessagesDetailsEntry
                    {
                        Content = "EXAMPLE-------content-Value"
                    }
                }
            };
            string QueueIdf = "ocid1.queue.oc1.ap-seoul-1.amaaaaaaak7gbriamql65bnf6bp6fvqjzyukbjeac7xtrdvkshtshaw6ft4q";

            var putMessagesRequest = new Oci.QueueService.Requests.PutMessagesRequest
            {
                QueueId = QueueIdf,
                PutMessagesDetails = putMessagesDetails,
                OpcRequestId = "0M20ZFHD84BUPN2UD4JD<udnique_ID>"
            };

            // Create a default authentication provider that uses the DEFAULT
            // profile in the configuration file.
            // Refer to <see href="https://docs.cloud.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm#SDK_and_CLI_Configuration_File>the public documentation</see> on how to prepare a configuration file. 
            var provider = new ConfigFileAuthenticationDetailsProvider("DEFAULT");
            try
            {
                // Create a service client and send the request.
                using (var client = new QueueClient(provider, new ClientConfiguration()))
                {
                    client.SetEndpoint("https://cell-1.queue.messaging.ap-singapore-1.oci.oraclecloud.com");

                    var response = await client.PutMessages(putMessagesRequest);
                    // Retrieve value from the response.
                    var messagesValue = response.PutMessages.Messages;
                }
            }
            catch (Exception e)
            {
                Console.WriteLine($"PutMessages Failed with {e.Message}");
                throw e;
            }
        }

    }

    public class GetMessage
    {

        public static  async Task mm()
        {
            string QueueId = "ocid1.queue.oc1.ap-seoul-1.amaaaaaaak7gbriamql65bnf6bp6fvqjzyukbjeac7xtrdvkshtshaw6ft4q";

            var getMessagesRequest = new Oci.QueueService.Requests.GetMessagesRequest
            {
                QueueId = QueueId,
                VisibilityInSeconds = 1381,
                TimeoutInSeconds = 7,
                Limit = 18,
                OpcRequestId = "PMWLZUX4HNL0BQSY6311<unique_ID>"
            };

            // Create a default authentication provider that uses the DEFAULT
            // profile in the configuration file.
            // Refer to <see href="https://docs.cloud.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm#SDK_and_CLI_Configuration_File>the public documentation</see> on how to prepare a configuration file. 
            var provider = new ConfigFileAuthenticationDetailsProvider("DEFAULT");
            try
            {
                // Create a service client and send the request.
                using (var client = new QueueClient(provider, new ClientConfiguration()))
                {
                    client.SetEndpoint("https://cell-1.queue.messaging.ap-singapore-1.oci.oraclecloud.com");

                    var response = await client.GetMessages(getMessagesRequest);
                    // Retrieve value from the response.
                    var messagesValue = response.GetMessages.Messages;
                    foreach (var i in messagesValue)
                    {
                        Console.WriteLine(i.Content);
                    }
                }
            }
            catch (Exception e)
            {
                Console.WriteLine($"GetMessages Failed with {e.Message}");
                throw e;
            }
        }
    }
}
