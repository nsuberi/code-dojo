"""Code parser for extracting architectural elements from source code.

Supports parsing imports, API routes, and database models across multiple languages.
"""

import re
from typing import List, Dict, Set, Optional
from dataclasses import dataclass


@dataclass
class Import:
    """Represents an import statement."""
    module: str
    items: List[str]  # Specific items imported (empty for wildcard imports)
    is_relative: bool
    language: str
    line_number: Optional[int] = None


@dataclass
class APIRoute:
    """Represents an API endpoint."""
    method: str  # GET, POST, PUT, DELETE, PATCH, etc.
    path: str
    function_name: str
    decorators: List[str]
    language: str
    line_number: Optional[int] = None


@dataclass
class DatabaseModel:
    """Represents a database model/schema."""
    name: str
    fields: List[Dict[str, str]]  # [{name, type, nullable, etc}]
    table_name: Optional[str]
    language: str
    line_number: Optional[int] = None


class CodeParser:
    """Language-agnostic code parser for architectural analysis."""

    def __init__(self):
        self.language_parsers = {
            'python': PythonParser(),
            'javascript': JavaScriptParser(),
            'typescript': TypeScriptParser(),
            'java': JavaParser(),
        }

    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
        }
        for ext, lang in extension_map.items():
            if file_path.endswith(ext):
                return lang
        return None

    def parse_imports(self, code: str, language: str) -> List[Import]:
        """Parse import statements from code."""
        parser = self.language_parsers.get(language)
        if not parser:
            return []
        return parser.parse_imports(code)

    def parse_api_routes(self, code: str, language: str) -> List[APIRoute]:
        """Parse API route definitions from code."""
        parser = self.language_parsers.get(language)
        if not parser:
            return []
        return parser.parse_api_routes(code)

    def parse_database_models(self, code: str, language: str) -> List[DatabaseModel]:
        """Parse database model definitions from code."""
        parser = self.language_parsers.get(language)
        if not parser:
            return []
        return parser.parse_database_models(code)


class PythonParser:
    """Python-specific parser."""

    def parse_imports(self, code: str) -> List[Import]:
        """Parse Python imports."""
        imports = []
        lines = code.split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # import X, Y, Z
            match = re.match(r'^import\s+([\w\.,\s]+)', line)
            if match:
                modules = [m.strip() for m in match.group(1).split(',')]
                for module in modules:
                    imports.append(Import(
                        module=module,
                        items=[],
                        is_relative=False,
                        language='python',
                        line_number=line_num
                    ))

            # from X import Y, Z
            match = re.match(r'^from\s+(\.*)(\w[\w\.]*)\s+import\s+(.+)', line)
            if match:
                dots = match.group(1)
                module = match.group(2)
                items_str = match.group(3)

                # Handle continuation lines (not perfect but covers most cases)
                if '(' in items_str and ')' not in items_str:
                    # Multi-line import - skip for simplicity
                    continue

                # Parse imported items
                items = []
                if items_str.strip() == '*':
                    items = ['*']
                else:
                    # Remove parentheses and split
                    items_str = items_str.replace('(', '').replace(')', '')
                    items = [i.strip().split(' as ')[0] for i in items_str.split(',')]

                imports.append(Import(
                    module=module,
                    items=items,
                    is_relative=len(dots) > 0,
                    language='python',
                    line_number=line_num
                ))

        return imports

    def parse_api_routes(self, code: str) -> List[APIRoute]:
        """Parse Flask/FastAPI route decorators."""
        routes = []
        lines = code.split('\n')

        for i, line in enumerate(lines):
            line = line.strip()

            # Flask: @app.route('/path', methods=['GET'])
            match = re.match(r'@(?:app|bp|router|api)\.route\([\'"]([^\'"]+)[\'"](?:,\s*methods=\[([^\]]+)\])?', line)
            if match:
                path = match.group(1)
                methods_str = match.group(2) if match.group(2) else "'GET'"
                methods = [m.strip('\'" ') for m in methods_str.split(',')]

                # Get function name from next non-decorator line
                func_name = self._get_function_name(lines, i + 1)

                for method in methods:
                    routes.append(APIRoute(
                        method=method.upper(),
                        path=path,
                        function_name=func_name,
                        decorators=[line],
                        language='python',
                        line_number=i + 1
                    ))

            # FastAPI: @router.get('/path')
            match = re.match(r'@(?:app|router)\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]', line)
            if match:
                method = match.group(1).upper()
                path = match.group(2)
                func_name = self._get_function_name(lines, i + 1)

                routes.append(APIRoute(
                    method=method,
                    path=path,
                    function_name=func_name,
                    decorators=[line],
                    language='python',
                    line_number=i + 1
                ))

        return routes

    def parse_database_models(self, code: str) -> List[DatabaseModel]:
        """Parse SQLAlchemy/Django ORM models."""
        models = []
        lines = code.split('\n')

        # Look for class definitions that inherit from db.Model or Model
        for i, line in enumerate(lines):
            line = line.strip()

            # SQLAlchemy: class User(db.Model):
            match = re.match(r'class\s+(\w+)\((?:db\.)?Model\):', line)
            if match:
                model_name = match.group(1)
                fields = []
                table_name = None

                # Parse fields and table name in subsequent lines
                for j in range(i + 1, min(i + 100, len(lines))):
                    field_line = lines[j].strip()

                    # End of class
                    if field_line and not field_line.startswith((' ', '\t', '#')):
                        if not field_line.startswith('class '):
                            break

                    # __tablename__ = 'users'
                    table_match = re.match(r'__tablename__\s*=\s*[\'"](\w+)[\'"]', field_line)
                    if table_match:
                        table_name = table_match.group(1)

                    # field_name = db.Column(...)
                    field_match = re.match(r'(\w+)\s*=\s*db\.Column\(([\w\.,\s]+)', field_line)
                    if field_match:
                        field_name = field_match.group(1)
                        field_type = field_match.group(2).split(',')[0].strip()
                        fields.append({
                            'name': field_name,
                            'type': field_type,
                        })

                models.append(DatabaseModel(
                    name=model_name,
                    fields=fields,
                    table_name=table_name,
                    language='python',
                    line_number=i + 1
                ))

        return models

    def _get_function_name(self, lines: List[str], start_idx: int) -> str:
        """Get function name from next def line."""
        for i in range(start_idx, min(start_idx + 5, len(lines))):
            match = re.match(r'def\s+(\w+)\s*\(', lines[i].strip())
            if match:
                return match.group(1)
        return 'unknown'


class JavaScriptParser:
    """JavaScript-specific parser."""

    def parse_imports(self, code: str) -> List[Import]:
        """Parse JavaScript/ES6 imports."""
        imports = []
        lines = code.split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # import X from 'module'
            match = re.match(r'import\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]', line)
            if match:
                imports.append(Import(
                    module=match.group(2),
                    items=[match.group(1)],
                    is_relative=match.group(2).startswith('.'),
                    language='javascript',
                    line_number=line_num
                ))

            # import { X, Y } from 'module'
            match = re.match(r'import\s+\{([^}]+)\}\s+from\s+[\'"]([^\'"]+)[\'"]', line)
            if match:
                items = [i.strip().split(' as ')[0] for i in match.group(1).split(',')]
                imports.append(Import(
                    module=match.group(2),
                    items=items,
                    is_relative=match.group(2).startswith('.'),
                    language='javascript',
                    line_number=line_num
                ))

            # const X = require('module')
            match = re.match(r'(?:const|var|let)\s+(?:\{([^}]+)\}|(\w+))\s*=\s*require\([\'"]([^\'"]+)[\'"]\)', line)
            if match:
                if match.group(1):  # Destructured
                    items = [i.strip() for i in match.group(1).split(',')]
                else:  # Direct assignment
                    items = [match.group(2)]

                imports.append(Import(
                    module=match.group(3),
                    items=items,
                    is_relative=match.group(3).startswith('.'),
                    language='javascript',
                    line_number=line_num
                ))

        return imports

    def parse_api_routes(self, code: str) -> List[APIRoute]:
        """Parse Express.js routes."""
        routes = []
        lines = code.split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # app.get('/path', handler)
            # router.post('/path', middleware, handler)
            match = re.match(r'(?:app|router)\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]', line)
            if match:
                routes.append(APIRoute(
                    method=match.group(1).upper(),
                    path=match.group(2),
                    function_name='inline',
                    decorators=[],
                    language='javascript',
                    line_number=line_num
                ))

        return routes

    def parse_database_models(self, code: str) -> List[DatabaseModel]:
        """Parse Sequelize/Mongoose models."""
        models = []
        # Simplified - would need more sophisticated parsing for real use
        return models


class TypeScriptParser(JavaScriptParser):
    """TypeScript parser - inherits from JavaScript with extensions."""

    def parse_imports(self, code: str) -> List[Import]:
        """Parse TypeScript imports (similar to JavaScript)."""
        imports = super().parse_imports(code)
        # Update language
        for imp in imports:
            imp.language = 'typescript'
        return imports


class JavaParser:
    """Java-specific parser."""

    def parse_imports(self, code: str) -> List[Import]:
        """Parse Java imports."""
        imports = []
        lines = code.split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # import package.Class;
            match = re.match(r'import\s+([\w\.]+)(?:\.\*)?;', line)
            if match:
                module = match.group(1)
                items = ['*'] if line.endswith('.*;') else [module.split('.')[-1]]

                imports.append(Import(
                    module=module,
                    items=items,
                    is_relative=False,
                    language='java',
                    line_number=line_num
                ))

        return imports

    def parse_api_routes(self, code: str) -> List[APIRoute]:
        """Parse Spring Boot annotations."""
        routes = []
        lines = code.split('\n')

        for i, line in enumerate(lines):
            line = line.strip()

            # @GetMapping("/path")
            match = re.match(r'@(Get|Post|Put|Delete|Patch)Mapping\([\'"]([^\'"]+)[\'"]', line)
            if match:
                routes.append(APIRoute(
                    method=match.group(1).upper(),
                    path=match.group(2),
                    function_name='unknown',
                    decorators=[line],
                    language='java',
                    line_number=i + 1
                ))

            # @RequestMapping(value="/path", method=RequestMethod.GET)
            match = re.match(r'@RequestMapping\(.*value\s*=\s*[\'"]([^\'"]+)[\'"].*method\s*=\s*RequestMethod\.(\w+)', line)
            if match:
                routes.append(APIRoute(
                    method=match.group(2).upper(),
                    path=match.group(1),
                    function_name='unknown',
                    decorators=[line],
                    language='java',
                    line_number=i + 1
                ))

        return routes

    def parse_database_models(self, code: str) -> List[DatabaseModel]:
        """Parse JPA entities."""
        models = []
        # Simplified - would need more sophisticated parsing for real use
        return models
