#!/usr/bin/env python3
"""
Schema Drift Detection for PrepSense API

Detects breaking changes and schema drift between API versions by:
- Comparing OpenAPI schemas across deployments
- Identifying breaking changes in request/response formats
- Validating backward compatibility requirements
- Generating drift reports for monitoring

Usage:
    python schema_drift_detector.py --baseline path/to/baseline.json --current http://localhost:8001/openapi.json
    python schema_drift_detector.py --auto-detect  # Auto-detect changes from last run
    python schema_drift_detector.py --ci-mode     # For continuous integration
"""

import os
import sys
import json
import argparse
import requests
import hashlib
from typing import Dict, Any, List, Set, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import difflib

@dataclass
class SchemaDiff:
    """Represents a difference between two schema versions."""
    change_type: str  # 'added', 'removed', 'modified'
    severity: str     # 'breaking', 'warning', 'info'
    path: str        # JSONPath to the changed element
    old_value: Any   # Previous value (None for additions)
    new_value: Any   # New value (None for removals)
    description: str # Human-readable description
    impact: str      # Impact assessment

@dataclass
class DriftReport:
    """Complete drift analysis report."""
    baseline_version: str
    current_version: str
    timestamp: datetime
    breaking_changes: List[SchemaDiff]
    warnings: List[SchemaDiff]
    additions: List[SchemaDiff]
    compatibility_score: float  # 0-100, higher is better
    summary: Dict[str, int]
    recommendations: List[str]

class SchemaDriftDetector:
    """Detects and analyzes API schema drift."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {
            'ignore_paths': [
                '$.info.x-build-time',
                '$.servers',
                '$.x-*',  # Extension fields
            ],
            'breaking_change_rules': {
                'removed_paths': True,
                'removed_required_fields': True,
                'changed_types': True,
                'removed_enum_values': True,
                'stricter_validation': True,
            },
            'warning_rules': {
                'added_required_fields': True,
                'deprecated_fields': True,
                'changed_descriptions': False,
                'reordered_enum_values': True,
            }
        }
        
        self.drift_storage = Path('.schema_drift')
        self.drift_storage.mkdir(exist_ok=True)
    
    def load_schema_from_url(self, url: str) -> Dict[str, Any]:
        """Load OpenAPI schema from URL."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to load schema from {url}: {e}")
    
    def load_schema_from_file(self, filepath: str) -> Dict[str, Any]:
        """Load OpenAPI schema from file."""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to load schema from {filepath}: {e}")
    
    def normalize_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize schema by removing ignorable paths."""
        normalized = json.loads(json.dumps(schema))  # Deep copy
        
        # Remove ignored paths
        for ignore_path in self.config['ignore_paths']:
            if ignore_path.startswith('$.info.x-'):
                info = normalized.get('info', {})
                keys_to_remove = [k for k in info.keys() if k.startswith('x-')]
                for key in keys_to_remove:
                    info.pop(key, None)
            elif ignore_path == '$.servers':
                normalized.pop('servers', None)
            elif ignore_path.startswith('$.x-'):
                keys_to_remove = [k for k in normalized.keys() if k.startswith('x-')]
                for key in keys_to_remove:
                    normalized.pop(key, None)
        
        return normalized
    
    def get_schema_fingerprint(self, schema: Dict[str, Any]) -> str:
        """Generate a fingerprint for schema comparison."""
        normalized = self.normalize_schema(schema)
        schema_str = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(schema_str.encode()).hexdigest()[:16]
    
    def extract_paths_and_operations(self, schema: Dict[str, Any]) -> Dict[str, Set[str]]:
        """Extract all paths and their operations."""
        paths_ops = {}
        for path, methods in schema.get('paths', {}).items():
            paths_ops[path] = set(methods.keys())
        return paths_ops
    
    def extract_schema_definitions(self, schema: Dict[str, Any]) -> Dict[str, Dict]:
        """Extract schema definitions for comparison."""
        components = schema.get('components', {})
        return components.get('schemas', {})
    
    def compare_path_operations(self, baseline: Dict[str, Set[str]], current: Dict[str, Set[str]]) -> List[SchemaDiff]:
        """Compare path operations between schemas."""
        diffs = []
        
        all_paths = set(baseline.keys()) | set(current.keys())
        
        for path in all_paths:
            baseline_ops = baseline.get(path, set())
            current_ops = current.get(path, set())
            
            # Removed paths (breaking)
            if path in baseline and path not in current:
                diffs.append(SchemaDiff(
                    change_type='removed',
                    severity='breaking',
                    path=f'$.paths.{path}',
                    old_value=list(baseline_ops),
                    new_value=None,
                    description=f'API path {path} was removed',
                    impact='Clients using this path will fail'
                ))
                continue
            
            # Added paths (info)
            if path not in baseline and path in current:
                diffs.append(SchemaDiff(
                    change_type='added',
                    severity='info',
                    path=f'$.paths.{path}',
                    old_value=None,
                    new_value=list(current_ops),
                    description=f'New API path {path} was added',
                    impact='New functionality available to clients'
                ))
                continue
            
            # Compare operations for existing paths
            removed_ops = baseline_ops - current_ops
            added_ops = current_ops - baseline_ops
            
            for op in removed_ops:
                diffs.append(SchemaDiff(
                    change_type='removed',
                    severity='breaking',
                    path=f'$.paths.{path}.{op}',
                    old_value=op,
                    new_value=None,
                    description=f'HTTP method {op.upper()} removed from {path}',
                    impact='Clients using this method will receive 405 Method Not Allowed'
                ))
            
            for op in added_ops:
                diffs.append(SchemaDiff(
                    change_type='added',
                    severity='info',
                    path=f'$.paths.{path}.{op}',
                    old_value=None,
                    new_value=op,
                    description=f'HTTP method {op.upper()} added to {path}',
                    impact='New method available for clients'
                ))
        
        return diffs
    
    def compare_schemas(self, baseline_schemas: Dict[str, Dict], current_schemas: Dict[str, Dict]) -> List[SchemaDiff]:
        """Compare schema definitions."""
        diffs = []
        
        all_schema_names = set(baseline_schemas.keys()) | set(current_schemas.keys())
        
        for schema_name in all_schema_names:
            baseline_schema = baseline_schemas.get(schema_name, {})
            current_schema = current_schemas.get(schema_name, {})
            
            # Removed schemas (breaking)
            if schema_name in baseline_schemas and schema_name not in current_schemas:
                diffs.append(SchemaDiff(
                    change_type='removed',
                    severity='breaking',
                    path=f'$.components.schemas.{schema_name}',
                    old_value=baseline_schema,
                    new_value=None,
                    description=f'Schema {schema_name} was removed',
                    impact='Clients expecting this schema will fail validation'
                ))
                continue
            
            # Added schemas (info)
            if schema_name not in baseline_schemas and schema_name in current_schemas:
                diffs.append(SchemaDiff(
                    change_type='added',
                    severity='info',
                    path=f'$.components.schemas.{schema_name}',
                    old_value=None,
                    new_value=current_schema,
                    description=f'New schema {schema_name} was added',
                    impact='New data structure available'
                ))
                continue
            
            # Compare schema properties
            diffs.extend(self.compare_schema_properties(schema_name, baseline_schema, current_schema))
        
        return diffs
    
    def compare_schema_properties(self, schema_name: str, baseline: Dict, current: Dict) -> List[SchemaDiff]:
        """Compare properties within a schema."""
        diffs = []
        
        baseline_props = baseline.get('properties', {})
        current_props = current.get('properties', {})
        baseline_required = set(baseline.get('required', []))
        current_required = set(current.get('required', []))
        
        # Compare properties
        all_props = set(baseline_props.keys()) | set(current_props.keys())
        
        for prop_name in all_props:
            baseline_prop = baseline_props.get(prop_name, {})
            current_prop = current_props.get(prop_name, {})
            
            # Removed properties (breaking)
            if prop_name in baseline_props and prop_name not in current_props:
                severity = 'breaking' if prop_name in baseline_required else 'warning'
                diffs.append(SchemaDiff(
                    change_type='removed',
                    severity=severity,
                    path=f'$.components.schemas.{schema_name}.properties.{prop_name}',
                    old_value=baseline_prop,
                    new_value=None,
                    description=f'Property {prop_name} removed from {schema_name}',
                    impact='Clients sending this property will have it ignored' if severity == 'warning' 
                           else 'Required property missing will cause validation errors'
                ))
                continue
            
            # Added properties
            if prop_name not in baseline_props and prop_name in current_props:
                severity = 'breaking' if prop_name in current_required else 'info'
                impact = 'Clients must provide this required property' if severity == 'breaking' \
                        else 'Optional new property available'
                
                diffs.append(SchemaDiff(
                    change_type='added',
                    severity=severity,
                    path=f'$.components.schemas.{schema_name}.properties.{prop_name}',
                    old_value=None,
                    new_value=current_prop,
                    description=f'Property {prop_name} added to {schema_name}',
                    impact=impact
                ))
                continue
            
            # Modified properties
            if baseline_prop != current_prop:
                severity = self.assess_property_change_severity(baseline_prop, current_prop)
                diffs.append(SchemaDiff(
                    change_type='modified',
                    severity=severity,
                    path=f'$.components.schemas.{schema_name}.properties.{prop_name}',
                    old_value=baseline_prop,
                    new_value=current_prop,
                    description=f'Property {prop_name} modified in {schema_name}',
                    impact=self.assess_property_change_impact(baseline_prop, current_prop)
                ))
        
        # Check required field changes
        added_required = current_required - baseline_required
        removed_required = baseline_required - current_required
        
        for field in added_required:
            diffs.append(SchemaDiff(
                change_type='modified',
                severity='breaking',
                path=f'$.components.schemas.{schema_name}.required',
                old_value=list(baseline_required),
                new_value=list(current_required),
                description=f'Field {field} is now required in {schema_name}',
                impact='Clients not providing this field will fail validation'
            ))
        
        for field in removed_required:
            diffs.append(SchemaDiff(
                change_type='modified',
                severity='info',
                path=f'$.components.schemas.{schema_name}.required',
                old_value=list(baseline_required),
                new_value=list(current_required),
                description=f'Field {field} is no longer required in {schema_name}',
                impact='Field is now optional for clients'
            ))
        
        return diffs
    
    def assess_property_change_severity(self, baseline_prop: Dict, current_prop: Dict) -> str:
        """Assess the severity of a property change."""
        baseline_type = baseline_prop.get('type')
        current_type = current_prop.get('type')
        
        # Type changes are breaking
        if baseline_type != current_type:
            return 'breaking'
        
        # Enum value removals are breaking
        baseline_enum = set(baseline_prop.get('enum', []))
        current_enum = set(current_prop.get('enum', []))
        if baseline_enum and current_enum and not current_enum.issuperset(baseline_enum):
            return 'breaking'
        
        # Stricter validation is breaking
        baseline_max = baseline_prop.get('maxLength', baseline_prop.get('maximum'))
        current_max = current_prop.get('maxLength', current_prop.get('maximum'))
        if baseline_max and current_max and current_max < baseline_max:
            return 'breaking'
        
        baseline_min = baseline_prop.get('minLength', baseline_prop.get('minimum'))
        current_min = current_prop.get('minLength', current_prop.get('minimum'))
        if baseline_min and current_min and current_min > baseline_min:
            return 'breaking'
        
        # Format changes can be breaking
        baseline_format = baseline_prop.get('format')
        current_format = current_prop.get('format')
        if baseline_format != current_format:
            return 'warning'
        
        # Description changes are informational
        return 'info'
    
    def assess_property_change_impact(self, baseline_prop: Dict, current_prop: Dict) -> str:
        """Assess the impact of a property change."""
        baseline_type = baseline_prop.get('type')
        current_type = current_prop.get('type')
        
        if baseline_type != current_type:
            return f'Type changed from {baseline_type} to {current_type} - clients may fail validation'
        
        baseline_enum = set(baseline_prop.get('enum', []))
        current_enum = set(current_prop.get('enum', []))
        if baseline_enum and current_enum:
            removed_values = baseline_enum - current_enum
            if removed_values:
                return f'Enum values {removed_values} removed - clients using these values will fail'
        
        return 'Property definition updated - check client compatibility'
    
    def calculate_compatibility_score(self, diffs: List[SchemaDiff]) -> float:
        """Calculate backward compatibility score (0-100)."""
        if not diffs:
            return 100.0
        
        breaking_count = sum(1 for d in diffs if d.severity == 'breaking')
        warning_count = sum(1 for d in diffs if d.severity == 'warning')
        info_count = sum(1 for d in diffs if d.severity == 'info')
        
        # Weighted scoring
        total_impact = (breaking_count * 10) + (warning_count * 3) + (info_count * 1)
        max_score = 100
        
        # Calculate score with logarithmic penalty for many changes
        import math
        score = max_score - (total_impact * (1 + math.log(max(len(diffs), 1))))
        
        return max(0.0, min(100.0, score))
    
    def generate_recommendations(self, diffs: List[SchemaDiff]) -> List[str]:
        """Generate recommendations based on detected changes."""
        recommendations = []
        
        breaking_changes = [d for d in diffs if d.severity == 'breaking']
        
        if breaking_changes:
            recommendations.append(
                "⚠️  Breaking changes detected! Consider bumping the major version number."
            )
            
            path_removals = [d for d in breaking_changes if d.change_type == 'removed' and d.path.startswith('$.paths')]
            if path_removals:
                recommendations.append(
                    f"🚫 {len(path_removals)} API endpoints were removed. Consider deprecation period."
                )
            
            required_additions = [d for d in breaking_changes if 'now required' in d.description]
            if required_additions:
                recommendations.append(
                    f"📋 {len(required_additions)} new required fields added. Provide default values or migration guide."
                )
        
        # Check for good practices
        additions = [d for d in diffs if d.change_type == 'added']
        if additions:
            recommendations.append(
                f"✅ {len(additions)} new features added. Update API documentation."
            )
        
        return recommendations
    
    def compare_schemas_full(self, baseline: Dict[str, Any], current: Dict[str, Any]) -> DriftReport:
        """Perform comprehensive schema comparison."""
        baseline_normalized = self.normalize_schema(baseline)
        current_normalized = self.normalize_schema(current)
        
        # Compare paths and operations
        baseline_paths = self.extract_paths_and_operations(baseline_normalized)
        current_paths = self.extract_paths_and_operations(current_normalized)
        path_diffs = self.compare_path_operations(baseline_paths, current_paths)
        
        # Compare schema definitions
        baseline_schemas = self.extract_schema_definitions(baseline_normalized)
        current_schemas = self.extract_schema_definitions(current_normalized)
        schema_diffs = self.compare_schemas(baseline_schemas, current_schemas)
        
        # Combine all differences
        all_diffs = path_diffs + schema_diffs
        
        # Categorize by severity
        breaking_changes = [d for d in all_diffs if d.severity == 'breaking']
        warnings = [d for d in all_diffs if d.severity == 'warning']
        additions = [d for d in all_diffs if d.severity == 'info']
        
        # Calculate compatibility score
        compatibility_score = self.calculate_compatibility_score(all_diffs)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(all_diffs)
        
        return DriftReport(
            baseline_version=baseline.get('info', {}).get('version', 'unknown'),
            current_version=current.get('info', {}).get('version', 'unknown'),
            timestamp=datetime.now(),
            breaking_changes=breaking_changes,
            warnings=warnings,
            additions=additions,
            compatibility_score=compatibility_score,
            summary={
                'breaking_changes': len(breaking_changes),
                'warnings': len(warnings),
                'additions': len(additions),
                'total_changes': len(all_diffs)
            },
            recommendations=recommendations
        )
    
    def save_baseline(self, schema: Dict[str, Any], name: str = 'default'):
        """Save a schema as baseline for future comparisons."""
        baseline_path = self.drift_storage / f'{name}_baseline.json'
        with open(baseline_path, 'w') as f:
            json.dump(schema, f, indent=2)
        
        # Save metadata
        metadata = {
            'saved_at': datetime.now().isoformat(),
            'version': schema.get('info', {}).get('version', 'unknown'),
            'fingerprint': self.get_schema_fingerprint(schema),
            'paths_count': len(schema.get('paths', {})),
            'schemas_count': len(schema.get('components', {}).get('schemas', {}))
        }
        
        metadata_path = self.drift_storage / f'{name}_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Baseline saved: {baseline_path}")
    
    def load_baseline(self, name: str = 'default') -> Optional[Dict[str, Any]]:
        """Load a previously saved baseline schema."""
        baseline_path = self.drift_storage / f'{name}_baseline.json'
        if baseline_path.exists():
            return self.load_schema_from_file(str(baseline_path))
        return None
    
    def auto_detect_drift(self, current_url: str, baseline_name: str = 'default') -> Optional[DriftReport]:
        """Auto-detect drift against saved baseline."""
        baseline = self.load_baseline(baseline_name)
        if not baseline:
            print(f"❌ No baseline found for '{baseline_name}'. Use --save-baseline first.")
            return None
        
        current = self.load_schema_from_url(current_url)
        
        # Quick fingerprint check
        current_fingerprint = self.get_schema_fingerprint(current)
        baseline_fingerprint = self.get_schema_fingerprint(baseline)
        
        if current_fingerprint == baseline_fingerprint:
            print("✅ No schema drift detected.")
            return None
        
        print(f"🔍 Schema drift detected. Analyzing changes...")
        return self.compare_schemas_full(baseline, current)

def format_report(report: DriftReport, output_format: str = 'text') -> str:
    """Format drift report for output."""
    if output_format == 'json':
        report_dict = asdict(report)
        # Convert datetime to string for JSON serialization
        report_dict['timestamp'] = report.timestamp.isoformat()
        return json.dumps(report_dict, indent=2, default=str)
    
    # Text format
    lines = []
    lines.append("=" * 80)
    lines.append("API SCHEMA DRIFT REPORT")
    lines.append("=" * 80)
    lines.append(f"Baseline Version: {report.baseline_version}")
    lines.append(f"Current Version:  {report.current_version}")
    lines.append(f"Analysis Time:    {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Compatibility Score: {report.compatibility_score:.1f}/100")
    lines.append("")
    
    # Summary
    lines.append("SUMMARY:")
    lines.append(f"  Breaking Changes: {report.summary['breaking_changes']}")
    lines.append(f"  Warnings:        {report.summary['warnings']}")
    lines.append(f"  Additions:       {report.summary['additions']}")
    lines.append(f"  Total Changes:   {report.summary['total_changes']}")
    lines.append("")
    
    # Breaking changes
    if report.breaking_changes:
        lines.append("🚨 BREAKING CHANGES:")
        for change in report.breaking_changes:
            lines.append(f"  • {change.description}")
            lines.append(f"    Path: {change.path}")
            lines.append(f"    Impact: {change.impact}")
            lines.append("")
    
    # Warnings
    if report.warnings:
        lines.append("⚠️  WARNINGS:")
        for warning in report.warnings:
            lines.append(f"  • {warning.description}")
            lines.append(f"    Path: {warning.path}")
            lines.append("")
    
    # Recommendations
    if report.recommendations:
        lines.append("💡 RECOMMENDATIONS:")
        for rec in report.recommendations:
            lines.append(f"  {rec}")
        lines.append("")
    
    # Additions (truncated)
    if report.additions:
        lines.append(f"ℹ️  NEW ADDITIONS ({len(report.additions)}):")
        for addition in report.additions[:5]:  # Show first 5
            lines.append(f"  • {addition.description}")
        if len(report.additions) > 5:
            lines.append(f"  ... and {len(report.additions) - 5} more")
        lines.append("")
    
    lines.append("=" * 80)
    
    return "\n".join(lines)

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Detect API schema drift')
    parser.add_argument('--baseline', help='Baseline schema file or URL')
    parser.add_argument('--current', help='Current schema file or URL')
    parser.add_argument('--auto-detect', action='store_true', help='Auto-detect against saved baseline')
    parser.add_argument('--save-baseline', help='Save current schema as baseline with given name')
    parser.add_argument('--baseline-name', default='default', help='Name for baseline (default: "default")')
    parser.add_argument('--output-format', choices=['text', 'json'], default='text', help='Output format')
    parser.add_argument('--output-file', help='Save report to file')
    parser.add_argument('--ci-mode', action='store_true', help='CI mode - exit with error code if breaking changes')
    parser.add_argument('--api-url', default='http://localhost:8001', help='API base URL for auto-detect')
    
    args = parser.parse_args()
    
    detector = SchemaDriftDetector()
    
    try:
        # Save baseline mode
        if args.save_baseline:
            schema_url = f"{args.api_url}/openapi.json"
            schema = detector.load_schema_from_url(schema_url)
            detector.save_baseline(schema, args.save_baseline)
            return 0
        
        # Auto-detect mode
        if args.auto_detect:
            schema_url = f"{args.api_url}/openapi.json"
            report = detector.auto_detect_drift(schema_url, args.baseline_name)
            
            if report is None:
                return 0  # No drift
        
        # Manual comparison mode
        elif args.baseline and args.current:
            if args.baseline.startswith('http'):
                baseline = detector.load_schema_from_url(args.baseline)
            else:
                baseline = detector.load_schema_from_file(args.baseline)
            
            if args.current.startswith('http'):
                current = detector.load_schema_from_url(args.current)
            else:
                current = detector.load_schema_from_file(args.current)
            
            report = detector.compare_schemas_full(baseline, current)
        
        else:
            parser.error("Must specify either --auto-detect, --save-baseline, or both --baseline and --current")
        
        # Format and output report
        if 'report' in locals():
            formatted_report = format_report(report, args.output_format)
            
            if args.output_file:
                with open(args.output_file, 'w') as f:
                    f.write(formatted_report)
                print(f"📄 Report saved to {args.output_file}")
            else:
                print(formatted_report)
            
            # CI mode exit codes
            if args.ci_mode:
                if report.breaking_changes:
                    print("💥 Breaking changes detected - failing CI build")
                    return 1
                elif report.warnings:
                    print("⚠️  Warnings detected - check compatibility")
                    return 0
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())