from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch
from .. import models

class JiraInstanceTests(TestCase):
    def setUp(self):
        self.instance = models.JiraInstance.objects.create(
            name='Test Instance',
            base_url='https://test.atlassian.net',
            api_version='3',
            auth_token='test-token'
        )

    def test_str_representation(self):
        self.assertEqual(str(self.instance), 'Test Instance')

class ProjectTests(TestCase):
    def setUp(self):
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

    def test_str_representation(self):
        self.assertEqual(str(self.project), 'TEST - Test Project')

    def test_sync_configuration(self):
        # Mock the Jira API response
        mock_config = {
            'project': {'id': '10000', 'key': 'TEST'},
            'workflows': [],
            'permissions': {},
            'security': {},
            'fields': [],
            'field_configurations': []
        }
        
        with patch('core.jira_api.JiraAPI.sync_project_configuration') as mock_sync:
            mock_sync.return_value = mock_config
            self.project.sync_configuration()
            
            # Verify configuration was updated
            self.assertEqual(self.project.configuration_snapshot, mock_config)
            # Verify snapshot was created
            self.assertEqual(
                self.project.snapshots.filter(configuration_type='full_sync').count(),
                1
            ) 