import hmac
import hashlib
from functools import wraps
from django.http import HttpResponseForbidden
from django.conf import settings
from . import models

def verify_webhook_signature(func):
    """Decorator to verify Jira webhook signatures."""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not settings.JIRA_WEBHOOK_SECRET:
            return func(request, *args, **kwargs)
        
        signature = request.headers.get('X-Hub-Signature')
        if not signature:
            return HttpResponseForbidden('No signature provided')
        
        expected_signature = hmac.new(
            settings.JIRA_WEBHOOK_SECRET.encode(),
            request.body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return HttpResponseForbidden('Invalid signature')
        
        return func(request, *args, **kwargs)
    return wrapper

class WebhookHandler:
    def handle_configuration_change(self, data: dict) -> None:
        """Handle configuration change webhook."""
        project_key = data.get('project', {}).get('key')
        if not project_key:
            return
        
        try:
            project = models.Project.objects.get(key=project_key)
            project.sync_configuration()
        except models.Project.DoesNotExist:
            pass

    def handle_project_update(self, data: dict) -> None:
        """Handle project update webhook."""
        project_key = data.get('project', {}).get('key')
        if not project_key:
            return
        
        try:
            project = models.Project.objects.get(key=project_key)
            # Update project details
            project.name = data['project'].get('name', project.name)
            project.save()
            # Sync configuration if needed
            if data.get('configurationChanged', False):
                project.sync_configuration()
        except models.Project.DoesNotExist:
            pass

    def handle_security_change(self, data: dict) -> None:
        """Handle security change webhook."""
        project_key = data.get('project', {}).get('key')
        if not project_key:
            return
        
        try:
            project = models.Project.objects.get(key=project_key)
            # Create a new snapshot for security changes
            project.snapshots.create(
                configuration_type='security_change',
                data=data
            )
            # Sync full configuration
            project.sync_configuration()
        except models.Project.DoesNotExist:
            pass 