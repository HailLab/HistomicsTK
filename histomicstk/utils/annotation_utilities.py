#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utility functions for working with Girder annotation exports/imports.
Includes validation, comparison, and migration tools.
"""

from __future__ import print_function
import os
import json
import argparse
import datetime
from collections import defaultdict

import girder_client


class AnnotationUtilities(object):
    def __init__(self, api_url=None, api_key=None, token=None):
        if api_url:
            self.gc = girder_client.GirderClient(apiUrl=api_url)
            
            # Authenticate
            if api_key:
                self.gc.authenticate(apiKey=api_key)
            elif token:
                self.gc.authenticate(token=token)
            else:
                raise ValueError("Either API key or token must be provided")
    
    def validate_export(self, manifest_path):
        """Validate the integrity of an export."""
        print("Validating export: {}".format(manifest_path))
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        issues = []
        
        # Check for orphaned annotations
        for ann_id, annotation in manifest['annotations'].items():
            if annotation['itemId'] not in manifest['items']:
                issues.append("Orphaned annotation {}: references non-existent item {}".format(
                    ann_id, annotation['itemId']))
        
        # Check for orphaned items
        for item_id, item in manifest['items'].items():
            if item['folderId'] not in manifest['folders']:
                issues.append("Orphaned item {}: references non-existent folder {}".format(
                    item_id, item['folderId']))
        
        # Check folder hierarchy
        for folder_id, folder in manifest['folders'].items():
            if folder.get('parentId'):
                if folder['parentId'] not in manifest['folders']:
                    issues.append("Broken folder hierarchy: {} references non-existent parent {}".format(
                        folder_id, folder['parentId']))
        
        # Summary
        print("\nValidation Results:")
        print("Total issues found: {}".format(len(issues)))
        
        if issues:
            print("\nIssues:")
            for issue in issues[:10]:  # Show first 10 issues
                print("  - {}".format(issue))
            
            if len(issues) > 10:
                print("  ... and {} more issues".format(len(issues) - 10))
        else:
            print("✓ Export is valid")
        
        return len(issues) == 0
    
    def compare_exports(self, manifest1_path, manifest2_path):
        """Compare two exports to find differences."""
        print("Comparing exports:")
        print("  Export 1: {}".format(manifest1_path))
        print("  Export 2: {}".format(manifest2_path))
        
        with open(manifest1_path, 'r') as f:
            manifest1 = json.load(f)
        
        with open(manifest2_path, 'r') as f:
            manifest2 = json.load(f)
        
        # Compare collections
        collections1 = set(manifest1['collections'].keys())
        collections2 = set(manifest2['collections'].keys())
        
        # Compare annotations
        annotations1 = set(manifest1['annotations'].keys())
        annotations2 = set(manifest2['annotations'].keys())
        
        # Find differences
        results = {
            'collections': {
                'only_in_1': collections1 - collections2,
                'only_in_2': collections2 - collections1,
                'in_both': collections1 & collections2
            },
            'annotations': {
                'only_in_1': annotations1 - annotations2,
                'only_in_2': annotations2 - annotations1,
                'in_both': annotations1 & annotations2
            }
        }
        
        # Print summary
        print("\n=== Comparison Results ===")
        print("Collections:")
        print("  Only in export 1: {}".format(len(results['collections']['only_in_1'])))
        print("  Only in export 2: {}".format(len(results['collections']['only_in_2'])))
        print("  In both exports: {}".format(len(results['collections']['in_both'])))
        
        print("\nAnnotations:")
        print("  Only in export 1: {}".format(len(results['annotations']['only_in_1'])))
        print("  Only in export 2: {}".format(len(results['annotations']['only_in_2'])))
        print("  In both exports: {}".format(len(results['annotations']['in_both'])))
        
        return results
    
    def extract_subset(self, manifest_path, output_path, collection_ids=None, 
                       item_ids=None, user_names=None):
        """Extract a subset of the export based on filters."""
        print("Extracting subset from: {}".format(manifest_path))
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Create new manifest with subset
        subset = {
            'export_date': datetime.datetime.utcnow().isoformat(),
            'original_export': manifest.get('export_date'),
            'subset_criteria': {
                'collection_ids': collection_ids,
                'item_ids': item_ids,
                'user_names': user_names
            },
            'collections': {},
            'folders': {},
            'items': {},
            'annotations': {},
            'users': manifest.get('users', {}),
            'groups': manifest.get('groups', {})
        }
        
        # Filter collections
        if collection_ids:
            for col_id in collection_ids:
                if col_id in manifest['collections']:
                    subset['collections'][col_id] = manifest['collections'][col_id]
        else:
            subset['collections'] = manifest['collections']
        
        # Filter folders (include all folders under selected collections)
        for folder_id, folder in manifest['folders'].items():
            if collection_ids:
                if folder.get('parentCollection') in subset['collections']:
                    subset['folders'][folder_id] = folder
            else:
                subset['folders'][folder_id] = folder
        
        # Filter items
        if item_ids:
            for item_id in item_ids:
                if item_id in manifest['items']:
                    subset['items'][item_id] = manifest['items'][item_id]
                    # Include the folder
                    folder_id = manifest['items'][item_id]['folderId']
                    if folder_id in manifest['folders']:
                        subset['folders'][folder_id] = manifest['folders'][folder_id]
        else:
            # Include all items in selected folders
            for item_id, item in manifest['items'].items():
                if item['folderId'] in subset['folders']:
                    subset['items'][item_id] = item
        
        # Filter annotations
        for ann_id, annotation in manifest['annotations'].items():
            include = False
            
            # Check if item is included
            if annotation['itemId'] in subset['items']:
                include = True
            
            # Check user filter
            if user_names and include:
                ann_user = annotation.get('annotation', {}).get('name', '')
                if ann_user not in user_names:
                    include = False
            
            if include:
                subset['annotations'][ann_id] = annotation
        
        # Save subset
        with open(output_path, 'w') as f:
            json.dump(subset, f, indent=2)
        
        # Print summary
        print("\n=== Subset Extraction Results ===")
        print("Collections: {} / {}".format(
            len(subset['collections']), len(manifest['collections'])))
        print("Folders: {} / {}".format(
            len(subset['folders']), len(manifest['folders'])))
        print("Items: {} / {}".format(
            len(subset['items']), len(manifest['items'])))
        print("Annotations: {} / {}".format(
            len(subset['annotations']), len(manifest['annotations'])))
        print("\nSubset saved to: {}".format(output_path))
        
        return subset
    
    def generate_report(self, manifest_path, output_path):
        """Generate a detailed report from an export."""
        print("Generating report from: {}".format(manifest_path))
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        report = []
        report.append("# Girder Annotation Export Report")
        report.append("\nExport Date: {}".format(manifest.get('export_date', 'Unknown')))
        report.append("Source: {}\n".format(manifest.get('girder_url', 'Unknown')))
        
        # Summary statistics
        report.append("## Summary Statistics")
        report.append("- Collections: {}".format(len(manifest['collections'])))
        report.append("- Folders: {}".format(len(manifest['folders'])))
        report.append("- Items: {}".format(len(manifest['items'])))
        report.append("- Annotations: {}".format(len(manifest['annotations'])))
        report.append("- Users referenced: {}".format(len(manifest.get('users', {}))))
        report.append("- Groups referenced: {}\n".format(len(manifest.get('groups', {}))))
        
        # Annotations per user
        report.append("## Annotations by User")
        user_counts = defaultdict(int)
        for annotation in manifest['annotations'].values():
            user = annotation.get('annotation', {}).get('name', 'Unknown')
            user_counts[user] += 1
        
        for user, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True):
            report.append("- {}: {} annotations".format(user, count))
        
        # Annotations per collection
        report.append("\n## Annotations by Collection")
        collection_counts = defaultdict(int)
        
        # Map items to collections through folders
        item_to_collection = {}
        for item_id, item in manifest['items'].items():
            folder_id = item['folderId']
            # Traverse up to find collection
            while folder_id and folder_id in manifest['folders']:
                folder = manifest['folders'][folder_id]
                if folder.get('parentCollection'):
                    item_to_collection[item_id] = folder['parentCollection']
                    break
                folder_id = folder.get('parentId')
        
        # Count annotations per collection
        for annotation in manifest['annotations'].values():
            item_id = annotation['itemId']
            if item_id in item_to_collection:
                col_id = item_to_collection[item_id]
                col_name = manifest['collections'][col_id]['name']
                collection_counts[col_name] += 1
        
        for collection, count in sorted(collection_counts.items()):
            report.append("- {}: {} annotations".format(collection, count))
        
        # Annotation types
        report.append("\n## Annotation Element Types")
        element_types = defaultdict(int)
        for annotation in manifest['annotations'].values():
            elements = annotation.get('annotation', {}).get('elements', [])
            for element in elements:
                element_types[element.get('type', 'Unknown')] += 1
        
        for elem_type, count in sorted(element_types.items()):
            report.append("- {}: {} elements".format(elem_type, count))
        
        # Save report
        with open(output_path, 'w') as f:
            f.write('\n'.join(report))
        
        print("\nReport saved to: {}".format(output_path))
        
        return report


def main():
    parser = argparse.ArgumentParser(
        description='Utilities for Girder annotation exports'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate export integrity')
    validate_parser.add_argument('manifest', help='Path to manifest.json')
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare two exports')
    compare_parser.add_argument('manifest1', help='Path to first manifest.json')
    compare_parser.add_argument('manifest2', help='Path to second manifest.json')
    
    # Extract subset command
    subset_parser = subparsers.add_parser('subset', help='Extract subset of export')
    subset_parser.add_argument('manifest', help='Path to manifest.json')
    subset_parser.add_argument('-o', '--output', required=True, help='Output path')
    subset_parser.add_argument('-c', '--collections', nargs='+', help='Collection IDs')
    subset_parser.add_argument('-i', '--items', nargs='+', help='Item IDs')
    subset_parser.add_argument('-u', '--users', nargs='+', help='User names')
    
    # Generate report command
    report_parser = subparsers.add_parser('report', help='Generate detailed report')
    report_parser.add_argument('manifest', help='Path to manifest.json')
    report_parser.add_argument('-o', '--output', default='report.md', help='Output path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    utils = AnnotationUtilities()
    
    if args.command == 'validate':
        utils.validate_export(args.manifest)
    
    elif args.command == 'compare':
        utils.compare_exports(args.manifest1, args.manifest2)
    
    elif args.command == 'subset':
        utils.extract_subset(
            args.manifest,
            args.output,
            collection_ids=args.collections,
            item_ids=args.items,
            user_names=args.users
        )
    
    elif args.command == 'report':
        utils.generate_report(args.manifest, args.output)


if __name__ == '__main__':
    main()

