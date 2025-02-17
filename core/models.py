from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from typing import List
from . import jira_api
from django.conf import settings

class JiraInstance(models.Model):
    name = models.CharField(max_length=255)
    base_url = models.URLField()
    username = models.EmailField(null=True, blank=True)
    api_token = models.CharField(max_length=255, null=True, blank=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Jira Instance')
        verbose_name_plural = _('Jira Instances')
        ordering = ['name']


    def get_workflow_schemes(self, project_id):
        """Fetch workflow schemes for a project"""
        api = self.get_api_client()
        try:
            # First get the workflow scheme ID
            project_response = api._make_request('GET', f'/rest/api/3/project/{project_id}')
            
            if project_response and 'workflowScheme' in project_response:
                scheme_id = project_response['workflowScheme']['id']
                # Then get the workflow scheme details
                scheme_response = api._make_request('GET', f'/rest/api/3/workflowscheme/{scheme_id}')
                return scheme_response if scheme_response else {}
            return {}
        except Exception as e:
            print(f"Error in get_workflow_schemes: {str(e)}")
            return {}

    def get_permission_scheme(self, project_id):
        """Fetch permission scheme for a project"""
        return self.make_request('GET', f'/rest/api/2/project/{project_id}/permissionscheme')

    def get_security_scheme(self, project_id):
        """Fetch security scheme for a project"""
        return self.make_request('GET', f'/rest/api/2/project/{project_id}/issuesecuritylevelscheme')

    def sync_projects(self):
        """Fetch and sync all projects from Jira."""
        api = self.get_api_client()
        try:
            # Fetch all projects from Jira API
            projects_response = api._make_request('GET', '/rest/api/3/project')
            
            for jira_project in projects_response:
                # Get or create project
                project, created = self.projects.get_or_create(
                    project_id=jira_project['id'],
                    defaults={
                        'key': jira_project['key'],
                        'name': jira_project['name'],
                        'last_sync': timezone.now(),
                        'configuration_snapshot': {}
                    }
                )
                
                if not created:
                    # Update existing project
                    project.name = jira_project['name']
                    project.save()
                
                # Sync project configuration
                project.sync_configuration()
            
            # Update instance last_sync time
            self.last_sync = timezone.now()
            self.save()
            
            return True
        except Exception as e:
            print(f"Error syncing projects: {str(e)}")
            return False

    def get_api_client(self):
        """Get an instance of the Jira API client."""
        from .jira_api import JiraAPI
        return JiraAPI(
            base_url=self.base_url,
            auth_token=self.auth_token
        )

def get_default_configuration():
    return {
        "project": {},
        "workflows": [],
        "permissions": {},
        "fields": [],
        "sync_timestamp": None
    }

class Project(models.Model):
    jira_instance = models.ForeignKey(
        JiraInstance,
        on_delete=models.CASCADE,
        related_name='projects',
        verbose_name=_('Jira Instance')
    )
    project_id = models.CharField(_('Project ID'), max_length=20)
    key = models.CharField(_('Project Key'), max_length=20)
    name = models.CharField(_('Project Name'), max_length=200)
    documentation_url = models.URLField(
        _('Documentation URL'),
        max_length=500,
        blank=True,
        null=True,
        help_text=_('URL to external project documentation (e.g., Confluence)')
    )
    configuration_snapshot = models.JSONField(
        _('Configuration Snapshot'),
        default=get_default_configuration
    )
    last_sync = models.DateTimeField(_('Last Sync'))

    class Meta:
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')
        unique_together = [['jira_instance', 'project_id']]

    def __str__(self):
        return f"{self.key} - {self.name}"

    def get_jira_api(self) -> jira_api.JiraAPI:
        """Get a JiraAPI instance for this project."""
        return jira_api.JiraAPI(
            self.jira_instance.base_url,
            self.jira_instance.auth_token
        )

    def sync_configuration(self) -> None:
        """Sync project configuration from Jira."""
        api = self.get_jira_api()
        config = api.sync_project_configuration(self.key)
        
        # Update configuration snapshot
        self.configuration_snapshot = config
        self.last_sync = timezone.now()
        self.save()

        # Create configuration snapshot record
        self.snapshots.create(
            configuration_type='full_sync',
            data=config
        )

    def export_documentation(self, format: str, sections: List[str]) -> str:
        """Export project documentation in the specified format."""
        from . import exporters
        exporter = exporters.get_exporter(format)
        file_path = exporter.export(self, sections)
        
        # Create export record
        self.exports.create(
            format=format,
            file_path=file_path
        )
        
        return file_path

class ConfigurationSnapshot(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='snapshots',
        verbose_name=_('Project')
    )
    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)
    configuration_type = models.CharField(_('Configuration Type'), max_length=50)
    data = models.JSONField(_('Configuration Data'))

    class Meta:
        verbose_name = _('Configuration Snapshot')
        verbose_name_plural = _('Configuration Snapshots')

    def __str__(self):
        return f"{self.project.key} - {self.configuration_type} - {self.timestamp}"

class DocumentationExport(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='exports')
    format = models.CharField(max_length=10, choices=[
        ('pdf', 'PDF'),
        ('html', 'HTML'),
        ('xml', 'XML')
    ])
    file = models.FileField(upload_to='exports/%Y/%m/%d/', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='pending')
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project.key} - {self.format} ({self.created_at:%Y-%m-%d %H:%M})"

class ApplicationSettings(models.Model):
    DEFAULT_EXPORT_FORMATS = [
        ('html', 'HTML'),
        ('pdf', 'PDF'),
        ('md', 'Markdown')
    ]

    default_jira_instance = models.ForeignKey(
        JiraInstance,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_for_settings',
        verbose_name=_('Default Jira Instance')
    )
    default_export_format = models.CharField(
        _('Default Export Format'),
        max_length=10,
        choices=DEFAULT_EXPORT_FORMATS,
        default='html'
    )
    auto_sync_enabled = models.BooleanField(
        _('Auto-sync Enabled'),
        default=False
    )
    sync_interval = models.IntegerField(
        _('Sync Interval (minutes)'),
        default=60,
        help_text=_('How often to sync projects (in minutes)')
    )

    class Meta:
        verbose_name = _('Application Settings')
        verbose_name_plural = _('Application Settings')

    @classmethod
    def get_settings(cls):
        """Get or create the application settings"""
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings 