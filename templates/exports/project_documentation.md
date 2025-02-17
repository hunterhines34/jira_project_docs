# {{ project.name }} ({{ project.key }})

## Overview
- **Instance:** {{ project.jira_instance.name }}
- **Last Sync:** {{ project.last_sync|date:"F j, Y, P" }}
- **Description:** {{ project.configuration_snapshot.project.description|default:"No description" }}
- **Project Lead:** {{ project.configuration_snapshot.project.lead.displayName|default:"Not specified" }}

{% if 'issue_types' in sections %}
## Issue Types and Schemes
### Issue Types
{% for type in project.configuration_snapshot.issue_types %}
- **{{ type.name }}**
  - Description: {{ type.description|default:"No description" }}
  - Type: {{ type.type }}
  - Subtask: {{ type.subtask|yesno:"Yes,No" }}
{% endfor %}

### Issue Type Schemes
{% for scheme in project.configuration_snapshot.issue_type_scheme %}
- **{{ scheme.name }}**
  - Description: {{ scheme.description|default:"No description" }}
  - Default Issue Type: {{ scheme.defaultIssueType.name|default:"None" }}
{% endfor %}
{% endif %}

{% if 'screens' in sections %}
## Screens and Field Configuration
### Screens
{% for screen in project.configuration_snapshot.screens %}
- **{{ screen.name }}**
  - Description: {{ screen.description|default:"No description" }}
  {% for tab in screen.tabs %}
  - Tab: {{ tab.name }}
    {% for field in tab.fields %}
    - {{ field.name }}
    {% endfor %}
  {% endfor %}
{% endfor %}

### Field Configuration Schemes
{% for scheme in project.configuration_snapshot.field_configuration_scheme %}
- **{{ scheme.name }}**
  - Description: {{ scheme.description|default:"No description" }}
  {% for config in scheme.configurations %}
  - Configuration: {{ config.name }}
    {% for field in config.fields %}
    - {{ field.fieldId }}: {{ field.description|default:"No description" }}
    {% endfor %}
  {% endfor %}
{% endfor %}
{% endif %}

{% if 'workflows' in sections %}
## Workflows

### Workflow Schemes
{% for scheme in project.configuration_snapshot.workflow_scheme %}
- **{{ scheme.name }}**
  - Description: {{ scheme.description|default:"No description" }}
  - Default Workflow: {{ scheme.defaultWorkflow }}
  {% if scheme.issueTypeMappings %}
  - Issue Type Mappings:
    {% for type, workflow in scheme.issueTypeMappings.items %}
    - {{ type }}: {{ workflow }}
    {% endfor %}
  {% endif %}
{% endfor %}

### Individual Workflows
{% for workflow in project.configuration_snapshot.workflows %}
- **{{ workflow.name }}**
  - Description: {{ workflow.description|default:"No description" }}
  - Steps: {{ workflow.steps|length }}
  {% if workflow.statuses %}
  - Statuses:
    {% for status in workflow.statuses %}
    - {{ status.name }}
    {% endfor %}
  {% endif %}
{% endfor %}
{% endif %}

{% if 'security' in sections %}
## Security

### Permission Schemes
{% for permission in project.configuration_snapshot.permission_scheme.permissions %}
- **{{ permission.holder.type }}**: {{ permission.permission.name }}
  {% if permission.holder.parameter %}
  - Granted to: {{ permission.holder.parameter }}
  {% endif %}
{% endfor %}

### Security Scheme
{% if project.configuration_snapshot.security_scheme %}
- **Name:** {{ project.configuration_snapshot.security_scheme.name }}
- **Description:** {{ project.configuration_snapshot.security_scheme.description|default:"No description" }}
{% for level in project.configuration_snapshot.security_scheme.levels %}
- Security Level: {{ level.name }}
  - Description: {{ level.description|default:"No description" }}
{% endfor %}
{% endif %}
{% endif %}

{% if 'fields' in sections %}
## Fields

### Custom Fields
{% for field in project.configuration_snapshot.fields %}
{% if field.custom %}
- **{{ field.name }}** ({{ field.type }})
  - ID: {{ field.id }}
  - Description: {{ field.description|default:"No description" }}
{% endif %}
{% endfor %}

### Standard Fields
{% for field in project.configuration_snapshot.fields %}
{% if not field.custom %}
- **{{ field.name }}** ({{ field.type }})
  - ID: {{ field.id }}
  - Description: {{ field.description|default:"No description" }}
{% endif %}
{% endfor %}
{% endif %}

## Additional Components
{% if project.configuration_snapshot.components %}
### Components
{% for component in project.configuration_snapshot.components %}
- **{{ component.name }}**
  - Description: {{ component.description|default:"No description" }}
  - Lead: {{ component.lead.displayName|default:"No lead assigned" }}
{% endfor %}
{% endif %}

{% if project.configuration_snapshot.versions %}
### Versions
{% for version in project.configuration_snapshot.versions %}
- **{{ version.name }}**
  - Description: {{ version.description|default:"No description" }}
  - Status: {{ version.released|yesno:"Released,Unreleased" }}
  {% if version.releaseDate %}
  - Release Date: {{ version.releaseDate }}
  {% endif %}
{% endfor %}
{% endif %}

{% if project.configuration_snapshot.priority_scheme %}
### Priority Scheme
- **Name:** {{ project.configuration_snapshot.priority_scheme.name }}
- **Description:** {{ project.configuration_snapshot.priority_scheme.description|default:"No description" }}
{% for priority in project.configuration_snapshot.priority_scheme.priorities %}
- {{ priority.name }}
  - Description: {{ priority.description|default:"No description" }}
  {% if priority.iconUrl %}
  - Icon: {{ priority.iconUrl }}
  {% endif %}
{% endfor %}
{% endif %} 