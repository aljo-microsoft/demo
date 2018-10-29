package demo;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;

import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestMapping;

@RestController
public class JavaService {

    @RequestMapping("/")
    public String index() {
                // Connection String
        String connectionUrl = "jdbc:sqlserver://sfbpsqlserver.database.windows.net:1433;database=sfbpdatabase;user=aljo@sfbpsqlserver;password=Password#1234;encrypt=true;trustServerCertificate=false;hostNameInCertificate=*.database.windows.net;loginTimeout=30";
        String tableData = "SERVICETABLE\n";

        try (Connection con = DriverManager.getConnection(connectionUrl); Statement stmt = con.createStatement();) {
            // Create Table
            String sqlCreateTable = "CREATE TABLE SFBPTABLE " +
                                    "(name VARCHAR(255), " +
                                    "id INTEGER not NULL, " +
                                    "PRIMARY KEY (id))";
            stmt.executeUpdate(sqlCreateTable);
            System.out.println("Created sfbpdatabase database SFBPTABLE table.");
            // Insert Table Demo Data
            String sqlUser1Data = "INSERT INTO SFBPTABLE " +
                                   "VALUES('user1', 18006427676, 1)";
            stmt.executeUpdate(sqlUser1Data);
            String sqlUser2Data = "INSERT INTO SFBPTABLE " +
                                   "VALUES('user2', 18006427676, 2)";
            stmt.executeUpdate(sqlUser2Data);
            // Query Table
            String SQL = "SELECT * FROM SFBPTABLE";
            ResultSet rs = stmt.executeQuery(SQL);
            // Display Table Data
            while (rs.next()) {
                tableData += "| " + rs.getString("name") + " | " + rs.getString("id") + " | \n";
            }
        }
        // Handle Exceptions
        catch (Exception e) {
            e.printStackTrace();
        }
        return tableData;
    }

}
