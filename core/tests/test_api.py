from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .. import models
import json

class JiraInstanceAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.instance = models.JiraInstance.objects.create(
            name='Test Instance',
            base_url='https://test.atlassian.net',
            api_version='3',
            auth_token='test-token'
        )

    def test_list_instances(self):
        response = self.client.get(reverse('api:instance-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Instance')

    def test_create_instance(self):
        data = {
            'name': 'New Instance',
            'base_url': 'https://new.atlassian.net',
            'api_version': '3',
            'auth_token': 'new-token'
        }
        response = self.client.post(reverse('api:instance-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.JiraInstance.objects.count(), 2)

    def test_update_instance(self):
        data = {'name': 'Updated Instance'}
        response = self.client.patch(
            reverse('api:instance-detail', kwargs={'pk': self.instance.pk}),
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.name, 'Updated Instance')

class ProjectAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
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

    def test_list_projects(self):
        response = self.client.get(reverse('api:project-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['key'], 'TEST')

    def test_create_project(self):
        data = {
            'jira_instance': self.instance.pk,
            'project_id': '10001',
            'key': 'NEW',
            'name': 'New Project'
        }
        response = self.client.post(reverse('api:project-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.Project.objects.count(), 2)

    def test_sync_project(self):
        response = self.client.post(
            reverse('api:project-sync', kwargs={'pk': self.project.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')

    def test_export_project(self):
        data = {
            'format': 'json',
            'sections': ['overview', 'workflows']
        }
        response = self.client.post(
            reverse('api:project-export', kwargs={'pk': self.project.pk}),
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('file_path' in response.data) 