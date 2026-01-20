"""Mermaid diagram generator for architectural visualizations."""

from typing import Dict, List, Set


class DiagramGenerator:
    """Generates Mermaid diagrams for architectural analysis."""

    def generate_component_diagram(self, components: Dict, dependencies: Dict) -> str:
        """
        Generate a component dependency diagram.

        Shows how architectural components relate to each other.
        """
        if not components:
            return ""

        lines = ["graph TD"]

        # Add component nodes
        comp_ids = {}
        for i, (comp_name, comp_data) in enumerate(components.items()):
            comp_id = f"C{i}"
            comp_ids[comp_name] = comp_id

            # Style based on component type
            comp_type = comp_data.get('type', 'module')
            file_count = comp_data.get('file_count', 0)

            lines.append(f"    {comp_id}[\"{comp_name}<br/>{file_count} files\"]")

            # Add styling based on type
            if comp_type == 'api':
                lines.append(f"    style {comp_id} fill:#e1f5ff")
            elif comp_type == 'data':
                lines.append(f"    style {comp_id} fill:#fff3e0")
            elif comp_type == 'business_logic':
                lines.append(f"    style {comp_id} fill:#f3e5f5")

        # Add dependency relationships from added/removed imports
        added_deps = dependencies.get('added', [])
        removed_deps = dependencies.get('removed', [])

        # Create edges for new dependencies
        for dep in added_deps[:10]:  # Limit to avoid clutter
            # Try to map to existing components
            for comp_name, comp_id in comp_ids.items():
                if dep in comp_name or comp_name in dep:
                    # Find source component (simplified - assumes first component)
                    if len(comp_ids) > 0:
                        source_id = list(comp_ids.values())[0]
                        lines.append(f"    {source_id} -->|new| {comp_id}")
                    break

        return "\n".join(lines)

    def generate_dependency_graph(self, dependencies: Dict) -> str:
        """
        Generate a dependency diff diagram.

        Shows added/removed external dependencies.
        """
        added = dependencies.get('added', [])
        removed = dependencies.get('removed', [])
        external = dependencies.get('external_dependencies', [])

        if not (added or removed):
            return ""

        lines = ["graph LR"]
        lines.append("    Project[\"Your Project\"]")

        # Added dependencies (green)
        for i, dep in enumerate(added[:8]):  # Limit to 8 for readability
            dep_id = f"ADD{i}"
            # Shorten long package names
            display_name = dep.split('/')[-1] if '/' in dep else dep
            lines.append(f"    {dep_id}[\"{display_name}\"]")
            lines.append(f"    Project -->|added| {dep_id}")
            lines.append(f"    style {dep_id} fill:#c8e6c9")

        # Removed dependencies (red)
        for i, dep in enumerate(removed[:8]):
            dep_id = f"REM{i}"
            display_name = dep.split('/')[-1] if '/' in dep else dep
            lines.append(f"    {dep_id}[\"{display_name}\"]")
            lines.append(f"    Project -.->|removed| {dep_id}")
            lines.append(f"    style {dep_id} fill:#ffcdd2")

        return "\n".join(lines)

    def generate_api_surface_diagram(self, api_changes: Dict) -> str:
        """
        Generate API surface changes diagram.

        Shows new/modified/removed endpoints.
        """
        new_endpoints = api_changes.get('new_endpoints', [])
        removed_endpoints = api_changes.get('removed_endpoints', [])

        if not (new_endpoints or removed_endpoints):
            return ""

        lines = ["graph TD"]
        lines.append("    API[\"API Surface\"]")

        # Group by HTTP method
        methods = {}
        for endpoint in new_endpoints[:10]:  # Limit for readability
            method = endpoint.get('method', 'GET')
            if method not in methods:
                methods[method] = {'new': [], 'removed': []}
            methods[method]['new'].append(endpoint)

        for endpoint in removed_endpoints[:10]:
            method = endpoint.get('method', 'GET')
            if method not in methods:
                methods[method] = {'new': [], 'removed': []}
            methods[method]['removed'].append(endpoint)

        # Create nodes for each method group
        for i, (method, endpoints) in enumerate(methods.items()):
            method_id = f"M{i}"
            lines.append(f"    {method_id}[\"{method}\"]")
            lines.append(f"    API --> {method_id}")

            # Add new endpoints
            for j, endpoint in enumerate(endpoints['new'][:5]):
                endpoint_id = f"{method_id}_NEW{j}"
                path = endpoint.get('path', '/')
                lines.append(f"    {endpoint_id}[\"{path}\"]")
                lines.append(f"    {method_id} -->|new| {endpoint_id}")
                lines.append(f"    style {endpoint_id} fill:#c8e6c9")

            # Add removed endpoints
            for j, endpoint in enumerate(endpoints['removed'][:5]):
                endpoint_id = f"{method_id}_REM{j}"
                path = endpoint.get('path', '/')
                lines.append(f"    {endpoint_id}[\"{path}\"]")
                lines.append(f"    {method_id} -.->|removed| {endpoint_id}")
                lines.append(f"    style {endpoint_id} fill:#ffcdd2")

        return "\n".join(lines)

    def generate_dataflow_diagram(self, components: Dict, api_changes: Dict) -> str:
        """
        Generate a simple data flow sequence diagram.

        Shows how data flows through new/modified endpoints.
        """
        new_endpoints = api_changes.get('new_endpoints', [])

        if not new_endpoints:
            return ""

        lines = ["sequenceDiagram"]
        lines.append("    participant Client")
        lines.append("    participant API")

        # Identify unique components
        component_names = set()
        for endpoint in new_endpoints[:5]:  # Limit to 5 for readability
            file = endpoint.get('file', '')
            # Extract component from file path
            if '/' in file:
                component = file.split('/')[0]
                component_names.add(component)

        # Add component participants
        for comp in sorted(component_names):
            lines.append(f"    participant {comp.capitalize()}")

        # Add sequence for each new endpoint
        for i, endpoint in enumerate(new_endpoints[:5]):
            method = endpoint.get('method', 'GET')
            path = endpoint.get('path', '/')
            file = endpoint.get('file', '')

            component = 'Service'
            if '/' in file:
                component = file.split('/')[0].capitalize()

            lines.append(f"    Client->>+API: {method} {path}")
            lines.append(f"    API->>+{component}: Process request")
            lines.append(f"    {component}-->>-API: Response")
            lines.append(f"    API-->>-Client: Result")

            if i < len(new_endpoints) - 1:
                lines.append("")  # Blank line between sequences

        return "\n".join(lines)

    def generate_schema_diagram(self, schema_changes: Dict) -> str:
        """
        Generate database schema changes diagram.

        Shows new/modified/removed models and tables.
        """
        new_models = schema_changes.get('new_models', [])
        removed_models = schema_changes.get('removed_models', [])

        if not (new_models or removed_models):
            return ""

        lines = ["graph TD"]
        lines.append("    DB[(Database)]")

        # Add new models
        for i, model in enumerate(new_models[:8]):
            model_id = f"NEW{i}"
            model_name = model.get('name', 'Unknown')
            table_name = model.get('table', model_name.lower())
            lines.append(f"    {model_id}[\"{model_name}<br/>{table_name}\"]")
            lines.append(f"    DB -->|new| {model_id}")
            lines.append(f"    style {model_id} fill:#c8e6c9")

        # Add removed models
        for i, model in enumerate(removed_models[:8]):
            model_id = f"REM{i}"
            model_name = model.get('name', 'Unknown')
            table_name = model.get('table', model_name.lower())
            lines.append(f"    {model_id}[\"{model_name}<br/>{table_name}\"]")
            lines.append(f"    DB -.->|removed| {model_id}")
            lines.append(f"    style {model_id} fill:#ffcdd2")

        return "\n".join(lines)

    def generate_impact_summary_diagram(self, impact: Dict) -> str:
        """
        Generate a visual summary of impact assessment.

        Shows scope, risk, and complexity in a radial diagram.
        """
        scope = impact.get('scope', 'low')
        risk = impact.get('risk', 'low')
        complexity = impact.get('complexity', 'low')

        # Map levels to numbers (for visualization)
        level_map = {'low': 1, 'medium': 2, 'high': 3}

        lines = ["graph TB"]
        lines.append("    Impact[\"Impact Assessment\"]")

        # Scope node
        scope_level = level_map.get(scope, 1)
        scope_color = self._get_level_color(scope)
        lines.append(f"    Scope[\"{scope.upper()}<br/>Scope\"]")
        lines.append(f"    Impact --> Scope")
        lines.append(f"    style Scope fill:{scope_color}")

        # Risk node
        risk_level = level_map.get(risk, 1)
        risk_color = self._get_level_color(risk)
        lines.append(f"    Risk[\"{risk.upper()}<br/>Risk\"]")
        lines.append(f"    Impact --> Risk")
        lines.append(f"    style Risk fill:{risk_color}")

        # Complexity node
        complexity_level = level_map.get(complexity, 1)
        complexity_color = self._get_level_color(complexity)
        lines.append(f"    Complexity[\"{complexity.upper()}<br/>Complexity\"]")
        lines.append(f"    Impact --> Complexity")
        lines.append(f"    style Complexity fill:{complexity_color}")

        return "\n".join(lines)

    def _get_level_color(self, level: str) -> str:
        """Get color for impact level."""
        colors = {
            'low': '#c8e6c9',    # Green
            'medium': '#fff9c4', # Yellow
            'high': '#ffcdd2'    # Red
        }
        return colors.get(level, '#e0e0e0')

    def generate_all_diagrams(self, analysis_results: Dict) -> Dict[str, str]:
        """
        Generate all relevant diagrams from analysis results.

        Returns:
            Dict mapping diagram names to Mermaid markdown
        """
        diagrams = {}

        # Component diagram
        components = analysis_results.get('components', {})
        dependencies = analysis_results.get('dependencies', {})
        if components:
            diagrams['component'] = self.generate_component_diagram(components, dependencies)

        # Dependency graph
        if dependencies:
            diagrams['dependency'] = self.generate_dependency_graph(dependencies)

        # API surface diagram
        api_changes = analysis_results.get('api_changes', {})
        if api_changes:
            api_diagram = self.generate_api_surface_diagram(api_changes)
            if api_diagram:
                diagrams['api_surface'] = api_diagram

        # Data flow diagram
        if components and api_changes:
            dataflow = self.generate_dataflow_diagram(components, api_changes)
            if dataflow:
                diagrams['dataflow'] = dataflow

        # Schema diagram
        schema_changes = analysis_results.get('schema_changes', {})
        if schema_changes:
            schema_diagram = self.generate_schema_diagram(schema_changes)
            if schema_diagram:
                diagrams['schema'] = schema_diagram

        # Impact summary
        impact = analysis_results.get('impact', {})
        if impact:
            diagrams['impact'] = self.generate_impact_summary_diagram(impact)

        return diagrams
