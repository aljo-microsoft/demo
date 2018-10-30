# Demo Service Fabric Best Practices
Demo Microservices Application Best Practices in Azure with Service Fabric

This is a Microservices architected application, comprised of a Java and Golang Docker containerized services, declared as a Service Fabric Application ARM Resource.

The Go Service is implemented to serve a HTML UI for writing mongodb collections to CosmosDB.

The Java Service is implemented to create a MS SQL Database table, insert Data, Query Data, and Serve the Data.

# Status
Last Tested 10/30/2019

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

Currently testing MSI use below, which I planned to leverage for replacing Package Secret values, by using tokens to fetch secrets.
## Process to Test MSI
### Create RG
az group create --name aljomsitest --location westus
### Create VM with SysAssigned MSI
ssh-keygen -t rsa -b 2048

az vm create --resource-group aljomsitest --name aljovm --image UbuntuLTS --assign-identity --admin-username aljo --ssh-key-value @~/.ssh/id_rsa.pub
### Create Cosmos DB Account
az cosmosdb create --name aljodb --resource-group aljomsitest --kind MongoDB
### Get PrinipalID
az resource show --id /subscriptions/eec8e14e-b47d-40d9-8bd9-23ff5c381b40/resourceGroups/aljomsitest/providers/Microsoft.Compute/virtualMachines/aljovm--api-version 2017-12-01
### Grant VM MSI access to CosmosDB Keys
az role assignment create --assignee <PrincipalID> --role Contributor --scope "/subscriptions/eec8e14e-b47d-40d9-8bd9-23ff5c381b40/resourceGroups/aljomsitest/providers/Microsoft.DocumentDB/databaseAccounts/aljomsitestdb"

### SSH into Machine
ssh aljo@aljovm.westus.cloudapp.azure.com
### GET Access Token for ARM from Machine
curl 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https%3A%2F%2Fmanagement.azure.com%2F' -H Metadata:true
### Get Access Keys for Cosmos DB using MSI Access Token
curl 'https://management.azure.com/subscriptions/<SUBSCRIPTION ID>/resourceGroups/<RESOURCE GROUP>/providers/Microsoft.DocumentDB/databaseAccounts/<COSMOS DB ACCOUNT NAME>/<KEY OPERATION TYPE>?api-version=2016-03-31' -X POST -d "" -H "Authorization: Bearer <ACCESS TOKEN>"

### Update Go App to get DB Password using MSI instead of from App Manifest Declared Environment Variable
msi_arm_token := request.get("'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https%3A%2F%2Fmanagement.azure.com%2F' -H Metadata:true")

cosmos_db_keys := request.get("'https://management.azure.com/subscriptions/eec8e14e-b47d-40d9-8bd9-23ff5c381b4/resourceGroups/aljomsitest/providers/Microsoft.DocumentDB/databaseAccounts/aljodb/listKeys?api-version=2016-03-31' -X POST -d '' -H \"Authorization: Bearer msi_arm_token['access_token']\"")

cosmos_db_password := cosmos_db_keys["primaryReadonlyMasterKey"]
