from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.artifacts.serializers import ArtifactUploadSerializer, SourceArtifactSerializer
from apps.artifacts.services import create_artifact_from_upload
from apps.cases.models import ReviewCase


class CaseArtifactListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=ArtifactUploadSerializer,
        responses={201: SourceArtifactSerializer},
    )
    def post(self, request, id):
        case = get_object_or_404(ReviewCase, id=id)
        serializer = ArtifactUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        artifact = create_artifact_from_upload(
            case=case,
            uploaded_file=serializer.validated_data["file"],
            artifact_type=serializer.validated_data["artifact_type"],
            uploaded_by=request.user,
            correlation_id=getattr(request, "correlation_id", None),
        )

        response_serializer = SourceArtifactSerializer(artifact)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(responses={200: SourceArtifactSerializer(many=True)})
    def get(self, request, id):
        case = get_object_or_404(ReviewCase, id=id)
        artifacts = case.artifacts.all().order_by("-uploaded_at")
        serializer = SourceArtifactSerializer(artifacts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
