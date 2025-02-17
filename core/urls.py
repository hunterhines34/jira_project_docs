from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Web Views
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('projects/', views.ProjectListView.as_view(), name='projects'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project-detail'),
    path('reports/', views.ReportListView.as_view(), name='reports'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    
    # Project Actions
    path('projects/create/', views.ProjectCreateView.as_view(), name='project-create'),
    path('projects/<int:pk>/sync/', views.ProjectSyncView.as_view(), name='project-sync'),
    path('projects/<int:pk>/export/', views.ProjectExportView.as_view(), name='project-export'),
    
    # Project Tabs
    path('projects/<int:pk>/overview/', views.ProjectOverviewView.as_view(), name='project-overview'),
    path('projects/<int:pk>/workflows/', views.ProjectWorkflowsView.as_view(), name='project-workflows'),
    path('projects/<int:pk>/security/', views.ProjectSecurityView.as_view(), name='project-security'),
    path('projects/<int:pk>/fields/', views.ProjectFieldsView.as_view(), name='project-fields'),
    
    # Project detail tab views
    path('projects/<int:pk>/issue-types/', 
         views.ProjectIssueTypesView.as_view(), name='project-issue-types'),
    path('projects/<int:pk>/screens/', 
         views.ProjectScreensView.as_view(), name='project-screens'),
    path('projects/<int:pk>/priorities/', 
         views.ProjectPrioritiesView.as_view(), name='project-priorities'),
    path('projects/<int:pk>/roles/', 
         views.ProjectRolesView.as_view(), name='project-roles'),
    
    # Webhook Endpoints
    path('webhooks/configuration-change/', views.ConfigurationChangeWebhook.as_view(), name='webhook-config-change'),
    path('webhooks/project-update/', views.ProjectUpdateWebhook.as_view(), name='webhook-project-update'),
    path('webhooks/security-change/', views.SecurityChangeWebhook.as_view(), name='webhook-security-change'),
    
    # Project Last Sync
    #path('projects/<int:pk>/last-sync/', views.ProjectLastSyncView.as_view(), name='project-last-sync'),
    path('projects/<int:pk>/activities/', views.ProjectActivitiesView.as_view(), name='project-activities'),
    path('projects/<int:pk>/components/', 
         views.ProjectComponentsView.as_view(), name='project-components'),
    path('projects/<int:pk>/versions/', 
         views.ProjectVersionsView.as_view(), name='project-versions'),
    path('projects/search/', views.project_search, name='project-search'),
    path('recent-activity/', views.recent_activity, name='recent-activity'),
    path('sync-all/', views.sync_all, name='sync-all'),
    path('instances/', views.InstanceListView.as_view(), name='instances'),
    path('exports/', views.export_list, name='exports'),
    path('reports/generate/', views.generate_report, name='generate-report'),
    path('add-instance/', views.add_instance, name='add-instance'),
    path('toggle-dropdown/', views.toggle_dropdown, name='toggle-dropdown'),
    path('projects/<int:pk>/edit/', views.ProjectEditView.as_view(), name='project-edit'),
    path('projects/<int:project_id>/workflows/', views.project_workflows, name='project-workflows'),
    path('instances/add/', views.add_instance, name='add-instance'),
    path('instances/create/', views.create_instance, name='instance-create'),
    path('instances/<int:instance_id>/edit/', views.edit_instance, name='edit-instance'),
    path('instances/<int:instance_id>/delete/', views.delete_instance, name='delete-instance'),
    path('exports/<int:export_id>/delete/', views.delete_export, name='delete-export'),
] 