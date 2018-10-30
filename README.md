# Demo Service Fabric Best Practices
Demo Microservices Application Best Practices in Azure with Service Fabric

This is a Microservices architected application, comprised of a Java and Golang Docker containerized services, declared as a Service Fabric Application ARM Resource.

The Go Service is implemented to serve a HTML UI for writing mongodb collections to CosmosDB.

The Java Service is implemented to create a MS SQL Database table, insert Data, Query Data, and Serve the Data.

# Status
Last Tested 10/29/2019

Test Execution Process using Azure Cloud Shell:

git clone https://github.com/aljo-microsoft/demo.git

cd demo/deploy

python

'Python 3.5.2 (default, Nov 23 2017, 16:37:01)'

'[GCC 5.4.0 20160609] on linux'

'Type "help", "copyright", "credits" or "license" for more information.'

'>>> from servicefabric_bestpractices import ResourceManagerClient'

'>>> rmc = ResourceManagerClient()'

'>>> rmc.declare_secret_parameter_values()'

'>>> rmc.go_service_build()'

'>>> rmc.microservices_cosmos_db_creation()'

'>>> rmc.java_service_build()'

'>>> rmc.java_azure_sql_resource_declaration()'

'>>> rmc.microservices_app_sfpkg_declaration()'

'>>> rmc.microservices_app_sfpkg_staging()'

'>>> rmc.microservices_app_resource_declaration()'

'>>> rmc.validate_declaration()'

'>>> rmc.deploy_resources()'

'>>> rmc.setup_cluster_client()'

NOTES:
Executing servicefabric_bestpractices.py will timeout in Azure Cloud Shell, as it takes approximately 30 minutes to complete end to end, and understand there is a 20 mins timeout.

I then plan to enhance the JavaService's security to use VMSS MSI instead of DB user name and password.

Lastly I plan to implement inbound and outbound NSG rules to further secure the environment.
