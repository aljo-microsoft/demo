mvn package

java -jar -Dserver.port=8082 ./target/javaservice-0.0.1.jar

"""
TODO: Update Project to include JavaService in MicroservicesApp:

1. main():
- rmc.java_service_build()
2. init
Change
        self.acregistry = self.go_service_acr_name + ".azurecr.io"
        self.acregistry_image_tag = self.acregistry + "/" + self.go_service_image_tag
To
        self.go_acregistry = self.go_service_acr_name + ".azurecr.io"
        self.go_acregistry_image_tag = self.go_acregistry + "/" + self.go_service_image_tag
        self.java_acregistry = self.java_service_acr_name + ".azurecr.io"
        self.java_acregistry_image_tag = self.java_acregistry + "/" + self.java_service_image_tag
      
3. microservices_app_sfpkg_declaration()
Change
go_service_manifest_image_name.text = self.acregistry_image_tag
To
go_service_manifest_image_name.text = self.go_acregistry_image_tag
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
                
4. SFPKG:
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

"""
