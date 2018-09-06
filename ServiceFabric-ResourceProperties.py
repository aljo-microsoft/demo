import subprocess
import json
from pathlib import Path
import sys

class ResourceProperties:
	
	def __init__(
		self,
		subscription="eec8e14e-b47d-40d9-8bd9-23ff5c381b40",
		template_file="AzureDeploy.json",
		parameters_file="AzureDeploy.Parameters.json",
		deployment_resource_group="aljoDeploymentRG",
		keyvault_resource_group="aljoKeyVaultRG",
		keyvault_name="aljoKeyvault",
		clusterName="aljocluster",
		adminUserName="aljo",
		adminPassword="Password#1234",
		clusterLocation="westus",
		certificate_name="clusterCertificate",
		certificateThumbprint="GEN-CUSTOM-DOMAIN-SSLCERT-THUMBPRINT",
		sourceVaultValue="GEN-KEYVAULT-RESOURCE-ID",
		certificateUrlValue="GEN-KEYVAULT-SSL-SECRET-URI"
		):

		# Set Parameters
		self.subscription = subscription
		self.template_file = template_file
		self.parameters_file = parameters_file
		self.deployment_resource_group = deployment_resource_group
		self.keyvault_resource_group = keyvault_resource_group
		self.clusterName = clusterName
		self.adminUserName = adminUserName
		self.adminPassword = adminPassword
		self.clusterLocation = clusterLocation
		self.certificate_name = certificate_name
		self.certificateThumbprint = certificateThumbprint
		self.sourceVaultValue = sourceVaultValue
		self.certificateUrlValue = certificateUrlValue
		
		# Az CLI Client	
		loginCmd = 'az login'
		accountSetCmd = 'az account set --subscription " + self.subscription
		cmds = loginCmd + ";" accountSetCmd
		
		subprocess.call(cmds, shell=True)

		# Validate Template and Parameters
		if (Path(self.parameters_file)).exists() and (Path(self.template_file)).exists():
			print("Template and Parameter File's Found")
			
			self.parameters_file_json = json.load(open(self.parameters_file))
			
			# Keyvault Cluster Certificate Exist or Create
			if self.sourceVaultValue.find("/subscriptions/") == 0 and len(self.certificateThumbprint) > 36 and self.certificateUrlValue.find("vault.azure.net") != -1:
				# Use Keyvault Certificate Arguments
				print("Using Keyvault Certificate Arguments")
				
			elif self.parameters_file_json['parameters']['sourceVaultValue']['value'].find("/subscriptions/") == 0 and len(self.parameters_file_json['parameters']['certificateThumbprint']['value'] !> 36 and self.parameters_file_json['parameters']['certificateUrlValue']['value'].find("vault.azure.net"):
				# use Parameters File Keyvault Certificate Declarations
				print("Using keyvault Certificate Parameters File Declaration")
																       
				self.sourceVaultValue = self.parameters_file_json['parameters']['sourceVaultValue']['value']
				self.certificateThumbprint = self.parameters_file_json['parameters']['certificateThumbprint']['value']
				self.certificateUrlValue = self.parameters_file_json['parameters']['certificateUrlValue']['value']
																       
			else:
				# Create KeyVault
				print("Creating Keyvault Self Signed Certificate")
				groupCreateCmd = 'az group create --name ' + self.keyvault_resource_group + ' --location ' + self.clusterLocation
				keyVaultCreateCmd = 'az keyvault create --name ' + self.keyvault_name + ' --resource-group ' + self.keyvault_resource_group
				groupKeyVaultCmd = groupCreateCmd + ';' + keyVaultCreateCmd
				
				subprocess.call(groupKeyVaultCmd, shell=True)
																       
				# Keyvault DNS Population Takes 10 Secs
				keyvaultShowCmd = 'az keyvault show -n ' + self.keyvault_name + ' -g ' + self.keyvault_resource_group
				subprocess.call(keyvaultShowCmd, shell=True)
				
				# Create Self Signed Certificate
				certificateCreateCmd = 'az keyvault certificate create --vault-name ' + self.keyvault_name + ' p "$(az keyvault certificate get-default-policy)"'
				subprocess.call(certificateCreateCmd, shell=True)
																       
				# Get Keyvault Self Signed Certificate Properties
				# Get resource Id
				resourceIdProcess = subprocess.Popen(["az", "keyvault", "show", "--name", self.keyvault_name, "--query", "id", "-o", "tsv"], stdout=subprocess.PIPE)
				stdout = resourceIdProcess.communicate()
				
				if resourceIdProcess.wait() == 0:
					self.sourceVaultValue = stdout.decode("utf-8")
				else:
					sys.exit("Couldn't get KeyVault Self Signed Certificate Resource Id")
				# Get Thumbprint										
				thumbprintProcess = subprocess.Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name "--query", "sid", "-o", "tsv"], stdout=subprocess.PIPE)
				stdout = thumbprintProcess.communicate()
				
				if thumbprintProcess.wait() == 0:
					self.certificateThumbprint = stdout.decode("utf-8")
				else:
					sys.exit("Couldn't get KeyVault Self Signed Certificate Thumbprint")
				# Get Certificate URL
				urlProcess = subprocess.Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "x509ThumbprintHex", "-o", "tsv"], stdout=subprocess.PIPE)
				stdout = urlProcess.communicate()
				
				if urlProcess.wait() == 0:
					self.certificateUrlValue = stdout.decode("utf-8")
				else:
					sys.exit("Couldn't get KeyVault Self Signed Certificate URL")
			# Write Declarative Parameters File													       
			json.dump(self.parameters_file_json, open(self.parameters_file, 'w')) 											       
		else:
			sys.exit('Parameters File NOT Found')
		
	def createCluster(self):
		# resource put command
																       
	def setupClient(self):
		# Down load certificate and add to trustedpeople store for windows
		# Convert to PEM format for linux
		# test connection using sfctl or az sf?
																       
	def patchOrchestrationApplication(self):
		# update template to declare app as resource
		# download POA
		# create storage account
		# Upload POA To Storage account
		# Get URL with read permissions to storage account file
		# Deploy POA as resource
																       
	def enableHostMSI(self):
		# Update template to enable host MSi and apply policies
																       
	def setMSIPermissions(self):
		# grant AAD permissions to MSI for resource such as Cosmos DB
																       
	def deployNativeDemoApp(self):															       
		# Deploy ACR hosted container using data encryption certificate for ACR password
		# App implementation to use MSI to write authenticate to resource such as Cosmos DB														       
