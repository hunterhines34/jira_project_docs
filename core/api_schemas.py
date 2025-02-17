from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from . import serializers

# Project API schemas
project_list_docs = {
    'summary': "List all projects",
    'description': "Returns a list of all Jira projects with their configuration snapshots.",
    'responses': {200: serializers.ProjectSerializer(many=True)}
}

project_create_docs = {
    'summary': "Create a new project",
    'description': "Creates a new Jira project and syncs its configuration.",
    'request': serializers.ProjectCreateSerializer,
    'responses': {201: serializers.ProjectSerializer}
}

project_sync_docs = {
    'summary': "Sync project configuration",
    'description': "Syncs the project configuration from Jira and creates a new snapshot.",
    'responses': {
        200: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT
    },
    'examples': [
        OpenApiExample(
            'Success Response',
            value={'status': 'success', 'message': 'Project configuration synced'}
        )
    ]
}

project_export_docs = {
    'summary': "Export project documentation",
    'description': "Exports project documentation in the specified format.",
    'parameters': [
        OpenApiParameter(
            name='format',
            type=str,
            enum=['pdf', 'html', 'md', 'json', 'yaml'],
            description='Export format'
        ),
        OpenApiParameter(
            name='sections',
            type=list,
            description='List of sections to include'
        )
    ],
    'responses': {
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT
    },
    'examples': [
        OpenApiExample(
            'Success Response',
            value={'file_path': '/media/exports/TEST_doc_20240320.pdf'}
        )
    ]
} 