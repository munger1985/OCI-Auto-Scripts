package com.util;

import oracle.ucp.jdbc.PoolDataSource;
import oracle.ucp.jdbc.PoolDataSourceFactory;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

public class ADWJDBCHelper {
    public static void main(String args[]) throws Exception {
        // Make sure to have Oracle JDBC driver 18c or above
        // to pass TNS_ADMIN as part of a connection URL.
        // TNS_ADMIN - Should be the path where the client credentials zip (wallet_dbname.zip) file is downloaded.
        // dbname_medium - It is the TNS alias present in tnsnames.ora.
         String DB_URL="jdbc:oracle:thin:@justinadw_high?TNS_ADMIN=/root/bdws/Wallet_JustinADW";
        // Update the Database Username and Password to point to your Autonomous Database
         String DB_USER = "mluser1";
        String DB_PASSWORD = "Welcome1!123" ;
        if(args!=null && args.length>0){
            DB_USER=args[0];
            DB_PASSWORD=args[1];
            if(args.length>=3){
                DB_URL=args[2];
            }
        }
        System.out.println("DB_USER:"+DB_USER +"  DB_PASSWORD:"+DB_PASSWORD);
        System.out.println("DB_URL:"+DB_URL);
        final String CONN_FACTORY_CLASS_NAME="oracle.jdbc.pool.OracleDataSource";
        // Get the PoolDataSource for UCP
        PoolDataSource pds = PoolDataSourceFactory.getPoolDataSource();
        // Set the connection factory first before all other properties
        pds.setConnectionFactoryClassName(CONN_FACTORY_CLASS_NAME);
        pds.setURL(DB_URL);
        pds.setUser(DB_USER);
        pds.setPassword(DB_PASSWORD);
        pds.setConnectionPoolName("JDBC_UCP_POOL");
        // Default is 0. Set the initial number of connections to be created
        // when UCP is started.
        pds.setInitialPoolSize(5);
        // Default is 0. Set the minimum number of connections
        // that is maintained by UCP at runtime.
        pds.setMinPoolSize(5);
        // Default is Integer.MAX_VALUE (2147483647). Set the maximum number of
        // connections allowed on the connection pool.
        pds.setMaxPoolSize(20);
        // Get the database connection from UCP.
        try (Connection conn = pds.getConnection()) {
            System.out.println("Available connections after checkout: "
                    + pds.getAvailableConnectionsCount());
            System.out.println("Borrowed connections after checkout: "
                    + pds.getBorrowedConnectionsCount());
            // Perform a database operation
            doSQLWork(conn);
        } catch (SQLException e) {
            System.out.println("ADBQuickStart - "
                    + "doSQLWork()- SQLException occurred : " + e.getMessage());
        }
        System.out.println("Available connections after checkin: "
                + pds.getAvailableConnectionsCount());
        System.out.println("Borrowed connections after checkin: "
                + pds.getBorrowedConnectionsCount());
    }
    /*
     * Selects 20 rows from the SH (Sales History) Schema that is the accessible to all
     * the database users of autonomous database.
     */
    private static void doSQLWork(Connection conn) throws SQLException {
        String queryStatement = "SELECT topicName, iOTMsgKey, productId, productName,create_time"
                + " FROM iotcar_message WHERE ROWNUM < 20 order by create_time";

        System.out.println("\n Query is " + queryStatement);

        conn.setAutoCommit(true);
        // Prepare a statement to execute the SQL Queries.
        try (Statement statement = conn.createStatement();
             // Select 20 rows from the CUSTOMERS table from SH schema.
             ResultSet resultSet = statement.executeQuery(queryStatement)) {
            System.out.println(String.join(" ", "topicName, iOTMsgKey, productId, productName,create_time"));
            System.out.println("-----------------------------------------------------------");
            while (resultSet.next()) {
                System.out.println(resultSet.getString(1) + " " + resultSet.getString(2) + " " +
                        resultSet.getString(3)+ " " + resultSet.getString(4) + " " +
                        resultSet.getInt(5));
            }
            System.out.println("\nCongratulations! You have successfully used Oracle Autonomous Database\n");
        }
    } // End of doSQLWork

}
