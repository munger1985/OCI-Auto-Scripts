using System;
using System.Configuration;
using Oracle.ManagedDataAccess.Client;
using Oracle.ManagedDataAccess.Types;
using System.Threading.Tasks;
using System.Data.Odbc;
using System.Transactions;
//// install odp.net nuget package
//     <PackageReference Include="Oracle.ManagedDataAccess.Core" Version="3.21.100" />
namespace ODP.NET_Autonomous
{
    class Program
    {
        static void Main()
        {


         

            //Enter your ADB's user id, password, and net service name
            string conString = "User Id=ADMIN;Password=qweqwe!23123;Data Source=pl7ptfa75pe9uwde_high;Connection Timeout=30;";

            //Enter directory where you unzipped your cloud credentials
            OracleConfiguration.TnsAdmin = @"C:\Users\opc\oci\Wallet_PL7PTFA75PE9UWDE";
            OracleConfiguration.WalletLocation = OracleConfiguration.TnsAdmin;

            using (TransactionScope scope = new TransactionScope())
            {
                Parallel.For(0, 33, i =>
                {
                    using (OracleConnection con = new OracleConnection(conString))
                    {
                        using (OracleCommand cmd = con.CreateCommand())
                        {
                            try
                            {
                                con.Open();
                                // Console.WriteLine("Successfully connected to Oracle Autonomous Database");
                                // Console.WriteLine();

                                // cmd.CommandText = "select CUST_FIRST_NAME, CUST_LAST_NAME, CUST_CITY, CUST_CREDIT_LIMIT " +
                                //     "from SH.CUSTOMERS order by CUST_ID fetch first 20 rows only";
                                // OracleDataReader reader = cmd.ExecuteReader();
                                // while (reader.Read())
                                // Console.WriteLine(reader.GetString(0) + " " + reader.GetString(1) + " in " +

                                // reader.GetString(2) + " has " + reader.GetInt16(3) + " in credit.");

 


                                Guid newGuid = Guid.NewGuid();
                                newGuid = Guid.NewGuid();
                                //generate time based uuid and insert it as dd table primary key

                                string guid = Guid.NewGuid().ToString().Substring(0, 31);

                                cmd.CommandText = "INSERT INTO dd (id, name) VALUES (:id, :name)";
                                cmd.Parameters.Add(":id", guid);
                                cmd.Parameters.Add(":name", guid);
                                int numRowsInserted = cmd.ExecuteNonQuery();
                                Console.WriteLine("{0} rows inserted.", numRowsInserted);
                                Console.WriteLine("Hello from thread {0}", newGuid);


                            }
                            catch (Exception ex)
                            {
                                Console.WriteLine(ex.Message);
                            }
                        }
                    } // open connection
                });  //


                scope.Complete();
            }
               
        }
    }
}