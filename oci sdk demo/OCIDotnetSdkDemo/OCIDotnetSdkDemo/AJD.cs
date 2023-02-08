using MongoDB.Bson.Serialization.Attributes;
using MongoDB.Bson;
using System;
using System.Collections.Generic;
using System.Text;
using MongoDB.Driver;
using System.Linq;
using System.Threading.Tasks;

namespace Oci.Examples
{
    
    public class AJD
    {
    public static async Task mmAsync()
        {
            var client = new MongoClient("mongodb://admin:密码@G54369A47908C3A-SZNJ3QU6KOC8PQVD.adb.ap-singapore-1.oraclecloudapps.com:27017/admin?authMechanism=PLAIN&authSource=$external&ssl=true&retryWrites=false&loadBalanced=true");
            var database = client.GetDatabase("admin");
            var options = new CreateCollectionOptions { Capped = true, MaxSize = 1024 * 1024 };
            try
            {
                database.CreateCollection("cappedBar", options);
            }
            catch (MongoDB.Driver.MongoCommandException e) { }
            var collection = database.GetCollection<BsonDocument>("cappedBar");

            var documents = Enumerable.Range(0, 100).Select(i => new BsonDocument("counter", i));
            collection.InsertMany(documents);

            await collection.Find(new BsonDocument()).ForEachAsync(d => Console.WriteLine(d));



        }
    }
// Replace the uri string with your MongoDB deployment's connection string.

}
