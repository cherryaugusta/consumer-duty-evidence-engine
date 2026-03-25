from rest_framework import generics
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from apps.cases.models import ReviewCase

from .models import DocumentSection, SourceArtifact
from .serializers import (
    DocumentSectionSerializer,
    SourceArtifactCreateSerializer,
    SourceArtifactSerializer,
)
from .services import create_artifact_from_upload


class ArtifactListCreateView(generics.ListCreateAPIView):
    parser_classes = [MultiPartParser]

    def get_queryset(self):
        return SourceArtifact.objects.filter(case_id=self.kwargs["pk"]).order_by("-uploaded_at")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SourceArtifactCreateSerializer
        return SourceArtifactSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        case = ReviewCase.objects.get(pk=self.kwargs["pk"])
        artifact = create_artifact_from_upload(
            case=case,
            artifact_type=serializer.validated_data["artifact_type"],
            uploaded_file=serializer.validated_data["file"],
        )

        output = SourceArtifactSerializer(artifact, context=self.get_serializer_context())
        return Response(output.data, status=201)


class ArtifactDetailView(generics.RetrieveAPIView):
    queryset = SourceArtifact.objects.all()
    serializer_class = SourceArtifactSerializer


class ArtifactSectionsView(generics.ListAPIView):
    serializer_class = DocumentSectionSerializer

    def get_queryset(self):
        return DocumentSection.objects.filter(artifact_id=self.kwargs["pk"]).order_by(
            "section_index"
        )
