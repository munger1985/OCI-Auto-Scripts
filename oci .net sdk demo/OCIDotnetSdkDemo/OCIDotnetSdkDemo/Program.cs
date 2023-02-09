using Oci.Common;
using Oci.Common.Auth;
using Oci.ObjectstorageService;
using Oci.ObjectstorageService.Requests;
using Oci.ObjectstorageService.Responses;
using Oci.QueueService;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using System;
using Oci.Sdk.DotNet.Example.Ons;

namespace Oci.Examples
{


    public class OciExamples
    {
        static async Task Main(string[] args) {
            // sdk test for object storage
            //await ObjectStorageExamples.MainOS();

            // sdk test for object storage
            //await StreamsExample.MainStreaming();

            // sdk test for queue
            //await PutMessagesExample.mm();
            //await GetMessage.mm();
            //await ListQueues.Example.mm();

            // sdk test for Open Search
            //Opensearch.mm();

            // sdk test for AJD
            //await  AJD.mmAsync();

            // sdk test for notification
            await PublishMessageExample.MainNotification();
        }
        private static NLog.Logger logger = NLog.LogManager.GetCurrentClassLogger();
    }
}