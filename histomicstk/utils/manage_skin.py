import argparse
import datetime
import pytz
import urllib
import requests
import json
import os
import sys
import glob
import re
import tarfile
import time
import inspect
from dateutil import parser

from girder.models.upload import Upload
from girder.api.v1.item import Folder
from girder.models.token import Token
from girder.models.user import User
from girder.models.collection import Collection
from girder.exceptions import ValidationException


argparser = argparse.ArgumentParser(fromfile_prefix_chars='@')
argparser.add_argument('-t', '--token', type=str, default=os.environ.get('GIRDER_TOKEN', 'DID_NOT_SUPPLY_GIRDER_TOKEN'),
                       help='Girder token for access')
argparser.add_argument('-r', '--redcaptoken', type=str, default=os.environ.get('REDCAP_TOKEN', 'DID_NOT_SUPPLY_GIRDER_TOKEN'),
                       help='REDCap token for access')
argparser.add_argument('-u', '--url', type=str, default='https://skin.app.vumc.org/api/v1/',
                       help='Url for histomicsTK server')
argparser.add_argument('-f', '--folder', type=str, default='', help='Folder images are stored in for processing')
argparser.add_argument('-n', '--foldername', type=str, default='unnamed', help='Name of new folder')
argparser.add_argument('-w', '--workergroup', type=str, default='5f0dc554c9f8c18253ae949d', help='ID for worker group')
argparser.add_argument('-a', '--admingroup', type=str, default='5f0dc574c9f8c18253ae949e', help='ID for admin group')
argparser.add_argument('-b', '--baselinegroup', type=str, default='5f0dc532c9f8c18253ae949c', help='ID for baseline group')
argparser.add_argument('-c', '--collection', type=str, default='5f0dc3ffc9f8c18253ae9499',
                       help='Collection ID used for creating folders')
argparser.add_argument('-o', '--operation', type=str, default='process',
                       choices=['process', 'export', 'status', 'process_baseline', 'ingest_folder', 'get_from_recap'],
                       help='What to do with images')
argparser.add_argument('-s', '--startdate', type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'), default=None,
                       help='date before which no annotations will be returned (inclusive)')
argparser.add_argument('-e', '--enddate', type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'), default=None,
                       help='date after which no annotations will be returned (inclusive)')
argparser.add_argument('-d', '--datadir', type=str, default='/opt/histomicstk_data',
                       help='folder in which images will be temporarily stored before ingestion')
args = argparser.parse_args()

# scan images and create thumbnails
# set permission of image
# create an annotation with names from every member of group
# create permissions for groups for all annotations
# create copy all annotations from the first image to all the rest

ITEM_API_URL = 'item'
ITEM_QUERY_STRING = '&limit=5000&sort=lowerName&sortdir=1'
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


def meta_annotator_only(meta, annotator):
    for m in meta:
        if annotator in m:
            return m


# want to output dict without the leading unicode u for annotations
class unicode(unicode):
    def __repr__(self):
        return __builtins__.unicode.__repr__(self).lstrip("u")


def merge_dicts(x, y):
    z = x.copy()   # start with keys and values of x
    z.update(y)    # modifies z with keys and values of y
    return z


if args.operation in ['process', 'process_baseline', 'export', 'status']:
    item_url = args.url + ITEM_API_URL + '?folderId=' + args.folder + ITEM_QUERY_STRING
    items = requests.get(item_url, headers=item_headers)
    items = json.loads(items.content)
    if 'message' in items:
        sys.stderr.write(items['message'] + "\n")

if args.operation == 'process' or args.operation == 'process_baseline':
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
                # if a['firstName'] not in ['Xiaoqi']:
                #     continue
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
                print('No user {0} in group'.format(annotation['name']))
elif args.operation == 'export':
    folder_url = args.url + ACCESS_API_URL + '/' + args.folder
    folder = requests.get(folder_url, headers=item_headers)
    folder = json.loads(folder.content)

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
            meta_annotations_only = dict()
            if annotations_within_range:
                for m in item['meta']:
                    for annotator in annotations_within_range:
                        if annotator['annotation']['name'] in m:
                             meta_annotations_only[m] = item['meta'][m]
                item['meta'] = meta_annotations_only
                with open(item['name'] + '.json', 'wb') as f:
                    item['annotations'] = [anno for anno in annotations_within_range]
                    f.write(json.dumps(item))
    if startdate and enddate:
        range_str = '-' + str(startdate.date()) + '--' + str(enddate.date())
    elif startdate:
        range_str = '-before-' + str(startdate.date())
    elif enddate:
        range_str = '-after-' + str(enddate.date())
    else:
        range_str = ''
    tar_obj = tarfile.open(folder['name'] + '-' + item['folderId'] + range_str + '.tar.gz', 'w:gz')
    json_files = glob.glob("*.json")
    [tar_obj.add(json_file) for json_file in json_files]
    tar_obj.close()
    [os.remove(json_file) for json_file in json_files]
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
elif args.operation == 'ingest_folder':

    def getAllImageFiles(folderPath):
        return [f for f in os.listdir(folderPath) if os.path.isfile(os.path.join(folderPath, f))]

    def uploadFile(folder, path, user):
        """
        Providing this works around a limitation in phantom that makes us
        unable to upload binary files, or at least ones that contain certain
        byte values. The path parameter should be provided relative to the
        root directory of the repository.
        """
        name = os.path.basename(path)
        # folder = Folder().load(folderId, force=True)

        upload = Upload().createUpload(
            user=user, name=name, parentType='folder',
            parent=folder, size=os.path.getsize(path))

        with open(path, 'rb') as fd:
            file = Upload().handleChunk(upload, fd)

        return file

    def createGirderFolder(collectionId, folderName, user):
        collection = Collection().load(collectionId, force=True)
        newFolder = Folder().createFolder(collection, folderName, parentType='collection', creator=user)

    currentToken = Token().load(args.token, force=True, objectId=False)
    user = User().load(currentToken['userId'], force=True)
    try:
        folder = createGirderFolder(args.collection, args.foldername, user)
    except ValidationException:
        folder = [f for f in Folder().childFolders(parent=Collection().load(args.collection, force=True), parentType='collection', user=user) if f['lowerName'] == args.foldername][0]
    allItemNames = [i['lowerName'] for i in Folder().childItems(folder=folder)]
    # only upload new images
    allNewImageNames = [f for f in getAllImageFiles(folderPath=args.datadir) if f not in allItemNames]
    for filename in allNewImageNames:
        uploadFile(
            folder=folder,
            path=os.path.join(args.datadir, filename),
            user=user,
        )
elif args.operation == 'get_from_recap':
    apiurl = 'https://redcap.vanderbilt.edu/api/'
    fields_records = {
        'token': args.redcaptoken,
        'content': 'record',
        'format': 'json',
        'type': 'flat',
    }

    req_records = requests.post(apiurl, data=fields_records)
    records = {}
    for r in json.loads(req_records.text):
        if r['record_id'] not in records:
            records[r['record_id']] = r

    fields_file_base = {
        'token': args.redcaptoken,
        'content': 'file',
        'action': 'export',
    }
    file_fields_flash = [
        'face_f',
        'trunk_ant_f',
        'trunk_post_f',
        'up_arm_ant_left_f',
        'up_arm_ant_right_f',
        'up_arm_post_left_f',
        'up_arm_post_right_f',
        'forearm_dors_left_f',
        'forearm_dors_right_f',
        'forearm_vol_left_f',
        'forearm_vol_right_f',
        'thigh_ant_left_f',
        'thigh_ant_right_f',
        'thigh_post_left_f',
        'thigh_post_right_f',
        'shin_left_f',
        'shin_right_f',
        'calf_left_f',
        'calf_right_f',
        'bonus1_f',
        'bonus2_f',
        'bonus3_f',
        'bonus4_f',
        'bonus5_f',
    ]
    file_fields_noflash = [
        'face_nf',
        'trunk_ant_nf',
        'trunk_post_nf',
        'up_arm_ant_left_nf',
        'up_arm_ant_right_nf',
        'up_arm_post_left_nf',
        'up_arm_post_right_nf',
        'forearm_dors_left_nf',
        'forearm_dors_right_nf',
        'forearm_vol_left_nf',
        'forearm_vol_right_nf',
        'thigh_ant_left_nf',
        'thigh_ant_right_nf',
        'thigh_post_left_nf',
        'thigh_post_right_nf',
        'shin_left_nf',
        'shin_right_nf',
        'calf_left_nf',
        'calf_right_nf',
        'bonus1_nf',
        'bonus2_nf',
        'bonus3_nf',
        'bonus4_nf',
        'bonus5_nf',
    ]
    file_fields_annotator = [
        'face_nf1',
        'trunk_ant_nf1',
        'trunk_post_nf1',
        'up_arm_ant_left_nf1',
        'up_arm_ant_right_nf1',
        'up_arm_post_left_nf1',
        'up_arm_post_right_nf1',
        'forearm_dors_left_nf1',
        'forearm_dors_right_nf1',
        'forearm_vol_left_nf1',
        'forearm_vol_right_nf1',
        'thigh_ant_left_nf1',
        'thigh_ant_right_nf1',
        'thigh_post_left_nf1',
        'thigh_post_right_nf1',
        'shin_left_nf1',
        'shin_right_nf1',
        'calf_left_nf1',
        'calf_right_nf1',
        'bonus1_nf1',
        'bonus2_nf1',
        'bonus3_nf1',
        'bonus4_nf1',
        'bonus5_nf1',
    ]

    filename_regex = r'name="(.*)"'
    for record in records.keys():
        try:
            os.mkdir(os.path.join(args.datadir, record))
        except OSError:
            pass  # if the directory exists, just add to it
    import pdb; pdb.set_trace()
    fields_all = [merge_dicts(fields_file_base, {'record': record_id, 'field': filename}) for filename in file_fields_annotator for record_id in records.keys()]
    for fields in fields_all:
        req = requests.post(apiurl, data=fields)
        filename_original = re.findall(filename_regex, req.headers['Content-Type'])
        if filename_original:
            filename_output = '-'.join([fields['record'], fields['field'], filename_original[0]])
            f = open(os.path.join(args.datadir, fields['record'], filename_output), 'wb')
            f.write(req.content)
            f.close()

