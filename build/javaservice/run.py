mvn package

java -jar -Dserver.port=8082 ./target/javaservice-0.0.1.jar

"""
TODO: Update Project to include JavaService in MicroservicesApp:

1. servicefabric_bestpractices.py
- main():
Add
rmc.java_service_build()
rmc.java_azure_sql_resource_declaration()

-init
Change
        self.acregistry = self.go_service_acr_name + ".azurecr.io"
        self.acregistry_image_tag = self.acregistry + "/" + self.go_service_image_tag
To
        self.go_acregistry = self.go_service_acr_name + ".azurecr.io"
        self.go_acregistry_image_tag = self.go_acregistry + "/" + self.go_service_image_tag
        self.java_acregistry = self.java_service_acr_name + ".azurecr.io"
        self.java_acregistry_image_tag = self.java_acregistry + "/" + self.java_service_image_tag
      
- microservices_app_sfpkg_declaration()
Change
go_service_manifest_image_name.text = self.acregistry_image_tag
To
go_service_manifest_image_name.text = self.go_acregistry_image_tag
Change
            if parameter_name == 'ENV_DATABASE_NAME':
                parameter.set('DefaultValue', self.microservices_mongo_db_name)
            elif parameter_name == 'ENV_DB_USER_NAME':
                parameter.set('DefaultValue', self.microservices_mongo_db_account_name)
            elif parameter_name == 'ENV_DB_PASSWORD':
                parameter.set('DefaultValue', self.cosmos_db_password)
            elif parameter_name == 'ENV_ACR_USERNAME':
                parameter.set('DefaultValue', self.go_acr_username)
            elif parameter_name == 'ENV_ACR_PASSWORD':
                parameter.set('DefaultValue', self.go_acr_password)
To
            if parameter_name == 'GO_DATABASE_NAME':
                parameter.set('DefaultValue', self.microservices_mongo_db_name)
            elif parameter_name == 'GO_DB_USER_NAME':
                parameter.set('DefaultValue', self.microservices_mongo_db_account_name)
            elif parameter_name == 'GO_DB_PASSWORD':
                parameter.set('DefaultValue', self.cosmos_db_password)
            elif parameter_name == 'GO_ACR_USERNAME':
                parameter.set('DefaultValue', self.go_acr_username)
            elif parameter_name == 'GO_ACR_PASSWORD':
                parameter.set('DefaultValue', self.go_acr_password)
            elif parameter_name == 'JAVA_ACR_USERNAME':
                parameter.set('DefaultValue', self.java_acr_username)
            elif parameter_name == 'JAVA_ACR_PASSWORD':
                parameter.set('DefaultValue', self.java_acr_password)
Add
        java_service_manifest_path = self.microservices_app_package_path + "/JavaService/ServiceManifest.xml"
        java_service_manifest = xml.etree.ElementTree.parse(java_service_manifest_path)
        java_service_manifest_root = java_service_manifest.getroot()
        java_service_manifest_root.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
        java_service_manifest_root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        java_service_manifest_codepackage = java_service_manifest_root.find('{http://schemas.microsoft.com/2011/01/fabric}CodePackage')
        java_service_manifest_entrypoint = java_service_manifest_codepackage.find('{http://schemas.microsoft.com/2011/01/fabric}EntryPoint')
        java_service_manifest_containerhost = java_service_manifest_entrypoint.find('{http://schemas.microsoft.com/2011/01/fabric}ContainerHost')
        java_service_manifest_image_name = java_service_manifest_containerhost.find('{http://schemas.microsoft.com/2011/01/fabric}ImageName')
        java_service_manifest_image_name.text = self.java_acregistry_image_tag

        java_service_manifest.write(java_service_manifest_path)

- microservices_app_resource_declaration()
Add for ApplicationType
application_type_java_service_depends_on = "Microsoft.Sql/servers/sfbpsqlserver"
Add
        elif microservices[j].attrib['Name'].lower().find("java") > -1:
            sfpkg_java_service_name = microservices[j].attrib['Name']
            sfpkg_java_service_type = microservices[j].getchildren()[0].attrib['ServiceTypeName']
Add
        # Java Service
        java_service_name = "[concat(parameters('clusterName'), '/', '" + self.microservices_app_name + "', '/', '" + self.microservices_app_name + "~" + sfpkg_java_service_name + "')]"
        java_service_depends_on = "[concat('Microsoft.ServiceFabric/clusters/', parameters('clusterName'), '/applications/', '" + self.microservices_app_name + "')]"
        template_file_json["resources"] += [
            {
                "apiVersion": "2017-07-01-preview",
                "type": "Microsoft.ServiceFabric/clusters/applications/services",
                "name": java_service_name,
                "location": "[variables('location')]",
                "dependsOn": [
                    java_service_depends_on
                ],
                "properties": {
                    "provisioningState": "Default",
                    "serviceKind": "Stateless",
                    "serviceTypeName": sfpkg_java_service_type,
                    "instanceCount": "-1",
                    "partitionDescription": {
                        "partitionScheme": "Singleton"
                    },
                    "correlationScheme": [],
                    "serviceLoadMetrics": [],
                    "servicePlacementPolicies": []
                }
            }
        ]

Add
    def java_azure_sql_resource_declaration(self):
        # Update Template with JavaService Azure SQL Resource
        print("Updating Resource Declaration with JavaService Azure SQL Demo Dependencies")
        template_file_json = json.load(open(self.template_file, 'r'))
	
	# Azure SQL
	template_file_json["resources"] += [
        {
            "apiVersion": "2015-05-01-preview",
            "location": "[parameters('location')]",
            "type": "Microsoft.Sql/servers",
            "name": "sfbpsqlserver",
            "properties": {
                "administratorLogin": "aljo",
                "administratorLoginPassword": "Password#1234",
                "version": "12.0"
            },
            "resources": [
                {
                    "apiVersion": "2017-10-01-preview",
                    "dependsOn": [
                        "[concat('Microsoft.Sql/servers/', 'sfbpsqlserver')]"
                    ],
                    "location": "[parameters('location')]",
                    "name": "sfbpdatabase",
                    "properties": {
                        "collation": "SQL_Latin1_General_CP1_CI_AS",
                        "maxSizeBytes": 268435456000,
                        "sampleName": "",
                        "zoneRedundant": False,
                        "licenseType": ""
                    },
                    "sku": {
                        "name": "S0",
                        "tier": "Standard"
                    },
                    "type": "databases"
                },
                {
                    "condition": True,
                    "apiVersion": "2014-04-01-preview",
                    "dependsOn": [
                        "[concat('Microsoft.Sql/servers/', 'sfbpsqlserver')]"
                    ],
                    "location": "[parameters('location')]",
                    "name": "AllowAllWindowsAzureIps",
                    "properties": {
                        "endIpAddress": "0.0.0.0",
                        "startIpAddress": "0.0.0.0"
                    },
                    "type": "firewallrules"
                }
            ]
        }
    ]
    
    # Update Template File
    template_file = open(self.template_file, 'w')
    json.dump(template_file_json, template_file)
    template_file.close()

2. SFPKG:
ApplicationManifest.xml
Change
        <Parameter Name="ENV_DATABASE_NAME" DefaultValue="localhost" />
        <Parameter Name="ENV_DB_USER_NAME" DefaultValue="myuser" />
        <Parameter Name="ENV_DB_PASSWORD" DefaultValue="mypassword" />
        <Parameter Name="ENV_ACR_USERNAME" DefaultValue="myacr" />
        <Parameter Name="ENV_ACR_PASSWORD" DefaultValue="myacrpassword" />
To
        <Parameter Name="GO_DATABASE_NAME" DefaultValue="localhost" />
        <Parameter Name="GO_DB_USER_NAME" DefaultValue="myuser" />
        <Parameter Name="GO_DB_PASSWORD" DefaultValue="mypassword" />
        <Parameter Name="GO_ACR_USERNAME" DefaultValue="myacr" />
        <Parameter Name="GO_ACR_PASSWORD" DefaultValue="myacrpassword" />
        <Parameter Name="JAVA_ACR_USERNAME" DefaultValue="myacr" />
        <Parameter Name="JAVA_ACR_PASSWORD" DefaultValue="myacrpassword" />
Change
            <EnvironmentVariable Name="DATABASE_NAME" Value="[ENV_DATABASE_NAME]" />
            <EnvironmentVariable Name="DB_USER_NAME" Value="[ENV_DB_USER_NAME]" />
            <EnvironmentVariable Name="DB_PASSWORD" Value="[ENV_DB_PASSWORD]" />
To
            <EnvironmentVariable Name="DATABASE_NAME" Value="[GO_DATABASE_NAME]" />
            <EnvironmentVariable Name="DB_USER_NAME" Value="[GO_DB_USER_NAME]" />
            <EnvironmentVariable Name="DB_PASSWORD" Value="[GO_DB_PASSWORD]" />
Change
                <RepositoryCredentials AccountName="[ENV_ACR_USERNAME]" Password="[ENV_ACR_PASSWORD]" PasswordEncrypted="false"/>
To
                <RepositoryCredentials AccountName="[GO_ACR_USERNAME]" Password="[GO_ACR_PASSWORD]" PasswordEncrypted="false"/>
Add
    <ServiceManifestImport>
        <ServiceManifestRef ServiceManifestName="JavaService" ServiceManifestVersion="1.0.0" />
	      <Policies>
            <ContainerHostPolicies CodePackageRef="JavaCode">
                <RepositoryCredentials AccountName="[JAVA_ACR_USERNAME]" Password="[JAVA_ACR_PASSWORD]" PasswordEncrypted="false"/>
                <PortBinding ContainerPort="8082" EndpointRef="JavaServiceTypeEndpoint"/>
            </ContainerHostPolicies>
        </Policies>
    </ServiceManifestImport>
Add
        <Service Name="JavaService">
            <StatelessService ServiceTypeName="JavaServiceType" InstanceCount="-1" >
                <SingletonPartition />
            </StatelessService>
	      </Service>

- JavaService
-- JavaConfig
--- Settings.xml
<?xml version="1.0" encoding="utf-8" ?>
<Settings xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://schemas.microsoft.com/2011/01/fabric">
    <!--Declare your Services Configuration Values -->
</Settings>
-- ServiceManifest.xml
<?xml version="1.0" encoding="utf-8" ?>
<ServiceManifest xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" Name="JavaService" Version="1.0.0" xmlns="http://schemas.microsoft.com/2011/01/fabric">
   <ServiceTypes>
      <StatelessServiceType ServiceTypeName="JavaServiceType" UseImplicitHost="true"/>
   </ServiceTypes>
  <!-- Code package is your service executable. -->
  <CodePackage Name="JavaCode" Version="1.0.0">
    <EntryPoint>
      <ContainerHost>
        <!-- repo/name:version -->
            <ImageName>demosfbpjava.azurecr.io/javaservice:1.0.0</ImageName>
        <Commands></Commands>
      </ContainerHost>
    </EntryPoint>
    <!-- Pass environment variables to your container. -->
    <EnvironmentVariables>
      <EnvironmentVariable Name="IsContainer" Value="true"/>
    </EnvironmentVariables>
  </CodePackage>
  <!-- Config package is the contents of the Config directoy under PackageRoot that contains an 
       independently-updateable and versioned set of custom configuration settings for your service. -->
  <ConfigPackage Name="JavaConfig" Version="1.0.0" />
  <Resources>
    <Endpoints>
      <!-- This endpoint is used by the communication listener to obtain the port on which to 
           listen. For a guest executable is used to register with the NamingService at its REST endpoint
           with http scheme. In this case since no port is specified then one if created and assigned dynamically
           to the service.-->
      <Endpoint Name="JavaServiceTypeEndpoint" UriScheme="http" Port="8083" Protocol="http"/>
    </Endpoints>
  </Resources>
</ServiceManifest>

3. Debug using:
    python3
    from servicefabric_bestpractices import ResourceManagerClient
    rmc = ResourceManagerClient()
    rmc.declare_secret_parameter_values()
    rmc.go_service_build()
    rmc.microservices_cosmos_db_creation()
    rmc.java_service_build()
    rmc.java_azure_sql_resource_declaration()
    rmc.microservices_app_sfpkg_declaration()
    rmc.microservices_app_sfpkg_staging()
    rmc.microservices_app_resource_declaration()
    rmc.validate_declaration()
    rmc.deploy_resources()
"""
