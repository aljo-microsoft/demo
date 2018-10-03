# Demo Service Fabric Best Practices
Demo Reliable Production Service Fabric Application Best Practices

Executing ServiceFabricBestPractices.py will result in a Service Fabric Cluster Creation; as will importing ServiceFabricResourceDeclaration and executing functions individually.

# Status
10/3/2019

ARM deployment of Service Fabric Application Versions targetd for Linux hosts timeout, and using Windows hosts worked today.

Template that worked: https://github.com/Azure-Samples/service-fabric-cluster-templates/tree/master/5-VM-Windows-1-NodeTypes-Secure

To enable executing ServiceFabricBestPractices.py with AzureDeploy.json and AzureDeploy.Parameters.json file found at above samples repo:

Required changes to template:
Parameter "clusterLocation" to "location" and adding variable "location": "[parameters('location')]"

Required changes to Parmeters:
Parameter "clusterLocation" to "location"

Execute script and RM deployment will deploy application version.

Next step is to implement inbound and outbound NSG rules.
