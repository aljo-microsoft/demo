__author__ = "Alexander Johnson"
__email__ = "aljo-microsoft@github.com"
__status__ = "Development"

from datetime import datetime
import xml.etree.ElementTree
import json
from pathlib import Path
from subprocess import PIPE
from subprocess import Popen
import sys
import zipfile
import requests

class ServiceFabricResourceDeclaration:
    # Microservice development Best Practice in Azure, is Reliable Service Fabric Applications,
    # that leverage Azure Resource Manager API. Initialization of a deployment includes authoring
    # a declarative model in JSON format; that represents your goal state. As a demostration this
    # will succeed at provisioning it's goals state that, and can be built upon for deploying your
    # Application.
    #
    # A vital component of success in delivering your SLA/O's will require you to make decisions.
    # E.G. may include using a x509 certificates issued by an accessible Certificate Authority.
    #
    # This was tested September 19 2018 using Azure Cloud Shell.
    #
    # Arguments take precedence over declared values.
    def __init__(
        self,
        subscription='eec8e14e-b47d-40d9-8bd9-23ff5c381b40',
        template_uri='https://raw.githubusercontent.com/Microsoft/service-fabric-scripts-and-templates/master/templates/cluster-tutorial/vnet-linuxcluster.json',
        parameters_uri='https://raw.githubusercontent.com/Microsoft/service-fabric-scripts-and-templates/master/templates/cluster-tutorial/vnet-linuxcluster.parameters.json',
        template_file='AzureDeploy.json',
        parameters_file='AzureDeploy.Parameters.json',
        deployment_resource_group='bestpracticedeploymentresourceggroup',
        keyvault_resource_group='bestpracticekeyvaultresourcegroup',
        keyvault_name='bestpracticekeyvaultname',
        cluster_name='bestpracticecluster',
        admin_user_name='sudo',
        admin_password='Password#1234',
        location='westus',
        certificate_name='x509certificatename',
        certificate_thumbprint='GEN-CUSTOM-DOMAIN-SSLCERT-THUMBPRINT',
        source_vault_value='GEN-KEYVAULT-RESOURCE-ID',
        certificate_url_value='GEN-KEYVAULT-SSL-SECRET-URI',
        user_email='aljo-microsoft@github.com',
        poa_file_name='POA_v2.0.2.sfpkg',
        storage_account_name='bestpracticesstorage',
        container_name='bestpracticescontainer'):

	# Set Parameters
        self.subscription = subscription
        self.parameters_uri = parameters_uri
        self.template_uri = template_uri
        self.template_file = template_file
        self.parameters_file = parameters_file
        self.deployment_resource_group = deployment_resource_group
        self.keyvault_resource_group = keyvault_resource_group
        self.keyvault_name = keyvault_name
        self.cluster_name = cluster_name
        self.admin_user_name = admin_user_name
        self.admin_password = admin_password
        self.location = location
        self.dns_name = self.cluster_name + "." + self.location + ".cloudapp.azure.com"
        self.certificate_name = certificate_name
        self.certificate_file_name = certificate_name + ".pem"
        self.certificate_thumbprint = certificate_thumbprint
        self.source_vault_value = source_vault_value
        self.certificate_url_value = certificate_url_value
        self.user_email = user_email
        self.parameters_file_arg = "@" + self.parameters_file
        self.poa_file_name = poa_file_name
        self.storage_account_name = storage_account_name
        self.container_name = container_name

        # Az CLI Client
        account_set_process = Popen(["az", "account", "set", "--subscription", self.subscription], stdout=PIPE, stderr=PIPE)

        stdout, stderr = account_set_process.communicate()

        if account_set_process.wait() == 0:
            print("Account Set to Deployment Subscription")
        else:
            sys.exit(stderr)

        # Get Parameters
        if Path(self.parameters_file).exists():
            print("Using local Parameter File")
            parameters_file_json = json.load(open(self.parameters_file, 'r'))
        else:
            print("Using Tutorial Parameters File")
            parameters = requests.get(self.parameters_uri)
            parameters_bytes = parameters.content
            parameters_file_json = json.loads(parameters_bytes.decode("utf-8"))

        # Keyvault Cluster Certificate Exist or Create
        if self.source_vault_value.find('/subscriptions/') >= 0 and len(self.certificate_thumbprint) > 36 and self.certificate_url_value.find('vault.azure.net') != -1:
            # Use Keyvault Certificate Arguments for resource Validation
            print('Validating Keyvault Certificate Deployment Arguments')
        else:
            self.source_vault_value = parameters_file_json['parameters']['sourceVaultValue']['value']
            self.certificate_thumbprint = parameters_file_json['parameters']['certificateThumbprint']['value']
            self.certificate_url_value = parameters_file_json['parameters']['certificateUrlValue']['value']

        if self.source_vault_value.find("/subscriptions/") >= 0 and len(self.certificate_thumbprint) > 36 and self.certificate_url_value.find("vault.azure.net") >= 0:
            # Use Parameters File Keyvault Certificate Declarations for resource Validation
            print('Validating Keyvault Certificate Parameters File Declarations')
        else:
            # Create KeyVault
            print('Creating Deployment Keyvault Self Signed Certificate')
            keyvault_group_create_process = Popen(["az", "group", "create", "--name", self.keyvault_resource_group, "--location", self.location], stdout=PIPE, stderr=PIPE)

            stdout, stderr = keyvault_group_create_process.communicate()

            if keyvault_group_create_process.wait() == 0:
                print("Resource Group for KeyVault Created")
            else:
                sys.exit(stderr)

            keyvault_create_process = Popen(["az", "keyvault", "create", "--name", self.keyvault_name, "--resource-group", self.keyvault_resource_group, "--enabled-for-deployment", "true"], stdout=PIPE, stderr=PIPE)

            stdout, stderr = keyvault_create_process.communicate()

            if keyvault_create_process.wait() == 0:
                print("Keyvault Resource Created")
            else:
                sys.exit(stderr)

            # Keyvault DNS Population Takes 10 Secs
            keyvault_show_process = Popen(["az", "keyvault", "show", "-n", self.keyvault_name, "-g", self.keyvault_resource_group], stdout=PIPE, stderr=PIPE)

            stdout, stderr = keyvault_show_process.communicate()

            if keyvault_show_process.wait() == 0:
                print("Keyvault DNS has populated")
            else:
                sys.exit(stderr)

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

            stdout, stderr = certificate_create_process.communicate()

            if certificate_create_process.wait() == 0:
                print("Certificate Created")
            else:
                sys.exit(stderr)

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
            validate_source_vault = Popen(["az", "resource", "show", "--ids", self.source_vault_value], stdout=PIPE, stderr=PIPE)

            stdout, stderr = validate_source_vault.communicate()

            if validate_source_vault.wait() == 0:
                print("Source Vault Resource is Valid within subscription context")
            else:
                sys.exit(stderr)

            # Validate KeyVault Certificate
            # Certificate URL
            self.keyvault_name = self.certificate_url_value.rsplit("//", 1)[1].rsplit(".vault.", 1)[0]
            self.certificate_name = self.certificate_url_value.rsplit("//", 1)[1].rsplit(".vault.", 1)[1].rsplit("/", 3)[2]

            cert_url_validate_process = Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "sid", "-o", "tsv"], stdout=PIPE, stderr=PIPE)

            stdout, stderr = cert_url_validate_process.communicate()

            if cert_url_validate_process.wait() == 0 and stdout.decode("utf-8").replace('\n', '') == self.certificate_url_value:
                print("Certificate SID URL is valid within subscription context")
            else:
                sys.exit(stderr)

            # Certificate Thumbprint
            cert_thumbprint_validate_process = Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "x509ThumbprintHex", "-o", "tsv"], stdout=PIPE, stderr=PIPE)

            stdout, stderr = cert_thumbprint_validate_process.communicate()

            if cert_thumbprint_validate_process.wait() == 0 and stdout.decode("utf-8").replace('\n', '') == self.certificate_thumbprint:
                print("Certificate Thumbprint is valid within subscription context")
            else:
                print(stderr)
                sys.exit("Certificate Thumbprint is invalid within subscription context")

            # Write Declarative Parameters File
            parameters_file_json['parameters']['sourceVaultValue']['value'] = self.source_vault_value
            parameters_file_json['parameters']['certificateThumbprint']['value'] = self.certificate_thumbprint
            parameters_file_json['parameters']['certificateUrlValue']['value'] = self.certificate_url_value
            parameters_file_json['parameters']['clusterName']['value'] = self.cluster_name
            parameters_file_json['parameters']['adminUserName']['value'] = self.admin_user_name
            parameters_file_json['parameters']['adminPassword']['value'] = self.admin_password
            parameters_file_json['parameters']['location']['value'] = self.location

            json.dump(parameters_file_json, open(self.parameters_file, 'w'))

            # Exists or Create Deployment Group - needed for validation
            deployment_group_exists_process = Popen(["az", "group", "exists", "--name", self.deployment_resource_group], stdout=PIPE, stderr=PIPE)

            stdout, stderr = deployment_group_exists_process.communicate()

            if deployment_group_exists_process.wait() == 0 and stdout.decode('utf-8').replace('\n', '') == 'true':
                print("Deployment Group Exists")
                # TODO: Validate Group Location
            else:
                deployment_group_create_process = Popen(["az", "group", "create", "--location", self.location, "--name", self.deployment_resource_group], stdout=PIPE, stderr=PIPE)

                stdout, stderr = deployment_group_create_process.communicate()

                if deployment_group_create_process.wait() == 0:
                    print("Deployment Group Created")
                else:
                    sys.exit(stderr)

            # Get Template
            if Path(self.template_file).exists():
                print("Using local template File Found")
            else:
                print("Using Tutorial Template File")
                template = requests.get(template_uri)
                template_bytes = template.content
                template_file_json = json.loads(template_bytes.decode("utf-8"))
                template_file = open(self.template_file, 'x')
                json.dump(template_file_json, template_file)
                template_file.close()

    def validateDeclaration(self):
        # Validate Deployment Declaration
        print("Validating Deployment Declaration")

        deployment_validation_process = Popen(["az", "group", "deployment", "validate", "--resource-group", self.deployment_resource_group, "--template-file", self.template_file, "--parameters", self.parameters_file_arg], stdout=PIPE, stderr=PIPE)

        stdout, stderr = deployment_validation_process.communicate()

        if deployment_validation_process.wait() == 0:
            print("Your Deployment Declaration is Valid Syntactically")
        else:
            print(stderr)
            print("Your Deployment Declaration is Invalid Syntactically")

    def deployResources(self):
        # Reduce LiveSite issues by deploying Azure Resources in a Declarative way as a group
        print("Deploying Resources")
        group_deployment_create_process = Popen(["az", "group", "deployment", "create", "-g", self.deployment_resource_group, "--template-file", self.template_file, "--parameters", self.parameters_file_arg], stdout=PIPE, stderr=PIPE)

        stdout, stderr = group_deployment_create_process.communicate()

        if group_deployment_create_process.wait() == 0:
            print("Resource Deployment Successful")
        else:
            print(stderr)

    def setupClusterClient(self):
        # Downloads client admin certificate
        # Convert to PEM format for linux compatibility
        print("Downloading Certificate file in base64 format")
        certificate_b64_file = self.certificate_name + "64.pem"
        download_cert_process = Popen(["az", "keyvault", "secret", "download", "--file", certificate_b64_file, "--encoding", "base64", "--name", self.certificate_name, "--vault-name", self.keyvault_name], stdout=PIPE, stderr=PIPE)

        stdout, stderr = download_cert_process.communicate()

        if download_cert_process.wait() == 0:
            print("Download of Certificate file in Base 64 Format Successful")
        else:
            print(stderr)

        print("Converting Base 64 Certificate File to PEM format")
        convert_cert_process = Popen(["openssl", "pkcs12", "-in", certificate_b64_file, "-out", self.certificate_file_name, "-nodes", "-passin", "pass:"], stdout=PIPE, stderr=PIPE)

        stdout, stderr = convert_cert_process.communicate()

        if convert_cert_process.wait() == 0:
            print("Convert of base64 file to PEM format successful")
        else:
            print(stderr)
            print("Converting base64 file to PEM format failed")

    def clusterConnectionValidation(self):
        endpoint = 'https://' + self.dns_name + ':19080'

        not_connected_to_cluster = True
        print("Waiting For Cluster Provisioning To Complete")
        while not_connected_to_cluster:

            cluster_connect_process = Popen(["sfctl", "cluster", "select", "--endpoint", endpoint, "--pem", self.certificate_file_name, "--no-verify"], stdout=PIPE, stderr=PIPE)

            stdout, stderr = cluster_connect_process.communicate()

            if cluster_connect_process.wait() == 0:
                not_connected_to_cluster = False
                print("Connected to Cluster")
            else:
                print("Unable to Connect to Deployed Cluster Resource... Trying again")
                cluster_connect_process.kill()

        cluster_health_process = Popen(["sfctl", "cluster", "health"], stdout=PIPE, stderr=PIPE)

        stdout, stderr = cluster_health_process.communicate()

        if cluster_health_process.wait() == 0:
            print("Securely Connected to Healthy Cluster")
        else:
            # Expect Warning Error message if using Self Signed Certificate
            print(stderr)

    def repairManagerDeclaration(self):
        # Update Template
        # Enable or Validate RepairManager
        print("Enable or Validate Repair Manager")
        template_file_json = json.load(open(self.template_file, 'r'))

        number_of_resource = len(template_file_json["resources"])

        for i in range(0, number_of_resource):
            if template_file_json["resources"][i]["type"] == "Microsoft.ServiceFabric/clusters":
                if (("addonFeatures" in template_file_json["resources"][i]["properties"]) and ("RepairManager" in template_file_json["resources"][i]["properties"]["addonFeatures"])):
                    print('RepairManager already declared in Template')
                elif "addonFeatures" in template_file_json["resources"][i]["properties"]:
                    print('RepairManager enabled as add-on feature in Template')
                    template_file_json["resources"][i]["properties"]["addonFeatures"] += ["RepairManager"]
                else:
                    print('Add-On Feature RepairManager declared in Template')
                    template_file_json["resources"][i]["properties"]["addonFeatures"] = ["RepairManager"]
        # Update Template File with Repair Manager
        template_file = open(self.template_file, 'w')
        json.dump(template_file_json, template_file)
        template_file.close()
        
    def patchOrchestrationApplicationDeclaration(self):
        # Deploying Applications as Resources is a best practice for Production.
        # To demonstrate this, this will deploy the Patch Orchestration Application.
        # Steps to be performed to achieve this are:
        # 1. Download POA SFPKG
        # 2. Create Storage Account
        # 3. Get the Connection String to Storage Account
        # 4. Create Storage Account Blob Container
        # 5. Upload File to Storage Account Blob Container
        # 6. Get public URL to File in Storage Account Blob
        # 7. Declare Application and Services as Resources in Template

        print("Updating Declaration with Patch Orchestration Application")
        poa_name = 'poa'

        # Download POA SFPKG
        poa_url = "https://aka.ms/POA/" + self.poa_file_name
        r = requests.get(poa_url)
        open(self.poa_file_name, 'wb').write(r.content)
        print(self.poa_file_name + " Downloaded")

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

        # Upload SFPKG to Blob Container
        upload_poa_process = Popen(["az", "storage", "blob", "upload", "--file", self.poa_file_name, "--name", poa_name, "--connection-string", connection_string, "--container-name", self.container_name], stdout=PIPE, stderr=PIPE)

        stdout, stderr = upload_poa_process.communicate()

        if upload_poa_process.wait() == 0:
            print("Uploaded POA PKG To Storage Account Blob Container")
        else:
            sys.exit(stderr)

        # Get URL for POA in Storage Account Blob Container
        url_blob_process = Popen(["az", "storage", "blob", "url", "--container-name", self.container_name, "--connection-string", connection_string, "--name", poa_name], stdout=PIPE, stderr=PIPE)

        stdout, stderr = url_blob_process.communicate()

        if url_blob_process.wait() == 0:
            poa_package_url = stdout.decode("utf-8").replace('\n', '').replace('"', '')
            print("Got URL for POA file in Storage Account Blob")
        else:
            sys.exit(stderr)

        # Update Template
        # Enable or Validate RepairManager
        print("Declaring POA in template")
        template_file_json = json.load(open(self.template_file, 'r'))

        # Declare Patch Orchestration Application and Services as resources
        # Unzip SFPKG and Get Properties
        poa_sfpkg = zipfile.ZipFile(self.poa_file_name, "r")
        poa_sfpkg.extractall(poa_name)
        application_manifest_path = poa_name + "/ApplicationManifest.xml"
        application_manifest = xml.etree.ElementTree.parse(application_manifest_path).getroot()
        sfpkg_application_type_version = application_manifest.attrib['ApplicationTypeVersion']
        sfpkg_application_type_name = application_manifest.attrib['ApplicationTypeName']

        for i in range(len(application_manifest)):
            if application_manifest[i].tag == '{http://schemas.microsoft.com/2011/01/fabric}DefaultServices':
                poa_services = application_manifest[i].getchildren()
                for j in range(len(poa_services)):
                    if poa_services[j].attrib['Name'].lower().find("coordinator") > -1:
                        sfpkg_coordinator_service_name = poa_services[j].attrib['Name']
                        sfpkg_coordinator_service_type = poa_services[j].getchildren()[0].attrib['ServiceTypeName']
                    elif poa_services[j].attrib['Name'].lower().find("nodeagent") > -1:
                        sfpkg_node_agent_service_name = poa_services[j].attrib['Name']
                        sfpkg_node_agent_service_type = poa_services[j].getchildren()[0].attrib['ServiceTypeName']
                    else:
                        sys.exit("couldn't find coordinator or nodeagent services properties in Application Manifest")

        # Declare POA ApplicationType
        application_type_name = "[concat(parameters('clusterName'), '/', '" + sfpkg_application_type_name + "')]"
        template_file_json["resources"] += [
            {
                "apiVersion": "2017-07-01-preview",
                "type": "Microsoft.ServiceFabric/clusters/applicationTypes",
                "name": application_type_name,
                "location": "[variables('location')]",
                "dependsOn": [],
                "properties": {
                    "provisioningState": "Default"
                }
            }
        ]
        # Declare POA ApplicationTypeVersion
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
                    "appPackageUrl": poa_package_url
                }
            }
        ]

        # Declare POA Application
        application_name = "[concat(parameters('clusterName'), '/', '" + poa_name + "')]"
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

        # Declare POA Services
        # Declare POA Coordinator Service
        coordinator_service_name = "[concat(parameters('clusterName'), '/', '" + poa_name + "', '/', '" + poa_name + "~" + sfpkg_coordinator_service_name + "')]"
        coordinator_service_depends_on = "[concat('Microsoft.ServiceFabric/clusters/', parameters('clusterName'), '/applications/', '" + poa_name + "')]"
        template_file_json["resources"] += [
            {
                "apiVersion": "2017-07-01-preview",
                "type": "Microsoft.ServiceFabric/clusters/applications/services",
                "name": coordinator_service_name,
                "location": "[variables('location')]",
                "dependsOn": [
                    coordinator_service_depends_on
                ],
                "properties": {
                    "provisioningState": "Default",
                    "serviceKind": "Stateless",
                    "serviceTypeName": sfpkg_coordinator_service_type,
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
        # Declare POA NodeAgent Service
        node_agent_service_name = "[concat(parameters('clusterName'), '/', '" + poa_name + "', '/', '" + poa_name + "~" + sfpkg_node_agent_service_name + "')]"
        node_agent_service_depends_on = "[concat('Microsoft.ServiceFabric/clusters/', parameters('clusterName'), '/applications/', '" + poa_name + "')]"
        template_file_json["resources"] += [
            {
                "apiVersion": "2017-07-01-preview",
                "type": "Microsoft.ServiceFabric/clusters/applications/services",
                "name": node_agent_service_name,
                "location": "[variables('location')]",
                "dependsOn": [
                    node_agent_service_depends_on
                ],
                "properties": {
                    "provisioningState": "Default",
                    "serviceKind": "Stateful",
                    "serviceTypeName": sfpkg_node_agent_service_type,
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
        # Update Template File with POA Application
        template_file = open(self.template_file, 'w')
        json.dump(template_file_json, template_file)
        template_file.close()

    def enableHostMSI(self):
        # Update template to enable host MSi and apply policies
        print("TODO: Enable Host MSI")

    def setMSIPermissions(self):
        # grant AAD permissions to MSI for resource such as Cosmos DB
        print("TODO: Apply Permissions to Resource for MSI")

def main():
    demo_start = datetime.now()

    resource_declaration = ServiceFabricResourceDeclaration()
    print("Resource Declaration Initilization Duration: " + str(datetime.now() - demo_start))

    resource_declaration.validateDeclaration()
    print("Resource Declaration Validation Duration: " + str(datetime.now() - demo_start))

    resource_declaration.deployResources()
    print("Deploy Resources Duration: " + str(datetime.now() - demo_start))

    resource_declaration.setupClusterClient()
    print("Client Setup Duration: " + str(datetime.now() - demo_start))

    resource_declaration.clusterConnectionValidation()
    print("Connected to cluster: " + str(datetime.now() - demo_start))

    resource_declaration.repairManagerDeclaration()
    print("Declared RepairManager as Add-on Feature: " + str(datetime.now() - demo_start))

    resource_declaration.deployResources()
    print("Updating Cluster Configuration to enable RepairManager Duration: " + str(datetime.now() - demo_start))

    # Validate What System Services Are Enabled: sfctl service list --application-id System
    # Validate RepairManager Enabled: sfctl service info --service-id System~RepairManagerService --application-id System
    resource_declaration.patchOrchestrationApplicationDeclaration()
    print("Declared Patch Orchestration Application as Azure Resource: " + str(datetime.now() - demo_start))

    resource_declaration.validateDeclaration()
    print("Resource Declaration Updated with POA Validation Duration: " + str(datetime.now() - demo_start))

    resource_declaration.deployResources()
    print("Deployed POA Resource Duration: " + str(datetime.now() - demo_start))

    #resourceDeclaration.enableHostMSI()
    #resourceDeclaration.setMSIPermissions()

if __name__ == '__main__':
    main()
