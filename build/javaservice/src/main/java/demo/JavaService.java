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
            String sqlCreateTable = "IF NOT EXSITS (SELECT name FROM sys.tables WHERE name='SFBPTABLE' AND type='U')" +
                                    "  CREATE TABLE SFBPTABLE (" +
                                    "    name VARCHAR(255), " +
                                    "    id INTEGER not NULL, " +
                                    "    PRIMARY KEY (id)" +
                                    "  )" +
                                    "GO";
            stmt.executeUpdate(sqlCreateTable);
            System.out.println("sfbpdatabase database SFBPTABLE table exists.");
            // Insert Table Demo Data
            String sqlUser1Data = "IF (NOT EXISTS(SELECT * FROM SFBPTABLE WHERE name = 'user1'))" +
                                  "BEGIN" +
                                  "   INSERT INTO SFBPTABLE(name, id)" +
                                  "   VALUES('user1', 1)" +
                                  "END";
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
