from rest_framework import serializers
from . import models
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class JiraInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.JiraInstance
        fields = ['id', 'name', 'base_url', 'api_version', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class JiraInstanceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.JiraInstance
        fields = ['id', 'name', 'base_url', 'api_version', 'auth_token']

class ProjectSerializer(serializers.ModelSerializer):
    jira_instance = JiraInstanceSerializer(read_only=True)
    snapshots_count = serializers.IntegerField(read_only=True)
    exports_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = models.Project
        fields = [
            'id', 'jira_instance', 'project_id', 'key', 'name',
            'configuration_snapshot', 'last_sync', 'snapshots_count',
            'exports_count'
        ]
        read_only_fields = ['configuration_snapshot', 'last_sync']

class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Project
        fields = ['jira_instance', 'project_id', 'key', 'name']

class ConfigurationSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ConfigurationSnapshot
        fields = ['id', 'project', 'configuration_type', 'data', 'timestamp']
        read_only_fields = ['timestamp']

class DocumentationExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DocumentationExport
        fields = ['id', 'project', 'format', 'file_path', 'generated_at']
        read_only_fields = ['file_path', 'generated_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password', 'first_name', 'last_name')
    
    def create(self, validated_data):
        user = get_user_model().objects.create_user(**validated_data)
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data 