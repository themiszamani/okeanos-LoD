from rest_framework import viewsets
from rest_framework import status as rest_status
from rest_framework import generics, mixins
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from .models import LambdaInstance, LambdaApplication, User, Token
from .serializers import (UserSerializer, LambdaInstanceSerializer, LambdaApplicationSerializer)
# from .serializers import LambdaInstanceInfo
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework_xml.renderers import XMLRenderer
from rest_framework.parsers import JSONParser

from .authenticate_user import KamakiTokenAuthentication
from rest_framework.permissions import IsAuthenticated

from .exceptions import CustomParseError, CustomValidationError, CustomNotFoundError,\
    CustomAlreadyDoneError, CustomCantDoError

from .response_messages import ResponseMessages
import events

from django.conf import settings

# Create your views here.

# def authenticate(request):
#     user_auth_token = request.META.get('HTTP_AUTHORIZATION').split()[1]
#     token_obj= list(Token.objects.filter(key=user_auth_token))[0]
#     user = list(User.objects.filter(kamaki_token=token_obj))[0]
#     # if it does not exist, create them


class UsersViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Viewset for viewing Users.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer

class LambdaUsersCounterView(APIView):
    authentication_classes = KamakiTokenAuthentication,
    permission_classes = IsAuthenticated,
    renderer_classes = JSONRenderer, XMLRenderer, BrowsableAPIRenderer

    def get(self, request, format=None):
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
            lambdaUsersCount = LambdaInstance.objects.all().order_by('owner').distinct('owner').count() # This works only on Postgres
        else:
            lambdaUsersCount = LambdaInstance.objects.values('owner').distinct().count()

        status_code = rest_status.HTTP_202_ACCEPTED
        return Response(
            {
                "status": {
                    "code": status_code,
                    "short_description": ResponseMessages.short_descriptions['lambda_users_count'],
                },
                "data": {
                    "count": str(lambdaUsersCount),
                }

            },
            status=status_code)



class LambdaInstanceView(mixins.RetrieveModelMixin,
                         mixins.ListModelMixin, # debugging
                         viewsets.GenericViewSet):
    """
    APIView for viewing lambda instances
    """
    queryset = LambdaInstance.objects.all()
    serializer_class = LambdaInstanceSerializer
    authentication_classes = KamakiTokenAuthentication,
    permission_classes = IsAuthenticated,
    renderer_classes = JSONRenderer, XMLRenderer, BrowsableAPIRenderer
    parser_classes = (JSONParser,)

    lookup_field = 'uuid'

    # @detail_route(methods=['post'], url_path="foo")
    # def foo(self, request, *args, **kwargs):
    #     """
    #     Debug method for testing things. TODO: Delete it.
    #     :param request:
    #     :param args:
    #     :param kwargs:
    #     :return:
    #     """
    #     # data = request.data
    #     user_auth = request.auth
    #     user = request.user # this is the authenticated user.
    #
    #     user_headers = request.META['HTTP_AUTHORIZATION'].split()[-1]
    #
    #     response = Response({"user": str(user)}, status=201)
    #     return response

    def create(self, request, *args, **kwargs):
        """
        Create api call for lambda_instance.
        :param request: The HTTP POST request making the call.
        :param args:
        :param kwargs:
        :return: A response object according to the outcome of the call.
        """
        data = request.data

        instance_name = data['name']
        uuid = data['uuid']
        instance_info = data['instance_info']
        owner = request.user
        status = data['status']
        failure_message = data['failure_message']

        matching_instances = LambdaInstance.objects.filter(uuid=uuid)
        if matching_instances.exists():
            raise CustomAlreadyDoneError(CustomAlreadyDoneError.messages[
                'lambda_instance_already_exists'
                                         ])

        # Parse request json into a custom serializer
        # lambda_info = LambdaInstanceInfo(data=request.data)
        # try:
        #     # Check Instance info validity
        #     lambda_info.is_valid(raise_exception=True)
        # except ValidationError as exception:
        #     raise CustomValidationError(exception.detail)

        create_event = events.createLambdaInstance.delay(uuid, instance_name, instance_info, owner, status,
                                                         failure_message)

        status_code = rest_status.HTTP_202_ACCEPTED
        if settings.DEBUG:
            return Response({"status": {"code": status_code,
                                   "short_description": ResponseMessages.short_descriptions[
                                       'lambda_instances_create']},
                         "data": [
                             {"id": uuid}
                         ],
                         "debug": create_event.status
                         }, status=status_code)
        else:
            return Response({"status": {"code": status_code,
                                   "short_description": ResponseMessages.short_descriptions[
                                       'lambda_instances_create']},
                         "data": [
                             {"id": uuid}
                         ],}, status=status_code)

    @detail_route(methods=['post'], url_path="status")
    def updateStatus(self, request, uuid, *args, **kwargs):

        matching_instances = LambdaInstance.objects.filter(uuid=uuid)
        if not matching_instances.exists():
            raise CustomNotFoundError(CustomNotFoundError.messages['lambda_instance_not_found'])

        data = request.data

        status = data['status']
        failure_message = data['failure_message'] if 'failure_message' in data else None

        matching_instance = LambdaInstanceSerializer(matching_instances[0]).data
        if status == matching_instance['status']:
            raise CustomAlreadyDoneError(CustomAlreadyDoneError
                                         .messages['lambda_instance_already']
                                         .format(state=status))

        update_event = events.updateLambdaInstanceStatus.delay(uuid, status, failure_message)

        status_code = rest_status.HTTP_202_ACCEPTED

        if settings.DEBUG:
            return Response({
                "status": {"code": status_code,
                           "short_description": ResponseMessages.short_descriptions[
                                       'lambda_instances_update']},
                "data": [{"id": uuid}],
                "debug": update_event.status,
            }, status=status_code)
        else:
            return Response({
                "status": {"code": status_code,
                           "short_description": ResponseMessages.short_descriptions[
                                       'lambda_instances_update']},
                "data": [{"id": uuid}],
            }, status=status_code)

    def destroy(self, request, uuid, *args, **kwargs):

        lambda_instances = LambdaInstance.objects.filter(uuid=uuid)
        if not lambda_instances.exists():
            raise CustomNotFoundError(CustomNotFoundError.messages['lambda_instance_not_found'])

        destroy_event = events.deleteLambdaInstance.delay(uuid)

        status_code = rest_status.HTTP_202_ACCEPTED

        if settings.DEBUG:
            return Response({
                "status": {"code": status_code,
                           "short_description": ResponseMessages.short_descriptions[
                                       'lambda_instances_delete']},
                "data": [{"id": uuid},],
                "debug": destroy_event.status,
            }, status=status_code)
        else:
            return Response({
                "status": {"code": status_code,
                           "short_description": ResponseMessages.short_descriptions[
                                       'lambda_instances_delete']},
                "data": [{"id": uuid},],
            }, status=status_code)



class LambdaInstanceCounterView(APIView):

    authentication_classes = KamakiTokenAuthentication,
    permission_classes = IsAuthenticated,
    renderer_classes = JSONRenderer, XMLRenderer, BrowsableAPIRenderer

    def get(self, request, format=None):
        activeLambdaInstances = LambdaInstance.objects.filter(status="20").count()
        status_code = rest_status.HTTP_202_ACCEPTED
        return Response(
            {
                "status": {
                    "code": status_code,
                    "short_description": ResponseMessages.short_descriptions['lambda_instances_count'],
                },
                "data": {
                    "count": str(activeLambdaInstances),
                }

            },
            status=status_code)

class LambdaApplicationView(mixins.ListModelMixin, # debugging
                            mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):

    queryset = LambdaApplication.objects.all()
    serializer_class = LambdaApplicationSerializer
    authentication_classes = KamakiTokenAuthentication,
    permission_classes = IsAuthenticated,
    renderer_classes = JSONRenderer, XMLRenderer, BrowsableAPIRenderer

    lookup_field = 'uuid'

    def create(self, request, *args, **kwargs):
        """
        Create api call for lambda_application.
        :param request: The HTTP POST request making the call.
        :param args:
        :param kwargs:
        :return: A response object according to the outcome of the call.
        """
        data = request.data

        name = data['name']
        owner = request.user
        uuid = data['uuid']
        description = data['description']
        status = data['status']
        failure_message = data['failure_message']

        matching_applications = LambdaApplication.objects.filter(uuid=uuid)
        if matching_applications.exists():
            raise CustomAlreadyDoneError(CustomAlreadyDoneError.messages[
                'lambda_application_already_exists'
                                         ])

        create_event = events.createLambdaApplication.delay(
            uuid, status=status, name=name, description=description,
            owner=owner, failure_message=failure_message
        )

        status_code = rest_status.HTTP_202_ACCEPTED

        if settings.DEBUG:
            return Response({
                "status": {"code": status_code,
                           "short_description": ResponseMessages.short_descriptions[
                                       'lambda_applications_create']},
                "debug": create_event.status,
                "data": [{"id": uuid},],
            }, status=status_code)
        else:
            return Response({
                "status": {"code": status_code,
                           "short_description": ResponseMessages.short_descriptions[
                                       'lambda_application_create']},
                "data": [{"id": uuid},],
            }, status=status_code)

    @detail_route(methods=['post'], url_path="status")
    def updateStatus(self, request, uuid, *args, **kwargs):

        matching_applications = self.get_queryset().filter(uuid=uuid)
        if not matching_applications.exists():
            raise CustomNotFoundError(CustomNotFoundError.messages['application_not_found'])

        data = request.data
        status = data['status']
        failure_message = data['failure_message'] if 'failure_message' in data else None
        update_event = events.updateLambdaApplicationStatus.delay(uuid, status, failure_message)

        status_code = rest_status.HTTP_202_ACCEPTED

        matching_application = LambdaApplicationSerializer(matching_applications[0]).data
        if status == matching_application['status']:
            raise CustomAlreadyDoneError(CustomAlreadyDoneError
                                         .messages['lambda_instance_already']
                                         .format(state=status))

        if settings.DEBUG:
            return Response({
                "status": {"code": status_code,
                           "short_description": ResponseMessages.short_descriptions[
                                       'lambda_applications_update']},
                "data": [{"id": uuid}],
                "debug": update_event.status,
            }, status=status_code)
        else:
            return Response({
                "status": {"code": status_code,
                           "short_description": ResponseMessages.short_descriptions[
                                       'lambda_applications_update']},
                "data": [{"id": uuid}],
            }, status=status_code)

    def destroy(self, request, uuid, *args, **kwargs):

        applications = self.get_queryset().filter(uuid=uuid)
        if not applications.exists():
            raise CustomNotFoundError(CustomNotFoundError.messages['application_not_found'])

        destroy_event = events.deleteLambdaApplication.delay(uuid)

        status_code = rest_status.HTTP_202_ACCEPTED

        if settings.DEBUG:
            return Response({
                "status": {"code": status_code,
                           "short_description": ResponseMessages.short_descriptions[
                                       'lambda_applications_delete']},
                "data": [{"id": uuid},],
                "debug": destroy_event.status,
            }, status=status_code)
        else:
            return Response({
                "status": {"code": status_code,
                           "short_description": ResponseMessages.short_descriptions[
                                       'lambda_applications_delete']},
                "data": [{"id": uuid},],
            }, status=status_code)



class LambdaApplicationCounterView(APIView):

    authentication_classes = KamakiTokenAuthentication,
    permission_classes = IsAuthenticated,
    renderer_classes = JSONRenderer, XMLRenderer, BrowsableAPIRenderer

    def get(self, request, format=None):
        activeLambdaApplications = LambdaApplication.objects.filter(status="0").count()

        status_code = rest_status.HTTP_202_ACCEPTED
        return Response(
            {
                "status": {
                    "code": status_code,
                    "short_description": ResponseMessages.short_descriptions['lambda_applications_count'],
                },
                "data": {
                    "count": str(activeLambdaApplications),
                }

            },
            status=status_code)