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
			
			# Does Keyvault Cluster Certificate exists
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
																       
				# Get Keyvault Certificate Properties
				resourceIdProcess = subprocess.Popen(["az", "keyvault", "show", "--name", self.keyvault_name, "--query", "id", "-o", "tsv"], stdout=subprocess.PIPE)
				stdout = resourceIdProcess.communicate()
				if resourceIdProcess.wait() == 0:
					self.sourceVaultValue = stdout.decode("utf-8")
				else:
					sys.exit("Couldn't get KeyVault Self Signed Certificate Resource Id")
																       
				# TODO: Finish property gathering
				# self.certificateThumbprint = self.parameters_file_json['parameters']['certificateThumbprint']['value']
				# self.certificateUrlValue = self.parameters_file_json['parameters']['certificateUrlValue']['value']
																       
		else:
			sys.exit('Parameters File NOT Found')
		

	def selfSignedCertificate(self, keyVaultName="MyKeyVault", keyVaultResourceGroup="MyKeyVaultResourceGroup", certificateName="MySelfSignedCertificate", description="My Self Signed Certificate", certificatePassword="Password#1234"):
		
		self.description = description
		self.keyVaultName = keyVaultName
		self.keyVaultResourceGroup = keyVaultResourceGroup
		self.certificateName = certificateName
		self.certificatePassword = certificatePassword

		# Make KeyVault
		groupCreateCmd = 'az group create --name ' + self.keyVaultResourceGroup + ' --location ' + self.location
		keyVaultCreateCmd = 'az keyvault create --name ' + self.keyVaultName + ' --resource-group ' + self.keyVaultResourceGroup
		cmds = groupCreateCmd + ';' + keyVaultCreateCmd
		subprocess.call(cmds, shell=True)

		# KeyVault DNS Population 10 secs
		keyVaultCreateValidationCmd = 'az keyvault show -n ' + self.keyVaultName + ' -g ' + self.keyVaultResourceGroup
		subprocess.call(keyVaultCreateValidateCmd, shell=True)

		# Create Self Signed Certificate
		self.dnsName = self.clusterName + '.' + self.location + '.cloudapp.azure.com'
		certificateCreateCmd = 'az keyvault certificate create --vault-name ' + self.keyVaultName + ' -p "$(az keyvault certificate get-default-policy)"'

		subprocess.call(certificateCreateCmd, shell=True)

		# Download Cert: az keyvault certificate download --vault-name <keyvaultname> --name <certname> --file <pem file name>
		# Get Cert Properties: URL, URI, Thumbprint
		# Convert Cert format for client connection: openssl pkcs12 -in ~/Downloads/<keyvaultname>-<certname>-YYYYMMDD.pfx -out ./<certname>.pem -nodes
		# 
		self.PFXCertificate = self.dnsName + '.pfx'

		# Upload Certificate to KeyVault
		uploadCertificateCmd = "az keyvault secret set --description '" + self.description + "' --encoding base64 --file ./" + self.PFXCertificate + " --name " + self.certificateName + " --vault-name " + self.keyVaultName

		subprocess.call(uploadCertificateCmd, shell=True)

		# Update Resource ID Parameter
		resourceIdProcess = subprocess.Popen(["az", "keyvault", "show", "--name", self.keyVaultName, "--query", "id", "-o", "tsv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		stdout, stderr = resourceIdProcess.communicate()

		self.parameters_file_json['parameters']['sourceVaultValue']['value'] = stdout.decode("utf-8")

		# Update Thumbprint Parameter
		thumbprintProcess = subprocess.Popen(["az", "keyvault", "secret", "--vault-name", self.keyVaultName, "--name", self.certificateName, "--query", "x509ThumbprintHex", "-o", "tsv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		stdout, stderr = thumbprintProcess.communicate()

		self.parameters_file_json['parameters']['certificateThumbprint']['value'] = stdout.decode("utf-8")

		# Update URL Parameter
		urlProcess = subprocess.Popen(["az", "keyvault", "secret", "show", "--vault-name", self.keyVaultName, "--name", self.certificateName, "--query", "id", "-o", "tsv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		stdout, stderr = urlProcess.communicate()

		self.parameters_file_json['parameters']['certificateUrlValue']['value'] = stdout.decode("utf-8")

		# Update Parameters File
		json.dump(self.parameters_file_json, open(self.parameters_file, 'w')) 
	
	def deploy(self):
		# Validate Declaration; need to create resource group before running
		validateCmd = 'az group deployment validate --resource-group ' + resource_group + ' --mode Incremental --parameters @' + self.parameters_file + ' --template-file ' + self.template_file'
