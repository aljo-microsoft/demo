package demo;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;

public class Service {
    public static void main(String[] args) {

        // Connection String
        String connectionUrl = "jdbc:sqlserver://sfbpsqlserver.database.windows.net:1433;databaseName=sfbpdatabase;user=aljo;password=Password#1234";

        try (Connection con = DriverManager.getConnection(connectionUrl); Statement stmt = con.createStatement();) {
            // Create Table
            String sqlCreateTable = "CREATE TABLE SFBPTABLE " +
                                    "(name VARCHAR(255), " +
                                    "phone INTEGER, " +
                                    "cid INTEGER not NULL, " +
                                    "PRIMARY KEY (cid))";
            stmt.executeUpdate(sqlCreateTable);
            System.out.println("Created sfbpdatabase database SFBPTABLE table.");
            // Insert Table Demo Data
            String sqlUser1Data = "INSERT INTO SERVICETABLE " +
                                   "VALUES('user1', 18006427676, 1)";
            stmt.executeUpdate(sqlUser1Data);
            String sqlUser2Data = "INSERT INTO SERVICETABLE " +
                                   "VALUES('user2', 18006427676, 2)";
            stmt.executeUpdate(sqlUser2Data);
            String sqlUser3Data = "INSERT INTO SERVICETABLE " +
                                   "VALUES('user3', 18006427676, 3)";
            stmt.executeUpdate(sqlUser3Data);
            // Query Table
            String SQL = "SELECT * FROM SERVICETABLE";
            ResultSet rs = stmt.executeQuery(SQL);
            // Print Table Data
            while (rs.next()) {
                System.out.println(rs.getString("name") + " " + rs.getString("phone"));
            }
        }
        // Handle Exceptions
        catch (Exception e) {
            e.printStackTrace();
        }
    }
}
