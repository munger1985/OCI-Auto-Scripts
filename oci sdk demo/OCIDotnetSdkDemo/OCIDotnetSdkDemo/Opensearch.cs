
using System;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;
using Oci.Common.Auth;
using Oci.Common.Waiters;
using Oci.QueueService.Models;
using Oci.QueueService.Requests;
using Oci.QueueService.Responses;
using Oci.StreamingService;
using Oci.StreamingService.Models;
using Oci.StreamingService.Requests;
using Oci.StreamingService.Responses;
using OpenSearch.Client;
using GetMessagesRequest = Oci.StreamingService.Requests.GetMessagesRequest;
using GetMessagesResponse = Oci.StreamingService.Responses.GetMessagesResponse;
using PutMessagesDetails = Oci.StreamingService.Models.PutMessagesDetails;
using PutMessagesDetailsEntry = Oci.StreamingService.Models.PutMessagesDetailsEntry;
using PutMessagesResponse = Oci.StreamingService.Responses.PutMessagesResponse;
using Stream = Oci.StreamingService.Models.Stream;

namespace Oci.Examples
{
    /**
    * This class provides an example of basic streaming usage.
    * - List streams
    * - Get a stream
    * - Create a stream
    * - Delete a stream
    * - Publish to a stream
    * - Consume from a stream, using a partition cursor
    * - Consume from a stream, using a group cursor
    */
      class Student
    {
        public int Id { get; set; }
        public string FirstName { get; set; }
        public string LastName { get; set; }
        public int GradYear { get; set; }
        public double Gpa { get; set; }
    }
   public class Opensearch
    {

       static  public void mm()
        {
            var nodeAddress = new Uri("https://amaaaaaaak7gbria6za2fyaokym7ld25xi2h22qro6tahkm45dfjqjhryzyq.opensearch.ap-singapore-1.oci.oraclecloud.com:9200");
            var client = new OpenSearchClient(nodeAddress);
            var student = new Student { Id = 100, FirstName = "Paulo", LastName = "Santos", Gpa = 3.93, GradYear = 2021 };
            var response = client.Index(student, i => i.Index("students"));
            var searchResponse = client.Search<Student>(s => s
                                .Index("students")
                                .Query(q => q
                                    .Match(m => m
                                        .Field(fld => fld.LastName)
                                        .Query("Santos"))));

            if (searchResponse.IsValid)
            {
                foreach (var s in searchResponse.Documents)
                {
                    Console.WriteLine($"{s.Id} {s.LastName} {s.FirstName} {s.Gpa} {s.GradYear}");
                }
            }


        }
    }

}