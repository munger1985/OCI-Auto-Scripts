using OpenSearch.Client;
using System;
using System.Linq;
using System.Runtime.Intrinsics.X86;
using System.Threading.Tasks;

namespace ConsoleApp1
{
    class Student
    {
        public int Id { get; set; }
        public string FirstName { get; set; }
        public string LastName { get; set; }
        public int GradYear { get; set; }
        public double Gpa { get; set; }
    }
    class ParentDocument
    {
        public string JoinField { get; set; }
        public string Id { get; set; }
        public string Name { get; set; }
    }

    class ChildDocument

    {
        public string JoinField { get; set; }
        public string Id { get; set; }
        public string Name { get; set; }
        public string ParentId { get; set; }
    }

    public interface IOpenBookDocumentDemo
    {
        /// <summary>
        /// Id
        /// </summary>
        string Id { get; set; }


        /// <summary>
        /// Join
        /// </summary>
        JoinField Join { get; set; }
    }


    /// <summary>
    /// 小说信息
    /// </summary>
    [OpenSearchType(RelationName = "book-base")]
    public class OpenEsBookBaseDemo : IOpenBookDocumentDemo
    {
        public string Id { get; set; }

        /// <summary>
        /// 是否付费书籍
        /// </summary>
        public bool IsPay { get; set; }

        /// <summary>
        /// 标签
        /// </summary>
        public string[] Tags { get; set; }

        /// <summary>
        /// 别名列表
        /// </summary>
        public string[] Aliases { get; set; }

        /// <summary>
        /// 评分人数
        /// </summary>
        public int RatingCount { get; set; }

        /// <summary>
        /// 等待发布章节数
        /// </summary>
        public int WaitingReleaseCount { get; set; }


        #region 子项属性

        /// <summary>
        /// 策略编号
        /// </summary>
        public string StrategyId { get; set; }

        /// <summary>
        /// 定价策略编号
        /// </summary>
        public string PricingStrategyId { get; set; }

        /// <summary>
        /// 最新章节更新时间
        /// </summary>
        public DateTime? LastChapterTime { get; set; }

        /// <summary>
        /// 是否原创作品
        /// </summary>
        public bool? IsOriginal { get; set; }

        /// <summary>
        /// 仅支持充值购买
        /// </summary>
        public bool OnlyRechargePurchase { get; set; }

        #endregion

        /// <summary>
        /// Join
        /// </summary>
        public JoinField Join { get; set; }


        public string SeriesId { get; set; }
        public int? SeriesOrder { get; set; }
        /// <summary>
        /// 系列与书的关联时间
        /// </summary>
        public DateTime? SeriesBookJoinTime { get; set; }




    }


    /// <summary>
    /// 小说停更通知
    /// </summary>
    [OpenSearchType(RelationName = "stop-notice")]
    public class OpenEsBookStopNoticeDemo : IOpenBookDocumentDemo
    {

        public string Id { get; set; }
        /// <summary>
        /// Join
        /// </summary>
        ///
        public string nn { get; set; }
        public JoinField Join { get; set; }
    }

    internal class Program
    {

        public static async Task CreateBookDocumentAsync(OpenSearchClient _elasticClient, OpenEsBookBaseDemo book, params IOpenBookDocumentDemo[] children)
        {
            await CreateIndexAsync(_elasticClient);

            book.Join = JoinField.Root<OpenEsBookBaseDemo>();
            Func<BulkDescriptor, IBulkRequest> descriptor = s => s.Index<IOpenBookDocumentDemo>(i
                => i.Document(book)).Index("ii");
            if (children != null && children.Any(x => x != null))
            {
                children = children.Where(x => x != null).ToArray();
                foreach (var child in children)
                    child.Join = JoinField.Link(RelationName.Create(child.GetType()), book.Id);
                descriptor = s => s.Index<IOpenBookDocumentDemo>(i => i.Document(book)).IndexMany(children).Index("ii");
            }

            var response = await _elasticClient.BulkAsync(descriptor);
            if (!response.IsValid)

                Console.WriteLine($"create indexer failed. debug info: {response.DebugInformation}");
        }


        public static async Task CreateIndexAsync(OpenSearchClient _elasticClient)
        {
            var existsRep = await _elasticClient.Indices.ExistsAsync("ii");
            if (existsRep.ApiCall.HttpStatusCode == 200)
                return;




            var response = await _elasticClient.Indices.CreateAsync(
                "ii", c => c
                .Index<OpenEsBookBaseDemo>()
                .Map<IOpenBookDocumentDemo>(m => m
                        .RoutingField(r => r.Required())
                        .AutoMap<OpenEsBookBaseDemo>()
                        .AutoMap<OpenEsBookStopNoticeDemo>()
                        .Properties(props => props
                            .Join(j => j
                                .Name(p => p.Join)
                                .Relations(r => r
                                    .Join<OpenEsBookBaseDemo, OpenEsBookStopNoticeDemo>()
                                )
                            )
                            // TODO:指定属性为keyword类型
                            .Keyword(s => s.Name(f => f.Id))
                            .Keyword(s => new KeywordPropertyDescriptor<OpenEsBookBaseDemo>().Name(f => f.StrategyId))
                            .Keyword(s => new KeywordPropertyDescriptor<OpenEsBookBaseDemo>().Name(f => f.PricingStrategyId))
                            .Keyword(s => new KeywordPropertyDescriptor<OpenEsBookBaseDemo>().Name(f => f.Tags))
                        )
                    )
            );
            if (!response.IsValid)
            {
                Console.WriteLine($"create indexer failed. debug info: {response.DebugInformation}");
            }
        }

        static async Task Main(string[] args)
        {
            Console.WriteLine("Hello World!");
            var nodeAddress = new Uri("https://amaaaaaaak7gbriabeq5o6zmpml7szjax5imwav662iivbcajsyg7cek527q.opensearch.ap-singapore-1.oci.oraclecloud.com:9200");

            var connectionSettings = new ConnectionSettings(nodeAddress)
          .BasicAuthentication("ADMIN2", "gfg!sd");
            connectionSettings.DefaultMappingFor<OpenEsBookBaseDemo>(m => m
       .IndexName("ii") // 设置文档类型的默认索引名称
   );

            var client = new OpenSearchClient(connectionSettings);


            await CreateIndexAsync(client);
            var book = new OpenEsBookBaseDemo()
            {
                Id = "rff",
                RatingCount = 3,
                SeriesId = "33",
            };
            var child1 = new OpenEsBookStopNoticeDemo()
            {
                Id = "c3",
                nn = "nnd"
            };
            IOpenBookDocumentDemo[] iopenbooks = new IOpenBookDocumentDemo[] { child1 };

            await CreateBookDocumentAsync(client, book, iopenbooks);


           
            // 执行父子关联查询
            var response = client.Search<OpenEsBookBaseDemo>(s => s.Index("ii")
                .Query(q => q
                    .HasChild<OpenEsBookStopNoticeDemo>(
                                hc => hc
                        .Type("stop-notice")
                        .Query(cq => cq
                            .Match(m => m
                                .Field("nn")
                                .Query("nnd")
                            )
                        )
               )
                )
            );
            if (response.IsValid)
            {
                foreach (var hit in response.Hits)
                {
                    var parent = hit.Source;
                    Console.WriteLine($"Parent Document: Id={parent.Id}, Name={parent.IsPay}");

                    foreach (var innerHit in hit.InnerHits)
                    {
                        //Console.WriteLine(innerHit.ToString());
                        var child = innerHit.Value.Hits;
                        Console.WriteLine($"Child Document: Id={child.ToString()} ");
                    }
                }
            }

        }
    }
}
