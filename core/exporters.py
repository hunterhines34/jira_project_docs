import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from django.conf import settings
from django.template.loader import render_to_string
import json
import yaml
import markdown
import weasyprint
from datetime import datetime

class BaseExporter(ABC):
    @abstractmethod
    def export(self, project, sections: List[str]) -> str:
        """Export project documentation and return the file path."""
        pass

    def _get_export_path(self, project, extension: str) -> str:
        """Generate export file path."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        sections_str = '_'.join(sorted(sections))
        filename = f"{project.key}_{project.jira_instance.name}_{sections_str}_{timestamp}.{extension}"
        return os.path.join(settings.MEDIA_ROOT, 'exports', filename)

    def get_export_data(self, project, sections: List[str]) -> Dict[str, Any]:
        """Get data structure for export."""
        return {
            'project_key': project.key,
            'project_name': project.name,
            'instance': project.jira_instance.name,
            'configuration': {
                'overview': project.configuration_snapshot['project'] if 'overview' in sections else None,
                'workflows': project.configuration_snapshot['workflows'] if 'workflows' in sections else None,
                'security': {
                    'permissions': project.configuration_snapshot['permissions'],
                    'security_levels': project.configuration_snapshot['security']
                } if 'security' in sections else None,
                'fields': {
                    'custom_fields': project.configuration_snapshot['fields'],
                    'configurations': project.configuration_snapshot['field_configurations']
                } if 'fields' in sections else None
            }
        }

class MarkdownExporter(BaseExporter):
    def export(self, project, sections: List[str]) -> str:
        context = {
            'project': project,
            'sections': sections,
        }
        content = render_to_string('exports/project_documentation.md', context)
        
        file_path = self._get_export_path(project, 'md')
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        return file_path

class HTMLExporter(BaseExporter):
    def export(self, project, sections: List[str]) -> str:
        context = {
            'project': project,
            'sections': sections,
        }
        content = render_to_string('exports/project_documentation.html', context)
        
        file_path = self._get_export_path(project, 'html')
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        return file_path

class PDFExporter(BaseExporter):
    def export(self, project, sections: List[str]) -> str:
        # First generate HTML
        html_exporter = HTMLExporter()
        html_path = html_exporter.export(project, sections)
        
        # Convert HTML to PDF
        pdf_path = self._get_export_path(project, 'pdf')
        weasyprint.HTML(filename=html_path).write_pdf(pdf_path)
        
        return pdf_path

class JSONExporter(BaseExporter):
    def export(self, project, sections: List[str]) -> str:
        data = {
            'project_key': project.key,
            'project_name': project.name,
            'instance': project.jira_instance.name,
            'configuration': {}
        }
        
        if 'overview' in sections:
            data['configuration']['overview'] = project.configuration_snapshot['project']
        if 'workflows' in sections:
            data['configuration']['workflows'] = project.configuration_snapshot['workflows']
        if 'security' in sections:
            data['configuration']['security'] = {
                'permissions': project.configuration_snapshot['permissions'],
                'security_levels': project.configuration_snapshot['security']
            }
        if 'fields' in sections:
            data['configuration']['fields'] = {
                'custom_fields': project.configuration_snapshot['fields'],
                'configurations': project.configuration_snapshot['field_configurations']
            }
        
        file_path = self._get_export_path(project, 'json')
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return file_path

class YAMLExporter(BaseExporter):
    def export(self, project, sections: List[str]) -> str:
        # Reuse JSON exporter's data structure
        json_data = JSONExporter().get_export_data(project, sections)
        
        file_path = self._get_export_path(project, 'yaml')
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            yaml.dump(json_data, f, default_flow_style=False)
        
        return file_path

def get_exporter(format: str) -> BaseExporter:
    """Factory function to get the appropriate exporter."""
    exporters = {
        'md': MarkdownExporter,
        'html': HTMLExporter,
        'pdf': PDFExporter,
        'json': JSONExporter,
        'yaml': YAMLExporter,
    }
    
    exporter_class = exporters.get(format)
    if not exporter_class:
        raise ValueError(f"Unsupported export format: {format}")
    
    return exporter_class() 