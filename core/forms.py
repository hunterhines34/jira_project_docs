from django import forms
from . import models
from .models import ApplicationSettings

class ProjectForm(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = ['jira_instance', 'project_id', 'key', 'name'] 

class JiraInstanceForm(forms.ModelForm):
    class Meta:
        model = models.JiraInstance
        fields = ['name', 'base_url', 'username', 'api_token', 'instance_type']
        widgets = {
            'instance_type': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            })
        }

class ApplicationSettingsForm(forms.ModelForm):
    class Meta:
        model = ApplicationSettings
        fields = ['default_jira_instance', 'default_export_format', 
                 'auto_sync_enabled', 'sync_interval']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sync_interval'].widget = forms.Select(choices=[
            (15, 'Every 15 minutes'),
            (60, 'Every hour'),
            (360, 'Every 6 hours'),
            (1440, 'Daily'),
        ]) 

class ProjectEditForm(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = ['name', 'documentation_url']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
                'placeholder': 'Project Name'
            }),
            'documentation_url': forms.URLInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
                'placeholder': 'https://confluence.example.com/display/PROJECT',
                'style': 'min-width: 400px; width: 100%;'
            })
        } 