from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from .serializers import (
    CurrentOrganizationResponseSerializer,
    OrganizationSerializer,
)
from .utils import get_current_membership, is_owner_or_admin


class CurrentOrganizationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Organizations"],
        summary="Get current organization",
        description="Returns the current organization workspace and the user's membership role.",
        responses=CurrentOrganizationResponseSerializer,
    )
    def get(self, request):
        membership = get_current_membership(request)

        serializer = CurrentOrganizationResponseSerializer({
            "organization": membership.organization,
            "membership": membership,
        })

        return Response(serializer.data)

    @extend_schema(
        tags=["Organizations"],
        summary="Update current organization",
        description="Updates the current organization profile. Only OWNER and ADMIN can update.",
        request=OrganizationSerializer,
        responses=OrganizationSerializer,
    )
    def patch(self, request):
        membership = get_current_membership(request)

        if not is_owner_or_admin(membership):
            raise PermissionDenied(
                "Only organization owners and admins can update organization settings."
            )

        serializer = OrganizationSerializer(
            membership.organization,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)