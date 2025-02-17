from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch
from .. import models
import json

class WebhookTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.instance = models.JiraInstance.objects.create(
            name='Test Instance',
            base_url='https://test.atlassian.net',
            api_version='3',
            auth_token='test-token'
        )
        self.project = models.Project.objects.create(
            jira_instance=self.instance,
            project_id='10000',
            key='TEST',
            name='Test Project',
            configuration_snapshot={},
            last_sync=timezone.now()
        )

    @patch('core.models.Project.sync_configuration')
    def test_configuration_change_webhook(self, mock_sync):
        data = {
            'project': {'key': 'TEST'},
            'timestamp': '2024-03-20T10:00:00Z',
            'event': 'configuration_changed'
        }
        response = self.client.post(
            reverse('core:webhook-config-change'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        mock_sync.assert_called_once()

    @patch('core.models.Project.sync_configuration')
    def test_project_update_webhook(self, mock_sync):
        data = {
            'project': {
                'key': 'TEST',
                'name': 'Updated Project Name'
            },
            'configurationChanged': True
        }
        response = self.client.post(
            reverse('core:webhook-project-update'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Refresh project from database
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Updated Project Name')
        mock_sync.assert_called_once()

    def test_security_change_webhook(self):
        data = {
            'project': {'key': 'TEST'},
            'securityScheme': {'id': '10000', 'name': 'New Security Scheme'}
        }
        response = self.client.post(
            reverse('core:webhook-security-change'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify snapshot was created
        snapshot = self.project.snapshots.latest('timestamp')
        self.assertEqual(snapshot.configuration_type, 'security_change')
        self.assertEqual(snapshot.data['securityScheme']['id'], '10000') 