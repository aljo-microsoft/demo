# Demo Service Fabric Best Practices
Demo Microservices Application Best Practices in Azure with Service Fabric

This is a Microservices architected application, comprised of a Java and Golang Docker containerized services, declared as a Service Fabric Application ARM Resource.

The Go Service is implemented to serve a HTML UI for writing mongodb collections to CosmosDB.

The Java Service is implemented to create a MS SQL Database table, insert Data, Query Data, and Serve the Data.

# Status
Date 11/14/2019
Converting to Azure DevOps Project

### Build Pipeline:
#### Build GoService Image:
-Commands==build
-Dockerfile==./build/goservice/Dockerfile
-Image name==goservice
#### Tag GoService Image:
-Commands==tag
-Arguments==aljoacr.azurecr.io/goservice:1.0.0
-Image name==goservice
#### Push GoService Image:
-Commands==push
-Image name==aljoacr.azurecr.io/goservice:1.0.0
#### Bash Script:
-Inline
#### Note:
-Uncheck Qualify image name and Repeat Buid Tasks for each Container






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
### Set Subscription
az account set --subscription 'eec8e14e-b47d-40d9-8bd9-23ff5c381b40'
### Create RG
az group create --name aljorg --location westus
### Create VM with SysAssigned MSI
ssh-keygen -t rsa -b 2048

az vm create --resource-group aljorg --name aljovm --image UbuntuLTS --assign-identity --admin-username aljo --ssh-key-value @~/.ssh/id_rsa.pub
### Create Cosmos DB Account
az cosmosdb create --name aljodb --resource-group aljorg --kind MongoDB
### Get PrinipalID
principalid=$(az resource show --id /subscriptions/eec8e14e-b47d-40d9-8bd9-23ff5c381b40/resourceGroups/aljorg/providers/Microsoft.Compute/virtualMachines/aljovm --api-version 2017-12-01 | python -c "import sys, json; print(json.load(sys.stdin)['identity']['principalId'])")

### Grant VM MSI access to CosmosDB Keys
az role assignment create --assignee $principalid --role 'Contributor' --scope "/subscriptions/eec8e14e-b47d-40d9-8bd9-23ff5c381b40/resourceGroups/aljorg/providers/Microsoft.DocumentDB/databaseAccounts/aljodb"

### SSH into Machine (Validate NSG Rules Allow SSH from client)
ssh aljo@aljovm.westus.cloudapp.azure.com
### GET Access Token for ARM from Machine (Bash)
access_token=$(curl 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https%3A%2F%2Fmanagement.azure.com%2F' -H Metadata:true | python -c "import sys, json; print json.load(sys.stdin)['access_token']")

### Get Access Keys for Cosmos DB using MSI Access Token
cosmos_db_password=$(curl 'https://management.azure.com/subscriptions/eec8e14e-b47d-40d9-8bd9-23ff5c381b40/resourceGroups/aljorg/providers/Microsoft.DocumentDB/databaseAccounts/aljodb/listKeys?api-version=2016-03-31' -X POST -d "" -H "Authorization: Bearer $access_token" | python -c "import sys, json; print(json.load(sys.stdin)['primaryMasterKey'])")

echo "$cosmos_db_password"

### Update Go App to get DB Password using MSI instead of from App Manifest Declared Environment Variable
### Get/Use Access Token to Get Cosmos DB Primary Master Key in Golang
package main

import (
  "fmt"
  "io/ioutil"
  "net/http"
  "encoding/json"
)

func main() {
    // Get Access Token
    req, err := http.NewRequest("GET", "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https%3A%2F%2Fmanagement.azure.com%2F", nil)
    if err != nil {
        // handle err
    }
    req.Header.Set("Metadata", "true")

    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        // handle err
    }

    if resp.StatusCode == http.StatusOK {
        respBytes, _ := ioutil.ReadAll(resp.Body)
        var access_token_resp map[string]interface{}
        json.Unmarshal(respBytes, &access_token_resp)
        access_token, _ := access_token_resp["access_token"].(string)
        // Get Passsword
        var bearer_token = "Bearer " + access_token
        req_keys, err := http.NewRequest("POST", "https://management.azure.com/subscriptions/eec8e14e-b47d-40d9-8bd9-23ff5c381b40/resourceGroups/aljorg/providers/Microsoft.DocumentDB/databaseAccounts/aljodb/listKeys?api-version=2016-03-31", nil)
        req_keys.Header.Set("Authorization", bearer_token)
        if err != nil {
           // handle err
        }

        resp_keys, err := http.DefaultClient.Do(req_keys)
        if err != nil {
            // handle err
        }
        respBytes_keys, _ := ioutil.ReadAll(resp_keys.Body)
        var cosmos_listkeys_resp map[string]interface{}
        json.Unmarshal(respBytes_keys, &cosmos_listkeys_resp)
        primary_master_key, _ := cosmos_listkeys_resp["primaryMasterKey"].(string)
    }
}
