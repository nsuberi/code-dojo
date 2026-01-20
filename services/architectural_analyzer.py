"""Architectural analyzer for PR code changes.

Analyzes dependencies, API endpoints, schema changes, and component boundaries.
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from services.code_parser import CodeParser, Import, APIRoute, DatabaseModel


@dataclass
class DependencyChange:
    """Represents a change in dependencies."""
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)


@dataclass
class APIChange:
    """Represents changes to API surface."""
    new_endpoints: List[Dict] = field(default_factory=list)
    modified_endpoints: List[Dict] = field(default_factory=list)
    removed_endpoints: List[Dict] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)


@dataclass
class SchemaChange:
    """Represents database schema changes."""
    new_tables: List[str] = field(default_factory=list)
    modified_tables: List[Dict] = field(default_factory=list)
    removed_tables: List[str] = field(default_factory=list)
    migration_files: List[str] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)


@dataclass
class ComponentBoundary:
    """Represents an architectural component."""
    name: str
    files: List[str] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)
    component_type: str = 'module'  # module, service, model, route, etc.


@dataclass
class ImpactAssessment:
    """Overall impact assessment."""
    scope: str  # low, medium, high
    risk: str  # low, medium, high
    complexity: str  # low, medium, high
    files_changed: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    components_affected: List[str] = field(default_factory=list)


class ArchitecturalAnalyzer:
    """Analyzes architectural changes in PR diffs."""

    def __init__(self):
        self.parser = CodeParser()

    def analyze_pr_diff(self, diff_content: str, pr_files: Optional[List[Dict]] = None) -> Dict:
        """
        Analyze a PR diff for architectural changes.

        Args:
            diff_content: Unified diff content
            pr_files: Optional list of file change dicts from GitHub API
                     [{filename, status, additions, deletions, patch}, ...]

        Returns:
            Dict with architectural analysis results
        """
        # Parse the diff to extract file changes
        file_changes = self._parse_diff_files(diff_content, pr_files)

        # Analyze different aspects
        dependency_changes = self._analyze_dependencies(file_changes)
        api_changes = self._analyze_api_changes(file_changes)
        schema_changes = self._analyze_schema_changes(file_changes)
        components = self._identify_components(file_changes)
        impact = self._assess_impact(file_changes, dependency_changes, api_changes, schema_changes)

        return {
            'dependencies': dependency_changes,
            'api_changes': api_changes,
            'schema_changes': schema_changes,
            'components': components,
            'impact': impact,
            'files_changed': file_changes
        }

    def _parse_diff_files(self, diff_content: str, pr_files: Optional[List[Dict]] = None) -> Dict[str, Dict]:
        """Parse diff content to extract file-level changes."""
        file_changes = {}

        if pr_files:
            # Use GitHub API file data if available
            for file_info in pr_files:
                filename = file_info.get('filename', '')
                file_changes[filename] = {
                    'filename': filename,
                    'status': file_info.get('status', 'modified'),  # added, removed, modified
                    'additions': file_info.get('additions', 0),
                    'deletions': file_info.get('deletions', 0),
                    'patch': file_info.get('patch', ''),
                    'language': self.parser.detect_language(filename)
                }
        else:
            # Parse unified diff
            current_file = None
            current_patch = []

            for line in diff_content.split('\n'):
                # New file marker: diff --git a/file b/file
                if line.startswith('diff --git'):
                    # Save previous file
                    if current_file and current_patch:
                        file_changes[current_file]['patch'] = '\n'.join(current_patch)

                    # Extract filename
                    match = re.search(r'b/(.+)$', line)
                    if match:
                        current_file = match.group(1)
                        file_changes[current_file] = {
                            'filename': current_file,
                            'status': 'modified',
                            'additions': 0,
                            'deletions': 0,
                            'patch': '',
                            'language': self.parser.detect_language(current_file)
                        }
                        current_patch = []

                elif current_file:
                    # Track additions/deletions
                    if line.startswith('+') and not line.startswith('+++'):
                        file_changes[current_file]['additions'] += 1
                    elif line.startswith('-') and not line.startswith('---'):
                        file_changes[current_file]['deletions'] += 1

                    # Detect new/deleted files
                    if line.startswith('new file mode'):
                        file_changes[current_file]['status'] = 'added'
                    elif line.startswith('deleted file mode'):
                        file_changes[current_file]['status'] = 'removed'

                    current_patch.append(line)

            # Save last file
            if current_file and current_patch:
                file_changes[current_file]['patch'] = '\n'.join(current_patch)

        return file_changes

    def _analyze_dependencies(self, file_changes: Dict[str, Dict]) -> Dict:
        """Analyze changes in imports and dependencies."""
        added_imports = set()
        removed_imports = set()
        by_file = {}

        for filename, change in file_changes.items():
            language = change.get('language')
            if not language:
                continue

            patch = change.get('patch', '')
            if not patch:
                continue

            # Extract added and removed lines from patch
            added_lines = []
            removed_lines = []

            for line in patch.split('\n'):
                if line.startswith('+') and not line.startswith('+++'):
                    added_lines.append(line[1:])
                elif line.startswith('-') and not line.startswith('---'):
                    removed_lines.append(line[1:])

            # Parse imports from added/removed lines
            added_code = '\n'.join(added_lines)
            removed_code = '\n'.join(removed_lines)

            file_added = self.parser.parse_imports(added_code, language)
            file_removed = self.parser.parse_imports(removed_code, language)

            # Track imports by module
            for imp in file_added:
                added_imports.add(imp.module)
            for imp in file_removed:
                removed_imports.add(imp.module)

            by_file[filename] = {
                'added': [imp.module for imp in file_added],
                'removed': [imp.module for imp in file_removed]
            }

        # Calculate net changes
        truly_added = added_imports - removed_imports
        truly_removed = removed_imports - added_imports

        return {
            'added': sorted(list(truly_added)),
            'removed': sorted(list(truly_removed)),
            'by_file': by_file,
            'external_dependencies': self._identify_external_deps(truly_added)
        }

    def _identify_external_deps(self, modules: Set[str]) -> List[str]:
        """Identify which modules are external (npm packages, pip packages, etc)."""
        external = []
        internal_prefixes = ('.', '/', 'models', 'services', 'routes', 'utils', 'config')

        for module in modules:
            is_internal = any(module.startswith(prefix) for prefix in internal_prefixes)
            if not is_internal:
                external.append(module)

        return sorted(external)

    def _analyze_api_changes(self, file_changes: Dict[str, Dict]) -> Dict:
        """Analyze changes to API endpoints."""
        new_endpoints = []
        removed_endpoints = []
        modified_endpoints = []

        for filename, change in file_changes.items():
            language = change.get('language')
            if not language or language not in ['python', 'javascript', 'typescript', 'java']:
                continue

            patch = change.get('patch', '')
            if not patch:
                continue

            # Extract added and removed lines
            added_lines = []
            removed_lines = []

            for line in patch.split('\n'):
                if line.startswith('+') and not line.startswith('+++'):
                    added_lines.append(line[1:])
                elif line.startswith('-') and not line.startswith('---'):
                    removed_lines.append(line[1:])

            # Parse API routes
            added_code = '\n'.join(added_lines)
            removed_code = '\n'.join(removed_lines)

            added_routes = self.parser.parse_api_routes(added_code, language)
            removed_routes = self.parser.parse_api_routes(removed_code, language)

            # Categorize changes
            for route in added_routes:
                new_endpoints.append({
                    'method': route.method,
                    'path': route.path,
                    'file': filename,
                    'function': route.function_name
                })

            for route in removed_routes:
                removed_endpoints.append({
                    'method': route.method,
                    'path': route.path,
                    'file': filename,
                    'function': route.function_name
                })

        # Detect breaking changes
        breaking_changes = []
        if removed_endpoints:
            breaking_changes.append(
                f"Removed {len(removed_endpoints)} endpoint(s) - potential breaking change"
            )

        return {
            'new_endpoints': new_endpoints,
            'removed_endpoints': removed_endpoints,
            'modified_endpoints': modified_endpoints,
            'breaking_changes': breaking_changes,
            'summary': {
                'added': len(new_endpoints),
                'removed': len(removed_endpoints),
                'modified': len(modified_endpoints)
            }
        }

    def _analyze_schema_changes(self, file_changes: Dict[str, Dict]) -> Dict:
        """Analyze database schema changes."""
        migration_files = []
        new_models = []
        modified_models = []
        removed_models = []
        breaking_changes = []

        for filename, change in file_changes.items():
            # Detect migration files
            if self._is_migration_file(filename):
                migration_files.append(filename)

                # Check for breaking changes in migrations
                patch = change.get('patch', '')
                if any(keyword in patch.lower() for keyword in ['drop table', 'drop column', 'alter column']):
                    breaking_changes.append(f"Migration {filename} contains potentially breaking schema changes")

            # Detect model changes
            language = change.get('language')
            if language == 'python' and '/models/' in filename:
                patch = change.get('patch', '')

                # Parse models from added/removed code
                added_lines = [line[1:] for line in patch.split('\n') if line.startswith('+') and not line.startswith('+++')]
                removed_lines = [line[1:] for line in patch.split('\n') if line.startswith('-') and not line.startswith('---')]

                added_code = '\n'.join(added_lines)
                removed_code = '\n'.join(removed_lines)

                added_models = self.parser.parse_database_models(added_code, language)
                removed_models_list = self.parser.parse_database_models(removed_code, language)

                for model in added_models:
                    new_models.append({
                        'name': model.name,
                        'table': model.table_name,
                        'file': filename
                    })

                for model in removed_models_list:
                    removed_models.append({
                        'name': model.name,
                        'table': model.table_name,
                        'file': filename
                    })

        return {
            'migration_files': migration_files,
            'new_models': new_models,
            'modified_models': modified_models,
            'removed_models': removed_models,
            'breaking_changes': breaking_changes,
            'summary': {
                'migrations': len(migration_files),
                'models_added': len(new_models),
                'models_removed': len(removed_models)
            }
        }

    def _is_migration_file(self, filename: str) -> bool:
        """Check if a file is a database migration."""
        migration_patterns = [
            '/migrations/',
            '/migrate/',
            '/alembic/',
            '/db/migrate/',
            'migrations.py',
            'migrate.py'
        ]
        return any(pattern in filename for pattern in migration_patterns)

    def _identify_components(self, file_changes: Dict[str, Dict]) -> Dict[str, ComponentBoundary]:
        """Identify architectural component boundaries."""
        components = {}

        # Group files by component (directory structure)
        component_files = defaultdict(list)

        for filename in file_changes.keys():
            # Extract component from path
            component_name = self._extract_component_name(filename)
            component_files[component_name].append(filename)

        # Create component boundaries
        for comp_name, files in component_files.items():
            components[comp_name] = {
                'name': comp_name,
                'files': files,
                'type': self._classify_component_type(comp_name, files),
                'file_count': len(files)
            }

        return components

    def _extract_component_name(self, filepath: str) -> str:
        """Extract component name from file path."""
        # Handle common patterns
        if '/' not in filepath:
            return 'root'

        parts = filepath.split('/')

        # services/auth_service.py -> 'services'
        # models/user.py -> 'models'
        # routes/api/auth.py -> 'routes/api'
        if len(parts) >= 2:
            if parts[0] in ['services', 'models', 'routes', 'controllers', 'views']:
                if len(parts) >= 3 and parts[0] == 'routes':
                    return f"{parts[0]}/{parts[1]}"
                return parts[0]

        return parts[0]

    def _classify_component_type(self, component_name: str, files: List[str]) -> str:
        """Classify the type of component."""
        type_map = {
            'models': 'data',
            'services': 'business_logic',
            'routes': 'api',
            'controllers': 'api',
            'views': 'presentation',
            'utils': 'utility',
            'config': 'configuration',
            'tests': 'testing'
        }

        for key, comp_type in type_map.items():
            if key in component_name.lower():
                return comp_type

        return 'module'

    def _assess_impact(self, file_changes: Dict[str, Dict], dependency_changes: Dict,
                      api_changes: Dict, schema_changes: Dict) -> Dict:
        """Assess overall impact of the changes."""
        # Count metrics
        files_changed = len(file_changes)
        lines_added = sum(f.get('additions', 0) for f in file_changes.values())
        lines_removed = sum(f.get('deletions', 0) for f in file_changes.values())
        total_lines = lines_added + lines_removed

        # Assess scope (how many components affected)
        components_affected = set()
        for filename in file_changes.keys():
            components_affected.add(self._extract_component_name(filename))

        num_components = len(components_affected)

        # Determine scope level
        if num_components <= 1 and files_changed <= 3:
            scope = 'low'
        elif num_components <= 3 and files_changed <= 10:
            scope = 'medium'
        else:
            scope = 'high'

        # Assess risk (breaking changes, removed endpoints, schema changes)
        risk_factors = []
        if api_changes.get('breaking_changes'):
            risk_factors.extend(api_changes['breaking_changes'])
        if schema_changes.get('breaking_changes'):
            risk_factors.extend(schema_changes['breaking_changes'])
        if dependency_changes.get('removed'):
            risk_factors.append(f"Removed {len(dependency_changes['removed'])} dependencies")

        if len(risk_factors) >= 3:
            risk = 'high'
        elif len(risk_factors) >= 1:
            risk = 'medium'
        else:
            risk = 'low'

        # Assess complexity (lines changed, files touched)
        if total_lines > 500 or files_changed > 15:
            complexity = 'high'
        elif total_lines > 100 or files_changed > 5:
            complexity = 'medium'
        else:
            complexity = 'low'

        return {
            'scope': scope,
            'risk': risk,
            'complexity': complexity,
            'files_changed': files_changed,
            'lines_added': lines_added,
            'lines_removed': lines_removed,
            'components_affected': sorted(list(components_affected)),
            'risk_factors': risk_factors
        }
