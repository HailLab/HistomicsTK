import argparse
import datetime
import pytz
import urllib
import requests
import json
import os
import sys
from dateutil import parser


argparser = argparse.ArgumentParser(fromfile_prefix_chars='@')
argparser.add_argument('-t', '--token', type=str, default=os.environ.get('GIRDER_TOKEN', 'DID_NOT_SUPPLY_GIRDER_TOKEN'),
                       help='Girder token for access')
argparser.add_argument('-u', '--url', type=str, default='https://skin.app.vumc.org/api/v1/',
                       help='Url for histomicsTK server')
argparser.add_argument('-f', '--folder', type=str, default='', help='Folder images are stored in for processing')
argparser.add_argument('-w', '--workergroup', type=str, default='5f0dc554c9f8c18253ae949d', help='ID for worker group')
argparser.add_argument('-a', '--admingroup', type=str, default='5f0dc574c9f8c18253ae949e', help='ID for admin group')
argparser.add_argument('-b', '--baselinegroup', type=str, default='5f0dc532c9f8c18253ae949c', help='ID for baseline group')
argparser.add_argument('-o', '--operation', type=str, default='process',
                       choices=['process', 'export', 'status', 'process_baseline'], help='What to do with images')
argparser.add_argument('-s', '--startdate', type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'), default=None,
                       help='date before which no annotations will be returned (inclusive)')
argparser.add_argument('-e', '--enddate', type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'), default=None,
                       help='date after which no annotations will be returned (inclusive)')
args = argparser.parse_args()

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


# want to output dict without the leading unicode u for annotations
class unicode(unicode):
    def __repr__(self):
        return __builtins__.unicode.__repr__(self).lstrip("u")


if 'message' in items:
    sys.stderr.write(items['message'] + "\n")
elif args.operation == 'process' or args.operation == 'process_baseline':
    group_worker_or_baseline = args.workergroup if args.operation == 'process' else args.baselinegroup
    group_url = args.url + GROUP_API_URL + '/' + group_worker_or_baseline + '/member?ignore' + ITEM_QUERY_STRING
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

    if args.operation == 'process_baseline':
        access_dict['groups'].append(
            {
              "description": "Demarcating cGVHD photos for potential inclusion in study.",
              "flags": [],
              "id": args.baselinegroup,
              "level": 1,
              "name": "Baseline"
            }
        )

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
            try:
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
            except KeyError:
                print 'No user {0} in group'.format(annotation['name'])
elif args.operation == 'export':
    for item in items:
        updated = parser.parse(item['updated'])
        localtz = pytz.timezone("America/Chicago")
        # restrict by start and end dates
        startdate = localtz.localize(args.startdate) if args.startdate else None
        enddate = localtz.localize(args.enddate) + datetime.timedelta(1) if args.enddate else None
        start_range = startdate and startdate <= updated
        end_range = enddate and enddate >= updated
        if start_range and end_range or start_range and not enddate or end_range and not startdate or not startdate and not enddate:
            annotations_access_url = args.url + MULTIPLE_ANNOTATIONS + item['_id']
            annotations_blob = requests.get(annotations_access_url, headers=item_headers)
            annotations = json.loads(annotations_blob.content)
            annotations_within_range = []
            for annotation in annotations:
                try:
                    updated_anno = parser.parse(annotation['updated'])
                except TypeError:
                    updated_anno = parser.parse(annotation['created'])
                # restrict annotations by date
                start_range_anno = startdate and startdate <= updated_anno
                end_range_anno = enddate and enddate >= updated_anno
                if start_range_anno and end_range_anno or start_range_anno and not enddate or end_range_anno and not startdate or not startdate and not enddate:
                    annotations_within_range.append(annotation)
            if annotations_within_range:
                with open(item['name'] + '.json', 'wb') as f:
                    f.write(json.dumps([anno for anno in annotations_within_range]))
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
