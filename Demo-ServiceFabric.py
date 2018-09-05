import subprocess
import json

class Resources:

	def __init__(self, subscription="eec8e14e-b47d-40d9-8bd9-23ff5c381b40", template_file="AzureDeploy.json", parameters_file="AzureDeploy.Parameters.json", resource_group="MyDeploymentResourceGroup", clusterName="MyCluster", adminUserName="myAdmin", adminPassword="Password#1234"):
		self.clusterName = clusterName

		# Az CLI Client	
		self.subscription = subscription

		loginCmd = 'az login'
		accountSetCmd = 'az account set --subscription " + self.subscription
		cmds = loginCmd + ";" accountSetCmd
		subprocess.call(cmds, shell=True)

		# Validate Template and Parms Syntax
		self.template_file = template_file
		self.parameters_file = parameters_file

		self.parameters_file_json = json.load(open(self.parameters_file))

		self.location = parameters_file_json['parameters']['location']['value']
		
		validateCmd = 'az group deployment validate --resource-group ' + resource_group + ' --mode Incremental --parameters ' + parameters_file_json['parameters'] + ' --template-file ' + self.template_file'

		subprocess.call(validateCmd, shell=True)

		# Set Parameter values
		self.parameters_file_json['parameters']['clusterName']['value'] = self.clusterName
		self.parameters_file_json['parameters']['adminUserName']['value'] = adminUserName
		self.parameters_file_json['parameters']['adminPassword']['value'] = adminPassword

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
		certificateCreateCmd = "openssl req -x509 -newkey rsa:2048 -subj '/CN='" + self.dnsName + " -days 365 -out " + self.dnsName + ".crt -keyout " + self.dnsName + ".pem -passout pass:" + self.certificatePassword

		subprocess.call(certificateCreateCmd, shell=True)

		# Convert PEM to PFX
		convertCertificateCmd = "openssl pkcs12 -export -in " + self.dnsName + ".crt -inkey " + self.dnsName + ".pem -passin pass:" + self.certificatePassword + " -out " + self.dnsName + ".pfx -passout pass:" + self.certificatePassword

		subprocess.call(convertCertificateCmd, shell=True)

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
