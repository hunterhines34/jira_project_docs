from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse, FileResponse, HttpResponse
from . import models
from django.shortcuts import get_object_or_404, render
from django.db.models import Q
from django.views.generic.edit import CreateView
from django.http import JsonResponse, HttpResponse
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from .webhooks import verify_webhook_signature, WebhookHandler
import json
from django.template.loader import render_to_string
from . import forms
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import JiraInstance
import logging
import traceback
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
import xml.etree.ElementTree as ET
import markdown
import os

logger = logging.getLogger(__name__)

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['instances_count'] = models.JiraInstance.objects.count()
        context['projects_count'] = models.Project.objects.count()
        context['exports_count'] = models.DocumentationExport.objects.count()
        return context

class ProjectListView(LoginRequiredMixin, ListView):
    model = models.Project
    template_name = 'core/project_list.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search', '')
        instance = self.request.GET.get('instance', '')
        
        if search:
            queryset = queryset.filter(
                Q(key__icontains=search) |
                Q(name__icontains=search)
            )
        
        if instance:
            queryset = queryset.filter(jira_instance_id=instance)
            
        return queryset.select_related('jira_instance')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jira_instances'] = models.JiraInstance.objects.all()
        return context

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = models.Project
    template_name = 'core/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_snapshots'] = self.object.snapshots.all()[:5]
        return context

class ReportListView(LoginRequiredMixin, ListView):
    model = models.DocumentationExport
    template_name = 'core/report_list.html'
    context_object_name = 'exports'

class SettingsView(LoginRequiredMixin, View):
    template_name = 'core/settings.html'

    def get(self, request):
        settings = models.ApplicationSettings.get_settings()
        form = forms.ApplicationSettingsForm(instance=settings)
        return render(request, 'core/settings.html', {
            'form': form,
            'settings': settings
        })

    def post(self, request):
        settings = models.ApplicationSettings.get_settings()
        form = forms.ApplicationSettingsForm(request.POST, instance=settings)
        
        if form.is_valid():
            form.save()
            response = HttpResponse(status=200)
            response['HX-Trigger'] = json.dumps({
                'showMessage': {
                    'message': 'Settings updated successfully',
                    'type': 'success'
                }
            })
            return response
        
        return render(request, 'core/settings.html', {
            'form': form,
            'settings': settings
        })

# Webhook Views
@method_decorator(verify_webhook_signature, name='dispatch')
class ConfigurationChangeWebhook(View):
    def post(self, request, *args, **kwargs):
        handler = WebhookHandler()
        handler.handle_configuration_change(request.json())
        return JsonResponse({'status': 'success'})

@method_decorator(verify_webhook_signature, name='dispatch')
class ProjectUpdateWebhook(View):
    def post(self, request, *args, **kwargs):
        handler = WebhookHandler()
        handler.handle_project_update(request.json())
        return JsonResponse({'status': 'success'})

@method_decorator(verify_webhook_signature, name='dispatch')
class SecurityChangeWebhook(View):
    def post(self, request, *args, **kwargs):
        handler = WebhookHandler()
        handler.handle_security_change(request.json())
        return JsonResponse({'status': 'success'})

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = models.Project
    template_name = 'core/modals/project_create.html'
    fields = ['jira_instance', 'project_id', 'key', 'name']

class ProjectSyncView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            project = get_object_or_404(models.Project, pk=pk)
            project.sync_configuration()
            
            # Return success response with HX-Trigger
            response = HttpResponse("Sync completed")
            response['HX-Trigger'] = json.dumps({
                'showMessage': {
                    'message': f'Successfully synced {project.key}',
                    'type': 'success'
                }
            })
            return response
            
        except Exception as e:
            # Return error response with HX-Trigger
            response = HttpResponse(str(e), status=400)
            response['HX-Trigger'] = json.dumps({
                'showMessage': {
                    'message': f'Error syncing project: {str(e)}',
                    'type': 'error'
                }
            })
            return response

class ProjectExportView(LoginRequiredMixin, View):
    def get(self, request, pk):
        project = get_object_or_404(models.Project, pk=pk)
        
        # If format is specified, handle the export
        export_format = request.GET.get('format')
        if export_format:
            if export_format == 'pdf':
                # Handle PDF export
                return self.export_pdf(project)
            elif export_format == 'html':
                # Handle HTML export
                return self.export_html(project)
        
        # Otherwise show the modal
        return TemplateResponse(request, 'core/modals/project_export.html', {
            'project': project
        })

    def export_pdf(self, project):
        # Add PDF export logic here
        return HttpResponse("PDF export not yet implemented")

    def export_html(self, project):
        # Add HTML export logic here
        return HttpResponse("HTML export not yet implemented")

class ProjectOverviewView(LoginRequiredMixin, DetailView):
    model = models.Project
    template_name = 'core/includes/project_overview.html'
    context_object_name = 'project'

class ProjectIssueTypesView(LoginRequiredMixin, DetailView):
    model = models.Project
    template_name = 'core/includes/project_issue_types.html'
    context_object_name = 'project'

class ProjectScreensView(LoginRequiredMixin, DetailView):
    model = models.Project
    template_name = 'core/includes/project_screens.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        
        try:
            # Get screens from configuration snapshot
            config = project.configuration_snapshot or {}
            screens_data = config.get('screens', {})
            
            print("\nDebug - Project Screens View:")
            print(f"Config keys: {config.keys()}")
            print(f"Screens data: {screens_data}")
            print(f"Total screens: {screens_data.get('total_screens', 0)}")
            print(f"Total schemes: {screens_data.get('total_schemes', 0)}")
            
            context.update({
                'debug': True,  # Enable debug output in template
                'screens_data': screens_data
            })
            
        except Exception as e:
            print(f"Error fetching screen data: {str(e)}")
            context.update({
                'error_message': str(e)
            })
        
        return context

class ProjectPrioritiesView(LoginRequiredMixin, DetailView):
    model = models.Project
    template_name = 'core/includes/project_priorities.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        
        try:
            # Get priority scheme from configuration snapshot
            config = project.configuration_snapshot or {}
            priority_scheme = config.get('priority_scheme', {})
            
            print("\nDebug - Project Priorities View:")
            print(f"Config keys: {config.keys()}")
            print(f"Priority scheme data: {priority_scheme}")
            
            context.update({
                'debug': True  # Enable debug output in template
            })
            
        except Exception as e:
            print(f"Error fetching priority data: {str(e)}")
            context.update({
                'error_message': str(e)
            })
        
        return context

class ProjectRolesView(LoginRequiredMixin, DetailView):
    model = models.Project
    template_name = 'core/includes/project_roles.html'
    context_object_name = 'project'

class ProjectWorkflowsView(LoginRequiredMixin, DetailView):
    model = models.Project
    template_name = 'core/includes/project_workflows.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        
        try:
            # Get workflow scheme from configuration snapshot
            config = project.configuration_snapshot or {}
            workflow_scheme = config.get('workflow_scheme', {})
            
            print("Debug - Configuration keys:", config.keys())
            print("Debug - Workflow scheme data:", workflow_scheme)
            
            context.update({
                'workflow_scheme': workflow_scheme,
                'debug': True  # Enable debug output in template
            })
            
        except Exception as e:
            print(f"Error fetching workflow data: {str(e)}")
            context.update({
                'error_message': str(e)
            })
        
        return context

class ProjectSecurityView(LoginRequiredMixin, DetailView):
    model = models.Project
    template_name = 'core/includes/project_security.html'
    context_object_name = 'project'

class ProjectFieldsView(LoginRequiredMixin, DetailView):
    model = models.Project
    template_name = 'core/includes/project_fields.html'
    context_object_name = 'project'

class ProjectLastSyncView(LoginRequiredMixin, View):
    def get(self, request, pk):
        project = get_object_or_404(models.Project, pk=pk)
        return HttpResponse(f"Last synced: {project.last_sync|default:'Never'}")

class ProjectActivitiesView(LoginRequiredMixin, View):
    def get(self, request, pk):
        project = get_object_or_404(models.Project, pk=pk)
        return TemplateResponse(request, 'core/includes/project_overview.html', {'project': project}) 

class ProjectComponentsView(LoginRequiredMixin, DetailView):
    model = models.Project
    template_name = 'core/includes/project_components.html'
    context_object_name = 'project'

class ProjectVersionsView(LoginRequiredMixin, DetailView):
    model = models.Project
    template_name = 'core/includes/project_versions.html'
    context_object_name = 'project'

def project_search(request):
    search_query = request.GET.get('search', '').strip()
    
    if search_query:
        projects = models.Project.objects.filter(
            Q(name__icontains=search_query) |
            Q(key__icontains=search_query)
        ).select_related('jira_instance')
    else:
        projects = models.Project.objects.all().select_related('jira_instance')
    
    return render(request, 'core/partials/project_list_content.html', {
        'projects': projects
    })
    
def recent_activity(request):
    time_filter = request.GET.get('time_filter', 'all')  # Default to 'all'
    
    # Base querysets
    projects_qs = models.Project.objects.exclude(last_sync__isnull=True)
    exports_qs = models.DocumentationExport.objects.select_related('project')
    
    # Apply time filtering
    if time_filter != 'all':
        time_threshold = timezone.now()
        if time_filter == 'today':
            time_threshold = time_threshold - timezone.timedelta(days=1)
        elif time_filter == 'week':
            time_threshold = time_threshold - timezone.timedelta(weeks=1)
        elif time_filter == 'month':
            time_threshold = time_threshold - timezone.timedelta(days=30)
            
        projects_qs = projects_qs.filter(last_sync__gte=time_threshold)
        exports_qs = exports_qs.filter(created_at__gte=time_threshold)
    
    # Get recent projects
    recent_projects = projects_qs.order_by('-last_sync')[:5]
    recent_exports = exports_qs.order_by('-created_at')[:5]
    
    activities = []
    
    # Add projects to activities
    for project in recent_projects:
        activities.append({
            'type': 'project_sync',
            'object': project,
            'timestamp': project.last_sync,
            'message': f'Project {project.key} was synced'
        })

    # Add exports to activities
    for export in recent_exports:
        activities.append({
            'type': 'export',
            'object': export,
            'timestamp': export.created_at,
            'message': f'Documentation exported for {export.project.key}'
        })

    # Sort activities
    def get_timestamp(activity):
        return activity['timestamp'] or timezone.datetime.min.replace(tzinfo=timezone.utc)
    
    activities.sort(key=get_timestamp, reverse=True)
    activities = activities[:5]

    return render(request, 'core/includes/recent_activity.html', {
        'activities': activities,
        'current_filter': time_filter
    })

def sync_all(request):
    # Add your sync logic here
    return JsonResponse({
        'message': 'Sync started successfully',
        'type': 'success'
    })

class InstanceListView(LoginRequiredMixin, ListView):
    model = models.JiraInstance
    template_name = 'core/instance_list.html'
    context_object_name = 'instances'
    
    def get_queryset(self):
        return models.JiraInstance.objects.all().order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for instance in context['instances']:
            instance.project_count = models.Project.objects.filter(jira_instance=instance).count()
        return context

class ExportListView(LoginRequiredMixin, ListView):
    model = models.DocumentationExport
    template_name = 'core/export_list.html'
    context_object_name = 'exports'
    
    def get_queryset(self):
        return models.DocumentationExport.objects.all().order_by('-created_at')

@login_required
def generate_report(request):
    if request.method == 'POST':
        project_id = request.POST.get('project')
        export_format = request.POST.get('format')
        
        try:
            project = models.Project.objects.get(id=project_id)
            
            # Create export record
            export = models.DocumentationExport.objects.create(
                project=project,
                format=export_format,
                generated_by=request.user,
                status='processing'
            )

            # Get project configuration
            config = project.configuration_snapshot or {}
            
            if not config:
                raise ValueError("No configuration data available for this project")

            context = {
                'project': project,
                'sections': ['issue_types', 'screens', 'workflows', 'security', 'fields'],
                'generated_at': timezone.now(),
                'generated_by': request.user
            }

            response = None
            if export_format == 'pdf':
                response = generate_pdf_report(context, export)
            elif export_format == 'html':
                response = generate_html_report(context, export)
            elif export_format == 'xml':
                response = generate_xml_report(context, export)

            # Update export status
            export.status = 'completed'
            export.save()

            # Return response with HTMX headers for redirect and modal closure
            response['HX-Redirect'] = reverse('core:exports')
            response['HX-Trigger'] = json.dumps({
                'showMessage': {
                    'message': f'Report generated successfully',
                    'type': 'success'
                }
            })
            return response

        except Exception as e:
            if export:
                export.status = 'failed'
                export.error_message = str(e)
                export.save()
            
            response = HttpResponse(status=500)
            response['HX-Trigger'] = json.dumps({
                'showMessage': {
                    'message': f'Error generating report: {str(e)}',
                    'type': 'error'
                }
            })
            return response

    # GET request - show the form
    projects = models.Project.objects.all()
    return render(request, 'core/modals/generate_report.html', {
        'projects': projects
    })

def generate_pdf_report(context, export):
    # First generate markdown
    md_content = render_to_string('exports/project_documentation.md', context)
    
    # Convert markdown to HTML
    html_content = markdown.markdown(md_content)
    
    # Create PDF from HTML
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    
    # Convert HTML to PDF elements
    for line in html_content.split('\n'):
        if line.startswith('#'):
            # Handle headers
            level = line.count('#')
            text = line.strip('#').strip()
            style = f'Heading{level}'
            elements.append(Paragraph(text, styles[style]))
        else:
            # Handle regular text
            if line.strip():
                elements.append(Paragraph(line, styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    
    # Save to export record
    export.file.save(
        f"{context['project'].key}_documentation.pdf", 
        buffer
    )
    
    return FileResponse(
        buffer, 
        as_attachment=True, 
        filename=f'{context["project"].key}_documentation.pdf'
    )

def generate_html_report(context, export):
    html_content = render_to_string('exports/project_documentation.html', context)
    
    # Save to export record
    export.file.save(
        f"{context['project'].key}_documentation.html", 
        io.StringIO(html_content)
    )
    
    response = HttpResponse(html_content, content_type='text/html')
    response['Content-Disposition'] = f'attachment; filename="{context["project"].key}_documentation.html"'
    return response

def generate_xml_report(context, export):
    # First generate markdown as base
    md_content = render_to_string('exports/project_documentation.md', context)
    
    # Create XML structure
    root = ET.Element("project_documentation")
    
    # Add metadata
    metadata = ET.SubElement(root, "metadata")
    ET.SubElement(metadata, "project_key").text = context['project'].key
    ET.SubElement(metadata, "project_name").text = context['project'].name
    ET.SubElement(metadata, "generated_at").text = context['generated_at'].isoformat()
    ET.SubElement(metadata, "generated_by").text = context['generated_by'].username
    
    # Add configuration sections
    config = context['project'].configuration_snapshot
    for section in context['sections']:
        section_elem = ET.SubElement(root, section)
        section_data = config.get(section, {})
        
        if isinstance(section_data, dict):
            for key, value in section_data.items():
                if isinstance(value, (str, int, float, bool)):
                    ET.SubElement(section_elem, key).text = str(value)
                elif isinstance(value, list):
                    items_elem = ET.SubElement(section_elem, f"{key}_items")
                    for item in value:
                        if isinstance(item, dict):
                            item_elem = ET.SubElement(items_elem, "item")
                            for item_key, item_value in item.items():
                                if isinstance(item_value, (str, int, float, bool)):
                                    ET.SubElement(item_elem, item_key).text = str(item_value)
    
    xml_str = ET.tostring(root, encoding='unicode', method='xml')
    
    # Save to export record
    export.file.save(
        f"{context['project'].key}_documentation.xml", 
        io.StringIO(xml_str)
    )
    
    response = HttpResponse(xml_str, content_type='application/xml')
    response['Content-Disposition'] = f'attachment; filename="{context["project"].key}_documentation.xml"'
    return response

def add_instance(request):
    if request.method == 'POST':
        form = forms.JiraInstanceForm(request.POST)
        if form.is_valid():
            instance = form.save()
            return HttpResponse(status=204)
    else:
        form = forms.JiraInstanceForm()
    
    return render(request, 'core/modals/instance_create.html', {
        'form': form
    })

def toggle_dropdown(request):
    return render(request, 'core/includes/dropdown_menu.html', {
        'user': request.user
    })

class ProjectEditView(LoginRequiredMixin, View):
    def get(self, request, pk):
        project = get_object_or_404(models.Project, pk=pk)
        form = forms.ProjectEditForm(instance=project)
        return render(request, 'core/modals/project_edit.html', {
            'form': form,
            'project': project
        })
    
    def post(self, request, pk):
        project = get_object_or_404(models.Project, pk=pk)
        form = forms.ProjectEditForm(request.POST, instance=project)
        
        if form.is_valid():
            form.save()
            response = HttpResponse(status=200)
            response['HX-Trigger'] = json.dumps({
                'showMessage': {
                    'message': 'Project updated successfully',
                    'type': 'success'
                },
                'refreshContent': True,
                'closeModal': True
            })
            return response
        
        return render(request, 'core/modals/project_edit.html', {
            'form': form,
            'project': project
        })

def project_workflows(request, project_id):
    """View for project workflows tab."""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        # Get the configuration snapshot and add debug info
        config = project.configuration_snapshot or {}
        workflow_scheme = config.get('workflow_scheme', {})
        
        print("\nDebug - Project Workflows View:")
        print(f"Config keys: {config.keys()}")
        print(f"Workflow scheme: {workflow_scheme}")
        
        context = {
            'project': project,
            'workflow_scheme': workflow_scheme,
            'debug': True,  # Enable debug output in template
            'error_message': None
        }
        
        if not workflow_scheme:
            context['error_message'] = "No workflow scheme found. Try syncing the project."
        
        return render(request, 'core/includes/project_workflows.html', context)
        
    except Exception as e:
        print(f"Error in project_workflows view: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render(request, 'core/includes/project_workflows.html', {
            'error_message': f"Error loading workflows: {str(e)}"
        })

@login_required
def create_instance(request):
    """Handle the instance creation POST request"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            base_url = request.POST.get('base_url')
            username = request.POST.get('username')
            api_token = request.POST.get('api_token')

            # Basic validation
            if not all([name, base_url, username, api_token]):
                raise ValueError("All fields are required")

            # Create the instance
            instance = JiraInstance.objects.create(
                name=name,
                base_url=base_url,
                username=username,
                api_token=api_token
            )
            
            # Return success with toast notification and redirect
            response = HttpResponse()
            response['HX-Trigger'] = json.dumps({
                'showMessage': {
                    'message': f'Jira instance "{instance.name}" was created successfully',
                    'type': 'success'
                }
            })
            response['HX-Redirect'] = reverse('core:instances')
            return response
            
        except Exception as e:
            context = {
                'error': str(e),
                'form_data': request.POST
            }
            return render(request, 'core/modals/instance_create.html', context)

@login_required
def edit_instance(request, instance_id):
    """Show the edit instance modal"""
    try:
        # Log the request
        logger.info(f"Editing instance {instance_id}")
        
        # Get the instance
        instance = JiraInstance.objects.get(id=instance_id)
        logger.info(f"Found instance: {instance.name}")
        
        if request.method == 'POST':
            try:
                # Update instance fields
                instance.name = request.POST.get('name')
                instance.base_url = request.POST.get('base_url')
                instance.username = request.POST.get('username')
                
                # Only update api_token if provided
                new_token = request.POST.get('api_token')
                if new_token:
                    instance.api_token = new_token
                    
                instance.save()
                logger.info(f"Successfully updated instance {instance.name}")
                
                # Return success with toast notification and redirect
                response = HttpResponse()
                response['HX-Trigger'] = json.dumps({
                    'showMessage': {
                        'message': f'Jira instance "{instance.name}" was updated successfully',
                        'type': 'success'
                    }
                })
                response['HX-Redirect'] = reverse('core:instances')
                return response
                
            except Exception as e:
                logger.error(f"Error updating instance: {str(e)}")
                logger.error(traceback.format_exc())
                return render(request, 'core/modals/instance_edit.html', {
                    'instance': instance,
                    'error': str(e)
                })
        
        # Render the edit form
        try:
            html = render_to_string('core/modals/instance_edit.html', {
                'instance': instance
            }, request=request)
            return HttpResponse(html)
        except Exception as template_error:
            logger.error(f"Template rendering error: {str(template_error)}")
            logger.error(traceback.format_exc())
            return HttpResponse(
                f"<div class='text-red-600 p-4'>Error rendering template: {str(template_error)}</div>",
                status=500
            )
                
    except JiraInstance.DoesNotExist:
        logger.error(f"Instance {instance_id} not found")
        return HttpResponse(
            "<div class='text-red-600 p-4'>Instance not found</div>",
            status=404
        )
    except Exception as e:
        logger.error(f"Unexpected error in edit_instance view: {str(e)}")
        logger.error(traceback.format_exc())
        return HttpResponse(
            f"<div class='text-red-600 p-4'>Unexpected error: {str(e)}</div>",
            status=500
        )

@login_required
def delete_instance(request, instance_id):
    """Delete a Jira instance"""
    if request.method == 'DELETE':
        try:
            instance = get_object_or_404(JiraInstance, id=instance_id)
            name = instance.name
            instance.delete()
            
            # Return success with toast notification and refresh
            response = HttpResponse()
            response['HX-Trigger'] = json.dumps({
                'showMessage': {
                    'message': f'Jira instance "{name}" was deleted successfully',
                    'type': 'success'
                }
            })
            response['HX-Refresh'] = 'true'
            return response
            
        except Exception as e:
            response = HttpResponse(str(e), status=500)
            response['HX-Trigger'] = json.dumps({
                'showMessage': {
                    'message': f'Error deleting instance: {str(e)}',
                    'type': 'error'
                }
            })
            return response
    return HttpResponseNotAllowed(['DELETE'])

@login_required
def export_list(request):
    try:
        # Get filter parameters
        project_id = request.GET.get('project')
        format_type = request.GET.get('format')
        date_range = request.GET.get('date_range')
        status = request.GET.get('status')

        # Start with all exports
        exports = models.DocumentationExport.objects.select_related('project').order_by('-created_at')

        # Apply filters
        if project_id and project_id.isdigit():
            exports = exports.filter(project_id=int(project_id))
        if format_type:
            exports = exports.filter(format=format_type)
        if status:
            exports = exports.filter(status=status)
        if date_range:
            time_threshold = timezone.now()
            if date_range == 'today':
                time_threshold = time_threshold - timezone.timedelta(days=1)
            elif date_range == 'week':
                time_threshold = time_threshold - timezone.timedelta(weeks=1)
            elif date_range == 'month':
                time_threshold = time_threshold - timezone.timedelta(days=30)
            exports = exports.filter(created_at__gte=time_threshold)

        # Get all projects for the filter dropdown
        projects = models.Project.objects.all()

        context = {
            'exports': exports,
            'projects': projects,
            'selected_project': project_id,
            'selected_format': format_type,
            'selected_date': date_range,
            'selected_status': status,
        }

        # Check if it's an HTMX request
        if request.headers.get('HX-Request'):
            return render(request, 'core/includes/reports_list.html', context)
        return render(request, 'core/report_list.html', context)
        
    except Exception as e:
        import traceback
        print(f"Error in export_list view: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        if request.headers.get('HX-Request'):
            return HttpResponse(
                f"Error loading reports: {str(e)}", 
                status=500
            )
        raise

@login_required
def delete_export(request, export_id):
    if request.method == 'DELETE':
        try:
            export = models.DocumentationExport.objects.get(id=export_id)
            
            # Delete the file if it exists
            if export.file:
                if os.path.exists(export.file.path):
                    os.remove(export.file.path)
            
            # Delete the export record
            export.delete()

            # Return the updated list
            return export_list(request)

        except models.DocumentationExport.DoesNotExist:
            return HttpResponse(status=404)
        except Exception as e:
            return HttpResponse(str(e), status=500)

    return HttpResponse(status=405)  # Method not allowed
