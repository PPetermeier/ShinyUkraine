"""Script to track migration progress and assist with refactoring."""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple

class MigrationTracker:
    """Tracks and assists with code migration."""
    
    def __init__(self):
        self.old_imports: Set[str] = set()
        self.files_to_migrate: Dict[str, List[str]] = {}
        self.migrated_files: Set[str] = set()
    
    def scan_file(self, file_path: str) -> None:
        """Scan a file for old-style imports.
        
        Args:
            file_path: Path to Python file to scan
        """
        with open(file_path, 'r') as f:
            try:
                tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module == 'server.queries':
                            imports = [n.name for n in node.names]
                            self.old_imports.update(imports)
                            if imports:
                                self.files_to_migrate[file_path] = imports
            except SyntaxError:
                print(f"Error parsing {file_path}")
    
    def scan_directory(self, directory: str) -> None:
        """Scan directory for files needing migration.
        
        Args:
            directory: Directory path to scan
        """
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    self.scan_file(os.path.join(root, file))
    
    def generate_report(self) -> str:
        """Generate migration status report.
        
        Returns:
            str: Formatted report of migration status
        """
        report = ["Migration Status Report", "=" * 20]
        
        report.append("\nOld imports found:")
        for imp in sorted(self.old_imports):
            report.append(f"- {imp}")
        
        report.append("\nFiles requiring migration:")
        for file, imports in self.files_to_migrate.items():
            report.append(f"\n{file}:")
            for imp in imports:
                report.append(f"  - {imp}")
        
        return "\n".join(report)

def main():
    """Run migration tracking scan."""
    tracker = MigrationTracker()
    
    # Scan current directory
    tracker.scan_directory(".")
    
    # Generate and save report
    report = tracker.generate_report()
    
    with open("migration_report.txt", "w") as f:
        f.write(report)
    
    print("Migration report generated: migration_report.txt")

if __name__ == "__main__":
    main()
