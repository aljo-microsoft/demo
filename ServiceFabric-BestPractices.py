import subprocess
import json
from pathlib import Path
import sys

class Deployment:
	
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
					certificateCreateCmd = 'az keyvault certificate create --vault-name ' + self.keyvault_name + ' -n ' + self.certificate_name + ' -p "$(az keyvault certificate get-default-policy)"'
					
					subprocess.call(certificateCreateCmd, shell=True)

					# Get Keyvault Self Signed Certificate Properties
					# Get resource Id
					resourceIdProcess = subprocess.Popen(["az", "keyvault", "show", "--name", self.keyvault_name, "--query", "id", "-o", "tsv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

					stdout, stderr = resourceIdProcess.communicate()

					if resourceIdProcess.wait() == 0:
						self.sourceVaultValue = stdout.decode("utf-8")
					else:
						print(stderr)
						sys.exit("Couldn't get KeyVault Self Signed Certificate Resource Id")

					# Get Certificate Url
					urlProcess = subprocess.Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "sid", "-o", "tsv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

					stdout, stderr = urlProcess.communicate()

					if urlProcess.wait() == 0:
						self.certificateUrlValue = stdout.decode("utf-8")
					else:
						print(stderr)
						sys.exit("Couldn't get KeyVault Self Signed Certificate URL")

					# Get Certificate Thumbprint
					thumbprintProcess = subprocess.Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "x509ThumbprintHex", "-o", "tsv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

					stdout, stderr = thumbprintProcess.communicate()
				
					if thumbprintProcess.wait() == 0:
						self.certificateThumbprint = stdout.decode("utf-8")
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

			# TODO: Validate KeyVault Certificate Url and Thumbprint Resource Availability
			 
			# Write Declarative Parameters File
			self.parameters_file_json['parameters']['sourceVaultValue']['value'] = self.sourceVaultValue
			self.parameters_file_json['parameters']['certificateThumbprint']['value'] = self.certificateThumbprint
			self.parameters_file_json['parameters']['certificateUrlValue']['value'] = self.certificateUrlValue

			json.dump(self.parameters_file_json, open(self.parameters_file, 'w')) 											       
		else:
			sys.exit('Parameters File NOT Found')
		
	def createCluster(self):
		# az deployment create
		# az sf is an option, but in Azure it isn't the only resource
		print("Creating Cluster")

	def setupClient(self):
		# Down load certificate
		# Convert to PEM format if for Linux
		# Import pfx self signed cert into trustedpeople store for windows
		# Convert to PEM format for linux import into chrome browser trusted root authority
		print("Setting Up Client")

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
	deployment = Deployment()
	deployment.createCluster()
	deployment.setupClient()
	deployment.patchOrchestrationApplication()
	deployment.enableHostMSI()
	deployment.setMSIPermissions()
	deployment.deployNativeDemoApplication()

if __name__ == '__main__':
	main()

# TODO: Mesh demo of Secure Store Service
# enableSecureStoreService()
# Reason: Feature announcement and how to enable it on OneBox
# deployMeshDemoSecrets(acrSecretName, acrSecretValue) - password for ACR
# Reason: Management operations of Secure Store Service
# deployMeshDemoApp() - update package, deploy containerized App, use 3S secure password for ACR, and MSI to write data to DB.
# Reason: 3S to secure secrets, and MSI to avoid manual handling of secrets																       
