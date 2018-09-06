import subprocess
import json
from pathlib import Path
import sys

class ResourceProperties:

	def __init__(self, subscription="eec8e14e-b47d-40d9-8bd9-23ff5c381b40", template_file="AzureDeploy.json", parameters_file="AzureDeploy.Parameters.json"):

		# Az CLI Client	
		self.subscription = subscription

		loginCmd = 'az login'
		accountSetCmd = 'az account set --subscription " + self.subscription
		cmds = loginCmd + ";" accountSetCmd
		subprocess.call(cmds, shell=True)

		# Validate Template and Parameters Files Exists
		self.template_file = template_file
		self.parameters_file = parameters_file

		if (Path(self.parameters_file)).exists():
			print("Parameter File Found")
		else:
			sys.exit('Parameters File NOT Found')
		
		if (Path(self.template_file)).exists():
			print("Template File Found")
		else:
			sys.exit('Template file NOT Found')

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
