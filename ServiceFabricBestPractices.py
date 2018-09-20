__author__ = "Alexander Johnson"
__email__ = "aljo-microsoft@github.com"
__status__ = "Development"

""" This demostrates best practices for a Reliable microservice in Azure using the Service Fabric platform """

from subprocess import Popen
from subprocess import PIPE
import json
from pathlib import Path
import sys
from datetime import datetime
import requests
import time
import zipfile
import getpass
import xml.etree.ElementTree

class ServiceFabricResourceDeclaration:
	# Microservice development Best Practice in Azure, is Reliable Service Fabric Applications, 
	# that leverage Azure Resource Manager API. Initialization of a deployment includes authoring
	# a declarative model in JSON format; that represents your goal state. As a demostration this
	# will succeed at provisioning it's goals state that, and can be built upon for deploying your
	# Application.
	# 
	# A vital component of success in adoption to deliver your SLA/O's will require you to make decisions.
	# E.G. may include provisioning an x509 certificates issued by an accessible Certificate Authority.
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
		user_email='aljo-microsoft@github.com'
		):

		# Set Parameters
		self.subscription = subscription
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
		
		# Az CLI Client
		accountSetProcess = Popen(["az", "account", "set", "--subscription", self.subscription], stdout=PIPE, stderr=PIPE)
		
		stdout, stderr = accountSetProcess.communicate()
		
		if accountSetProcess.wait() == 0:
			print("Account Set to Deployment Subscription")
		else:
			sys.exit(stderr)
		
		# Get Parameters
		if (Path(self.parameters_file).exists()):
			print("Using local Parameter File")
			
			parametersFileJson = json.load(open(self.parameters_file, 'r'))
		else:
			print("Using Tutorial Parameters File")
			parameters = requests.get(self.parameters_uri)
			parametersBytes = parameters.content
			parametersFileJson = json.loads(parametersBytes.decode("utf-8"))
			
		# Keyvault Cluster Certificate Exist or Create
		if self.source_vault_value.find('/subscriptions/') >= 0 and len(self.certificate_thumbprint) > 36 and self.certificate_url_value.find('vault.azure.net') != -1:
			# Use Keyvault Certificate Arguments for resource Validation
			print('Validating Keyvault Certificate Deployment Arguments')
		else:
			self.source_vault_value = parametersFileJson['parameters']['sourceVaultValue']['value']
			self.certificate_thumbprint = parametersFileJson['parameters']['certificateThumbprint']['value']
			self.certificate_url_value = parametersFileJson['parameters']['certificateUrlValue']['value']

			if self.source_vault_value.find("/subscriptions/") >= 0 and len(self.certificate_thumbprint) > 36 and self.certificate_url_value.find("vault.azure.net") >= 0:
				# Use Parameters File Keyvault Certificate Declarations for resource Validation
				print('Validating Keyvault Certificate Parameters File Declarations')
			else:
				# Create KeyVault
				print('Creating Deployment Keyvault Self Signed Certificate')
				keyvaultGroupCreateProcess = Popen(["az", "group", "create", "--name", self.keyvault_resource_group, "--location", self.location], stdout=PIPE, stderr=PIPE)
				
				stdout, stderr = keyvaultGroupCreateProcess.communicate()
				
				if keyvaultGroupCreateProcess.wait() == 0:
					print("Resource Group for KeyVault Created")
				else:
					sys.exit(stderr)
				
				keyvaultCreateProcess = Popen(["az", "keyvault", "create", "--name", self.keyvault_name, "--resource-group", self.keyvault_resource_group, "--enabled-for-deployment", "true"], stdout=PIPE, stderr=PIPE)
				
				stdout, stderr = keyvaultCreateProcess.communicate()
				
				if keyvaultCreateProcess.wait() == 0:
					print("Keyvault Resource Created")
				else:
					sys.exit(stderr)
				
				# Keyvault DNS Population Takes 10 Secs
				keyvaultShowProcess = Popen(["az", "keyvault", "show", "-n", self.keyvault_name, "-g", self.keyvault_resource_group], stdout=PIPE, stderr=PIPE)
				
				stdout, stderr = keyvaultShowProcess.communicate()
				
				if keyvaultShowProcess.wait() == 0:
					print("Keyvault DNS has populated")
				else:
					sys.exit(stderr)

				# Create Self Signed Certificate
				# Get Default Policy
				defaultPolicyProcess = Popen(["az", "keyvault", "certificate", "get-default-policy"], stdout=PIPE, stderr=PIPE)
					
				stdout, stderr = defaultPolicyProcess.communicate()
					
				if defaultPolicyProcess.wait() == 0:
					defaultPolicyJson = json.loads(stdout.decode("utf-8"))
				else:
					sys.exit(stderr)

				# Set Subject Name to FQDN
				# Browsers won't trust certificates with subject names that don't match FQDN
				defaultPolicyJson['x509CertificateProperties']['subject'] = "CN=" + self.dns_name
				defaultPolicyJson['x509CertificateProperties']['sans'] = {'dns_names': [self.dns_name], 'emails': [self.user_email], 'upns': [self.user_email]} 
				policyFileName = "policy.json"
				json.dump(defaultPolicyJson, open(policyFileName, 'w+'))
				policyFileArgFormat = "@" + policyFileName

				certificateCreateProcess = Popen(["az", "keyvault", "certificate", "create", "--vault-name", self.keyvault_name, "-n", self.certificate_name, "-p", policyFileArgFormat], stdout=PIPE, stderr=PIPE)

				stdout, stderr = certificateCreateProcess.communicate()

				if certificateCreateProcess.wait() == 0:
					print(stdout)
				else:
					sys.exit(stderr)
					
				# Get Keyvault Self Signed Certificate Properties
				# Get resource Id
				resourceIdProcess = Popen(["az", "keyvault", "show", "--name", self.keyvault_name, "--query", "id", "-o", "tsv"], stdout=PIPE, stderr=PIPE)

				stdout, stderr = resourceIdProcess.communicate()

				if resourceIdProcess.wait() == 0:
					self.source_vault_value = stdout.decode("utf-8").replace('\n', '')
				else:
					sys.exit(stderr)

				# Get Certificate Url
				urlProcess = Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "sid", "-o", "tsv"], stdout=PIPE, stderr=PIPE)

				stdout, stderr = urlProcess.communicate()

				if urlProcess.wait() == 0:
					self.certificate_url_value = stdout.decode("utf-8").replace('\n', '')
				else:
					sys.exit(stderr)

				# Get Certificate Thumbprint
				thumbprintProcess = Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "x509ThumbprintHex", "-o", "tsv"], stdout=PIPE, stderr=PIPE)

				stdout, stderr = thumbprintProcess.communicate()
				
				if thumbprintProcess.wait() == 0:
					self.certificate_thumbprint = stdout.decode("utf-8").replace('\n', '')
				else:
					sys.exit(stderr)
			
		# Validate KeyVault Resource Availability
		validateSourceVault = Popen(["az", "resource", "show", "--ids", self.source_vault_value], stdout=PIPE, stderr=PIPE)

		stdout, stderr = validateSourceVault.communicate()

		if validateSourceVault.wait() == 0:
			print("Source Vault Resource is Valid within subscription context")
		else:
			sys.exit(stderr)

		# Validate KeyVault Certificate
		# Certificate URL
		self.keyvault_name = self.certificate_url_value.rsplit("//", 1)[1].rsplit(".vault.", 1)[0]
		self.certificate_name = self.certificate_url_value.rsplit("//", 1)[1].rsplit(".vault.", 1)[1].rsplit("/", 3)[2]			 
			
		certUrlValidateProcess = Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "sid", "-o", "tsv"], stdout=PIPE, stderr=PIPE)

		stdout, stderr = certUrlValidateProcess.communicate()

		if certUrlValidateProcess.wait() == 0 and stdout.decode("utf-8").replace('\n', '') == self.certificate_url_value:
			print("Certificate SID URL is valid within subscription context")
		else:
			sys.exit(stderr)
 
		# Certificate Thumbprint
		certThumbprintValidateProcess = Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "x509ThumbprintHex", "-o", "tsv"], stdout=PIPE, stderr=PIPE)

		stdout, stderr = certThumbprintValidateProcess.communicate()

		if certThumbprintValidateProcess.wait() == 0 and stdout.decode("utf-8").replace('\n', '') == self.certificate_thumbprint:
			print("Certificate Thumbprint is valid within subscription context")
		else:
			print(stderr)
			sys.exit("Certificate Thumbprint is invalid within subscription context")

		# Write Declarative Parameters File
		parametersFileJson['parameters']['sourceVaultValue']['value'] = self.source_vault_value
		parametersFileJson['parameters']['certificateThumbprint']['value'] = self.certificate_thumbprint
		parametersFileJson['parameters']['certificateUrlValue']['value'] = self.certificate_url_value
		parametersFileJson['parameters']['clusterName']['value'] = self.cluster_name
		parametersFileJson['parameters']['adminUserName']['value'] = self.admin_user_name
		parametersFileJson['parameters']['adminPassword']['value'] = self.admin_password
		parametersFileJson['parameters']['location']['value'] = self.location

		json.dump(parametersFileJson, open(self.parameters_file, 'w'))

		# Exists or Create Deployment Group - needed for validation
		deploymentGroupExistsProcess = Popen(["az", "group", "exists", "--name", self.deployment_resource_group], stdout=PIPE, stderr=PIPE)

		stdout, stderr = deploymentGroupExistsProcess.communicate()

		if deploymentGroupExistsProcess.wait() == 0 and stdout.decode('utf-8').replace('\n', '') == 'true':
			print("Deployment Group Exists")
			# TODO: Validate Group Location
		else:
			deploymentGroupCreateProcess = Popen(["az", "group", "create", "--location", self.location, "--name", self.deployment_resource_group], stdout=PIPE, stderr=PIPE)
				
			stdout, stderr = deploymentGroupCreateProcess.communicate()

			if deploymentGroupCreateProcess.wait() == 0:
				print("Deployment Group Created")
			else:
				sys.exit(stderr)

		# Get Template
		if (Path(self.template_file).exists()):
			print("Using local template File Found")
		else:
			print("Using Tutorial Template File")
			template = requests.get(template_uri)
			templateBytes = template.content
			templateFileJson = json.loads(templateBytes.decode("utf-8"))
			
			templateFile = open(self.template_file, 'x')
			json.dump(templateFileJson, templateFile)
			templateFile.close()

		# Validate Deployment Declaration
		print("Validating Deployment Declaration")

		deploymentValidationProcess = Popen(["az", "group", "deployment", "validate", "--resource-group", self.deployment_resource_group, "--template-file", self.template_file, "--parameters", self.parameters_file_arg], stdout=PIPE, stderr=PIPE)

		stdout, stderr = deploymentValidationProcess.communicate()

		if deploymentValidationProcess.wait() == 0:
			print("Your Deployment Declaration is Valid Syntactically")
		else:
			print(stderr)
			print("Your Deployment Declaration is Invalid Syntactically")
		
	def deployResources(self):
		# Reduce LiveSite issues by deploying Azure Resources in a Declarative way as a group
		print("Deploying Resources")
		
		groupDeploymentCreateProcess = Popen(["az", "group", "deployment", "create", "-g", self.deployment_resource_group, "--template-file", self.template_file, "--parameters", self.parameters_file_arg], stdout=PIPE, stderr=PIPE)

		stdout, stderr = groupDeploymentCreateProcess.communicate()

		if groupDeploymentCreateProcess.wait() == 0:
			print("Resource Deployment Successful")
		else:
			print(stderr)

	def setupClusterClient(self):
		# Downloads client admin certificate
		# Convert to PEM format for linux compatibility
		print("Downloading Certificate file in base64 format")
		certificateB64File = self.certificate_name + "64.pem"
		downloadCertProcess = Popen(["az", "keyvault", "secret", "download", "--file", certificateB64File, "--encoding", "base64", "--name", self.certificate_name, "--vault-name", self.keyvault_name], stdout=PIPE, stderr=PIPE)

		stdout, stderr = downloadCertProcess.communicate()

		if downloadCertProcess.wait() == 0:
			print("Download of Certificate file in Base 64 Format Successful")
		else:
			print(stderr)
		
		print("Converting Base 64 Certificate File to PEM format")
		convertCertProcess = Popen(["openssl", "pkcs12", "-in", certificateB64File, "-out", self.certificate_file_name, "-nodes", "-passin", "pass:"], stdout=PIPE, stderr=PIPE)
		
		stdout, stderr = convertCertProcess.communicate()
		
		if convertCertProcess.wait() == 0:
			print("Convert of base64 file to PEM format successful")
		else:
			print(stderr)
			print("Converting base64 file to PEM format failed")

	def clusterConnectionValidation(self):
		endpoint = 'https://' + self.dns_name + ':19080'
		
		notConnectedToCluster = True
		
		print("")
		while notConnectedToCluster:
			
			clusterConnectProcess = Popen(["sfctl", "cluster", "select", "--endpoint", endpoint, "--pem", self.certificate_file_name, "--no-verify"], stdout=PIPE, stderr=PIPE)
			
			stdout, stderr = clusterConnectProcess.communicate()
			
			if clusterConnectProcess.wait() == 0:
				notConnectedToCluster = False
				print("Connected to Cluster")
			else:
				print("Unable to Connect to Deployed Cluster Resource... Waiting 15 secs to try again")
				time.sleep(15)
				
		clusterHealthProcess = Popen(["sfctl", "cluster", "health"], stdout = PIPE, stderr = PIPE)
		
		stdout, stderr = clusterHealthProcess.communicate()
		
		if clusterHealthProcess.wait() == 0:
			print("Provisioned Healthy Cluster")
		else:
			print(stderr)
			sys.exit("Cluster Provisioning Failed")
	
	def patchOrchestrationApplicationDeclaration(self):
		# Deploying Applications as Resources is a best practice for Production.
		# To demonstrate this, this will deploy the Patch Orchestration Application.
		# Steps to be performed to achieve this are:
		# 1. Download POA SFPKG
		# 2. Create Storage Account
		# 3. Get the Connection String to Storage Account
		# 4. Create Storage Account File Share
		# 5. Upload File to Storage Account Share
		# 6. Get secured URL to File in Storage Account Share
		# 8. Declare Application and Services as Resources in Template
		# 9. Declarative Resource Deployment
		
		print("Updating Declaration with Patch Orchestration Application")
		poa_name = 'poa'
		self.poa_file_name = "POA_v2.0.2.sfpkg"
		self.storage_account_name = 'bestpracticesstorage'
		self.share_name = "bestpracticesshare"
		
		# Download POA SFPKG
		poaUrl = "https://aka.ms/POA/" + self.poa_file_name
		r = requests.get(poaUrl)
		open(self.poa_file_name, 'wb').write(r.content)
		print(self.poa_file_name + " Downloaded")
		
		# Create Storate
		createStorageProcess = Popen(["az", "storage", "account", "create", "-n", self.storage_account_name, "-g", self.deployment_resource_group, "-l", self.location, "--sku", "Standard_LRS"], stdout=PIPE, stderr=PIPE)
			
		stdout, stderr = createStorageProcess.communicate()
			
		if createStorageProcess.wait() == 0:
			print("Storage Account Created")
		else:
			sys.exit(stderr)
		
		# Get Connection String
		connectionStringProcess = Popen(["az", "storage", "account", "show-connection-string", "-g", self.deployment_resource_group, "-n", self.storage_account_name], stdout=PIPE, stderr=PIPE)
			
		stdout, stderr = connectionStringProcess.communicate()
			
		if connectionStringProcess.wait() == 0:
			connectionString = str(json.loads(stdout.decode("utf-8"))['connectionString'])
			print("Got Storage Connection String")
		else:
			sys.exit(stderr)

		# Create storage account file share
		createShareProcess = Popen(["az", "storage", "share", "create", "--name", self.share_name, "--connection-string", connectionString], stdout=PIPE, stderr=PIPE)
			
		stdout, stderr = createShareProcess.communicate()
			
		if createShareProcess.wait() == 0:
			print("Created Share")
		else:
			sys.exit(stderr)
		
		# Upload File To Share
		uploadFileProcess = Popen(["az", "storage", "file", "upload", "-s", self.share_name, "--source", self.poa_file_name, "--connection-string", connectionString], stdout=PIPE, stderr=PIPE)
			
		stdout, stderr = uploadFileProcess.communicate()
			
		if uploadFileProcess.wait() == 0:
			print("Uploaded POA PKG To Storage Account")
		else:
			sys.exit(stderr)
		
		# Get URL for POA in Storage Account Share
		urlShareProcess = Popen(["az", "storage", "file", "url", "--path", self.poa_file_name, "--share-name", self.share_name, "--connection-string", connectionString], stdout=PIPE, stderr=PIPE)
			
		stdout, stderr = urlShareProcess.communicate()
			
		if urlShareProcess.wait() == 0:
			poaPackageUrl = stdout.decode("utf-8")
			print("Got URL for POA file in Storage Account Share")
		else:
			sys.exit(stderr)
		
		# Update Template
		# Enable or Validate RepairManager
		print("Enable or Validate Repair Manager")
		templateFileJson = json.load(open(self.template_file, 'r'))
		
		numberOfResource = len(templateFileJson["resources"])
	
		for i in range(0, numberOfResource):
			if (templateFileJson["resources"][i]["type"] == "Microsoft.ServiceFabric/clusters"):
				if (("addonFeatures" in templateFileJson["resources"][i]["properties"]) and ("RepairManager" in templateFileJson["resources"][i]["properties"]["addonFeatures"])):
					print('RepairManager already declared in Template')
				elif ("addonFeatures" in templateFileJson["resources"][i]["properties"]):
					print('RepairManager enabled as add-on feature in Template')
					templateFileJson["resources"][i]["properties"]["addonFeatures"] += ["RepairManager"]
				else:
					print('Add-On Feature RepairManager declared in Template')
					templateFileJson["resources"][i]["properties"]["addonFeatures"] = ["RepairManager"]
		
		# Declare Patch Orchestration Application and Services as resources
		# Unzip SFPKG and Get Properties
		poaSfpkg = zipfile.ZipFile(self.poa_file_name, "r")
		poaSfpkg.extractall(poa_name)
		applicationManifestPath = poa_name + "/ApplicationManifest.xml"
									       
		applicationManifest = xml.etree.ElementTree.parse(applicationManifestPath).getroot()							       
									 
		sfpkgApplicationTypeVersion = applicationManifest.attrib['ApplicationTypeVersion']
		sfpkgApplicationTypeName = applicationManifest.attrib['ApplicationTypeName']	       
		sfpkgApplicationName = poa_name
		
		for i in range(len(applicationManifest)):
			if (applicationManifest[i].tag == '{http://schemas.microsoft.com/2011/01/fabric}DefaultServices'):
				poaServices = applicationManifest[i].getchildren()
				
				for j in range(len(poaServices)):
					if (poaServices[j].attrib['Name'].lower().find("coordinator") > -1):
						sfpkgCoordinatorServiceName = poaServices[j].attrib['Name']
						sfpkgCoordinatorServiceType = poaServices[j].getchildren()[0].attrib['ServiceTypeName']
					elif (poaServices[j].attrib['Name'].lower().contains("nodeagent") > -1):
						sfpkgNodeAgentServiceName = poaServices[j].attrib['Name']
						sfpkgNodeAgentServiceType = poaServices[j].getchildren()[0].attrib['ServiceTypeName']
					else:
						sys.exit("couldn't find coordinator or nodeagent services properties in Application Manifest")
		
		# Declare POA ApplicationType
		applicationTypeName = "[concat(parameters('clusterName'), '/', '" + sfpkgApplicationTypeName + "')]"
		templateFileJson["resources"] += {"apiVersion": "2017-07-01-preview",
     						  "type": "Microsoft.ServiceFabric/clusters/applicationTypes",
     						  "name": applicationTypeName,
     						  "location": "[variables('location')]",
     					          "dependsOn": {},
     					          "properties": {
       						     "provisioningState": "Default"
						  }
						  }
   		
		# Declare POA ApplicationTypeVersion
		applicationTypeVersion = "[concat(parameters('clusterName'), '/', '" + sfpkgApplicationTypeName + "', '/', '" + sfpkgApplicationTypeVersion + "')]"
		applicationTypeVersiondependsOn = "[concat('Microsoft.ServiceFabric/clusters/', parameters('clusterName'), '/applicationTypes/', '" + sfpkgApplicationTypeName + "')]"					       
		templateFileJson["resources"] += {"apiVersion": "2017-07-01-preview",
     						  "type": "Microsoft.ServiceFabric/clusters/applicationTypes/versions",
     						  "name": applicationTypeVersion,
     						  "location": "[variables('location')]",
     						  "dependsOn": {
 							applicationTypeVersiondependsOn
						  },
     						  "properties": {
      						  "provisioningState": "Default",
       						  "appPackageUrl": poaPackageUrl
						  }
						  }
		# Declare POA Application
		applicationName = "[concat(parameters('clusterName'), '/', '" + sfpkgApplicationName + "')]"
		applicationNameDependendsOn = "[concat('Microsoft.ServiceFabric/clusters/', parameters('clusterName'), '/applicationTypes/', '" + sfpkgApplicationTypeName + "', '/versions/', '" + sfpkgApplicationTypeVersion + "')]"
		templateFileJson["resources"] += {"apiVersion": "2017-07-01-preview",
						  "type": "Microsoft.ServiceFabric/clusters/applications",
						  "name": applicationName,
						  "location": "[variables('location')]",
						  "dependsOn": {
							applicationNameDependendsOn
						  },
						  "properties": {
							"provisioningState": "Default",
							"typeName": sfpkgApplicationTypeName,
							"typeVersion": sfpkgApplicationTypeVersion,
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
									       
		# Declare POA Services
		# Declare POA Coordinator Service
		coordinatorServiceName = "[concat(parameters('clusterName'), '/', '" + sfpkgApplicationName + "', '/', '" + sfpkgCoordinatorServiceName + "')]"						       
		coordinatorServiceDependsOn = "[concat('Microsoft.ServiceFabric/clusters/', parameters('clusterName'), '/applications/', '" + sfpkgApplicationName + "')]"
		templateFileJson["resources"] += {"apiVersion": "2017-07-01-preview",
						  "type": "Microsoft.ServiceFabric/clusters/applications/services",
						  "name": coordinatorServiceName ,
						  "location": "[variables('location')]",
						  "dependsOn": {
							coordinatorServiceDependsOn
						  },
						  "properties": {
							"provisioningState": "Default",
							"serviceKind": "Stateless",
							"serviceTypeName": sfpkgCoordinatorServiceType,
							"instanceCount": "-1",
							"partitionDescription": {
								"partitionScheme": "Singleton"
							},
							"correlationScheme": {},
							"serviceLoadMetrics": {},
							"servicePlacementPolicies": {}
						 }
						}
     
     		# Declare POA NodeAgent Service
		nodeAgentServiceName = "[concat(parameters('clusterName'), '/', '" + sfpkgApplicationName + "', '/', '" + sfpkgNodeAgentServiceName + "')]"
		nodeAgentServiceDependsOn =  "[concat('Microsoft.ServiceFabric/clusters/', parameters('clusterName'), '/applications/', '" + sfpkgApplicationName + "')]"
		templateFileJson["resources"] += {"apiVersion": "2017-07-01-preview",
						  "type": "Microsoft.ServiceFabric/clusters/applications/services",
						  "name": nodeAgentServiceName,
						  "location": "[variables('location')]",
						  "dependsOn": {
							nodeAgentServiceDependsOn
						  },
						  "properties": {
						  "provisioningState": "Default",
						  "serviceKind": "Stateful",
						  "serviceTypeName": sfpkgNodeAgentServiceName,
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
						  "correlationScheme": {},
						  "serviceLoadMetrics": {},
						  "servicePlacementPolicies": {},
						  "defaultMoveCost": "Low"
						  }
						 }
						  
		# Write New Template File with POA Application
		poaTemplateFileName = "AzureDeployPOA.json"
		poaTemplateFile = open(poaTemplateFileName, 'x')
		json.dump(templateFileJson, poaTemplateFile)
		poaTemplateFile.close()
						  
		print("Validating POA Deployment Declaration")

		deploymentValidationProcess = Popen(["az", "group", "deployment", "validate", "--resource-group", self.deployment_resource_group, "--template-file", poaTemplateFileName, "--parameters", self.parameters_file_arg], stdout=PIPE, stderr=PIPE)

		stdout, stderr = deploymentValidationProcess.communicate()

		if deploymentValidationProcess.wait() == 0:
			print("Your Deployment Declaration is Valid Syntactically")
		else:
			print(stderr)
			print("Your Deployment Declaration is Invalid Syntactically")

	def enableHostMSI(self):
		# Update template to enable host MSi and apply policies
		print("Enabling Host MIS")

	def setMSIPermissions(self):
		# grant AAD permissions to MSI for resource such as Cosmos DB
		print("Applying Permissions to Resource for MSI")

def main():
	demoStart = datetime.now()
	
	resourceDeclaration = ServiceFabricResourceDeclaration()
	print("Resource Declaration Initilization Duration: " + str(datetime.now() - demoStart))
	
	resourceDeclaration.deployResources()
	print("Deploy Resources Duration: " + str(datetime.now() - demoStart))
	
	resourceDeclaration.setupClusterClient()
	print("Client Setup Duration: " + str(datetime.now() - demoStart))
	
	resourceDeclaration.clusterConnectionValidation()
	print("Connected to cluster: " + str(datetime.now() - demoStart))
	
	resourceDeclaration.patchOrchestrationApplicationDeclaration()
	print("Deployed Patch Orchestration Application as Azure Resource: " + str(datetime.now() - demoStart))
	
	#resourceDeclaration.deployResources()
	#print("Deployed POA Resource Duration: " + str(datetime.now() - demoStart))
	
	#resourceDeclaration.enableHostMSI()
	#resourceDeclaration.setMSIPermissions()

if __name__ == '__main__':
	main()
