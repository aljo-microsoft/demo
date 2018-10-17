# Demo Service Fabric Best Practices
Demo Microservices Application Best Practices in Azure with Service Fabric

Executing servicefabric_bestpractices.py will result in a Service Fabric Cluster Creation; as will importing
ResourceManagerClient and executing functions individually.

# Status
Last Tested 10/17/2019

Open Azure Cloud Shell

Enter the following commands:

git clone https://github.com/aljo-microsoft/demo.git

cd demo/deploy

python3 servicefabric_bestpractices.py


NOTES:
This takes approximately 30 minutes to provisiong end to end.

This is a modern microservices architected application, which is composed of a Golang docker containizered Service, declared as an ARM Service Fabric Application resource.

The Go Service is implemented to serve a HTML UI for writing mongodb collections to CosmosDB.

I am actively developing this solution, with intentsions of adding a non containerized Java service; as a very common classic enterprise application is a JVM that isn't containerized.

For the Java service I'm currently evaluating using:
The Java [Computes sample](https://github.com/Azure-Samples/compute-java-manage-user-assigned-msi-enabled-virtual-machine/blob/master/src/main/java/com/microsoft/azure/management/compute/samples/ManageUserAssignedMSIEnabledVirtualMachine.java) for managing virtual machines using a user Assigned MSI.

This will allow a single microservices solution, comprised of modern Golang Dockerized service, and Classic Java service; to be deployed as a single ARM SF Application Resource.

I then plan to enhance the GoApp's security to use VMSS MSI instead of DB user name and password.

Lastly I plan to implement inbound and outbound NSG rules to further secure the environment.
