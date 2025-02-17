from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .. import models
import json

class ProjectViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
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
        self.client.login(username='testuser', password='testpass123')

    def test_project_list_view(self):
        response = self.client.get(reverse('core:projects'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/project_list.html')
        self.assertContains(response, 'TEST')
        self.assertContains(response, 'Test Project')

    def test_project_detail_view(self):
        response = self.client.get(
            reverse('core:project-detail', kwargs={'pk': self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/project_detail.html')
        self.assertContains(response, 'TEST')
        self.assertContains(response, 'Test Project')

    def test_project_sync_view(self):
        response = self.client.post(
            reverse('core:project-sync', kwargs={'pk': self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')

    def test_project_export_view(self):
        response = self.client.get(
            reverse('core:project-export', kwargs={'pk': self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/modals/project_export.html') 