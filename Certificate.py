from subprocess import call
 
class Certificate:

	def __init__(self, clusterName="aljoDemo", location="westus", password="Password#1234"):

		self.clusterName = clusterName
		self.location = location
		self.password = password

		self.certDNSName = self.clusterName + "." + self.location + ".cloudapp.azure.com"

		# Create a new self-signed cert, specifying the FQDN as the subject
		self.create = "openssl req -x509 -newkey rsa:2048 -subj '/CN='" + self.certDNSName + " -days 365 -out " + self.certDNSName + ".crt -keyout " + self.certDNSName + ".pem -passout pass:" + self.password

		call([self.create], shell=True)
	
		# Convert PEM to PFX
		self.convert = "openssl pkcs12 -export -in " + self.certDNSName + ".crt -inkey " + self.certDNSName + ".pem -passin pass:" + self.password + " -out " + self.certDNSName + ".pfx -passout pass:" + self.password

		call([self.convert], shell=True)

		self.pfx = self.certDNSName + ".pfx"
