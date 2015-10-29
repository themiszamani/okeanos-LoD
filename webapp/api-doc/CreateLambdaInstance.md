---
title: API | create lambda instance
description: create a new lambda instance
---

# API - create lambda instance - Description

Lambda instance creation call. Given an authentication token through the header x-api-key, and the instance specifications through other HTTP headers, it will firstly check the validity of the token. If the token is invalid, the API will reply with a 401 error. If the token is valid, the API will start creating a new lambda instance, using the instance specifications specified via the HTTP headers. For creating the cluster, the fokia library will be used. This library firstly uses kamaki to create the desired cluster of VMs, then runs ansible on the VMs to build a complete lambda instance. After starting the lambda instance creation, the API will reply with the details of the cluster in creation, along with a 200 success code.

## Basic Parameters

Type | Description |
-------|-----------------|
 **Description** | create a new lambda instance
 **URL**         | /backend/create_lambda_instance
 **HTTP Method** | POST
 **Security**    | Basic Authentication


### Headers

Type | Description | Required | Default value | Example value |
------|-------------|----------|---------------|---------------|
Authorization | authentication token | `Yes`    | None          | Token tJ3b3f32f23ceuqdoS_TH7m0d6yxmlWL1r2ralKcttR 


### Body

Type | Description | Required | Default value | Example value |
------|-------------|----------|---------------|---------------|
instance_name | Name of the lambda instance | `Yes` | None | My first Lambda Instance
master_name | Name of the master node | `Yes` | None | lambda-master
slaves | Number of slaves | `Yes` | None | 3
vcpus_master | Number of CPUs of the master node | `Yes` | None | 4
vcpus_slave | Number of CPUs of each slave node | `Yes` | None | 2
ram_master | Amount of RAM of master node in MB | `Yes` | None | 4096
ram_master | Amount of RAM of each slave node in MB | `Yes` | None | 2048
disk_master | Amount of HDD space of master node in GB | `Yes` | None | 40
disk_slave | Amount of HDD space of each slave node in GB | `Yes` | None | 40
ip_allocation | Allocation of public ips. Choose between none, master, all | `Yes` | None | master
network_request | Number of private networks | `Yes` | None | 1
project_name | Name of the project | `Yes` | None | lambda.grnet.gr


## Example

In this example we are going to create a new lambda instance, using the specs specified in the json-formatted body, and the authentication token specified by HTTP header.

The request in curl

```
curl -X POST -H "Content-Type: application/json" -H "Authorization: Token tJ3b3f32f23ceuqdoS_TH7m0d6yxmlWL1r2ralKcttR" -d '{"project_name": "lambda.grnet.gr", "instance_name": "My first Lambda Instance", "network_request": 1, "master_name": "lambda-master", "vcpus_master": 4, "disk_slave": 40, "slaves": 1, "ram_slave": 4096, "ram_master": 4096, "vcpus_slave": 4, "ip_allocation": "master", "disk_master": 40}' '<url>:<port>/backend/create_lambda_instance/'
```


### Response body

If the authentication token and url is correct, and all the headers are given correctly, a sample response is

```
{
  "uuid": "35380a49-aae4-4935-9844-dfd6737b8c51"
}
```


### Response messages

The main response messages are:

- HTTP/1.1 202 ACCEPTED : (Success)
- HTTP/1.1 401 UNAUTHORIZED : (Fail)
