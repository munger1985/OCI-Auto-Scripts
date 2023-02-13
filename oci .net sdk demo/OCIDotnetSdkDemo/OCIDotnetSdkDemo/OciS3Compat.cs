using System;
using System.Collections.Generic;
using System.Text;

namespace ListBucketsExample
{
    using System;
    using System.Collections.Generic;
    using System.Threading.Tasks;
    using Amazon;
    using Amazon.S3;
    using Amazon.S3.Model;
    using Oci.ObjectstorageService.Responses;

    class OciS3Compat
    {
        private static IAmazonS3 _s3Client;

     public   static async Task mm()
        {
            // The client uses the AWS Region of the default user.
            // If the Region where the buckets were created is different,
            // pass the Region to the client constructor. For example:
            // _s3Client = new AmazonS3Client(RegionEndpoint.USEast1);
            const string accessKeyId = "aab850123236424ac7d7123ea8958c1ee8253a";
            const string accessKeySecret = "ugZQuW02323iABULNvwme2Xmgj9W+60yq4IneE=";
            const string endpoint = "https://sehubjapacprod.compat.objectstorage.ap-singapore-1.oraclecloud.com";
            var s3ClientConfig = new AmazonS3Config
            {
                ServiceURL = endpoint,
                SignatureVersion = "3",
                UseHttp = false,
            };
            PutObjectRequest request = new PutObjectRequest
            {
                BucketName = "velero",
                Key = "Item1",
                ContentBody = "This is sample content...",
                UseChunkEncoding = false
            };
            IAmazonS3 s3Client    = new AmazonS3Client(accessKeyId, accessKeySecret, s3ClientConfig);
            var response = await GetBuckets(s3Client);
            DisplayBucketList(response.Buckets);
            // Put object
            //Amazon.S3.Model.PutObjectResponse response = s3Client.PutObjectAsync(request);
            //s3Client = new AmazonS3Client(accessKeyId, accessKeySecret, s3ClientConfig);

            //var response = await GetBuckets(s3Client);
            //DisplayBucketList(response.Buckets);
        }

        /// <summary>
        /// Get a list of the buckets owned by the default user.
        /// </summary>
        /// <param name="client">An initialized Amazon S3 client object.</param>
        /// <returns>The response from the ListingBuckets call that contains a
        /// list of the buckets owned by the default user.</returns>
        public static async Task<Amazon.S3.Model.ListBucketsResponse> GetBuckets(IAmazonS3 client)
        {
            return await client.ListBucketsAsync();
        }

        /// <summary>
        /// This method lists the name and creation date for the buckets in
        /// the passed List of S3 buckets.
        /// </summary>
        /// <param name="bucketList">A List of S3 bucket objects.</param>
        public static void DisplayBucketList(List<S3Bucket> bucketList)
        {
            bucketList
                .ForEach(b => Console.WriteLine($"Bucket name: {b.BucketName}, created on: {b.CreationDate}"));
        }
    }
}
