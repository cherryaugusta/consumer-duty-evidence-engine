from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.artifacts.models import DocumentSection, SourceArtifact
from apps.artifacts.serializers import ArtifactUploadSerializer, SourceArtifactSerializer
from apps.artifacts.services import create_artifact_from_upload
from apps.cases.models import ReviewCase
from apps.parsing.tasks import parse_artifact_task


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

        parse_artifact_task.delay(str(artifact.id))

        return Response(
            SourceArtifactSerializer(artifact).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(responses={200: SourceArtifactSerializer(many=True)})
    def get(self, request, id):
        case = get_object_or_404(ReviewCase, id=id)
        artifacts = case.artifacts.all().order_by("-uploaded_at")
        return Response(
            SourceArtifactSerializer(artifacts, many=True).data,
            status=status.HTTP_200_OK,
        )


class ArtifactDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        artifact = get_object_or_404(SourceArtifact, pk=pk)
        return Response(SourceArtifactSerializer(artifact).data)


class ArtifactSectionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        artifact = get_object_or_404(SourceArtifact, pk=pk)

        sections = DocumentSection.objects.filter(artifact=artifact).order_by("section_index")

        return Response(
            [
                {
                    "id": str(section.id),
                    "artifact": str(artifact.id),
                    "section_index": section.section_index,
                    "heading": section.heading,
                    "text": section.text,
                    "page_number": section.page_number,
                }
                for section in sections
            ]
        )
