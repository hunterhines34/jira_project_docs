import requests
from django.conf import settings
from typing import Dict, Any, List, Optional
from datetime import datetime
import base64

class JiraAPI:
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url.rstrip('/')
        # Cloud-specific authentication
        email = settings.JIRA_CLOUD_EMAIL
        encoded_auth = base64.b64encode(f"{email}:{auth_token}".encode()).decode()
        self.headers = {
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Jira API with detailed logging."""
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        
        print(f"Making {method} request to: {url}")
        
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            print(f"Response status code: {response.status_code}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Status code: {e.response.status_code}")
                print(f"Response content: {e.response.content.decode()}")
            raise

    def get_project(self, project_key: str) -> Dict[str, Any]:
        """Get project details using v3 API."""
        return self._make_request('GET', f'/rest/api/3/project/{project_key}')

    def get_project_workflows(self, project_key: str) -> List[Dict[str, Any]]:
        """Get workflows for a project using v3 API."""
        response = self._make_request('GET', f'/rest/api/3/workflow/search')
        workflows = response.get('values', [])
        return [w for w in workflows if any(
            p.get('key') == project_key 
            for p in w.get('projects', [])
        )]

    def get_project_permissions(self, project_key: str) -> Dict[str, Any]:
        """Get complete permission scheme information for a project using v3 API."""
        try:
            # First get the permission scheme ID associated with the project
            scheme_info = self._make_request('GET', f'/rest/api/3/project/{project_key}/permissionscheme')
            print(f"\nPermission Scheme Initial Response for {project_key}:")
            print(f"Keys available: {scheme_info.keys() if scheme_info else 'None'}")
            print(f"Raw scheme info: {scheme_info}")
            
            if not scheme_info or 'id' not in scheme_info:
                print(f"No permission scheme found for project {project_key}")
                return {}
            
            # Get detailed permission scheme information including all grants
            scheme_id = scheme_info['id']
            detailed_scheme = self._make_request('GET', f'/rest/api/3/permissionscheme/{scheme_id}')
            print(f"\nDetailed Permission Scheme Response:")
            print(f"Keys available: {detailed_scheme.keys() if detailed_scheme else 'None'}")
            print(f"Raw detailed scheme: {detailed_scheme}")
            
            result = {
                'scheme': detailed_scheme,
                'permissions': detailed_scheme.get('permissions', []),
                'name': detailed_scheme.get('name'),
                'description': detailed_scheme.get('description'),
                'id': scheme_id
            }
            print(f"\nFinal Permission Scheme Result:")
            print(f"Keys being returned: {result.keys()}")
            print(f"Number of permissions: {len(result['permissions'])}")
            return result
            
        except Exception as e:
            print(f"Error getting permission scheme: {str(e)}")
            raise

    def get_project_fields(self) -> List[Dict[str, Any]]:
        """Get all fields including custom fields using v3 API."""
        fields = self._make_request('GET', f'/rest/api/3/field')
        return [{
            'id': field.get('id'),
            'name': field.get('name'),
            'type': field.get('schema', {}).get('type'),
            'custom': field.get('custom', False),
            'description': field.get('description')
        } for field in fields]

    def sync_project_configuration(self, project_key: str) -> dict:
        """Fetch complete project configuration from Jira Cloud using v3 API."""
        try:
            project_info = self.get_project(project_key)
            project_id = project_info['id']
            
            print(f"\nStarting configuration sync for project {project_key} (ID: {project_id})")
            
            config = {
                "project": project_info,
                "workflows": self.get_project_workflows(project_key),
                "workflow_scheme": self.get_project_workflow_scheme(project_id),
                "permission_scheme": self.get_project_permissions(project_key),
                "security_scheme": self.get_project_security_scheme(project_key),
                "fields": self.get_project_fields(),
                "issue_types": self.get_project_issue_types(project_key),
                "issue_type_scheme": self.get_issue_type_scheme(project_key),
                "issue_type_screen_scheme": self.get_issue_type_screen_scheme(project_key),
                "screens": self.get_project_screens(project_key),
                "field_configuration_scheme": self.get_field_configuration_scheme(project_key),
                "components": self.get_project_components(project_key),
                "versions": self.get_project_versions(project_key),
                "roles": self.get_project_roles(project_key),
                "priority_scheme": self.get_priority_scheme(project_key),
                "sync_timestamp": datetime.now().isoformat()
            }
            
            print(f"\nFinal Configuration Keys:")
            print(f"Top-level keys: {config.keys()}")
            print(f"Workflow scheme present: {'workflow_scheme' in config}")
            print(f"Permission scheme present: {'permission_scheme' in config}")
            print(f"Security scheme present: {'security_scheme' in config}")
            
            return config
            
        except requests.exceptions.RequestException as e:
            print(f"Error syncing project configuration: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response content: {e.response.content.decode()}")
            raise

    def test_connection(self, project_key: str) -> bool:
        """Test the API connection with a simple project query."""
        try:
            self.get_project(project_key)
            return True
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False 

    def get_project_issue_types(self, project_key: str) -> List[Dict[str, Any]]:
        """Get issue types for a project using v3 API."""
        try:
            # Get project details which includes issueTypes
            project = self.get_project(project_key)
            
            # Debug logging
            print(f"Project response for {project_key}:")
            print(f"Keys available: {project.keys()}")
            if 'issueTypes' in project:
                print(f"Found {len(project['issueTypes'])} issue types")
            
            return project.get('issueTypes', [])
        except Exception as e:
            print(f"Error in get_project_issue_types: {str(e)}")
            raise

    def _get_project_id(self, project_key: str) -> str:
        """Helper method to get project ID from project key."""
        try:
            project = self.get_project(project_key)
            return project['id']
        except Exception as e:
            print(f"Error getting project ID for {project_key}: {str(e)}")
            raise

    def get_issue_type_scheme(self, project_key: str) -> Dict[str, Any]:
        """Get issue type scheme for a project using v3 API."""
        try:
            project_id = self._get_project_id(project_key)
            # The API expects projectId as a query parameter array
            response = self._make_request('GET', f'/rest/api/3/issuetypescheme/project?projectId={project_id}')
            
            # The API returns a PageBeanIssueTypeSchemeProjects object
            # We want to return the actual schemes with their project associations
            return {
                'schemes': response.get('values', []),
                'total': response.get('total', 0),
                'is_last': response.get('isLast', True)
            }
        except Exception as e:
            print(f"Error getting issue type scheme for {project_key}: {str(e)}")
            raise

    def get_issue_type_screen_scheme(self, project_key: str) -> Dict[str, Any]:
        """Get issue type screen scheme for a project using v3 API."""
        project_id = self._get_project_id(project_key)
        return self._make_request('GET', f'/rest/api/3/issuetypescreenscheme/project?projectId={project_id}')
    
    def get_project_components(self, project_key: str) -> List[Dict[str, Any]]:
        """Get components for a project using v3 API."""
        return self._make_request('GET', f'/rest/api/3/project/{project_key}/components')

    def get_project_versions(self, project_key: str) -> List[Dict[str, Any]]:
        """Get versions for a project using v3 API."""
        return self._make_request('GET', f'/rest/api/3/project/{project_key}/versions') 

    def get_project_roles(self, project_key: str) -> List[Dict[str, Any]]:
        """Get detailed project roles including members using v3 API."""
        try:
            print(f"\nFetching roles for project {project_key}")
            
            # First get all roles for the project
            roles_response = self._make_request('GET', f'/rest/api/3/project/{project_key}/role')
            print(f"Initial roles response keys: {roles_response.keys() if roles_response else 'None'}")
            
            detailed_roles = []
            for role_key, role_url in roles_response.items():
                print(f"\nProcessing role: {role_key}")
                
                role_id = role_url.split('/')[-1]
                role_details = self._make_request('GET', 
                    f'/rest/api/3/project/{project_key}/role/{role_id}')
                
                print(f"Role details keys: {role_details.keys() if role_details else 'None'}")
                print(f"Number of actors: {len(role_details.get('actors', []))}")
                
                actors = []
                for actor in role_details.get('actors', []):
                    actor_info = {
                        'displayName': actor.get('displayName'),
                        'type': actor.get('type'),
                    }
                    
                    # Handle avatar URLs for users
                    if actor.get('type') == 'atlassian-user-role-actor' and actor.get('avatarUrl'):
                        # Use the complete avatar URL directly from the API response
                        actor_info['avatarUrl'] = actor.get('avatarUrl')
                        print(f"Avatar URL for {actor.get('displayName')}: {actor_info['avatarUrl']}")
                    
                    actors.append(actor_info)
                
                detailed_roles.append({
                    'name': role_key,
                    'id': role_id,
                    'description': role_details.get('description'),
                    'actors': actors
                })
            
            print(f"\nFinal roles data:")
            print(f"Number of roles: {len(detailed_roles)}")
            print(f"Sample role names: {[r['name'] for r in detailed_roles]}")
            
            return detailed_roles
            
        except Exception as e:
            print(f"Error getting project roles: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return []

    def get_priority_scheme(self, project_key: str) -> Dict[str, Any]:
        """Get priority scheme and priorities for a project using v3 API."""
        try:
            project_id = self._get_project_id(project_key)
            print(f"\nFetching priority scheme for project {project_key} (ID: {project_id})")
            
            # First, get all priority schemes
            schemes_response = self._make_request('GET', '/rest/api/3/priorityscheme')
            print(f"Priority schemes response: {schemes_response}")
            
            # Find either the project-specific scheme or the default scheme
            project_scheme = None
            default_scheme = None
            
            for scheme in schemes_response.get('values', []):
                # Check if this scheme is specifically assigned to our project
                projects = scheme.get('projects', {}).get('values', [])
                if any(str(p.get('id')) == str(project_id) for p in projects):
                    project_scheme = scheme
                    break
                # Keep track of the default scheme as fallback
                if scheme.get('isDefault'):
                    default_scheme = scheme
            
            # Use project-specific scheme or fall back to default
            selected_scheme = project_scheme or default_scheme
            
            if not selected_scheme:
                print(f"No priority scheme found for project {project_key}")
                return {}
            
            print(f"Using priority scheme: {selected_scheme.get('name')} (ID: {selected_scheme.get('id')})")
            
            # Get priorities for this scheme
            scheme_id = selected_scheme.get('id')
            priorities_response = self._make_request('GET', f'/rest/api/3/priorityscheme/{scheme_id}/priorities')
            print(f"Priorities response: {priorities_response}")
            
            # Get global priorities for additional details
            global_priorities = self._make_request('GET', '/rest/api/3/priority')
            priorities_map = {p['id']: p for p in global_priorities}
            
            # Enhance priorities with global priority details
            enhanced_priorities = []
            for priority in priorities_response.get('values', []):
                priority_id = priority.get('id')
                if priority_id in priorities_map:
                    global_priority = priorities_map[priority_id]
                    enhanced_priorities.append({
                        **priority,
                        'iconUrl': global_priority.get('iconUrl'),
                        'statusColor': global_priority.get('statusColor'),
                        'description': global_priority.get('description')
                    })
            
            result = {
                'id': scheme_id,
                'name': selected_scheme.get('name'),
                'description': selected_scheme.get('description'),
                'isDefault': selected_scheme.get('isDefault', False),
                'priorities': enhanced_priorities,
                'defaultPriorityId': selected_scheme.get('defaultPriorityId')
            }
            
            print(f"\nFinal priority scheme result:")
            print(f"Keys: {result.keys()}")
            print(f"Number of priorities: {len(result['priorities'])}")
            print(f"Sample priority data: {result['priorities'][0] if result['priorities'] else 'No priorities'}")
            
            return result
            
        except Exception as e:
            print(f"Error getting priority scheme: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return {}

    def get_project_screens(self, project_key: str) -> Dict[str, Any]:
        """Get screens and screen schemes for a project using v3 API."""
        try:
            print("\nStarting screen fetch process...")
            project_id = self._get_project_id(project_key)
            
            # Get the issue type screen scheme for this project
            screen_schemes_response = self._make_request('GET', 
                f'/rest/api/3/issuetypescreenscheme/project?projectId={project_id}')
            print(f"Project screen schemes response: {screen_schemes_response}")
            
            screen_ids = set()
            issue_type_screen_schemes = screen_schemes_response.get('values', [])
            
            # Get all screen schemes that are associated with this project's screen scheme
            project_screen_scheme_ids = set()
            for scheme_data in issue_type_screen_schemes:
                scheme = scheme_data.get('issueTypeScreenScheme', {})
                if scheme.get('id'):
                    project_screen_scheme_ids.add(scheme.get('id'))
            
            # Get all screen schemes
            screen_schemes = self._make_request('GET', '/rest/api/3/screenscheme')
            print(f"\nAll screen schemes: {screen_schemes}")
            
            # Extract screen IDs only from relevant screen schemes
            for screen_scheme in screen_schemes.get('values', []):
                try:
                    # Only process screen schemes that are associated with this project
                    if any(screen_scheme.get('name', '').startswith(f"{scheme.get('name', '').split(':')[0]}:")
                           for scheme_data in issue_type_screen_schemes
                           for scheme in [scheme_data.get('issueTypeScreenScheme', {})]):
                        
                        screens_dict = screen_scheme.get('screens', {})
                        print(f"\nProcessing project-related screen scheme: {screen_scheme.get('name')}")
                        print(f"Screens dict: {screens_dict}")
                        
                        for screen_type, screen_id in screens_dict.items():
                            if screen_id:
                                screen_ids.add(screen_id)
                                print(f"Added screen ID: {screen_id} from {screen_type}")
                except Exception as e:
                    print(f"Error processing screen scheme: {str(e)}")
                    continue

            # Now get details for each screen using batched requests
            screens = []
            print(f"\nFetching details for {len(screen_ids)} screens: {screen_ids}")
            
            # Convert screen_ids to list and process in batches
            screen_id_list = list(screen_ids)
            batch_size = 25  # API default max results
            
            for i in range(0, len(screen_id_list), batch_size):
                batch = screen_id_list[i:i + batch_size]
                try:
                    # Build query string for this batch
                    id_params = "&".join([f"id={id}" for id in batch])
                    screens_response = self._make_request('GET', f'/rest/api/3/screens?{id_params}')
                    batch_screens = screens_response.get('values', [])
                    
                    for screen in batch_screens:
                        try:
                            screen_id = screen.get('id')
                            if not screen_id:
                                continue
                                
                            # Get tabs for this screen
                            tabs_response = self._make_request('GET', f'/rest/api/3/screens/{screen_id}/tabs')
                            print(f"Raw tabs response for screen {screen_id}: {tabs_response}")
                            
                            # Handle tabs as a list
                            screen_tabs = []
                            if isinstance(tabs_response, list):
                                for tab in tabs_response:
                                    tab_id = tab.get('id')
                                    if tab_id:
                                        # Get fields for each tab
                                        fields_response = self._make_request('GET', 
                                            f'/rest/api/3/screens/{screen_id}/tabs/{tab_id}/fields')
                                        fields = fields_response.get('values', []) if isinstance(fields_response, dict) else fields_response
                                        tab['fields'] = fields
                                        screen_tabs.append(tab)
                            
                            screen['tabs'] = screen_tabs
                            screens.append(screen)
                            print(f"Successfully processed screen {screen_id} with {len(screen_tabs)} tabs")
                            
                        except Exception as e:
                            print(f"Error processing screen {screen_id}: {str(e)}")
                            print(f"Error type: {type(e)}")
                            import traceback
                            print(f"Traceback: {traceback.format_exc()}")
                            continue
                            
                except Exception as e:
                    print(f"Error processing batch: {str(e)}")
                    continue

            result = {
                'screens': screens,
                'screen_schemes': issue_type_screen_schemes,
                'total_screens': len(screens),
                'total_schemes': len(issue_type_screen_schemes)
            }
            
            print(f"\nFinal screens result:")
            print(f"Total screens found: {len(screens)}")
            print(f"Total schemes found: {len(issue_type_screen_schemes)}")
            print(f"Screen IDs found: {screen_ids}")
            print(f"First screen sample: {screens[0] if screens else 'No screens'}")
            
            return result
            
        except Exception as e:
            print(f"Error getting screens for project {project_key}: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return {
                'screens': [],
                'screen_schemes': issue_type_screen_schemes,
                'total_screens': 0,
                'total_schemes': len(issue_type_screen_schemes)
            }

    def get_field_configuration_scheme(self, project_key: str) -> Dict[str, Any]:
        """Get field configuration scheme for a project using v3 API."""
        try:
            project_id = self._get_project_id(project_key)
            print(f"\nFetching field configuration scheme for project {project_key} (ID: {project_id})")
            
            # Get project's field configuration scheme
            project_schemes = self._make_request('GET', 
                f'/rest/api/3/fieldconfigurationscheme/project?projectId={project_id}')
            print(f"Project's field configuration schemes: {project_schemes}")
            
            schemes = []
            if project_schemes and project_schemes.get('values'):
                for project_scheme in project_schemes.get('values', []):
                    try:
                        # Get field configurations for this project
                        field_configs = self._make_request('GET', 
                            f'/rest/api/3/fieldconfiguration')
                        print(f"Field configurations: {field_configs}")
                        
                        # Only process configurations that belong to this project
                        project_configs = [
                            config for config in field_configs.get('values', [])
                            if (config.get('name', '').endswith(f'for Project {project_key}') or 
                                config.get('name') == 'Default Field Configuration')
                        ]
                        
                        for config in project_configs:
                            config_id = config.get('id')
                            if not config_id:
                                continue
                                
                            # Get configuration details
                            config_details = self._make_request('GET', 
                                f'/rest/api/3/fieldconfiguration/{config_id}/fields')
                            print(f"Configuration details for {config_id}: {config_details}")
                            
                            schemes.append({
                                'id': config_id,
                                'name': config.get('name'),
                                'description': config.get('description'),
                                'configurations': [{
                                    'id': config_id,
                                    'name': config.get('name'),
                                    'description': config.get('description'),
                                    'fields': config_details.get('values', [])
                                }]
                            })
                    except Exception as e:
                        print(f"Error processing configuration: {str(e)}")
                        continue
            
            print(f"Final field configuration schemes: {schemes}")
            return schemes
            
        except Exception as e:
            print(f"Error getting field configuration scheme: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return []

    def get_project_security_scheme(self, project_key: str) -> Dict[str, Any]:
        """Get issue security scheme information for a project using v3 API."""
        try:
            project_id = self._get_project_id(project_key)
            print(f"\nFetching security scheme for project {project_key} (ID: {project_id})")
            
            # Get the issue security scheme associated with the project
            security_scheme = self._make_request('GET', 
                f'/rest/api/3/issuesecurityschemes/project?projectId={project_id}')
            print(f"\nSecurity Scheme Initial Response:")
            print(f"Keys available: {security_scheme.keys() if security_scheme else 'None'}")
            print(f"Raw security scheme: {security_scheme}")
            
            if not security_scheme or not security_scheme.get('values'):
                print(f"No security scheme found for project {project_key}")
                return {}
            
            # Get the first security scheme
            scheme = security_scheme['values'][0]
            scheme_id = scheme.get('id')
            print(f"\nSelected scheme ID: {scheme_id}")
            print(f"Selected scheme data: {scheme}")
            
            if scheme_id:
                # Get the security levels
                security_levels = self._make_request('GET',
                    f'/rest/api/3/issuesecurityschemes/{scheme_id}/members')
                print(f"\nSecurity Levels Response:")
                print(f"Keys available: {security_levels.keys() if security_levels else 'None'}")
                print(f"Raw security levels: {security_levels}")
                
                result = {
                    'scheme': scheme,
                    'levels': security_levels.get('levels', []),
                    'name': scheme.get('name'),
                    'description': scheme.get('description'),
                    'defaultSecurityLevelId': scheme.get('defaultSecurityLevelId')
                }
                print(f"\nFinal Security Scheme Result:")
                print(f"Keys being returned: {result.keys()}")
                print(f"Number of levels: {len(result['levels'])}")
                return result
                
            return {}
            
        except Exception as e:
            print(f"Error getting security scheme: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return {}

    def get_project_workflow_scheme(self, project_id: str) -> Dict[str, Any]:
        """Get workflow scheme associated with a project."""
        try:
            print(f"\nFetching workflow scheme for project {project_id}")
            
            # Get workflow scheme associations
            response = self._make_request('GET', f'/rest/api/3/workflowscheme/project?projectId={project_id}')
            
            if response and response.get('values'):
                scheme = response['values'][0]  # Get first scheme since one project has one scheme
                workflow_scheme = scheme.get('workflowScheme', {})
                
                result = {
                    'name': workflow_scheme.get('name'),
                    'description': workflow_scheme.get('description'),
                    'defaultWorkflow': workflow_scheme.get('defaultWorkflow'),
                    'issueTypeMappings': workflow_scheme.get('issueTypeMappings', {}),
                    'id': workflow_scheme.get('id')
                }
                
                # Get detailed workflow information for each mapped workflow
                workflows = {}
                workflow_ids = set([result['defaultWorkflow']] + list(result['issueTypeMappings'].values()))
                
                for workflow_name in workflow_ids:
                    if workflow_name:
                        workflow_details = self._make_request('GET', f'/rest/api/3/workflow/search?workflowName={workflow_name}')
                        if workflow_details.get('values'):
                            workflow = workflow_details['values'][0]
                            workflows[workflow_name] = {
                                'description': workflow.get('description'),
                                'steps': workflow.get('steps', 0),  # Use the steps count directly
                                'isDefault': workflow.get('isDefault', False)
                            }
                
                result['workflows'] = workflows
                return result
                
            return {}
            
        except Exception as e:
            print(f"Error getting workflow scheme: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return {}