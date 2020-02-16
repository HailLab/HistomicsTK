import argparse
import urllib
import requests
import json
import os


parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
parser.add_argument('-t', '--token', type=str, default=os.environ.get('GIRDER_TOKEN', 'DID_NOT_SUPPLY_GIRDER_TOKEN'),
                    help='Girder token for access')
parser.add_argument('-u', '--url', type=str, default='https://skin.app.vumc.org/api/v1/',
                    help='Url for histomicsTK server')
parser.add_argument('-f', '--folder', type=str, default='', help='Folder images are stored in for processing')
parser.add_argument('-w', '--workergroup', type=str, default='5e310290e3c0d89a0744bf47', help='ID for worker group')
parser.add_argument('-a', '--admingroup', type=str, default='5e3102c0e3c0d89a0744bf50', help='ID for admin group')
parser.add_argument('-o', '--operation', type=str, default='process', choices=['process', 'export', 'status'],
                    help='What to do with images')
args = parser.parse_args()

# scan images and create thumbnails
# set permission of image
# create an annotation with names from every member of group
# create permissions for groups for all annotations
# create copy all annotations from the first image to all the rest

ITEM_API_URL = 'item'
ITEM_QUERY_STRING = '&limit=50&sort=lowerName&sortdir=1'
ANNOTATION_API_URL = 'annotation'
GROUP_API_URL = 'group'
MULTIPLE_ANNOTATIONS = 'annotation/item/'
LARGEIMAGE_QUERY_STRING = '&notify=false'
ACCESS_API_URL = 'folder'
ACCESS_QUERY_STRING = '&public=false&recurse=true&progress=false'
ANNOTATION = 'annotation/'


item_headers = {'Girder-Token': args.token, 'Accept': 'application/json'}
largeimage_headers = {'Content-Type': 'application/x-www-form-urlencoded',
                     'Girder-Token': args.token, 'Accept': 'application/json'}
access_headers = {'Content-Type': 'application/json',
                  'Girder-Token': args.token, 'Accept': 'application/json'}

item_url = args.url + ITEM_API_URL + '?folderId=' + args.folder + ITEM_QUERY_STRING
items = requests.get(item_url, headers=item_headers)
items = json.loads(items.content)

if args.operation == 'process':
    group_url = args.url + GROUP_API_URL + '/' + args.workergroup + '/member?ignore' + ITEM_QUERY_STRING
    group = requests.get(group_url, headers=item_headers)
    group = json.loads(group.content)
    group_by_name = {g['login']: g for g in group}
    annotations_dict = [{'name': u['login'], 'description': u['firstName'] + ' ' + u['lastName']} for u in group]
    admin_user = {
        "flags": [],
        "id": "5e2f35c7e7a8d01deb3964f3",
        "level": 2,
        "login": "admin",
        "name": "admin admin"
    }
    access_dict = {
      "groups": [
        {
          "description": "Demarcating cGVHD photos for expert dermatologist consensus.",
          "flags": [],
          "id": args.workergroup,
          "level": 1,
          "name": "cGVHD"
        },
        {
          "description": "Allow users to see entire interface for cGVHD paint tool.",
          "flags": [],
          "id": args.admingroup,
          "level": 2,
          "name": "cGVHD Superuser"
        }
      ], "users": [
          admin_user
      ]
    }

    access_url = args.url + ACCESS_API_URL + '/' + args.folder + '/access?access=' + urllib.quote_plus(json.dumps(access_dict)) + ACCESS_QUERY_STRING
    access = requests.put(access_url, headers=item_headers)

    for item in items:
        image_url = args.url + ITEM_API_URL + '/' + item['_id'] + '/files' + '?ignore' + ITEM_QUERY_STRING
        image_headers = {'Girder-Token': args.token, 'Accept': 'application/json'}
        image = requests.get(image_url, headers=image_headers)
        image = json.loads(image.content)
        file_id = image[0]['_id']

        largeimage_url = args.url + ITEM_API_URL + '/' + item['_id'] + '/tiles?fileId=' + file_id + LARGEIMAGE_QUERY_STRING
        requests.post(largeimage_url, headers=largeimage_headers)

        annotations_url = args.url + ANNOTATION_API_URL + '?itemId=' + item['_id'] + ITEM_QUERY_STRING
        annotations = requests.get(annotations_url, headers=item_headers)
        annotations = json.loads(annotations.content)
        # [requests.delete(args.url + ANNOTATION_API_URL + '/' + a['_id'], headers=item_headers) for a in annotations]
        annotations_details = {a['_id']: a['annotation'] for a in annotations}
        annotations_access_url = args.url + MULTIPLE_ANNOTATIONS + item['_id']
        requests.post(annotations_access_url, headers=item_headers, data=json.dumps([a for a in annotations_dict if a not in annotations_details.values()]))
        annotation_access_update_url = args.url + ANNOTATION
        for aid, annotation in annotations_details.iteritems():
            a = group_by_name[annotation['name']]
            access_dict["users"] = [
            admin_user,
            {
                "flags": [],
                "id": a['_id'],
                "level": 2,
                "login": a['login'],
                "name": a['firstName'] + ' ' + a['lastName']
            }]
            requests.put(annotation_access_update_url + aid + '/access?access=' + urllib.quote_plus(json.dumps(access_dict)) + '&public=false', headers=access_headers)
elif args.operation == 'export':
    for item in items:
        annotations_access_url = args.url + MULTIPLE_ANNOTATIONS + item['_id']
        with open(item['name'] + '.json', 'wb') as f:
            annotations = requests.get(annotations_access_url, headers=item_headers)
            f.write(annotations.content)
elif args.operation == 'status':
    completed_annotations_cts = {}
    completed_annotations = {}
    for item in items:
        annotations_access_url = args.url + MULTIPLE_ANNOTATIONS + item['_id']
        annotations = json.loads(requests.get(annotations_access_url, headers=item_headers).content)
        for annotation in annotations:
            try:
                user = annotation['annotation']['description']
                if user not in completed_annotations_cts:
                    completed_annotations_cts[user] = 0
                    completed_annotations[user] = []
                if len(annotation['annotation']['elements']) and len(annotation['annotation']['elements'][0]['points']):
                    completed_annotations_cts[user] = completed_annotations_cts[user] + 1
                    completed_annotations[user].append(annotation['itemId'])
            except Exception:
                print("Skipped annotation " + annotation['_id'])
    print(completed_annotations)
    print(completed_annotations_cts)
