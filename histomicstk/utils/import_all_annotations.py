#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Import annotations from a compressed archive back into Girder.
This script restores annotations along with their metadata and folder structure.
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


class GirderAnnotationImporter(object):
    def __init__(self, api_url, api_key=None, token=None):
        self.gc = girder_client.GirderClient(apiUrl=api_url)
        
        # Authenticate
        if api_key:
            self.gc.authenticate(apiKey=api_key)
        elif token:
            self.gc.authenticate(token=token)
        else:
            raise ValueError("Either API key or token must be provided")
        
        # Mapping of old IDs to new IDs
        self.id_map = {
            'collections': {},
            'folders': {},
            'items': {},
            'annotations': {}
        }
        
        self.stats = defaultdict(int)
    
    def extract_archive(self, archive_path, extract_dir):
        """Extract the compressed archive."""
        print("Extracting archive: {}".format(archive_path))
        
        with tarfile.open(archive_path, 'r:gz') as tar:
            tar.extractall(extract_dir)
        
        # Find the manifest file
        for root, dirs, files in os.walk(extract_dir):
            if 'manifest.json' in files:
                return os.path.join(root, 'manifest.json')
        
        raise ValueError("Manifest file not found in archive")
    
    def find_or_create_collection(self, collection_data, old_id):
        """Find existing collection by name or create new one."""
        # Check if collection already exists
        collections = self.gc.get('collection')
        
        for col in collections:
            if col['name'] == collection_data['name']:
                print("  Found existing collection: {}".format(col['name']))
                self.id_map['collections'][old_id] = col['_id']
                return col['_id']
        
        # Create new collection
        print("  Creating collection: {}".format(collection_data['name']))
        
        new_collection = self.gc.post('collection', data={
            'name': collection_data['name'],
            'description': collection_data.get('description', '')
        })
        
        # Set metadata if present
        if collection_data.get('meta'):
            self.gc.put(
                "collection/{}/metadata".format(new_collection['_id']),
                json=collection_data['meta']
            )
        
        self.id_map['collections'][old_id] = new_collection['_id']
        self.stats['collections_created'] += 1
        
        return new_collection['_id']
    
    def find_or_create_folder(self, folder_data, old_id):
        """Find existing folder or create new one."""
        parent_type = 'collection' if folder_data.get('parentCollection') else 'folder'
        
        if parent_type == 'collection':
            parent_id = self.id_map['collections'].get(
                folder_data['parentCollection']
            )
        else:
            parent_id = self.id_map['folders'].get(folder_data['parentId'])
        
        if not parent_id:
            print("  Warning: Parent not found for folder {}".format(folder_data['name']))
            return None
        
        # Check if folder exists
        existing_folders = self.gc.get(
            "folder?parentType={}&parentId={}".format(parent_type, parent_id)
        )
        
        for folder in existing_folders:
            if folder['name'] == folder_data['name']:
                print("  Found existing folder: {}".format(folder_data['export_path']))
                self.id_map['folders'][old_id] = folder['_id']
                return folder['_id']
        
        # Create new folder
        print("  Creating folder: {}".format(folder_data['export_path']))
        
        new_folder = self.gc.post('folder', data={
            'parentType': parent_type,
            'parentId': parent_id,
            'name': folder_data['name']
        })
        
        # Set metadata if present
        if folder_data.get('meta'):
            self.gc.put(
                "folder/{}/metadata".format(new_folder['_id']),
                json=folder_data['meta']
            )
        
        self.id_map['folders'][old_id] = new_folder['_id']
        self.stats['folders_created'] += 1
        
        return new_folder['_id']
    
    def find_or_create_item(self, item_data, old_id):
        """Find existing item or create new one."""
        folder_id = self.id_map['folders'].get(item_data['folderId'])
        
        if not folder_id:
            print("  Warning: Folder not found for item {}".format(item_data['name']))
            return None
        
        # Check if item exists
        existing_items = self.gc.get("item?folderId={}".format(folder_id))
        
        for item in existing_items:
            if item['name'] == item_data['name']:
                print("    Found existing item: {}".format(item_data['name']))
                self.id_map['items'][old_id] = item['_id']
                return item['_id']
        
        # Create new item (placeholder - actual file upload would be needed)
        print("    Creating item placeholder: {}".format(item_data['name']))
        
        new_item = self.gc.post('item', data={
            'folderId': folder_id,
            'name': item_data['name']
        })
        
        # Set metadata if present
        if item_data.get('meta'):
            self.gc.put(
                "item/{}/metadata".format(new_item['_id']),
                json=item_data['meta']
            )
        
        self.id_map['items'][old_id] = new_item['_id']
        self.stats['items_created'] += 1
        
        return new_item['_id']
    
    def create_annotation(self, annotation_data, old_id):
        """Create annotation on item."""
        item_id = self.id_map['items'].get(annotation_data['itemId'])
        
        if not item_id:
            print("    Warning: Item not found for annotation {}".format(old_id))
            return None
        
        # Check if annotation already exists with same content
        existing_annotations = self.gc.get("annotation/item/{}".format(item_id))
        
        for existing in existing_annotations:
            if (existing.get('annotation', {}).get('name') == 
                annotation_data['annotation'].get('name')):
                print("    Annotation already exists for user: {}".format(
                    annotation_data['annotation'].get('name')))
                self.stats['annotations_skipped'] += 1
                return existing['_id']
        
        # Create annotation
        print("    Creating annotation: {}".format(
            annotation_data['annotation'].get('name', 'Unknown')))
        
        # Post annotation data
        annotation_payload = annotation_data['annotation'].copy()
        
        new_annotation = self.gc.post(
            "annotation?itemId={}".format(item_id),
            json=annotation_payload
        )
        
        # Set access control if present
        if annotation_data.get('access_control'):
            try:
                self.gc.put(
                    "annotation/{}/access".format(new_annotation['_id']),
                    parameters={
                        'access': json.dumps(annotation_data['access_control']),
                        'public': 'false'
                    }
                )
            except Exception as e:
                print("      Warning: Could not set access control: {}".format(e))
        
        self.id_map['annotations'][old_id] = new_annotation['_id']
        self.stats['annotations_created'] += 1
        
        return new_annotation['_id']
    
    def import_all(self, manifest_path, skip_existing=True):
        """Import all data from manifest."""
        print("\nLoading manifest: {}".format(manifest_path))
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        print("Export date: {}".format(manifest['export_date']))
        print("Original Girder URL: {}".format(manifest['girder_url']))
        
        # Import collections
        print("\n=== Importing Collections ===")
        for old_id, collection_data in manifest['collections'].items():
            self.find_or_create_collection(collection_data, old_id)
        
        # Import folders (need to handle hierarchy)
        print("\n=== Importing Folders ===")
        
        # Sort folders by path depth to ensure parents are created first
        sorted_folders = sorted(
            manifest['folders'].items(),
            key=lambda x: x[1]['export_path'].count('/')
        )
        
        for old_id, folder_data in sorted_folders:
            self.find_or_create_folder(folder_data, old_id)
        
        # Import items
        print("\n=== Importing Items ===")
        for old_id, item_data in manifest['items'].items():
            self.find_or_create_item(item_data, old_id)
        
        # Import annotations
        print("\n=== Importing Annotations ===")
        for old_id, annotation_data in manifest['annotations'].items():
            self.create_annotation(annotation_data, old_id)
        
        return self.stats
    
    def verify_import(self, manifest_path):
        """Verify that import was successful."""
        print("\n=== Verifying Import ===")
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Check collections
        collections_found = 0
        for old_id in manifest['collections']:
            if old_id in self.id_map['collections']:
                collections_found += 1
        
        # Check annotations
        annotations_found = 0
        for old_id in manifest['annotations']:
            if old_id in self.id_map['annotations']:
                annotations_found += 1
        
        print("Collections mapped: {}/{}".format(
            collections_found, len(manifest['collections'])))
        print("Annotations mapped: {}/{}".format(
            annotations_found, len(manifest['annotations'])))
        
        return {
            'collections_mapped': collections_found,
            'annotations_mapped': annotations_found
        }


def main():
    parser = argparse.ArgumentParser(
        description='Import annotations into Girder from archive'
    )
    parser.add_argument(
        'archive',
        help='Path to the compressed archive file'
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
        '--extract-dir',
        default='./import_temp',
        help='Temporary directory for extraction'
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        default=True,
        help='Skip existing collections/folders/items'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be imported without actually importing'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.archive):
        print("Error: Archive file not found: {}".format(args.archive))
        sys.exit(1)
    
    # Create importer
    importer = GirderAnnotationImporter(
        args.url,
        api_key=args.apikey,
        token=args.token
    )
    
    # Extract archive
    try:
        os.makedirs(args.extract_dir)
    except OSError:
        if not os.path.isdir(args.extract_dir):
            raise
    
    manifest_path = importer.extract_archive(args.archive, args.extract_dir)
    
    if args.dry_run:
        print("\n=== DRY RUN - No changes will be made ===")
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        print("\nWould import:")
        print("  Collections: {}".format(len(manifest['collections'])))
        print("  Folders: {}".format(len(manifest['folders'])))
        print("  Items: {}".format(len(manifest['items'])))
        print("  Annotations: {}".format(len(manifest['annotations'])))
        
        return
    
    # Import all data
    stats = importer.import_all(manifest_path, args.skip_existing)
    
    # Print statistics
    print("\n=== Import Statistics ===")
    print("Collections created: {}".format(stats['collections_created']))
    print("Folders created: {}".format(stats['folders_created']))
    print("Items created: {}".format(stats['items_created']))
    print("Annotations created: {}".format(stats['annotations_created']))
    print("Annotations skipped: {}".format(stats['annotations_skipped']))
    
    # Verify import
    verification = importer.verify_import(manifest_path)
    
    # Save ID mappings for reference
    mapping_file = "import_mapping_{}.json".format(
        datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    
    with open(mapping_file, 'w') as f:
        json.dump(importer.id_map, f, indent=2)
    
    print("\nID mappings saved to: {}".format(mapping_file))
    
    # Cleanup
    import shutil
    response = raw_input("\nRemove temporary extraction directory? (y/N): ")
    if response.lower() == 'y':
        shutil.rmtree(args.extract_dir)
        print("Removed: {}".format(args.extract_dir))


if __name__ == '__main__':
    main()

