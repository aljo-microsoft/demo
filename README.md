# Demo Service Fabric Best Practices
Demo Microservices Application Best Practices in Azure with Service Fabric

Executing servicefabric_bestpractices.py will result in a Service Fabric Cluster Creation; as will importing
ResourceManagerClient and executing functions individually.

# Status
10/10/2019

This is a modern microservices architected application, which is composed of a Golang docker containizered Service, and a non containerized Java (see below for more) service; declared as a single ARM Service Fabric Application resource.

The Go Service is implemented to serve a HTML UI for writing mongodb collections to CosmosDB.

For the Java service I'm currently evaluating using:
The Java [Computes sample](https://github.com/Azure-Samples/compute-java-manage-user-assigned-msi-enabled-virtual-machine/blob/master/src/main/java/com/microsoft/azure/management/compute/samples/ManageUserAssignedMSIEnabledVirtualMachine.java) for managing virtual machines using a user Assigned MSI;

Requires I download Azure SDK before I can compile its dependencies

and https://docs.microsoft.com/en-us/azure/sql-database/sql-database-connect-query-java

The intention is to deploy a classic enterprise application that is using Azure SQL DB for its data; and enhance it's security to use VMSS MSI instead of DB user name and password.

Lastly will plan to implement inbound and outbound NSG rules to further secure the environment
