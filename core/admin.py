from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from . import models

# Change the admin site title, header, and index title
admin.site.site_header = "Jira Admin Documentation Generator"
admin.site.site_title = "Jira Admin Documentation Generator"
admin.site.index_title = "Jira Admin Documentation Generator"

@admin.register(models.JiraInstance)
class JiraInstanceAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_url', 'username', 'last_sync', 'created_at', 'updated_at', 'sync_button')
    search_fields = ('name', 'base_url', 'username')
    readonly_fields = ('created_at', 'updated_at', 'last_sync')
    ordering = ('name',)
    list_per_page = 25

    def sync_button(self, obj):
        return format_html(
            '<a class="button" href="{}">Sync Projects</a>',
            f'/admin/core/jirainstance/{obj.id}/sync/'
        )
    sync_button.short_description = 'Sync'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:instance_id>/sync/',
                self.admin_site.admin_view(self.sync_instance),
                name='jirainstance-sync',
            ),
        ]
        return custom_urls + urls

    def sync_instance(self, request, instance_id):
        from django.contrib import messages
        from django.http import HttpResponseRedirect
        try:
            instance = models.JiraInstance.objects.get(id=instance_id)
            if instance.sync_projects():
                messages.success(request, f'Successfully synced projects from {instance.name}')
            else:
                messages.error(request, f'Error syncing projects from {instance.name}')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return HttpResponseRedirect("../")

@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('key', 'name', 'jira_instance', 'last_sync', 'sync_button')
    list_filter = ('jira_instance',)
    search_fields = ('key', 'name')
    readonly_fields = ('last_sync',)
    ordering = ('key',)
    list_per_page = 25

    def save_model(self, request, obj, form, change):
        if not obj.last_sync:  # If last_sync is not set
            obj.last_sync = timezone.now()  # Set it to current time
        super().save_model(request, obj, form, change)

    def sync_button(self, obj):
        return format_html(
            '<a class="button" href="{}">Sync Now</a>',
            f'/admin/core/project/{obj.id}/sync/'
        )
    sync_button.short_description = 'Sync'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:project_id>/sync/',
                self.admin_site.admin_view(self.sync_project),
                name='project-sync',
            ),
        ]
        return custom_urls + urls

    def sync_project(self, request, project_id):
        from django.contrib import messages
        from django.http import HttpResponseRedirect
        try:
            project = models.Project.objects.get(id=project_id)
            project.sync_configuration()
            messages.success(request, f'Successfully synced project {project.key}')
        except Exception as e:
            messages.error(request, f'Error syncing project: {str(e)}')
        return HttpResponseRedirect("../")

@admin.register(models.ConfigurationSnapshot)
class ConfigurationSnapshotAdmin(admin.ModelAdmin):
    list_display = ('project', 'configuration_type', 'timestamp')
    list_filter = ('configuration_type', 'project')
    search_fields = ('project__key', 'project__name')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    list_per_page = 25

@admin.register(models.DocumentationExport)
class DocumentationExportAdmin(admin.ModelAdmin):
    list_display = ['project', 'format', 'created_at', 'generated_by', 'status']
    list_filter = ['format', 'status', 'created_at']
    search_fields = ['project__key', 'project__name', 'generated_by__username']
    readonly_fields = ['created_at', 'generated_by', 'status', 'error_message']
    list_per_page = 25
    ordering = ['-created_at']

    def download_link(self, obj):
        return format_html(
            '<a href="{}" class="button" target="_blank">Download</a>',
            obj.file_path
        )
    download_link.short_description = 'Download' 