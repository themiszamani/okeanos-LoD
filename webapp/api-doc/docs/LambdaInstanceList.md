---
title: API | lambda instances list
description: Lists all lambda instances
---

# API - lambda instances list - Description

Lambda instances list call, given an authentication token through the header x-api-key,
will firstly check the validity of the token. If the token is invalid, the API will reply
with a "401 Unauthorized" code. If the token is valid, the API will return all the lambda instances in JSON format along with a "200 OK" code. If there are no lambda instances the API will reply with a "404 Not Found" code. Lambda instances can be viewed in pages with a limited number of instances per page. If at least one of the parameters limit and page is less than or equal to zero or missing, the API will reply with a "400 Bad Request" code.


## Basic Parameters

Type            | Description
----------------|--------------------------
**Description** | lambda instances list
**URL**         | /backend/lambda-instances
**HTTP Method** | GET
**Security**    | Basic Authentication


### Headers

Type  | Description | Required | Default value | Example value
----------|-------------|----------|---------------|---------------
Authorization | ~okeanos authentication token. If you have an account you may find the authentication token at (Dashboad-> API Access) https://accounts.okeanos.grnet.gr/ui/api_access. | `Yes` | None | Token tJ3b3f32f23ceuqdoS_..


### Parameters

Name   | Description | Required | Default value | Example value
-------|-------------|----------|---------------|---------------
limit  | number of lambda instances on each page | `No` | None | 3
page   | the number of the page to return | `No` | None | 2


### Keywords in response
Name  | Description | Default value
------|------------|---------------
name  | The name of the lambda instance | Lambda Instance
uuid  | Unique integer identifying a lambda instance | None
id    | Unique integer used to enumerate lambda instances | Auto Increment


## Example

In this example we are going to list all the available lambda instances

The request in curl

```
curl -X GET -H "Authentication: Token tJ3b3f32f23ceuqdoS_TH7m0d6yxmlWL1r2ralKcttY" 'http://<url>/backend/lambda-instances/'
```


### Response body

If the authentication token is correct, a sample response is

```
{
  "data": [
    {"uuid": 1, "name": "Physics Lambda Instance", "id": 1},
    {"uuid": 2, "name": "Machine Learning Lambda Instance", "id": 3},
    {"uuid": 3, "name": "Another Lambda Instance", "id": 4},
    {"uuid": 4, "name": "Lambda Instance", "id": 5},
    {"uuid": 5, "name": "Lambda Instance for students", "id": 7},
  ]
}
```

For the case where the authentication token is not correct, refer to [Authentication page](Authentication.md).

In this example we are going to list the 2nd page of the lambda instances with a limit of 2
lambda instance in each page.

```
curl -X GET -H "Authentication: Token tJ3b3f32f23ceuqdoS_TH7m0d6yxmlWL1r2ralKcttY" 'http://<url>/backend/lambda-instances/?limit=2&page=2'
```

If the authentication token is correct, a sample response is

```
{
  "data": [
    {"uuid": 3, "name": "Another Lambda Instance", "id": 4},
    {"uuid": 4, "name": "Lambda Instance", "id": 5},
  ]
}
```

### Response messages

The main response messages are:

- HTTP/1.1 200 OK : (Success)
- HTTP/1.1 400 BAD REQUEST : (Fail)
- HTTP/1.1 401 UNAUTHORIZED : (Fail)
- HTTP/1.1 404 NOT FOUND : (Fail)
