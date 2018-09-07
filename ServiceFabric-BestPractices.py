__author__ = "Alexander Johnson"
__email__ = "aljo-microsoft@github.com"
__status__ = "Development"

""" This demostrates best practices for an Azure Service Fabric Cluster """

import subprocess
import json
from pathlib import Path
import sys

class ServiceFabricResourceDeclaration:
	# All Production Services have deployment time Resource Declaration values
	# E.G. Secrets being the most common dynamic values being declared
	def __init__(
		self,
		subscription='eec8e14e-b47d-40d9-8bd9-23ff5c381b40',
		template_file='AzureDeploy.json',
		parameters_file='AzureDeploy.Parameters.json',
		deployment_resource_group='aljoDeploymentRG',
		keyvault_resource_group='aljoKeyVaultRG',
		keyvault_name='aljoKeyvault',
		clusterName='aljocluster',
		adminUserName='aljo',
		adminPassword='Password#1234',
		clusterLocation='westus',
		certificate_name='clusterCertificate',
		certificateThumbprint='GEN-CUSTOM-DOMAIN-SSLCERT-THUMBPRINT',
		sourceVaultValue='GEN-KEYVAULT-RESOURCE-ID',
		certificateUrlValue='GEN-KEYVAULT-SSL-SECRET-URI'
		):

		# Set Parameters
		self.subscription = subscription
		self.template_file = template_file
		self.parameters_file = parameters_file
		self.deployment_resource_group = deployment_resource_group
		self.keyvault_resource_group = keyvault_resource_group
		self.keyvault_name = keyvault_name
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
		accountSetCmd = 'az account set --subscription ' + self.subscription
		cmds = loginCmd + ';' + accountSetCmd
		
		subprocess.call(cmds, shell=True)

		# Validate Template and Parameters
		if (Path(self.parameters_file)).exists() and (Path(self.template_file)).exists():
			print("Template and Parameter File's Found")
			
			self.parameters_file_json = json.load(open(self.parameters_file))
			
			# Keyvault Cluster Certificate Exist or Create
			if self.sourceVaultValue.find('/subscriptions/') >= 0 and len(self.certificateThumbprint) > 36 and self.certificateUrlValue.find('vault.azure.net') != -1:
				# Use Keyvault Certificate Arguments for resource Validation
				print('Validating Keyvault Certificate Deployment Arguments')
			else:
				self.sourceVaultValue = self.parameters_file_json['parameters']['sourceVaultValue']['value']
				self.certificateThumbprint = self.parameters_file_json['parameters']['certificateThumbprint']['value']
				self.certificateUrlValue = self.parameters_file_json['parameters']['certificateUrlValue']['value']

				if self.sourceVaultValue.find("/subscriptions/") >= 0 and len(self.certificateThumbprint) > 36 and self.certificateUrlValue.find("vault.azure.net") >= 0:
					# Use Parameters File Keyvault Certificate Declarations for resource Validation
					print('Validating Keyvault Certificate Parameters File Declarations')
				else:
					# Create KeyVault
					print('Creating Deployment Keyvault Self Signed Certificate')
					groupCreateCmd = 'az group create --name ' + self.keyvault_resource_group + ' --location ' + self.clusterLocation
					keyVaultCreateCmd = 'az keyvault create --name ' + self.keyvault_name + ' --resource-group ' + self.keyvault_resource_group + ' --enabled-for-deployment true'
					groupKeyVaultCmd = groupCreateCmd + ';' + keyVaultCreateCmd

					subprocess.call(groupKeyVaultCmd, shell=True)

					# Keyvault DNS Population Takes 10 Secs
					keyvaultShowCmd = 'az keyvault show -n ' + self.keyvault_name + ' -g ' + self.keyvault_resource_group
					subprocess.call(keyvaultShowCmd, shell=True)

					# Create Self Signed Certificate
					# Get Default Policy
					defaultPolicyProcess = subprocess.Popen(["az", "keyvault", "certificate", "get-default-policy"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
					
					stdout, stderr = defaultPolicyProcess.communicate()
					
					if defaultPolicyProcess.wait() == 0:
						defaultPolicy = stdout.decode("utf-8")
					else:
						print(stderr)
						sys.exit("Couldn't get kevault certificate default policy")
					
					defaultPolicyJson = json.loads(defaultPolicy)
					# Set Subject Name to FQDN
					# Browsers won't trust certificates with subject names that don't match FQDN
					defaultPolicyJson['x509CertificateProperties']['subject'] = self.clusterName + "." + self.clusterLocation + ".cloudapp.azure.com"
					
					certificateCreateProcess = subprocess.Popen(["az", "keyvault", "certificate", "create", "--vault-name", self.keyvault_name, "-n", self.certificate_name, "-p", defaultPolicyJson], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

					stdout, stderr = certificateCreateProcess.communicate()

					if certificateCreateProcess.wait() == 0:
						print(stdout)
					else:
						print(stderr)
						sys.exit("Failed to Create Certificate")
					
					# Get Keyvault Self Signed Certificate Properties
					# Get resource Id
					resourceIdProcess = subprocess.Popen(["az", "keyvault", "show", "--name", self.keyvault_name, "--query", "id", "-o", "tsv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

					stdout, stderr = resourceIdProcess.communicate()

					if resourceIdProcess.wait() == 0:
						self.sourceVaultValue = stdout.decode("utf-8").replace('\n', '')
					else:
						print(stderr)
						sys.exit("Couldn't get KeyVault Self Signed Certificate Resource Id")

					# Get Certificate Url
					urlProcess = subprocess.Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "sid", "-o", "tsv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

					stdout, stderr = urlProcess.communicate()

					if urlProcess.wait() == 0:
						self.certificateUrlValue = stdout.decode("utf-8").replace('\n', '')
					else:
						print(stderr)
						sys.exit("Couldn't get KeyVault Self Signed Certificate URL")

					# Get Certificate Thumbprint
					thumbprintProcess = subprocess.Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "x509ThumbprintHex", "-o", "tsv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

					stdout, stderr = thumbprintProcess.communicate()
				
					if thumbprintProcess.wait() == 0:
						self.certificateThumbprint = stdout.decode("utf-8").replace('\n', '')
					else:
						print(stderr)
						sys.exit("Couldn't get KeyVault Self Signed Certificate Thumbprint")
			
			# Validate KeyVault Resource Availability
			validateSourceVault = subprocess.Popen(["az", "resource", "show", "--ids", self.sourceVaultValue], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

			stdout, stderr = validateSourceVault.communicate()

			if validateSourceVault.wait() == 0:
				print("Source Vault Resource is Valid within subscription context")
			else:
				print(stderr)
				sys.exit("Source Vault is invalid within subscription context")

			# Validate KeyVault Certificate
			# Certificate URL
			self.keyvault_name = self.certificateUrlValue.rsplit("//", 1)[1].rsplit(".vault.", 1)[0]
			self.certificate_name = self.certificateUrlValue.rsplit("//", 1)[1].rsplit(".vault.", 1)[1].rsplit("/", 3)[2]			 
			
			certUrlValidateProcess = subprocess.Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "sid", "-o", "tsv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

			stdout, stderr = certUrlValidateProcess.communicate()

			if certUrlValidateProcess.wait() == 0 and stdout.decode("utf-8").replace('\n', '') == self.certificateUrlValue:
				print("Certificate SID URL is valid within subscription context")
			else:
				print(stderr)
				sys.exit("Certificate SID URL is invalid within subscription context")
 
			# Certificate Thumbprint
			certThumbprintValidateProcess = subprocess.Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "x509ThumbprintHex", "-o", "tsv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

			stdout, stderr = certThumbprintValidateProcess.communicate()

			if certThumbprintValidateProcess.wait() == 0 and stdout.decode("utf-8").replace('\n', '') == self.certificateThumbprint:
				print("Certificate Thumbprint is valid within subscription context")
			else:
				print(stderr)
				sys.exit("Certificate Thumbprint is invalid within subscription context")

			# Write Declarative Parameters File
			self.parameters_file_json['parameters']['sourceVaultValue']['value'] = self.sourceVaultValue
			self.parameters_file_json['parameters']['certificateThumbprint']['value'] = self.certificateThumbprint
			self.parameters_file_json['parameters']['certificateUrlValue']['value'] = self.certificateUrlValue
			self.parameters_file_json['parameters']['clusterName']['value'] = self.clusterName
			self.parameters_file_json['parameters']['adminUserName']['value'] = self.adminUserName
			self.parameters_file_json['parameters']['adminPassword']['value'] = self.adminPassword
			self.parameters_file_json['parameters']['clusterLocation']['value'] = self.clusterLocation

			json.dump(self.parameters_file_json, open(self.parameters_file, 'w'))

			# Exists or Create Deployment Group - needed for validation
			deploymentGroupExistsProcess = subprocess.Popen(["az", "group", "exists", "--name", self.deployment_resource_group], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

			stdout, stderr = deploymentGroupExistsProcess.communicate()

			if deploymentGroupExistsProcess.wait() == 0 and stdout.decode('utf-8').replace('\n', '') == 'true':
				print("Deployment Group Exists")
				# TODO: Validate Group Location
			else:
				deploymentGroupCreateProcess = subprocess.Popen(["az", "group", "create", "--location", self.clusterLocation, "--name", self.deployment_resource_group], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				
				stdout, stderr = deploymentGroupCreateProcess.communicate()

				if deploymentGroupCreateProcess.wait() == 0:
					print("Deployment Group Created")
				else:
					print(stderr)
					sys.exit("Problem creating deployment group")

			# Validate Deployment Declaration
			self.parametersFileArgFormat = "@" + self.parameters_file

			deploymentValidationProcess = subprocess.Popen(["az", "group", "deployment", "validate", "--resource-group", self.deployment_resource_group, "--template-file", self.template_file, "--parameters", self.parametersFileArgFormat], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

			stdout, stderr = deploymentValidationProcess.communicate()

			if deploymentValidationProcess.wait() == 0:
				print(stdout)
				print("Your Deployment Declaration is Valid Syntactically")
			else:
				print(stderr)
				print("Your Deployment Declaration is Invalid Syntactically")

		else:
			sys.exit('Template and Parameters Files NOT Found')
		
	def provisionCluster(self):
		# Reduce LiveSite issues by deploying Azure Resources in a Declarative way as a group
		print("Provisioning Cluster")
		
		groupDeploymentCreateProcess = subprocess.Popen(["az", "group", "deployment", "create", "-g", self.deployment_resource_group, "--template-file", self.template_file, "--parameters", self.parametersFileArgFormat], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		stdout, stderr = groupDeploymentCreateProcess.communicate()

		if groupDeploymentCreateProcess.wait() == 0:
			print(stdout)
			print("Provisioning Cluster Successful")
		else:
			print(stderr)
			print("Provisiong Cluster Failed")

	def setupClient(self):
		# SRE's whom Manage your Application can level SFX to gain state on the health of your Application
		# This sets up your local machine to authenticate you with a certificate authentication, which will
		# work for secure clusters, whether or not another authentication mechansim is used; e.g. If Azure
		# Active Directory is configured for a secure cluster, a certificate can be used to authenticated.
		# TODO: implement the following behavior
		# Down load admin certificate
		# Convert to PEM format if localhost is Linux and import into browsers trusted root authority for self signed certs
		# Import pfx cert into personal and/or trustedpeople store if cert is self signed for windows localhost
		# Download Certificate
		print("Downloading Certificate")
		certificateFile = self.certificate_name + ".pfx"
		downloadCertProcess = subprocess.Popen(["az", "keyvault", "certificate", "download", "--file", certificateFile, "--encoding", "PEM", "--name", self.certificate_name, "--vault-name", self.keyvault_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		stdout, stderr = downloadCertProcess.communicate()

		if downloadCertProcess.wait() == 0:
			print(stdout)
			print("Download of Certificate Successful")
		else:
			print(stderr)
			print("Download of Certificate Failed")

	def patchOrchestrationApplication(self):
		# Download POA and Archive Package
		# Create Storage Account, Upload POA, and Get Storage Properties
		# Use Package properties to declare App and Services as Resources in Template
		# Deploy POA as resource to SF Cluster
		print("Deploying Patch Orchestration Application")

	def enableHostMSI(self):
		# Update template to enable host MSi and apply policies
		print("Enabling Host MIS")

	def setMSIPermissions(self):
		# grant AAD permissions to MSI for resource such as Cosmos DB
		print("Applying Permissions to Resource for MSI")

	def deployNativeDemoApplication(self):
		# Deploy ACR hosted container using data encryption certificate for ACR password
		# App implementation to use MSI to authenticate to resource such as Cosmos DB
		print("Deploying SF Native Demo Application")

def main():
	resourceDeclaration = ServiceFabricResourceDeclaration()
	resourceDeclaration.provisionCluster()
	resourceDeclaration.setupClient()
	resourceDeclaration.patchOrchestrationApplication()
	resourceDeclaration.enableHostMSI()
	resourceDeclaration.setMSIPermissions()
	resourceDeclaration.deployNativeDemoApplication()

if __name__ == '__main__':
	main()

# TODO: Mesh demo of Secure Store Service
# enableSecureStoreService()
# Reason: Feature announcement and how to enable it on OneBox
# deployMeshDemoSecrets(acrSecretName, acrSecretValue) - password for ACR
# Reason: Management operations of Secure Store Service
# deployMeshDemoApp() - update package, deploy containerized App, use 3S secure password for ACR, and MSI to write data to DB.
# Reason: 3S to secure secrets, and MSI to avoid manual handling of secrets																       
