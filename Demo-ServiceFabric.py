from ServiceFabric-ResourceProperties import ResourceProperties

# TODO: Include az client validate or install logic
# Initialize RM Client with valid deployment properties
# HLT: ARM, Az cli, and minimum set of SF properties
rp = ResourceProperties()

# Create Keyvault Self Signed Cert and update deployment cert properties
# HLT: Thumbprint pain of updating template, and keyvault - I.E. Current State
rp.createCertificate()

# Create Service Fabric Cluster
# HLT: Minimum resource Types to create cluster: VMSS, Network, Storage, ect
rp.createCluster()

# TODO: SFRP demo steps
# clientSetup() - download cert, convert to proper format
# HLT: sfctl deployment - I.E. on prim and administration
# patchOrchestrationApplication() - create storage account, copy POA to storage, declare as resource, and deploy POA 
# HLT: App/Svc as resources
# enableHostMSI()
# HLT: MSI today and why it is important
# hostMSIPermissions(resourceName, permissions)
# HLT: policies grant permissions to resources
# deployNativeDemoApp() - Go guest exe, authenticate to Cosmos DB with MSI to write data
# HLT: app without secrets authenticates to cosmos DB - value add of MSI

# TODO: Mesh demo of Secure Store Service
# enableSecureStoreService()
# HLT: Feature announcement and how to enable it
# deployMeshDemoSecrets(acrSecretName, acrSecretValue) - password for ACR
# HLT: Management operations of 3S 
# deployMeshDemoApp() - update package, deploy containerized App, use 3S secure password for ACR, and MSI to write data to DB.
# HLT: 3S to secure secrets, and MSI to avoid manual handling of secrets

# TODO: Stretch goal is to get letsencrypt certificate deployment
