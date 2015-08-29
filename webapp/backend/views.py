import json

from django.http import JsonResponse

from fokia.utils import check_auth_token

import tasks
import events
from .models import LambdaInstance, Server


def authenticate(request):
    """
    Checks the validity of the authentication token of the user
    """

    # request.META contains all the headers of the request
    auth_token = request.META.get("HTTP_X_API_KEY")
    auth_url = request.META.get("HTTP_X_AUTH_URL")

    status, info = check_auth_token(auth_token, auth_url=auth_url)
    if status:
        return JsonResponse({"result": "Success"}, status=200)
    else:
        return JsonResponse({"errors": [json.loads(info)]}, status=401)


def list_lambda_instances(request):
    """
    Lists the lambda instances owned by the user.
    """

    # Authenticate user.
    authentication_response = authenticate(request)
    if authentication_response.status_code != 200:
        return authentication_response

    # Parse limit and page parameters.
    try:
        limit = int(request.GET.get("limit"))
        page = int(request.GET.get("page"))

        if limit <= 0 or page <= 0:
            return JsonResponse({"errors":
                                 [{"message": "Zero or negative indexing is not supported",
                                   "code": 500,
                                   "details": ""}]}, status=500)

        # Retrieve the lambda instances from the database.
        first_to_retrieve = (page - 1) * limit
        last_to_retrieve = page * limit
        database_instances = LambdaInstance.objects.all()[first_to_retrieve:last_to_retrieve]
    except:
        database_instances = LambdaInstance.objects.all()

    if len(database_instances) == 0:
        return JsonResponse({"errors": [{"message": "No instances found",
                                         "code": 404,
                                         "details": ""}]}, status=404)

    instances_list = []
    for database_instance in database_instances:
        instances_list.append({"name": database_instance.name,
                               "id": database_instance.id,
                               "uuid": database_instance.uuid})

    return JsonResponse({"data": instances_list}, status=200)


def lambda_instance_details(request, instance_uuid):
    """
    Returns the details for a specific lambda instance owned by the user.
    """

    # Authenticate user.
    authentication_response = authenticate(request)
    if authentication_response.status_code != 200:
        return authentication_response

    # Retrieve specified Lambda Instance.
    try:
        database_instance = LambdaInstance.objects.get(uuid=instance_uuid)
    except:
        return JsonResponse({"errors": [{"message": "Lambda instance not found",
                                         "code": 404,
                                         "details": ""}]}, status=404)

    return JsonResponse({"data": {"name": database_instance.name,
                                  "id": database_instance.id,
                                  "uuid": database_instance.uuid,
                                  "details": json.loads(database_instance.instance_info)}},
                        status=200)


def lambda_instance_status(request, instance_uuid):
    """
    Returns the status of a specified lambda instance owned by the user.
    """

    # Authenticate user.
    authentication_response = authenticate(request)
    if authentication_response.status_code != 200:
        return authentication_response

    # Retrieve specified Lambda Instance.
    try:
        database_instance = LambdaInstance.objects.get(uuid=instance_uuid)
    except:
        return JsonResponse({"errors": [{"message": "Lambda instance not found",
                                         "code": 404,
                                         "details": ""}]}, status=404)

    return JsonResponse({"data": {"name": database_instance.name,
                                  "status": LambdaInstance.
                                  status_choices[int(database_instance.status)][1],
                                  "uuid": database_instance.uuid,
                                  "id": database_instance.id}}, status=200)


def lambda_instance_start(request, instance_uuid):
    """
    Starts a specific lambda instance owned by the user.
    """

    # Authenticate user.
    authentication_response = authenticate(request)
    if authentication_response.status_code != 200:
        return authentication_response

    # Check if the specified lambda instance exists.
    if not LambdaInstance.objects.filter(uuid=instance_uuid).exists():
        return JsonResponse({"errors": [{"message": "Lambda instance not found",
                                         "code": 404,
                                         "details": ""}]}, status=404)

    instance_servers = Server.objects.filter(lambda_instance =LambdaInstance.objects.get(
        uuid=instance_uuid))
    master_id = instance_servers.exclude(pub_ip=None).values('id')[0]['id']
    slaves = instance_servers.filter(pub_ip=None).values('id')
    slave_ids = []
    for slave in slaves:
        slave_ids.append(slave['id'])

    # Create task to start the lambda instance.
    auth_token = request.META.get("HTTP_X_API_KEY")
    auth_url = request.META.get("HTTP_X_AUTH_URL")
    if not auth_url:
        auth_url = "https://accounts.okeanos.grnet.gr/identity/v2.0"

    tasks.lambda_instance_start.delay(instance_uuid, auth_url, auth_token, master_id, slave_ids)

    # Create event to update the database.
    events.set_lambda_instance_status.delay(instance_uuid, LambdaInstance.STARTING)

    return JsonResponse({"result": "Success"}, status=200)


def lambda_instance_stop(request, instance_uuid):
    """
    Stops a specific lambda instance owned by the user.
    """

    # Authenticate user.
    authentication_response = authenticate(request)
    if authentication_response.status_code != 200:
        return authentication_response

    # Check if the specified lambda instance exists.
    if not LambdaInstance.objects.filter(uuid=instance_uuid).exists():
        return JsonResponse({"errors": [{"message": "Lambda instance not found",
                                         "code": 404,
                                         "details": ""}]}, status=404)

    instance_servers = Server.objects.filter(lambda_instance =LambdaInstance.objects.get(
        uuid=instance_uuid))
    master_id = instance_servers.exclude(pub_ip=None).values('id')[0]['id']
    slaves = instance_servers.filter(pub_ip=None).values('id')
    slave_ids = []
    for slave in slaves:
        slave_ids.append(slave['id'])

    # Create task to stop the lambda instance.
    auth_token = request.META.get("HTTP_X_API_KEY")
    auth_url = request.META.get("HTTP_X_AUTH_URL")
    if not auth_url:
        auth_url = "https://accounts.okeanos.grnet.gr/identity/v2.0"

    tasks.lambda_instance_stop.delay(instance_uuid, auth_url, auth_token, master_id, slave_ids)

    # Create event to update the database.
    events.set_lambda_instance_status.delay(instance_uuid, LambdaInstance.STOPPING)

    return JsonResponse({"result": "Success"}, status=200)
