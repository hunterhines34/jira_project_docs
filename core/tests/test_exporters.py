from django.test import TestCase
from django.core.files.storage import default_storage
from django.utils import timezone
from django.conf import settings
from .. import models, exporters
import os
import json

class ExporterTests(TestCase):
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
            configuration_snapshot={
                'project': {'key': 'TEST', 'name': 'Test Project'},
                'workflows': [{'name': 'Test Workflow', 'steps': ['Open', 'Closed']}],
                'permissions': {'scheme': 'Default'},
                'security': {'levels': []},
                'fields': [{'name': 'Custom Field', 'type': 'text'}],
                'field_configurations': []
            },
            last_sync=timezone.now()
        )

    def test_markdown_export(self):
        exporter = exporters.MarkdownExporter()
        file_path = exporter.export(self.project, ['overview', 'workflows'])
        
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, 'r') as f:
            content = f.read()
            self.assertIn('# Test Project (TEST)', content)
            self.assertIn('Test Workflow', content)

    def test_html_export(self):
        exporter = exporters.HTMLExporter()
        file_path = exporter.export(self.project, ['overview', 'fields'])
        
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, 'r') as f:
            content = f.read()
            self.assertIn('<title>Test Project (TEST)', content)
            self.assertIn('Custom Field', content)

    def test_json_export(self):
        exporter = exporters.JSONExporter()
        file_path = exporter.export(self.project, ['overview'])
        
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, 'r') as f:
            data = json.load(f)
            self.assertEqual(data['project_key'], 'TEST')
            self.assertEqual(data['project_name'], 'Test Project')

    def tearDown(self):
        # Clean up exported files
        for root, dirs, files in os.walk(settings.MEDIA_ROOT):
            for file in files:
                if file.startswith('TEST_'):
                    os.remove(os.path.join(root, file)) 