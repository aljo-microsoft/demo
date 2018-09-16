__author__ = "Alexander Johnson"
__email__ = "aljo-microsoft@github.com"
__status__ = "Development"

""" This demostrates best practices for an Azure Service Fabric Cluster """

from subprocess import call
from subprocess import Popen
from subprocess import PIPE
import json
from pathlib import Path
import sys
from datetime import datetime
import requests
import time

class ServiceFabricResourceDeclaration:
	# All Production Services have deployment time Resource Declaration values
	# E.G. Secrets being the most common dynamic values being declared
	def __init__(
		self,
		subscription='eec8e14e-b47d-40d9-8bd9-23ff5c381b40',
		template_uri='https://raw.githubusercontent.com/Microsoft/service-fabric-scripts-and-templates/master/templates/cluster-tutorial/vnet-linuxcluster.json',
		parameters_uri='https://raw.githubusercontent.com/Microsoft/service-fabric-scripts-and-templates/master/templates/cluster-tutorial/vnet-linuxcluster.parameters.json',
		template_file='AzureDeploy.json',
		parameters_file='AzureDeploy.Parameters.json',
		deployment_resource_group='aljoDeploymentRG',
		keyvault_resource_group='aljoKeyVaultRG',
		keyvault_name='aljoKeyvault',
		clusterName='aljocluster',
		adminUserName='aljo',
		adminPassword='Password#1234',
		location='westus',
		certificate_name='clusterCertificate',
		certificateThumbprint='GEN-CUSTOM-DOMAIN-SSLCERT-THUMBPRINT',
		sourceVaultValue='GEN-KEYVAULT-RESOURCE-ID',
		certificateUrlValue='GEN-KEYVAULT-SSL-SECRET-URI',
		userEmail='aljo-microsoft@github.com'
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
		self.location = location
		self.dnsName = self.clusterName + "." + self.location + ".cloudapp.azure.com"
		self.certificate_name = certificate_name
		self.certificate_file_name = certificate_name + ".pem"
		self.certificateThumbprint = certificateThumbprint
		self.sourceVaultValue = sourceVaultValue
		self.certificateUrlValue = certificateUrlValue
		self.userEmail = userEmail
		
		# Az CLI Client
		accountSetCmd = 'az account set --subscription ' + self.subscription
		cmd = accountSetCmd
		
		call(cmd, shell=True)

		# Get Parameters
		if (Path(self.parameters_file).exists()):
			print("Using local Parameter File Found")
			
			parameters_file_json = json.load(open(self.parameters_file, 'r'))
		else:
			print("Using Tutorial Parameters File")
			parms = requests.get(parameters_uri)
			parmBytes = parms.content
			parameters_file_json = json.loads(parmBytes.decode("utf-8"))
			
		# Keyvault Cluster Certificate Exist or Create
		if self.sourceVaultValue.find('/subscriptions/') >= 0 and len(self.certificateThumbprint) > 36 and self.certificateUrlValue.find('vault.azure.net') != -1:
			# Use Keyvault Certificate Arguments for resource Validation
			print('Validating Keyvault Certificate Deployment Arguments')
		else:
			self.sourceVaultValue = parameters_file_json['parameters']['sourceVaultValue']['value']
			self.certificateThumbprint = parameters_file_json['parameters']['certificateThumbprint']['value']
			self.certificateUrlValue = parameters_file_json['parameters']['certificateUrlValue']['value']

			if self.sourceVaultValue.find("/subscriptions/") >= 0 and len(self.certificateThumbprint) > 36 and self.certificateUrlValue.find("vault.azure.net") >= 0:
				# Use Parameters File Keyvault Certificate Declarations for resource Validation
				print('Validating Keyvault Certificate Parameters File Declarations')
			else:
				# Create KeyVault
				print('Creating Deployment Keyvault Self Signed Certificate')
				groupCreateCmd = 'az group create --name ' + self.keyvault_resource_group + ' --location ' + self.location
				keyVaultCreateCmd = 'az keyvault create --name ' + self.keyvault_name + ' --resource-group ' + self.keyvault_resource_group + ' --enabled-for-deployment true'
				groupKeyVaultCmd = groupCreateCmd + ';' + keyVaultCreateCmd

				call(groupKeyVaultCmd, shell=True)

				# Keyvault DNS Population Takes 10 Secs
				keyvaultShowCmd = 'az keyvault show -n ' + self.keyvault_name + ' -g ' + self.keyvault_resource_group
				call(keyvaultShowCmd, shell=True)

				# Create Self Signed Certificate
				# Get Default Policy
				defaultPolicyProcess = Popen(["az", "keyvault", "certificate", "get-default-policy"], stdout=PIPE, stderr=PIPE)
					
				stdout, stderr = defaultPolicyProcess.communicate()
					
				if defaultPolicyProcess.wait() == 0:
					defaultPolicyJson = json.loads(stdout.decode("utf-8"))
				else:
					print(stderr)
					sys.exit("Couldn't get kevault certificate default policy")

				# Set Subject Name to FQDN
				# Browsers won't trust certificates with subject names that don't match FQDN
				defaultPolicyJson['x509CertificateProperties']['subject'] = "CN=" + self.dnsName
				defaultPolicyJson['x509CertificateProperties']['sans'] = {'dns_names': [self.dnsName], 'emails': [self.userEmail], 'upns': [self.userEmail]} 
				policyFileName = "policy.json"
				json.dump(defaultPolicyJson, open(policyFileName, 'w+'))
				policyFileArgFormat = "@" + policyFileName

				certificateCreateProcess = Popen(["az", "keyvault", "certificate", "create", "--vault-name", self.keyvault_name, "-n", self.certificate_name, "-p", policyFileArgFormat], stdout=PIPE, stderr=PIPE)

				stdout, stderr = certificateCreateProcess.communicate()

				if certificateCreateProcess.wait() == 0:
					print(stdout)
				else:
					print(stderr)
					sys.exit("Failed to Create Certificate")
					
				# Get Keyvault Self Signed Certificate Properties
				# Get resource Id
				resourceIdProcess = Popen(["az", "keyvault", "show", "--name", self.keyvault_name, "--query", "id", "-o", "tsv"], stdout=PIPE, stderr=PIPE)

				stdout, stderr = resourceIdProcess.communicate()

				if resourceIdProcess.wait() == 0:
					self.sourceVaultValue = stdout.decode("utf-8").replace('\n', '')
				else:
					print(stderr)
					sys.exit("Couldn't get KeyVault Self Signed Certificate Resource Id")

				# Get Certificate Url
				urlProcess = Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "sid", "-o", "tsv"], stdout=PIPE, stderr=PIPE)

				stdout, stderr = urlProcess.communicate()

				if urlProcess.wait() == 0:
					self.certificateUrlValue = stdout.decode("utf-8").replace('\n', '')
				else:
					print(stderr)
					sys.exit("Couldn't get KeyVault Self Signed Certificate URL")

				# Get Certificate Thumbprint
				thumbprintProcess = Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "x509ThumbprintHex", "-o", "tsv"], stdout=PIPE, stderr=PIPE)

				stdout, stderr = thumbprintProcess.communicate()
				
				if thumbprintProcess.wait() == 0:
					self.certificateThumbprint = stdout.decode("utf-8").replace('\n', '')
				else:
					print(stderr)
					sys.exit("Couldn't get KeyVault Self Signed Certificate Thumbprint")
			
		# Validate KeyVault Resource Availability
		validateSourceVault = Popen(["az", "resource", "show", "--ids", self.sourceVaultValue], stdout=PIPE, stderr=PIPE)

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
			
		certUrlValidateProcess = Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "sid", "-o", "tsv"], stdout=PIPE, stderr=PIPE)

		stdout, stderr = certUrlValidateProcess.communicate()

		if certUrlValidateProcess.wait() == 0 and stdout.decode("utf-8").replace('\n', '') == self.certificateUrlValue:
			print("Certificate SID URL is valid within subscription context")
		else:
			print(stderr)
			sys.exit("Certificate SID URL is invalid within subscription context")
 
		# Certificate Thumbprint
		certThumbprintValidateProcess = Popen(["az", "keyvault", "certificate", "show", "--vault-name", self.keyvault_name, "--name", self.certificate_name, "--query", "x509ThumbprintHex", "-o", "tsv"], stdout=PIPE, stderr=PIPE)

		stdout, stderr = certThumbprintValidateProcess.communicate()

		if certThumbprintValidateProcess.wait() == 0 and stdout.decode("utf-8").replace('\n', '') == self.certificateThumbprint:
			print("Certificate Thumbprint is valid within subscription context")
		else:
			print(stderr)
			sys.exit("Certificate Thumbprint is invalid within subscription context")

		# Write Declarative Parameters File
		parameters_file_json['parameters']['sourceVaultValue']['value'] = self.sourceVaultValue
		parameters_file_json['parameters']['certificateThumbprint']['value'] = self.certificateThumbprint
		parameters_file_json['parameters']['certificateUrlValue']['value'] = self.certificateUrlValue
		parameters_file_json['parameters']['clusterName']['value'] = self.clusterName
		parameters_file_json['parameters']['adminUserName']['value'] = self.adminUserName
		parameters_file_json['parameters']['adminPassword']['value'] = self.adminPassword
		parameters_file_json['parameters']['location']['value'] = self.location

		json.dump(parameters_file_json, open(self.parameters_file, 'w'))

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
				print(stderr)
				sys.exit("Problem creating deployment group")

		# Get Template
		if (Path(self.template_file).exists()):
			print("Using local template File Found")
		else:
			print("Using Tutorial Template File")
			template = requests.get(template_uri)
			templateBytes = template.content
			template_file_json = json.loads(templateBytes.decode("utf-8"))
			
			templateFile = open(self.template_file, 'x')
			json.dump(template_file_json, templateFile)
			templateFile.close()

		# Validate Deployment Declaration
		print("Validating Deployment Declaration")
		self.parametersFileArgFormat = "@" + self.parameters_file

		deploymentValidationProcess = Popen(["az", "group", "deployment", "validate", "--resource-group", self.deployment_resource_group, "--template-file", self.template_file, "--parameters", self.parametersFileArgFormat], stdout=PIPE, stderr=PIPE)

		stdout, stderr = deploymentValidationProcess.communicate()

		if deploymentValidationProcess.wait() == 0:
			print("Your Deployment Declaration is Valid Syntactically")
		else:
			print(stderr)
			print("Your Deployment Declaration is Invalid Syntactically")
		
	def deployResources(self):
		# Reduce LiveSite issues by deploying Azure Resources in a Declarative way as a group
		print("Provisioning Cluster")
		
		groupDeploymentCreateProcess = Popen(["az", "group", "deployment", "create", "-g", self.deployment_resource_group, "--template-file", self.template_file, "--parameters", self.parametersFileArgFormat], stdout=PIPE, stderr=PIPE)

		stdout, stderr = groupDeploymentCreateProcess.communicate()

		if groupDeploymentCreateProcess.wait() == 0:
			print("Provisioning Cluster Successful")
		else:
			print(stderr)
			print("Provisiong Cluster Failed")

	def setupClient(self):
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
			print("Download of Certificate file in Base 64 Format Failed")
		print("Converting Base 64 Certificate File to PEM format")
		convertCertProcess = Popen(["openssl", "pkcs12", "-in", certificateB64File, "-out", self.certificate_file_name, "-nodes", "-passin", "pass:"], stdout=PIPE, stderr=PIPE)
		
		stdout, stderr = convertCertProcess.communicate()
		
		if convertCertProcess.wait() == 0:
			print("Convert of base64 file to PEM format successful")
		else:
			print(stderr)
			print("Converting base64 file to PEM format failed")

	def clusterHealthyProvisioning(self):
		endpoint = 'https://' + self.dnsName + ':19080'
		
		notConnectedToCluster = True
		
		while notConnectedToCluster:
			clusterConnectProcess = Popen(["sfctl", "cluster", "select", "--endpoint", endpoint, "--pem", self.certificate_file_name, "--no-verify"], stdout=PIPE, stderr=PIPE)
			
			stdout, stderr = clusterConnectProcess.communicate()
			
			if clusterConnectProcess.wait() == 0:
				notConnectedToCluster = False
			
			print("Unable to Connect to Deployed Cluster Resource... Waiting 30 secs to try again")
			time.sleep(30)
				
		clusterHealthProcess = Popen(["sfctl", "cluster", "health"], stdout = PIPE, stderr = PIPE)
		
		stdout, stderr = clusterHealthProcess.communicate()
		
		if clusterHealthProcess.wait() == 0:
			print("Provisioning Healthy Cluster Complete")
		else:
			print(stderr)
			sys.exit("Provisioning Health Cluster Failed")
	
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
	demoStart = datetime.now()
	
	resourceDeclaration = ServiceFabricResourceDeclaration()
	print("Resource Declaration Initilization Duration: " + str(datetime.now() - demoStart))
	
	resourceDeclaration.deployResources()
	print("Deploy Resources Duration: " + str(datetime.now() - demoStart))
	
	resourceDeclaration.setupClient()
	print("Client Setup Duration: " + str(datetime.now() - demoStart))
	
	resourceDeclaration.clusterHealthyProvisioning()
	print("Provisioned healthy cluster for Deployment Duration: " + str(datetime.now() - demoStart))
	
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
