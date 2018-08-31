from Certificate import Certificate
import subprocess
import time

class ResourceManager:

	def __init__(self, subscription="eec8e14e-b47d-40d9-8bd9-23ff5c381b40"):

		self.subscription = subscription

		# RM Client
		login = "az login"
		setAccount = "az account set --subscription " + self.subscription
		commands = login + ";" + setAccount

		subprocess.call(commands, shell=True)

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
