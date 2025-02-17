from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from django.db.models import Count
from . import models, serializers, api_schemas
from . import permissions as custom_permissions
from drf_spectacular.openapi import OpenApiTypes
import logging

logger = logging.getLogger(__name__)

@extend_schema(tags=['instances'])
class JiraInstanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Jira instances.
    """
    queryset = models.JiraInstance.objects.all()
    serializer_class = serializers.JiraInstanceSerializer
    permission_classes = [IsAuthenticated, custom_permissions.IsInstanceAdmin]

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.JiraInstanceCreateSerializer
        return self.serializer_class

    @extend_schema(
        summary="Sync projects from Jira instance",
        description="Fetches and syncs all projects from the Jira instance",
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Sync all projects from Jira instance."""
        instance = self.get_object()
        try:
            logger.info(f"Starting sync for instance {instance.name} (ID: {instance.id})")
            success = instance.sync_projects()
            
            if success:
                logger.info(f"Successfully synced projects for instance {instance.name}")
                return Response({
                    'status': 'success',
                    'message': f'Successfully synced projects from {instance.name}'
                })
            
            logger.error(f"Failed to sync projects for instance {instance.name}")
            return Response(
                {'status': 'error', 'message': 'Error syncing projects'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception(f"Exception while syncing projects for instance {instance.name}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

@extend_schema(tags=['projects'])
class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Jira projects.
    """
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    permission_classes = [IsAuthenticated, custom_permissions.IsProjectMember]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related('jira_instance').annotate(
            snapshots_count=Count('snapshots'),
            exports_count=Count('exports')
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.ProjectCreateSerializer
        return self.serializer_class

    @extend_schema(**api_schemas.project_sync_docs)
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Sync project configuration from Jira."""
        project = self.get_object()
        try:
            project.sync_configuration()
            return Response({'status': 'success', 'message': 'Project configuration synced'})
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(**api_schemas.project_export_docs)
    @action(detail=True, methods=['post'])
    def export(self, request, pk=None):
        """Export project documentation."""
        project = self.get_object()
        format = request.data.get('format', 'pdf')
        sections = request.data.get('sections', ['overview'])

        try:
            file_path = project.export_documentation(format, sections)
            return Response({'file_path': file_path})
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class ConfigurationSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.ConfigurationSnapshot.objects.all()
    serializer_class = serializers.ConfigurationSnapshotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset.select_related('project')

class DocumentationExportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.DocumentationExport.objects.all()
    serializer_class = serializers.DocumentationExportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset.select_related('project') 