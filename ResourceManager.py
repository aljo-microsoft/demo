from Certificate import Certificate
import subprocess
import time
import json

class ResourceManager:

	def __init__(self, subscription="eec8e14e-b47d-40d9-8bd9-23ff5c381b40"):
		
		# RM Authenticated Client
		self.subscription = subscription

		login = "az login"
		setAccount = "az account set --subscription " + self.subscription
		commands = login + ";" + setAccount

		subprocess.call(commands, shell=True)

	def deploy(self, template_file="./AzureDeploy.json"):		
		
		self.template_file = template_file

		parameters = {
			"clusterLocation": "westus",
			"clusterName": "mycluster",
			"adminUserName": "Admin",
			"adminPassword": "Password#1234",
			"vmImagePublisher": "Canonical",
			"vmImageOffer": "UbuntuServer",
			"vmImageSku": "16.04-LTS",
			"vmImageVersion": "latest",
			"loadBalancedAppPort1": 80,
			"loadBalancedAppPort2": 8081,
			"clusterProtectionlevel": "EncryptAndSign",
			"certificateStoreValue": "My",
			"certificateThumbprint": "<CERTIFICATE_THUMBPRINT>",
			"sourceVaultValue": "<SOURCE_VAULT_VALUE>",
			"certificateUrlValue": "<CERTIFICATE_VALUE>",
			"storageAccountType": "Standard_LRS",
			"supportLogStorageAccountType": "Standard_LRS",
			"applicationDiagnosticsStorageAccountType": "Standard_LRS",
			"nt0InstanceCount": 5,
			"vmNodeType0Size": "Standard_D2_v2",
			"nt1InstanceCount": 1,
			"vmNodeType1Size": "Standard_D2_v2",
			"nt2InstanceCount": 1,
			"vmNodeType2Size": "Standard_D2_v2"
		}

		parameters = {k: {'value': v} for k, v in parameters.items()}

		command = "az deployment create --location " + self.parameters['location']['value'] + " --template-file " + self.template_file + " --parameters " + self.parameters

		subprocess.call(command, shell=True)

	def keyVault(self, keyVaultName="aljokv", keyVaultGroupName="aljokvrg", location="westus"):
		
		self.keyVaultName = keyVaultName
		self.keyVaultGroupName = keyVaultGroupName
		self.location = location

		group = "az group create --name " + self.keyVaultGroupName + " --location " + self.location

		keyvault = "az keyvault create --name " + self.keyVaultName + " --resource-group " + self.keyVaultGroupName + " --location " + self.location + " --enabled-for-deployment"
		commands = group + ";" + keyvault

		subprocess.call(commands, shell=True)
		
		command = "az keyvault show -n " + self.keyVaultName + " -g " + self.keyVaultGroupName
		 
		subprocess.call(command, shell=True)

	def selfSignedCertificate(self, name="selfSignedCertificate", description="Self Signed Certificate"):
		self.description = description
		self.selfSignedCertName = name
		cert = Certificate()
		pfxFilePath = "./" + cert.pfx
	
		# Upload Cert to KeyVault
		command = "az keyvault secret set --description '" + self.description + "' --encoding base64 --file " + pfxFilePath + " --name " + self.selfSignedCertName + " --vault-name " + self.keyVaultName
		
		subprocess.call(command, shell=True)

		# Get Resource ID of KV Self Signed Cert 
		resourceIdProc = subprocess.Popen(["az", "keyvault", "show", "--name", self.keyVaultName, "--query", "id", "-o", "tsv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	
		stdout, stderr = resourceIdProc.communicate()
	
		self.selfSignedCertResourceId = stdout.decode("utf-8")
		
		# Get Thumbprint of KV Self Signed Cert
		thumbprintProc = subprocess.Popen(["az", "keyvault", "secret", "--vault-name", self.keyVaultName, "--name", self.selfSignedCertName, "--query", "x509ThumbprintHex", "-o", "tsv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		stdout, stderr = thumbprintProc.communicate()

		self.selfSignedCertThumbprint = stdout.decode("utf-8")

		# Get URL of Self Signed Cert
		urlProc = subprocess.Popen(["az", "keyvault", "secret", "show", "--vault-name", self.keyVaultName, "--name", self.selfSignedCertName, "--query", "id", "-o", "tsv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		stdout, stderr = urlProc.communicate()

		self.selfSignedCertUrl = stdout.decode("utf-8")
