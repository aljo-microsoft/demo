# Open Dashboard
az aks browse --resource-group <RESOURCE_GROUP> --name <K8_NAME>

# Build Image
az acr build --os Linux --registry <ACR_NAME> --image main:<VERSION> ./

# Create K8 Secret for yaml reference ACR Credentials
# acr-auth used in main.yaml
ACR_USER_NAME= # Can get from Portal
ACR_PASSWORD= # Can get from Portal
ACR_NAME=<ACR_NAME>
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
kubectl create secret docker-registry acr-auth --docker-server $ACR_LOGIN_SERVER --docker-username <ACR_USER_NAME> --docker-password <ACR_PASSWORD> --docker-email "aljo@microsoft.com"

# Deploy Application to k8:
kubectl apply -f main-deployment.yaml

# Provision Loadbalancer for k8 Deployed Application
# Provides Pubic Endpoint for connecting to Deployed Container.
# Also without deployment first, can use: k8 Dashboard -> 'Discover and Loadbalacing' -> Create -> Create App -> External
# To deploy app as a service (w/ lb)
kubectl apply -f main-service.yaml
