#==========INSTRUCTIONS==========
#to run this first make it executable with:
#chmod +x run_kubernetes.sh
#then if in the same directory run with 
#./run_kubernetes.sh
#================================

function ask_to_push_new_docker {
    read -p "Do you want build and push docker(y/n) " -n 1 -r
    echo    # (optional) move to a new line
    if [[ ! $REPLY =~ ^[Yy]$ ]]
    then
        exit 1
    fi
}

function check_installation {
    group_name=$1
    output=$2

    RED='\033[0;31m'
    GREEN='\033[0;32m'
    NC='\033[0m' # No Color

    if [[ $output == *"No resources found in ${group_name} namespace"* ]]; then
      echo -e "${GREEN}Initialization - SUCCESS${NC}"
    else
      echo -e "${RED}Initialization - FAILED${NC}"
    fi
}

#EDIT THESE VARIABLES IF NEEDED
group-name=manrique

az login
az account set --subscription 4693832c-ac40-4623-80b9-79a0345fcfce
az acr login --name imperialswemlsspring2024
az aks get-credentials --resource-group imperial-swemls-spring-2024 --name imperial-swemls-spring-2024 --overwrite-existing
kubelogin convert-kubeconfig -l azurecli

output=$(kubectl --namespace=${group_name} get pods)

check_installation $group_name $output
ask_to_push_new_docker

docker build -t imperialswemlsspring2024.azurecr.io/coursework4-${group-name} .
docker push imperialswemlsspring2024.azurecr.io/coursework4-${group-name}

kubectl apply -f coursework4.yaml
kubectl --namespace=${group-name} get deployments
kubectl logs --namespace=${group-name} -l app=aki-detection