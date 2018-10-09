# Demo Service Fabric Best Practices
Demo Microservices Application Best Practices in Azure with Service Fabric

Executing servicefabric_bestpractices.py will result in a Service Fabric Cluster Creation; as will importing
ResourceManagerClient and executing functions individually.

# Status
10/8/2019

ARM deployment of Service Fabric Application Versions tarteged for Linux hosts doesn't work; requires using SF client
(sfctl or powershell) to deploy applications to Linux.

This modern microservices architected application, is composed of a Golang Docker containizered Service, and a non 
containerized Java Service; declared as a single ARM Service Fabric Application resource. The Go Service is implemented to
serve an HTML UI for writing mongodb collections to CosmosDB. The Java Service currently is [Computes sample](https://github.com/Azure-Samples/compute-java-manage-user-assigned-msi-enabled-virtual-machine/blob/master/src/main/java/com/microsoft/azure/management/compute/samples/ManageUserAssignedMSIEnabledVirtualMachine.java) for managing virtual machines, by:
- Create a Resource Group and User Assigned MSI with CONTRIBUTOR access to the resource group
- Create a Linux VM and associate it with User Assigned MSI
   - Install Java8, Maven3 and GIT on the VM using Azure Custom Script Extension
- Run Java application in the MSI enabled Linux VM which uses MSI credentials to manage Azure resource
- Retrieve the Virtual machine created from the MSI enabled Linux VM.

Discovering how to update compute sample to Java Service, to write to the same cosmos db as Go Service, using VM MSI instead of Go Service used user name and password for cosmos db.

Next step is to implement inbound and outbound NSG rules.
