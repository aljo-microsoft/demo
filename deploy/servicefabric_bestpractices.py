__author__ = "Alexander Johnson"
__email__ = "aljo-microsoft@github.com"
__status__ = "Development"

from datetime import datetime
import xml.etree.ElementTree
import json
import os
from pathlib import Path
from subprocess import PIPE
from subprocess import Popen
import sys
import zipfile

class ResourceManagerClient:
    # Microservice development Best Practice in Azure, is Service Fabric Applications, that are managed by
    # Azure Resource Manager.
    #
    # A vital component of success in delivering your SLA/O's will require you to make decisions.
    # E.G. may include using a x509 certificates issued by a trusted Certificate Authority.
    #
    # This was tested October 5 2018 using Azure Cloud Shell.
    def __init__(
        self,
        subscription='eec8e14e-b47d-40d9-8bd9-23ff5c381b40',
        ):

        # Owner
        self.subscription = subscription
        
	# Az CLI Client
        account_set_process = Popen(["az", "account", "set", "--subscription", self.subscription])

        if account_set_process.wait() != 0:
            sys.exit()

        print("Deployment Subscription Valid")

	# Minimum Service Fabric Cluster Values
        self.template_file = 'AzureDeploy.json'
        self.parameters_file = 'AzureDeploy.Parameters.json'
        self.deployment_resource_group = 'demobpdeployrg'
        self.keyvault_resource_group = 'demobpkeyvaultrg'
        self.keyvault_name = 'demobpkeyvault'
        self.cluster_name = 'demobpcluster'
        self.admin_user_name = 'demo'
        self.admin_password = 'Password#1234'
        self.location = 'westus'
        self.certificate_name = 'x509certificatename'
        self.certificate_thumbprint = 'GEN-CUSTOM-DOMAIN-SSLCERT-THUMBPRINT'
        self.source_vault_value = 'GEN-KEYVAULT-RESOURCE-ID'
        self.certificate_url_value = 'GEN-KEYVAULT-SSL-SECRET-URI'
        self.user_email = 'aljo-microsoft@github.com'

        # Default Values for Microservices App
        self.dns_name = self.cluster_name + "." + self.location + ".cloudapp.azure.com"
        self.certificate_file_name = self.certificate_name + ".pem"
        self.parameters_file_arg = "@" + self.parameters_file
        self.microservices_app_package_url = "https://demobpstorage.blob.core.windows.net/demobpcontainer<ID>/MicroservicesApp.sfpkg"
        self.microservices_app_package_path = '../package'
        self.microservices_app_name = 'microservicesapp'
        self.microservices_app_package_name = 'MicroserviceApp.sfpkg'
        self.storage_account_name = 'demobpstorage'
        self.container_name = 'demobpcontainer'
        self.microservices_mongo_db_account_name = 'microservicesuser'
        self.microservices_mongo_db_name = 'microservicemongodb'

	# Default Valyes for GoService
        self.go_service_source_path = '../build/goservice'
        self.go_service_image_tag = "goservice:1.0.0"
        self.go_service_acr_name = "demosfbp"
        self.acr_username = self.microservices_mongo_db_name
        self.acr_password = 'GEN-UNIQUE-PASSWORD'
        self.acregistry = self.go_service_acr_name + ".azurecr.io"
        self.acregistry_image_tag = self.acregistry + "/" + self.go_service_image_tag
        self.cosmos_db_password = 'GEN-UNIQUE-PASSWORD'
	
        # Default values for JavaService
        self.java_service_source_path = '../build/javaservice'
        self.java_service_name = 'javaservice'

        # Resource Declaration
        if not Path(self.template_file).exists():
            sys.exit("Template File Not Found")

    def declare_secret_parameter_values(self):
        # Get Parameter Values
        if Path(self.parameters_file).exists():
            parameters_file_json = json.load(open(self.parameters_file, 'r'))
        else:
            sys.exit("Parameters Not Found")

        # Secrets are passed in as arguments, or fetched from Managed Service
        if self.source_vault_value.find('/subscriptions/') >= 0 and len(self.certificate_thumbprint) > 36 and self.certificate_url_value.find('vault.azure.net') > -1:
            print('Validating Secret Arguments')
        # Demo only - allow redeployment using declared secret values
        elif parameters_file_json['parameters']['sourceVaultValue']['value'].find('/subscriptions/') >= 0 and len(parameters_file_json['parameters']['certificateThumbprint']['value']) > 36 and parameters_file_json['parameters']['certificateUrlValue']['value'].find('vault.azure.net') > -1:
            print('Validating Secret in Parameters File')
            self.source_vault_value = parameters_file_json['parameters']['sourceVaultValue']['value']
            self.certificate_thumbprint = parameters_file_json['parameters']['certificateThumbprint']['value']
            self.certificate_url_value = parameters_file_json['parameters']['certificateUrlValue']['value']
        else:
            # Get Secrets from KeyVault
            print('Making Keyvault Certificate')
            keyvault_group_create_process = Popen(["az", "group", "create", "--name", self.keyvault_resource_group, "--location", self.location])

            if keyvault_group_create_process.wait() != 0:
                sys.exit()

            keyvault_create_process = Popen(["az", "keyvault", "create", "--name", self.keyvault_name, "--resource-group", self.keyvault_resource_group, "--enabled-for-deployment", "true"])

            if keyvault_create_process.wait() != 0:
                sys.exit()

            # Keyvault DNS Population Takes 10 Secs
            keyvault_show_process = Popen(["az", "keyvault", "show", "-n", self.keyvault_name, "-g", self.keyvault_resource_group])

            if keyvault_show_process.wait() != 0:
                sys.exit()

            # Create Self Signed Certificate
            # Get Default Policy
            default_policy_process = Popen(["az", "keyvault", "certificate", "get-default-policy"], stdout=PIPE, stderr=PIPE)

            stdout, stderr = default_policy_process.communicate()

            if default_policy_process.wait() == 0:
                default_policy_json = json.loads(stdout.decode("utf-8"))
            else:
                sys.exit(stderr)

            # Set Subject Name to FQDN
            # Browsers won't trust certificates with subject names that don't match FQDN
            default_policy_json['x509CertificateProperties']['subject'] = "CN=" + self.dns_name
            default_policy_json['x509CertificateProperties']['sans'] = {'dns_names': [self.dns_name], 'emails': [self.user_email], 'upns': [self.user_email]} 
            policy_file_name = "policy.json"
            policy_file_arg = "@" + policy_file_name
            json.dump(default_policy_json, open(policy_file_name, 'w+'))

            certificate_create_process = Popen(["az", "keyvault", "certificate", "create", "--vault-name", self.keyvault_name, "-n", self.certificate_name, "-p", policy_file_arg], stdout=PIPE, stderr=PIPE)

            if certificate_create_process.wait() != 0:
                sys.exit()

            # Get Keyvault Self Signed Certificate Properties
            # Get resource Id
            resource_id_process = Popen(["az", "keyvault", "show", "--name", self.keyvault_name, "--query", "id", "-o", "tsv"], stdout=PIPE, stderr=PIPE)

            stdout, stderr = resource_id_process.communicate()

            if resource_id_process.wait() == 0:
                self.source_vault_value = stdout.decode("utf-8").replace('\n', '')
            else:
                sys.exit(stderr)

            # Get Certificate Url
            url_process = Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "sid", "-o", "tsv"], stdout=PIPE, stderr=PIPE)

            stdout, stderr = url_process.communicate()

            if url_process.wait() == 0:
                self.certificate_url_value = stdout.decode("utf-8").replace('\n', '')
            else:
                sys.exit(stderr)

            # Get Certificate Thumbprint
            thumbprint_process = Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "x509ThumbprintHex", "-o", "tsv"], stdout=PIPE, stderr=PIPE)

            stdout, stderr = thumbprint_process.communicate()

            if thumbprint_process.wait() == 0:
                self.certificate_thumbprint = stdout.decode("utf-8").replace('\n', '')
            else:
                sys.exit(stderr)

        # Validate KeyVault Resource Availability
        validate_source_vault = Popen(["az", "resource", "show", "--ids", self.source_vault_value])

        if validate_source_vault.wait() != 0:
            sys.exit()

        # Certificate URL
        self.keyvault_name = self.certificate_url_value.rsplit("//", 1)[1].rsplit(".vault.", 1)[0]
        self.certificate_name = self.certificate_url_value.rsplit("//", 1)[1].rsplit(".vault.", 1)[1].rsplit("/", 3)[2]

        cert_url_validate_process = Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "sid", "-o", "tsv"])

        if cert_url_validate_process.wait() != 0:
            sys.exit()

        # Certificate Thumbprint
        cert_thumbprint_validate_process = Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "x509ThumbprintHex", "-o", "tsv"])

        if cert_thumbprint_validate_process.wait() != 0:
            sys.exit()

        # Declare Certificate
        parameters_file_json['parameters']['sourceVaultValue']['value'] = self.source_vault_value
        parameters_file_json['parameters']['certificateThumbprint']['value'] = self.certificate_thumbprint
        parameters_file_json['parameters']['certificateUrlValue']['value'] = self.certificate_url_value

        # Prefer Arguments
        parameters_file_json['parameters']['clusterName']['value'] = self.cluster_name
        parameters_file_json['parameters']['adminUserName']['value'] = self.admin_user_name
        parameters_file_json['parameters']['adminPassword']['value'] = self.admin_password
        parameters_file_json['parameters']['location']['value'] = self.location

        # Write Template
        json.dump(parameters_file_json, open(self.parameters_file, 'w'))

    def validate_declaration(self):
        # Exists or Create Deployment Group - needed for validation
        deployment_group_exists_process = Popen(["az", "group", "exists", "--name", self.deployment_resource_group], stdout=PIPE, stderr=PIPE)

        stdout, stderr = deployment_group_exists_process.communicate()

        if stdout.decode('utf-8').replace('\n', '') != 'true':
            deployment_group_create_process = Popen(["az", "group", "create", "--location", self.location, "--name", self.deployment_resource_group], stdout=PIPE, stderr=PIPE)

            if deployment_group_create_process.wait() != 0:
                sys.exit(stderr)

        # Validate Deployment Declaration
        deployment_validation_process = Popen(["az", "group", "deployment", "validate", "--resource-group", self.deployment_resource_group, "--template-file", self.template_file, "--parameters", self.parameters_file_arg], stdout=PIPE, stderr=PIPE)

        stdout, stderr = deployment_validation_process.communicate()

        if deployment_validation_process.wait() == 0:
            print("Your Deployment Declaration is Valid Syntactically")
        else:
            print(stdout)
            sys.exit(stderr)

    def deploy_resources(self):
        # Reduce LiveSite issues by deploying Azure Resources in a Declarative way as a group
        deployment_name = "bestpracticedeployment"

        print("Deploying Resources")
        group_deployment_create_process = Popen(["az", "group", "deployment", "create", "-g", self.deployment_resource_group, "--name", deployment_name, "--template-file", self.template_file, "--parameters", self.parameters_file_arg], stdout=PIPE, stderr=PIPE)

        stdout, stderr = group_deployment_create_process.communicate()

        if group_deployment_create_process.wait() != 0:
            print(stdout)
            print(stderr)
	
        print("Resource Deployment Successful")

    def setup_cluster_client(self):
        # Downloads client admin certificate
        # Convert to PEM format for linux compatibility
        print("Downloading Certificate")
        certificate_b64_file = self.certificate_name + "64.pem"
        download_cert_process = Popen(["az", "keyvault", "secret", "download", "--file", certificate_b64_file, "--encoding", "base64", "--name", self.certificate_name, "--vault-name", self.keyvault_name], stdout=PIPE, stderr=PIPE)

        stdout, stderr = download_cert_process.communicate()

        if download_cert_process.wait() != 0:
            print(stdout)
            print(stderr)

        convert_cert_process = Popen(["openssl", "pkcs12", "-in", certificate_b64_file, "-out", self.certificate_file_name, "-nodes", "-passin", "pass:"], stdout=PIPE, stderr=PIPE)

        stdout, stderr = convert_cert_process.communicate()

        if convert_cert_process.wait() != 0:
            print(stdout)
            print(stderr)

    def cluster_connection(self):
        endpoint = 'https://' + self.dns_name + ':19080'

        cluster_connect_process = Popen(["sfctl", "cluster", "select", "--endpoint", endpoint, "--pem", self.certificate_file_name, "--no-verify"])

        if cluster_connect_process.wait() != 0:
            sys.exit("Unable to Connect to Cluster")

    def go_service_build(self):
        # Create ACR for goservice Container
        acr_create_process = Popen(["az", "acr", "create", "--name", self.go_service_acr_name, "--resource-group", self.deployment_resource_group, "--sku", "Basic", "--admin-enabled", "true"])

        if acr_create_process.wait() != 0:
            sys.exit("Couldn't create ACR")

        # Build GoService Container Image
        go_service_build_process = Popen(["az", "acr", "build", "--os", "Linux", "registry", self.go_service_acr_name, "--image", self.go_service_image_tag, "../build/goservice/"])

        if go_service_build_process.wait() != 0:
            sys.exit("couldn't build GoService Docker Image")

        # Get ACR User Name
        acr_username_process = Popen(["az", "acr", "credential", "show", "-n", self.go_service_acr_name, "--query", "username"], stdout=PIPE, stderr=PIPE)

        stdout, stderr = acr_username_process.communicate()

        if acr_username_process.wait() == 0:
            self.acr_username = stdout.decode("utf-8").replace('\n', '')
        else:
            sys.exit(stderr)
        # Get ACR Password
        acr_password_process = Popen(["az", "acr", "credential", "show", "-n", self.go_service_acr_name, "--query", "passwords[0].value"], stdout=PIPE, stderr=PIPE)

        stdout, stderr = acr_password_process.communicate()

        if acr_password_process.wait() == 0:
            self.acr_password = stdout.decode("utf-8").replace('\n', '')
        else:
            sys.exit(stderr)

    def microservices_cosmos_db_creation(self):
        # Craete Cosmos DB Account
        cosmos_account_create_process = Popen(["az", "cosmosdb", "create", "--name", self.microservices_mongo_db_account_name, "--resource-group", self.deployment_resource_group, "--kind", "MongoDB"])

        if cosmos_account_create_process.wait() != 0:
            sys.exit("couldn't create GoApp Cosmos DB User")

        cosmos_database_create_process = Popen(["az", "cosmosdb", "database", "create", "--db-name", self.microservices_mongo_db_name, "--name", self.microservices_mongo_db_account_name, "--resource-group", self.deployment_resource_group])

        if cosmos_database_create_process.wait() != 0:
            sys.exit("Couldn't crate Go App Cosmos Mongo DB")

        cosmos_db_password_process = Popen(["az", "cosmosdb", "list-keys", "--name", self.microservices_mongo_db_account_name, "--resource-group", self.deployment_resource_group, "--query", "primaryMasterKey"], stdout=PIPE, stderr=PIPE)

        stdout, stderr = cosmos_db_password_process.communicate()

        if cosmos_db_password_process.wait() == 0:
            self.cosmos_db_password = stdout.decode("utf-8").replace('\n', '')
        else:
            sys.exit(stderr)

    def go_service_sfpkg_declaration(self):
        # - Set SF Package to acregistry_image_tag
        # service_manifest = xml.etree.ElementTree.parse(goservice_service_manifest_path).getroot()
        # service_manifest.getchildren()[0].attrib['ImageName'] = self.acregistry_image_tag
        # - Set Environment variable DATABASE_NAME variable to self.microservices_mongo_db_name
        # - Set Environment variable DB_ACCOUNT_NAME to self.microservices_mongo_db_account_name
        # - Set Environment variable DB_PASSWORD to self.microservices_mongo_db_password
        # TODO: Upload go_app_mongo_db_password to Keyvault, update to use HOST MSI to authenticate to KV, and retrive password.
        # Get Package Properties for RM Template
        print("Declared Go Service")

    def java_service_build(self):
        # Build Java class that uses VMSS MSI to write to cosmos_db
        print("build JavaService.java")

    def java_service_sfpkg_declaration(self):
        # Set service name
        print("Declare Java Service")

    def microservices_app_sfpkg_staging(self): 
        # Create microservices_app_v1.0.sfpkg
        # Create Storage Account
        # Get Connection String to Storage Account
        # Create Storage Account Blob Container
        # Upload SF Packge to Account blob
        # Get Public url to file in storage account blob
        print("Packing Microservices Solution")

        # Use Public URL instead of creating one
        # Create Storate
        create_storage_process = Popen(["az", "storage", "account", "create", "-n", self.storage_account_name, "-g", self.deployment_resource_group, "-l", self.location, "--sku", "Standard_LRS"], stdout=PIPE, stderr=PIPE)

        stdout, stderr = create_storage_process.communicate()

        if create_storage_process.wait() == 0:
            print("Storage Account Created")
        else:
            sys.exit(stderr)

        # Get Connection String
        connection_string_process = Popen(["az", "storage", "account", "show-connection-string", "-g", self.deployment_resource_group, "-n", self.storage_account_name], stdout=PIPE, stderr=PIPE)

        stdout, stderr = connection_string_process.communicate()

        if connection_string_process.wait() == 0:
            connection_string = str(json.loads(stdout.decode("utf-8"))['connectionString'])
            print("Got Storage Connection String")
        else:
            sys.exit(stderr)

        # Create Blob Container
        create_container_process = Popen(["az", "storage", "container", "create", "--name", self.container_name, "--connection-string", connection_string, "--public-access", "container"], stdout=PIPE, stderr=PIPE)

        stdout, stderr = create_container_process.communicate()

        if create_container_process.wait() == 0:
            print("Blob Container Created")
        else:
            sys.exit(stderr)

        # Zip SFPKG to Upload to Blob Container
        microservices_sfpkg = zipfile.ZipFile(self.microservices_app_package_name, 'w', zipfile.ZIP_DEFLATED)
        # Add each package element to zip file
        for root, dirs, files in os.walk(self.microservices_app_package_path):
            for file in files:
                microservices_sfpkg.write(os.path.join(root, file))
        # Close zip file
        microservices_sfpkg.close()

        # Upload SFPKG to Blob Container
        upload_sfpkg_process = Popen(["az", "storage", "blob", "upload", "--file", self.microservices_app_package_name, "--name", self.microservices_app_name, "--connection-string", connection_string, "--container-name", self.container_name], stdout=PIPE, stderr=PIPE)

        stdout, stderr = upload_sfpkg_process.communicate()

        if upload_sfpkg_process.wait() == 0:
            print("Uploaded SFPKG To Storage Account Blob Container")
        else:
            sys.exit(stderr)

        # Get URL for SFPKG in Storage Account Blob Container
        url_sfpkg_process = Popen(["az", "storage", "blob", "url", "--container-name", self.container_name, "--connection-string", connection_string, "--name", self.microservices_app_name], stdout=PIPE, stderr=PIPE)

        stdout, stderr = url_sfpkg_process.communicate()

        if url_sfpkg_process.wait() == 0:
            self.microservices_app_package_url = stdout.decode("utf-8").replace('\n', '').replace('"', '')
            print("Got URL for SFPKG in Storage Account Blob")
        else:
            sys.exit(stderr)

    def microservices_app_resource_declaration(self):
        # Update Template with Application, App Type, App Version, Service Type's (go app, and classic java)
        print("Updating Resource Declaration Microservices SolutionJavaApp")
        template_file_json = json.load(open(self.template_file, 'r'))

        # TODO: Below needs to be updated to only append Service to Application type
        #       Will delcare Type with GoApp.
	# Declare Classic App Services as resources that is apart of microservices Application
        # Unzip SFPKG and Get Properties
        print("Declaring classic app in template")
        application_manifest_path = self.microservices_app_package_path + "/ApplicationManifest.xml"
        application_manifest = xml.etree.ElementTree.parse(application_manifest_path).getroot()
        sfpkg_application_type_version = application_manifest.attrib['ApplicationTypeVersion']
        sfpkg_application_type_name = application_manifest.attrib['ApplicationTypeName']

        for i in range(len(application_manifest)):
            if application_manifest[i].tag == '{http://schemas.microsoft.com/2011/01/fabric}DefaultServices':
                microservices = application_manifest[i].getchildren()
                for j in range(len(microservices)):
                    if microservices[j].attrib['Name'].lower().find("go") > -1:
                        sfpkg_go_service_name = microservices[j].attrib['Name']
                        sfpkg_go_service_type = microservices[j].getchildren()[0].attrib['ServiceTypeName']
                    elif microservices[j].attrib['Name'].lower().find("java") > -1:
                        sfpkg_java_service_name = microservices[j].attrib['Name']
                        sfpkg_java_service_type = microservices[j].getchildren()[0].attrib['ServiceTypeName']
                    else:
                        sys.exit("couldn't find ApplicationManifest Services")

        # ApplicationType
        application_type_depends_on = "[concat('Microsoft.ServiceFabric/clusters/', parameters('clusterName'))]"
        application_type_name = "[concat(parameters('clusterName'), '/', '" + sfpkg_application_type_name + "')]"
        template_file_json["resources"] += [
            {
                "apiVersion": "2017-07-01-preview",
                "type": "Microsoft.ServiceFabric/clusters/applicationTypes",
                "name": application_type_name,
                "location": "[variables('location')]",
                "dependsOn": [
                    application_type_depends_on
                ],
                "properties": {
                    "provisioningState": "Default"
                }
            }
        ]
        # ApplicationTypeVersion
        application_type_version = "[concat(parameters('clusterName'), '/', '" + sfpkg_application_type_name + "', '/', '" + sfpkg_application_type_version + "')]"
        application_type_version_depends_on = "[concat('Microsoft.ServiceFabric/clusters/', parameters('clusterName'), '/applicationTypes/', '" + sfpkg_application_type_name + "')]"
        template_file_json["resources"] += [
            {
                "apiVersion": "2017-07-01-preview",
                "type": "Microsoft.ServiceFabric/clusters/applicationTypes/versions",
                "name": application_type_version,
                "location": "[variables('location')]",
                "dependsOn": [
                    application_type_version_depends_on
                ],
                "properties": {
                    "provisioningState": "Default",
                    "appPackageUrl": self.microservices_app_package_url
                }
            }
        ]

        # Application
        application_name = "[concat(parameters('clusterName'), '/', '" + self.microservices_app_name + "')]"
        application_name_dependends_on = "[concat('Microsoft.ServiceFabric/clusters/', parameters('clusterName'), '/applicationTypes/', '" + sfpkg_application_type_name + "', '/versions/', '" + sfpkg_application_type_version + "')]"
        template_file_json["resources"] += [
            {
                "apiVersion": "2017-07-01-preview",
                "type": "Microsoft.ServiceFabric/clusters/applications",
                "name": application_name,
                "location": "[variables('location')]",
                "dependsOn": [
                    application_name_dependends_on
                ],
                "properties": {
                    "provisioningState": "Default",
                    "typeName": sfpkg_application_type_name,
                    "typeVersion": sfpkg_application_type_version,
                    "parameters": {},
                    "upgradePolicy": {
                        "upgradeReplicaSetCheckTimeout": "01:00:00.0",
                        "forceRestart": "false",
                        "rollingUpgradeMonitoringPolicy": {
                            "healthCheckWaitDuration": "00:02:00.0",
                            "healthCheckStableDuration": "00:05:00.0",
                            "healthCheckRetryTimeout": "00:10:00.0",
                            "upgradeTimeout": "01:00:00.0",
                            "upgradeDomainTimeout": "00:20:00.0"
                        },
                        "applicationHealthPolicy": {
                            "considerWarningAsError": "false",
                            "maxPercentUnhealthyDeployedApplications": "50",
                            "defaultServiceTypeHealthPolicy": {
                                "maxPercentUnhealthyServices": "50",
                                "maxPercentUnhealthyPartitionsPerService": "50",
                                "maxPercentUnhealthyReplicasPerPartition": "50"
                            }
                        }
                    }
                }
            }
        ]

        # Go Service
        go_service_name = "[concat(parameters('clusterName'), '/', '" + self.microservices_app_name + "', '/', '" + self.microservices_app_name + "~" + sfpkg_go_service_name + "')]"
        go_service_depends_on = "[concat('Microsoft.ServiceFabric/clusters/', parameters('clusterName'), '/applications/', '" + self.microservices_app_name + "')]"
        template_file_json["resources"] += [
            {
                "apiVersion": "2017-07-01-preview",
                "type": "Microsoft.ServiceFabric/clusters/applications/services",
                "name": go_service_name,
                "location": "[variables('location')]",
                "dependsOn": [
                    go_service_depends_on
                ],
                "properties": {
                    "provisioningState": "Default",
                    "serviceKind": "Stateless",
                    "serviceTypeName": sfpkg_go_service_type,
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
                    "serviceKind": "Stateful",
                    "serviceTypeName": sfpkg_java_service_type,
                    "targetReplicaSetSize": "3",
                    "minReplicaSetSize": "2",
                    "replicaRestartWaitDuration": "00:01:00.0",
                    "quorumLossWaitDuration": "00:02:00.0",
                    "standByReplicaKeepDuration": "00:00:30.0",
                    "partitionDescription": {
                        "partitionScheme": "UniformInt64Range",
                        "count": "5",
                        "lowKey": "1",
                        "highKey": "5"
                    },
                    "hasPersistedState": "true",
                    "correlationScheme": [],
                    "serviceLoadMetrics": [],
                    "servicePlacementPolicies": [],
                    "defaultMoveCost": "Low"
                }
            }
        ]

        # Update Template File
        template_file = open(self.template_file, 'w')
        json.dump(template_file_json, template_file)
        template_file.close()

    def enable_host_msi(self):
        # Update template to enable host MSi and apply policies
        print("Enable Host MSI")

    def set_msi_permissions(self):
        # grant AAD permissions to MSI for resource such as Cosmos DB
        print("Apply Permissions to Resource for MSI")

def main():
    demo_start = datetime.now()
    # Intialize RM Client
    rmc = ResourceManagerClient()
    # Declare Secret Parameter Values
    rmc.declare_secret_parameter_values()
    # Build Demo Microservices - For production use CI
    rmc.go_service_build()
    #rmc.java_service_build()
    # Configure Pre-Package Demo Dependency's
    #rmc.enable_host_msi()
    #rmc.set_msi_permissions()
    rmc.microservices_cosmos_db_creation()
    # Package Demo Microservices
    rmc.go_service_sfpkg_declaration()
    #rmc.java_service_sfpkg_declaration()
    rmc.microservices_app_resource_declaration()
    rmc.microservices_app_sfpkg_staging()
    # Deploy Demo Microservices
    rmc.validate_declaration()
    rmc.deploy_resources()
    print("Deployed Modern Microservices solution on SF Cluster Duration: " + str(datetime.now() - demo_start))
    # Operate Demo Microservices
    rmc.setup_cluster_client()

if __name__ == '__main__':
    main()
