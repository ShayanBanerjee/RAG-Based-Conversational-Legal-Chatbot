# RAG-Based-Conversational-Legal-Chatbot
Indian Law Chatbot containing all basic laws in India


# How to run?
### Automate project setup directory

```bash
bash template.sh
```

Load your pdf data in ```data``` folder

### STEPS:

Clone the repository

```bash
git clone https://github.com/ShayanBanerjee/RAG-Based-Conversational-Legal-Chatbot.git
```
### STEP 01- Create python environment after opening the repository

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```


### STEP 02- install the requirements
```bash
pip install -r requirements.txt
```


### Create a `.env` file in the root directory and add your Pinecone & openai credentials as follows:

```ini
PINECONE_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
OPENAI_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

##### Fronted build
```python
cd frontend
npm install
npm start
```

##### run the following command to store embeddings to pinecone
```bash
python store_index.py
```

##### Finally run the following command
```bash
python app.py
```

Now,
```bash
open up localhost:
```


### Techstack Used:

- Python
- LangChain
- Flask
- GPT
- Pinecone



# AWS-CICD-Deployment-with-Github-Actions

## 1. Login to AWS console.

## 2. Create IAM user for deployment

#### with specific access (https://console.aws.com)

1. EC2 access : It is virtual machine

2. ECR: Elastic Container registry to save your docker image in aws


#### Description: About the deployment

1. Build docker image of the source code

2. Push your docker image to ECR

3. Launch Your EC2 

4. Pull Your image from ECR in EC2

5. Lauch your docker image in EC2

##### Policy:

1. AmazonEC2ContainerRegistryFullAccess

2. AmazonEC2FullAccess

	
## 3. Create ECR repo to store/save docker image
*Save the URI:* 680528876031.dkr.ecr.eu-north-1.amazonaws.com/medicalbot

	
## 4. Create EC2 machine (Ubuntu) 

## 5. Open EC2 and Install docker in EC2 Machine:
	
	
```bash
#optinal

sudo apt-get update -y

sudo apt-get upgrade

#required

curl -fsSL https://get.docker.com -o get-docker.sh

sudo sh get-docker.sh

sudo usermod -aG docker ubuntu

newgrp docker
```
	
# 6. Configure EC2 as self-hosted runner:
    Github repo (https://github.com/ShayanBanerjee/RAG-Based-Conversational-Legal-Chatbot.git) > setting > actions >runner >new self hosted runner > choose os (linux)> then run command one by one

### Next instructions (on EC2)
#### Create a folder
```bash
$ mkdir actions-runner && cd actions-runner
```
#### Download the latest runner package
```bash
$ curl -o actions-runner-linux-x64-2.329.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.329.0/actions-runner-linux-x64-2.329.0.tar.gz
```
#### Optional: Validate the hash
```bash
$ echo "194f1e1e4bd02f80b7e9633fc546084d8d4e19f3928a324d512ea53430102e1d  actions-runner-linux-x64-2.329.0.tar.gz" | shasum -a 256 -c
```

#### Extract the installer
```bash
$ tar xzf ./actions-runner-linux-x64-2.329.0.tar.gz
```

### Configure

#### Create the runner and start the configuration experience
```bash
./config.sh --url https://github.com/ShayanBanerjee/RAG-Based-Conversational-Medical-Chatbot --token AFBBXU6NDVVZGTNGPDPDC63JEZGGM
```
*Enter the name of runner: [press Enter for ip-172-31-32-105]* __self-hosted__

Keep others default 
#### Last step, run it!
```bash
./run.sh
```

To add port 8080 as our app is running on it in ec2
```bash
i-0a163ceb57747fcdb (medical-machine) -> Security -> Security groups (sg-0629661eff54cc5ca - launch-wizard-1) -> Edit inbound rules -> Add rule -> In Custom TCP change port to 8080 and 0.0.0.0/0 -> Save rules
```

Public IPv4 address of the instance with port:
http://51.21.152.95:8080/ 

# 7. Setup github secrets:

*Github repo -> Settings -> Secrets and variables -> Actions -> New repository secret*
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - AWS_DEFAULT_REGION
   - ECR_REPO
   - PINECONE_API_KEY
   - OPENAI_API_KEY
