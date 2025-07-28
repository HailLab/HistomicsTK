#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Export all annotations from Girder to a compressed archive.
This script exports annotations along with their metadata, folder structure,
and associated items for later reimport.
"""

from __future__ import print_function
import os
import sys
import json
import tarfile
import argparse
import datetime
from collections import defaultdict

import girder_client
from girder.utility import JsonEncoder


class GirderAnnotationExporter(object):
    def __init__(self, api_url, api_key=None, token=None):
        self.gc = girder_client.GirderClient(apiUrl=api_url)
        
        # Authenticate
        if api_key:
            self.gc.authenticate(apiKey=api_key)
        elif token:
            self.gc.authenticate(token=token)
        else:
            raise ValueError("Either API key or token must be provided")
        
        self.export_data = {
            'export_date': datetime.datetime.utcnow().isoformat(),
            'girder_url': api_url,
            'collections': {},
            'folders': {},
            'items': {},
            'annotations': {},
            'users': {},
            'groups': {},
            'access_control': {}
        }
    
    def get_all_collections(self):
        """Get all collections the user has access to."""
        print("Fetching collections...")
        collections = self.gc.get('collection')
        return collections
    
    def get_folders_recursive(self, parent_id, parent_type='collection', path=''):
        """Recursively get all folders under a parent."""
        folders = []
        
        # Get immediate child folders
        if parent_type == 'collection':
            folder_list = self.gc.get('folder?parentType=collection&parentId={}'.format(parent_id))
        else:  # folder
            folder_list = self.gc.get('folder?parentType=folder&parentId={}'.format(parent_id))
        
        for folder in folder_list:
            folder['export_path'] = os.path.join(path, folder['name'])
            folders.append(folder)
            
            # Recursively get subfolders
            subfolders = self.get_folders_recursive(
                folder['_id'], 
                'folder', 
                folder['export_path']
            )
            folders.extend(subfolders)
        
        return folders
    
    def get_items_in_folder(self, folder_id):
        """Get all items in a folder."""
        items = self.gc.get('item?folderId={}&limit=0'.format(folder_id))
        return items
    
    def get_annotations_for_item(self, item_id):
        """Get all annotations for an item."""
        try:
            annotations = self.gc.get('annotation/item/{}'.format(item_id))
            return annotations
        except girder_client.HttpError:
            return []
    
    def get_annotation_details(self, annotation_id):
        """Get full annotation details including access control."""
        try:
            annotation = self.gc.get('annotation/{}'.format(annotation_id))
            
            # Try to get access control info
            try:
                access = self.gc.get('annotation/{}/access'.format(annotation_id))
                annotation['access_control'] = access
            except:
                pass
            
            return annotation
        except girder_client.HttpError:
            return None
    
    def export_all(self, output_dir, collections_filter=None):
        """Export all annotations and related data."""
        try:
            os.makedirs(output_dir)
        except OSError:
            if not os.path.isdir(output_dir):
                raise
        
        # Get collections
        collections = self.get_all_collections()
        if collections_filter:
            collections = [c for c in collections if c['_id'] in collections_filter]
        
        total_annotations = 0
        
        for collection in collections:
            print("\nProcessing collection: {} ({})".format(collection['name'], collection['_id']))
            
            # Store collection info
            self.export_data['collections'][collection['_id']] = {
                'name': collection['name'],
                'description': collection.get('description', ''),
                'created': collection.get('created'),
                'updated': collection.get('updated'),
                'meta': collection.get('meta', {})
            }
            
            # Get all folders in collection
            folders = self.get_folders_recursive(collection['_id'], 'collection')
            
            for folder in folders:
                print("  Processing folder: {}".format(folder['export_path']))
                
                # Store folder info
                self.export_data['folders'][folder['_id']] = {
                    'name': folder['name'],
                    'parentId': folder['parentId'],
                    'parentCollection': folder.get('parentCollection'),
                    'export_path': folder['export_path'],
                    'created': folder.get('created'),
                    'updated': folder.get('updated'),
                    'meta': folder.get('meta', {})
                }
                
                # Get items in folder
                items = self.get_items_in_folder(folder['_id'])
                
                for item in items:
                    # Store item info
                    self.export_data['items'][item['_id']] = {
                        'name': item['name'],
                        'folderId': item['folderId'],
                        'created': item.get('created'),
                        'updated': item.get('updated'),
                        'meta': item.get('meta', {}),
                        'size': item.get('size')
                    }
                    
                    # Get annotations for item
                    annotations = self.get_annotations_for_item(item['_id'])
                    
                    if annotations:
                        print("    Found {} annotations for item: {}".format(len(annotations), item['name']))
                        total_annotations += len(annotations)
                        
                        for annotation in annotations:
                            # Get full annotation details
                            full_annotation = self.get_annotation_details(annotation['_id'])
                            
                            if full_annotation:
                                self.export_data['annotations'][annotation['_id']] = {
                                    'itemId': item['_id'],
                                    'created': full_annotation.get('created'),
                                    'updated': full_annotation.get('updated'),
                                    'creatorId': full_annotation.get('creatorId'),
                                    'annotation': full_annotation.get('annotation', {}),
                                    'access_control': full_annotation.get('access_control', {})
                                }
                                
                                # Track users and groups referenced in annotations
                                if 'access_control' in full_annotation:
                                    for user in full_annotation['access_control'].get('users', []):
                                        self.export_data['users'][user['id']] = user
                                    for group in full_annotation['access_control'].get('groups', []):
                                        self.export_data['groups'][group['id']] = group
        
        print("\nTotal annotations found: {}".format(total_annotations))
        
        # Write manifest
        manifest_path = os.path.join(output_dir, 'manifest.json')
        with open(manifest_path, 'w') as f:
            json.dump(self.export_data, f, cls=JsonEncoder, indent=2)
        
        print("Manifest written to: {}".format(manifest_path))
        
        return self.export_data
    
    def create_archive(self, output_dir, archive_name):
        """Create a compressed archive of the export."""
        archive_path = "{}.tar.gz".format(archive_name)
        
        print("\nCreating archive: {}".format(archive_path))
        
        with tarfile.open(archive_path, 'w:gz') as tar:
            tar.add(output_dir, arcname=os.path.basename(output_dir))
        
        print("Archive created: {}".format(archive_path))
        print("Archive size: {:.2f} MB".format(os.path.getsize(archive_path) / 1024.0 / 1024.0))
        
        return archive_path
    
    def calculate_md5(self, filepath):
        """Calculate MD5 hash of a file."""
        import hashlib
        hash_md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def check_and_remove_duplicate(self, archive_path, backup_pattern="Skin_Annotation_Backup_*.tar.gz"):
        """Check if new archive is duplicate of previous and remove if so."""
        import glob
        
        # Get all backup files matching the pattern
        backup_dir = os.path.dirname(archive_path) or '.'
        pattern = os.path.join(backup_dir, backup_pattern)
        existing_backups = sorted(glob.glob(pattern))
        
        if len(existing_backups) < 2:
            print("No previous backup found for comparison.")
            return False
        
        # The new archive should be the last one
        new_archive = existing_backups[-1]
        prev_archive = existing_backups[-2]
        
        if new_archive != archive_path:
            print("Warning: Expected {} to be the newest archive".format(archive_path))
            return False
        
        print("\nChecking for duplicate backup...")
        print("Comparing: {} vs {}".format(
            os.path.basename(new_archive), 
            os.path.basename(prev_archive)))
        
        # Calculate MD5 for both files
        new_md5 = self.calculate_md5(new_archive)
        prev_md5 = self.calculate_md5(prev_archive)
        
        print("New backup MD5:  {}".format(new_md5))
        print("Prev backup MD5: {}".format(prev_md5))
        
        if new_md5 == prev_md5:
            print("\n✓ Backups are identical. Removing redundant backup.")
            os.remove(new_archive)
            print("  Removed: {}".format(os.path.basename(new_archive)))
            print("  Keeping: {}".format(os.path.basename(prev_archive)))
            return True
        else:
            print("\n✓ Backups are different. Keeping new backup.")
            return False


def main():
    parser = argparse.ArgumentParser(
        description='Export all annotations from Girder'
    )
    parser.add_argument(
        '-u', '--url',
        default='https://girder.example.com/api/v1/',
        help='Girder API URL'
    )
    parser.add_argument(
        '-k', '--apikey',
        help='Girder API key'
    )
    parser.add_argument(
        '-t', '--token',
        help='Girder token'
    )
    parser.add_argument(
        '-o', '--output',
        default=None,
        help='Output archive name (default: Skin_Annotation_Backup_YYYY_MM_DD)'
    )
    parser.add_argument(
        '-c', '--collections',
        nargs='+',
        help='Specific collection IDs to export (default: all)'
    )
    parser.add_argument(
        '--no-compress',
        action='store_true',
        help='Skip creating compressed archive'
    )
    parser.add_argument(
        '--no-dedup',
        action='store_true',
        help='Skip duplicate detection and removal'
    )
    parser.add_argument(
        '--keep-temp',
        action='store_true',
        help='Keep temporary directory after creating archive'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Create exporter
    exporter = GirderAnnotationExporter(
        args.url,
        api_key=args.apikey,
        token=args.token
    )
    
    # Generate default output name if not provided
    if args.output is None:
        date_str = datetime.datetime.now().strftime('%Y_%m_%d')
        archive_name = "Skin_Annotation_Backup_{}".format(date_str)
    else:
        archive_name = args.output
    
    # Create output directory with timestamp for the temp files
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = "temp_export_{}".format(timestamp)
    
    # Export all data
    export_data = exporter.export_all(output_dir, args.collections)
    
    # Create statistics
    print("\n=== Export Statistics ===")
    print("Collections: {}".format(len(export_data['collections'])))
    print("Folders: {}".format(len(export_data['folders'])))
    print("Items: {}".format(len(export_data['items'])))
    print("Annotations: {}".format(len(export_data['annotations'])))
    print("Users referenced: {}".format(len(export_data['users'])))
    print("Groups referenced: {}".format(len(export_data['groups'])))
    
    # Create archive unless skipped
    archive_path = None
    if not args.no_compress:
        archive_path = exporter.create_archive(output_dir, archive_name)
        
        # Check for duplicates unless skipped
        if not args.no_dedup and archive_path:
            was_duplicate = exporter.check_and_remove_duplicate(archive_path)
            if was_duplicate:
                archive_path = None  # Archive was removed
    
    # Always remove uncompressed directory unless explicitly kept
    if not args.keep_temp and not args.no_compress:
        import shutil
        print("\nRemoving temporary directory: {}".format(output_dir))
        shutil.rmtree(output_dir)
        print("Temporary directory removed.")
    elif args.keep_temp:
        print("\nTemporary directory kept at: {}".format(output_dir))
    
    if archive_path and os.path.exists(archive_path):
        print("\n" + "="*50)
        print("EXPORT COMPLETE")
        print("="*50)
        print("Archive created: {}".format(archive_path))
        print("Archive size: {:.2f} MB".format(os.path.getsize(archive_path) / 1024.0 / 1024.0))
    elif not args.no_compress:
        print("\n" + "="*50)
        print("EXPORT COMPLETE")
        print("="*50)
        print("No new archive created (identical to previous backup)")
        print("Previous backup is sufficient - no changes detected")
    else:
        print("\n" + "="*50)
        print("EXPORT COMPLETE")
        print("="*50)
        print("Export data available at: {}".format(output_dir))


if __name__ == '__main__':
    main()

