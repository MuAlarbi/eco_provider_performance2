## Serverless QoS Metrics Collection Tool
This experimental tool is designed to collect Quality of Service (QoS) metrics for a serverless pipeline deployed in various settings across the cloud-edge continuum. The pipeline incorporates three FastAPI endpoints, each representing a distinct function within the pipeline.

## Prerequisites
Before you begin, ensure you have the following installed:

Python 3.x
Docker
Docker Compose
Additionally, you will need a configuration file named config.ini located in the same directory as the script. This configuration file should contain a NetworkSettings section which the script will read to operate correctly.

## Installation
No installation is necessary for the script itself, but you will need to have Docker and Docker Compose installed on your system to run the pipeline in a containerized environment.


## Usage
## Configuration
Create or modify the config.ini file to include the NetworkSettings section with the appropriate settings for your deployment.

## Running the Pipeline Locally
To execute the pipeline on your local machine, navigate to the root directory of the project and run:

```bash
docker-compose up --build
```

## Deploying on Multiple Nodes
To deploy the pipeline across multiple nodes, perform the following steps on each node:

## 1 - Open Required Ports:

Open port 8001 for function 1 host.
Open port 8002 for function 2 host.
Open port 8003 for function 3 host.
## 2 - Enable Inbound ICMP Requests:
Enable inbound connections for Custom ICMP - IPv4 Echo requests on every node.
## 3 - Run Docker Compose:

Navigate to the specified function's directory and execute the command docker-compose up --build.

 ## 4 - run the Datasource
 On the Edge node, navigate to the directory of the datasource and execute the following commands.
```bash
docker build -t source-app .
docker run -it source-app
```