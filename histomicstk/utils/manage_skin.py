import os


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
API_URL_REDCAP = 'https://redcap.vanderbilt.edu/api/'
LATEST_ANNOTATION_QUERY_STRING = 'annotation?limit=1&sort=created&sortdir=-1'
SKIN_APP_IMAGE_BASE_URL = 'histomicstk#?image='
LAST_REDCAP_PULL_KEY = 'histomicstk.last_redcap_pull'
NATIENS_ID_KEY_ORDER = ['natiens_id', 'natiens_id2', 'pilot_id2', 'pilot_id']

PROCESS_OP = 'process'
EXPORT_OP = 'export'
EXPORT_NATIENS_OP = 'export_natiens'
STATUS_OP = 'status'
PROCESS_BASELINE_OP = 'process_baseline'
PROCESS_NATIENS_OP = 'process_natiens'
INGEST_FOLDER_OP = 'ingest_folder'
GET_FROM_REDCAP_OP = 'get_from_redcap'
SEND_TO_REDCAP_OP = 'send_to_redcap'
RENDER_ANNOTATIONS_OP = 'render_annotations'
POLL_ANNOTATIONS_NATIENS_OP = 'poll_annotations_natiens'

FILE_FIELDS_VECTRA = {
    'face_f': '02',
    'trunk_ant_f': '04',
    'trunk_post_f': '26',
    'up_arm_ant_left_f': '06',
    'up_arm_ant_right_f': '08',
    'up_arm_post_left_f': '28',
    'up_arm_post_right_f': '30',
    'forearm_dors_left_f': '10',
    'forearm_dors_right_f': '12',
    'forearm_vol_left_f': '14',
    'forearm_vol_right_f': '16',
    'thigh_ant_left_f': '18',
    'thigh_ant_right_f': '20',
    'thigh_post_left_f': '',
    'thigh_post_right_f': '',
    'shin_left_f': '22',
    'shin_right_f': '24',
    'calf_left_f': '',
    'calf_right_f': '',
    'bonus1_f': '',
    'bonus2_f': '',
    'bonus3_f': '',
    'bonus4_f': '',
    'bonus5_f': '',
    'face_nf': '01',
    'trunk_ant_nf': '03',
    'trunk_post_nf': '25',
    'up_arm_ant_left_nf': '05',
    'up_arm_ant_right_nf': '07',
    'up_arm_post_left_nf': '27',
    'up_arm_post_right_nf': '29',
    'forearm_dors_left_nf': '09',
    'forearm_dors_right_nf': '11',
    'forearm_vol_left_nf': '13',
    'forearm_vol_right_nf': '15',
    'thigh_ant_left_nf': '17',
    'thigh_ant_right_nf': '19',
    'thigh_post_left_nf': '',
    'thigh_post_right_nf': '',
    'shin_left_nf': '21',
    'shin_right_nf': '23',
    'calf_left_nf': '',
    'calf_right_nf': '',
    'bonus1_nf': '',
    'bonus2_nf': '',
    'bonus3_nf': '',
    'bonus4_nf': '',
    'bonus5_nf': '',
    'face_nf1': '',
    'trunk_ant_nf1': '',
    'trunk_post_nf1': '',
    'up_arm_ant_left_nf1': '',
    'up_arm_ant_right_nf1': '',
    'up_arm_post_left_nf1': '',
    'up_arm_post_right_nf1': '',
    'forearm_dors_left_nf1': '',
    'forearm_dors_right_nf1': '',
    'forearm_vol_left_nf1': '',
    'forearm_vol_right_nf1': '',
    'thigh_ant_left_nf1': '',
    'thigh_ant_right_nf1': '',
    'thigh_post_left_nf1': '',
    'thigh_post_right_nf1': '',
    'shin_left_nf1': '',
    'shin_right_nf1': '',
    'calf_left_nf1': '',
    'calf_right_nf1': '',
    'bonus1_nf1': '',
    'bonus2_nf1': '',
    'bonus3_nf1': '',
    'bonus4_nf1': '',
    'bonus5_nf1': '',
}
VECTRA_FILE_FIELDS = dict([(v, k) for k, v in FILE_FIELDS_VECTRA.items()])

def meta_annotator_only(meta, annotator):
    for m in meta:
        if annotator in m:
            return m


# want to output dict without the leading unicode u for annotations
# class unicode(unicode):
#     def __repr__(self):
#         return __builtins__.unicode.__repr__(self).lstrip("u")


def merge_dicts(x, y):
    z = x.copy()   # start with keys and values of x
    z.update(y)    # modifies z with keys and values of y
    return z


def get_all_files(folderPath):
    return [f for f in os.listdir(folderPath) if os.path.isfile(os.path.join(folderPath, f))]


def get_all_folders(folderPath):
    return [f for f in os.listdir(folderPath) if os.path.isdir(os.path.join(folderPath, f))]


def make_dir_if_not_exists(path):
    try:
        return os.mkdir(path)
    except OSError:
        return False


def parse_filename(filename):
    name_constituents = filename.split('_')
    pilot_id = None
    site_id = None
    if len(name_constituents) == 3:
        pilot_id, imaging_session, imaging_device_and_vectra = name_constituents
    elif len(name_constituents) == 4:
        _, site_id, imaging_session, imaging_device_and_vectra = name_constituents
    imaging_device_and_vectra = os.path.splitext(imaging_device_and_vectra)[0]
    return pilot_id, site_id, imaging_session, imaging_device_and_vectra


if __name__ == '__main__':
    import argparse
    import datetime
    import pytz
    import urllib
    import requests
    import json
    import sys
    import glob
    import re
    import tarfile
    import time
    import inspect
    from dateutil import parser

    from girder.models.setting import Setting
    from girder.models.upload import Upload
    from girder.api.v1.item import Folder
    from girder.models.token import Token
    from girder.models.user import User
    from girder.models.item import Item
    from girder.models.collection import Collection
    from girder.exceptions import ValidationException
    from girder.utility import setting_utilities, JsonEncoder

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
    argparser.add_argument('-o', '--operation', type=str, default=[], nargs='+',
                           choices=[PROCESS_OP, EXPORT_OP, EXPORT_NATIENS_OP, STATUS_OP, PROCESS_BASELINE_OP, PROCESS_NATIENS_OP,
                                    INGEST_FOLDER_OP, GET_FROM_REDCAP_OP, SEND_TO_REDCAP_OP, RENDER_ANNOTATIONS_OP,
                                    POLL_ANNOTATIONS_NATIENS_OP],
                           help='What to do with images')
    argparser.add_argument('-s', '--startdate', type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'), default=None,
                           help='date before which no annotations will be returned (inclusive)')
    argparser.add_argument('-e', '--enddate', type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'), default=None,
                           help='date after which no annotations will be returned (inclusive)')
    argparser.add_argument('-d', '--datadir', type=str, default='/opt/histomicstk_data',
                           help='folder in which images will be temporarily stored before ingestion')
    argparser.add_argument('-z', '--zip', action='store_true', help='whether to tarball gunzip the json files')
    argparser.add_argument('-p', '--phi', action='store_true', help='Ignore PHI settings and export all images')
    argparser.add_argument('-i', '--ignoreexisting', action='store_true', help='Ignore whether a file exists or not')
    argparser.add_argument('-x', '--annotator', type=str, nargs='+', default=[], help='Users to export json for.')
    args = argparser.parse_args()

    item_headers = {'Girder-Token': args.token, 'Accept': 'application/json'}
    largeimage_headers = {'Content-Type': 'application/x-www-form-urlencoded',
                         'Girder-Token': args.token, 'Accept': 'application/json'}
    access_headers = {'Content-Type': 'application/json',
                      'Girder-Token': args.token, 'Accept': 'application/json'}
    fields_records_annotations = {
        'token': args.redcaptoken,
        'content': 'record',
        'format': 'json',
        'type': 'flat',
        'forms': 'annotation',
    }
    metadata_data = {
        'token': args.redcaptoken,
        'content': 'metadata',
        'format': 'json',
        'returnFormat': 'json',
        'fields': 'annotator',
        'forms': 'annotation',
    }
    annotation_instrument_data = {
        'token': args.redcaptoken,
        'content': 'record',
        'action': 'import',
        'format': 'json',
        'type': 'eav',
        'overwriteBehavior': 'overwrite',
        'forceAutoNumber': 'false',
        'data': '{"record":"%s","redcap_repeat_instrument":"annotation","redcap_repeat_instance":%s,"field_name":"%s","value":"%s"}',
        'returnContent': 'count',
        'returnFormat': 'json'
    }


def upload_file(folder, path, user):
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


def create_girder_folder(collection, folderName, user, parentType='collection'):
    return Folder().createFolder(collection, folderName, parentType=parentType, creator=user, reuseExisting=True)


def get_or_create_girder_folder(parent, folderName, user, parentType='collection'):
    try:
        folder = create_girder_folder(parent, folderName, user, parentType)
    except ValidationException:
        folder = [f for f in Folder().childFolders(parent=parent, parentType=parentType, user=user) if f['lowerName'] == folderName]
        if folder:
            folder = folder[0]
        else:
            folder = Folder().load(args.folder, force=True)
    return folder


def get_from_redcap(user):
    fields_records_download = {
        'token': args.redcaptoken,
        'content': 'record',
        'format': 'json',
        'type': 'flat',
        'forms': 'skinio_photography',
    }
    for i, pilot_id in enumerate(pilot_ids):
        fields_records_download['record[{i}]'.format(i=i)] = pilot_id

    req_records = requests.post(API_URL_REDCAP, data=fields_records_download)
    records = {}

    fields_file_base = {
        'token': args.redcaptoken,
        'content': 'file',
        'action': 'export',
    }
    file_fields_flash = [
        'trunk_ant_f',
        'trunk_post_f',
    ]
    file_fields_flash_all = [
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
        'trunk_ant_nf',
        'trunk_post_nf',
    ]
    file_fields_noflash_all = [
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
        'trunk_ant_nf1',
        'trunk_post_nf1',
    ]
    file_fields_annotator_all = [
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
    file_fields_photo = file_fields_flash + file_fields_noflash
    annotators = None

    filename_regex = r'name="(.*)"'
    phi_free_field_names = {}

    for r in json.loads(req_records.text):
        natiens_id = get_natiens_id(r)
        if natiens_id:  # only extract patients which have a pilot ID
            record_id = r['record_id']
            session_id = r['redcap_repeat_instance'] 
            patient_folder_name = record_id + '_' + natiens_id
            try:
                photography_date = '_' + str(datetime.datetime.strptime(r['date_photography'], '%Y-%m-%d').strftime('%y%m%d'))
            except ValueError:
                photography_date = ''
            session_folder_name = str(r['redcap_repeat_instance']) + photography_date
            make_dir_if_not_exists(os.path.join(args.datadir))
            make_dir_if_not_exists(os.path.join(args.datadir, args.foldername))
            make_dir_if_not_exists(os.path.join(args.datadir, args.foldername, natiens_id))
            make_dir_if_not_exists(os.path.join(args.datadir, args.foldername, natiens_id, str(session_folder_name)))
            # If we've already pulled the files, don't do it again
            exists = make_dir_if_not_exists(os.path.join(args.datadir, args.foldername, natiens_id, str(session_folder_name), 'imgsrc'))
            if args.phi:  # include all fields, regardless of PHI
                fields_keep = file_fields_photo
            else:
                if file_fields_flash != file_fields_flash_all or file_fields_noflash != file_fields_noflash_all:
                    field_range = [file_fields_flash_all.index(f) for f in file_fields_flash]
                else:
                    field_range = range(0, 24)
                phi_checks = map(lambda x: 'phi_check' + str(x) + '___0', field_range)
                
                try:
                    fields_keep = [file_fields_flash_all[f] for i, f in enumerate(field_range) if not int(r[phi_checks[i]])] + [file_fields_noflash_all[f] for i, f in enumerate(field_range) if not int(r[phi_checks[i]])]
                except ValueError, AttributeError:
                    pass
            download_files = [merge_dicts(fields_file_base, {'record': record_id, 'repeat_instance': session_id, 'field': field_file}) for field_file in fields_keep]
            for field in download_files:
                # Currently only pulling images which were captured on randomization day and day of reep
                if int(r['day_0___0']) or int(r['day_reepithelization___0']) and (not exists or args.ignoreexisting):
                    req = requests.post(API_URL_REDCAP, data=field)
                    # Project ID is different for pilot projects than NATIENS
                    pilot_field_name = get_natiens_id_field_name(r)
                    project_id = r[pilot_field_name] if 'ilot' in pilot_field_name else 'NAT' + '_' + r['site']
                    filename_original = re.findall(filename_regex, req.headers['Content-Type'])
                    if filename_original:
                        suffix = os.path.splitext(r[field['field']])[1]
                        file_base_name = '_'.join([project_id, r['imaging_session'].rjust(2, '0'), r['imaging_device___1'] + FILE_FIELDS_VECTRA[field['field']]])
                        filename_output = file_base_name + suffix 
                        print(os.path.join(args.datadir, args.foldername, natiens_id, str(session_folder_name), 'imgsrc', filename_output))
                        f = open(os.path.join(args.datadir, args.foldername, natiens_id, str(session_folder_name), 'imgsrc', filename_output), 'wb')
                        f.write(req.content)
                        f.close()


def get_status(items):
    completed_annotations_cts = {}
    completed_annotations = {}
    for item in items:
        annotations_access_url = args.url + MULTIPLE_ANNOTATIONS + str(item['_id'])
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


def get_key_in_order(dict, keys):
    return next((key for key in keys if key in dict), None)


def get_value_in_order(dict, keys):
    return next((dict[key] for key in keys if key in dict), None)


def get_natiens_id_field_name(dict):
    return get_key_in_order(dict, NATIENS_ID_KEY_ORDER)


def get_natiens_id(dict):
    return get_value_in_order(dict, NATIENS_ID_KEY_ORDER)


def poll_annotations_natiens(user):
    # Record and update state of last REDCap pull
    # Duplicating this validator code here because I can't import server because plugins aren't importing
    @setting_utilities.validator(LAST_REDCAP_PULL_KEY)
    def validateHistomicsTKLastRedcapPull(doc):
        try:
            datetime.datetime.strptime(doc['value'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValidationException('Last REDCap Pull must be a date time.')

    new_last_redcap_pull = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    last_redcap_pull = datetime.datetime.strptime(Setting().get(LAST_REDCAP_PULL_KEY), '%Y-%m-%d %H:%M:%S')

    # Gather record names from folder names
    folder_natiens = Folder().load(args.folder, force=True)
    fields_records = {
        'token': args.redcaptoken,
        'content': 'record',
        'format': 'json',
        'type': 'flat',
        'forms': 'annotation',
        'dateRangeBegin': last_redcap_pull,
    }
    req_records = requests.post(API_URL_REDCAP, data=fields_records)
    # pilot_ids = {}

    # for r in json.loads(req_records.text):
    #     pilot_ids.append(r['pilot_id2']
    req_records = json.loads(req_records.text)
    # In some REDCap databases, natiens_id is called pilot_id2
    if req_records:
        natiens_id_field = get_natiens_id_field_name(req_records[0])
        natiens_ids = set(r[natiens_id_field] for r in req_records if r[natiens_id_field]) or set()
    else:
        natiens_ids = set()
    return natiens_ids, new_last_redcap_pull


def set_image_metadata(all_new_image_names, session_folder, user, record_id, session_id):
    items = []
    for filepath in all_new_image_names:
        item_file = upload_file(
            folder=session_folder,
            path=filepath,
            user=user,
        )
        # set the record_id and session_id in metadata for access in ingestion
        item = Item().load(item_file['itemId'], user=user)
        Item().setMetadata(item, {'record_id': record_id, 'session_id': session_id})
        if item:
            items.append(item)
    return items


def ingest_folder_sessions(record_folder):
    record_id = record_folder['name']
    items = []
    for session_id in os.listdir(os.path.join(args.datadir, args.foldername, record_id)):
        session_folder = get_or_create_girder_folder(record_folder, session_id, user, 'folder')
        all_item_names = [i['name'] for i in Folder().childItems(folder=session_folder)]
        # only upload new images
        all_new_image_names = [f for f in glob.glob(os.path.join(args.datadir, args.foldername, record_id, session_id, 'imgsrc', '*')) if f not in all_item_names]
        items = items + set_image_metadata(all_new_image_names, session_folder, user, record_id, session_id)
    return items


def ingest_folder(user, pilot_id=None):
    collection = Collection().load(args.collection, force=True)
    parent_folder = get_or_create_girder_folder(collection, args.foldername, user)
    # Need to know what REDCap form to send this back to, so store the redcap token
    Folder().setMetadata(parent_folder, {'redcaptoken': args.redcaptoken})
    items = []
    if pilot_id:
        folder_names = [os.path.join(args.datadir, args.foldername, pilot_id)]
    else:
        folder_names = os.listdir(os.path.join(args.datadir, args.foldername))
    for record_path in folder_names:
        record_folder = get_or_create_girder_folder(parent_folder, os.path.basename(record_path), user, 'folder')
        items = items + ingest_folder_sessions(record_folder)
    return items


def process_access_helper():
    group_worker_or_baseline = args.workergroup if 'process' in args.operation else args.baselinegroup
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

    if PROCESS_BASELINE_OP in args.operation:
        access_dict['groups'].append(
            {
              "description": "Demarcating cGVHD photos for potential inclusion in study.",
              "flags": [],
              "id": args.baselinegroup,
              "level": 1,
              "name": "Baseline"
            }
        )
    return group_by_name, annotations_dict, access_dict


def process_natiens_create_annotation_layers_update_links(items):
    from nameparser import HumanName
    group_url = args.url + GROUP_API_URL + '/' + args.workergroup + '/member?ignore' + ITEM_QUERY_STRING
    group = requests.get(group_url, headers=item_headers)
    group = json.loads(group.content)
    group_by_name = {g['login']: g for g in group}
    # For creating all onnotation layers
    annotations_dict = [{'name': u['login'], 'description': u['firstName'] + ' ' + u['lastName']} for u in group]

    req_annotations = requests.post(API_URL_REDCAP, data=fields_records_annotations)
    req_metadata = requests.post(API_URL_REDCAP, data=metadata_data)
    annotator_names = []
    for m in json.loads(req_metadata.text):
        if m['field_name'] == 'annotator':
            annotators =  {annotator.split(', ')[0]: annotator.split(', ')[1] for annotator in m['select_choices_or_calculations'].split(' | ')}
    for a in json.loads(req_annotations.text):
        if a['annotator']:
            annotator = annotators[a['annotator']]
            from nameparser import HumanName
            annotator_names.append(HumanName(annotator))
    # TODO: Can't find a method within User() to filter to a specific user, so just grabbing all and manually filtering
    annotator_user = [u for u in User().list() if u['firstName'] in [n['first'] for n in annotator_names] and u['lastName'] in [n['last'] for n in annotator_names]]

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
          "description": "Allow users to see the entirety of the annotation tool.",
          "flags": [],
          "id": args.admingroup,
          "level": 2,
          "name": "NATIENS leads"
        }
      ], "users": [
          {
            "description": "",
            "flags": [],
            "id": str(u['_id']),
            "level": 1,
            "name": annotator
          } for u in annotator_user
      ] + [admin_user]
    }
    # Update links to images
    for item in items:
        annotation_instrument_data['data'] = '[{"record":"%s","redcap_repeat_instrument":"annotation","redcap_repeat_instance":"%s","field_name":"%s","value":"%s"}]'
        pilot_id, site_id, imaging_session, imaging_device_and_vectra = parse_filename(item['name'])
        image_link = args.url + SKIN_APP_IMAGE_BASE_URL + str(item['_id'])
        folder_name = Folder().load(item['folderId'], force=True)
        redcap_repeat_instance = folder_name['name'].split('_')[0]
        link_field = 'link_' + remove_all_except_last(VECTRA_FILE_FIELDS[imaging_device_and_vectra[1:]], '_')
        annotation_instrument_data['data'] = annotation_instrument_data['data'] % (
            item['meta']['record_id'],
            redcap_repeat_instance,
            link_field,
            image_link,
        )
        requests.post(API_URL_REDCAP, data=annotation_instrument_data)
    return group_by_name, annotations_dict, access_dict


def process_baseline_helper(access_dict):
    access_dict['groups'].append(
        {
          "description": "Demarcating cGVHD photos for potential inclusion in study.",
          "flags": [],
          "id": args.baselinegroup,
          "level": 1,
          "name": "Baseline"
        }
    )


def process_generate_thumbnails_and_permissions(items, group_by_name, annotations_dict, access_dict):
    access_url = args.url + ACCESS_API_URL + '/' + args.folder + '/access?access=' + urllib.quote_plus(json.dumps(access_dict)) + ACCESS_QUERY_STRING
    access = requests.put(access_url, headers=item_headers)

    for item in items:
        image_url = args.url + ITEM_API_URL + '/' + str(item['_id']) + '/files' + '?ignore' + ITEM_QUERY_STRING
        image_headers = {'Girder-Token': args.token, 'Accept': 'application/json'}
        image = requests.get(image_url, headers=image_headers)
        image = json.loads(image.content)
        file_id = image[0]['_id']

        largeimage_url = args.url + ITEM_API_URL + '/' + str(item['_id']) + '/tiles?fileId=' + file_id + LARGEIMAGE_QUERY_STRING
        requests.post(largeimage_url, headers=largeimage_headers)

        annotations_url = args.url + ANNOTATION_API_URL + '?itemId=' + str(item['_id']) + ITEM_QUERY_STRING
        annotations = requests.get(annotations_url, headers=item_headers)
        annotations = json.loads(annotations.content)
        # [requests.delete(args.url + ANNOTATION_API_URL + '/' + a['_id'], headers=item_headers) for a in annotations]
        annotations_details = {a['_id']: a['annotation'] for a in annotations}
        annotations_access_url = args.url + MULTIPLE_ANNOTATIONS + str(item['_id'])
        requests.post(annotations_access_url, headers=item_headers, data=json.dumps([a for a in annotations_dict if a not in annotations_details.values()]))
        annotation_access_update_url = args.url + ANNOTATION
        for aid, annotation in annotations_details.iteritems():
            try:
                a = group_by_name[annotation['name']]
                # if a['firstName'] not in ['Xiaoqi']:
                #     continue
                access_dict["users"] = [
                {
                    "flags": [],
                    "id": a['_id'],
                    "level": 2,
                    "login": a['login'],
                    "name": a['firstName'] + ' ' + a['lastName']
                }]
                # if a['login'] == 'kelseyparks2022':
                #     import pdb; pdb.set_trace()
                requests.put(annotation_access_update_url + aid + '/access?access=' + urllib.quote_plus(json.dumps(access_dict)) + '&public=false', headers=access_headers)
            except KeyError:
                print('No user {0} in group'.format(annotation['name']))


def export(items, args):
    folder = Folder().load(args.folder, force=True)
    try:
        os.mkdir(os.path.join(args.datadir, args.foldername))
    except OSError:
        pass  # if the directory exists, just add to it
    except NameError:
        pass  # args not passed in, this should be fine

    localtz = pytz.timezone("America/Chicago")
    # restrict by start and end dates
    startdate = localtz.localize(args.startdate) if args.startdate else None
    enddate = localtz.localize(args.enddate) + datetime.timedelta(1) if args.enddate else None
    if 'message' in items and 'AttributeError' in items['message']:
        raise ValueError('Likely an incorrect folderId was specified')
    for item in items:
        try:
            updated = parser.parse(item['updated'])
        except TypeError:
            updated = item['updated']
        start_range = startdate and startdate <= updated
        end_range = enddate and enddate >= updated
        if start_range and end_range or start_range and not enddate or end_range and not startdate or not startdate and not enddate:
            annotations_access_url = args.url + MULTIPLE_ANNOTATIONS + str(item['_id'])
            item_headers = {'Girder-Token': args.token, 'Accept': 'application/json'}
            annotations_blob = requests.get(annotations_access_url, headers=item_headers)
            annotations = json.loads(annotations_blob.content)
            annotations_within_range = []
            for annotation in annotations:
                if annotation['updated']:
                    try:
                        updated_anno = parser.parse(annotation['updated'])
                    except TypeError:
                        updated_anno = annotation['updated']
                else:
                    try:
                        updated_anno = parser.parse(annotation['created'])
                    except TypeError:
                        updated_anno = annotation['created']
                # restrict annotations by date and by user if necessary, not required
                start_range_anno = startdate and startdate <= updated_anno
                end_range_anno = enddate and enddate >= updated_anno
                if start_range_anno and end_range_anno or start_range_anno and not enddate or end_range_anno and not startdate or not startdate and not enddate and (not args.annotator or annotation['annotation']['name'] in args.annotator):
                    annotations_within_range.append(annotation)
            meta_annotations_only = dict()
            if annotations_within_range and item and 'meta' in item:
                for m in item['meta']:
                    for annotator in annotations_within_range:
                        if annotator['annotation']['name'] in m:
                             meta_annotations_only[m] = item['meta'][m]
                item['meta'] = meta_annotations_only
                if EXPORT_NATIENS_OP in args.operation:
                    pilot_id, site_id, imaging_session, imaging_device_and_vectra = parse_filename(item['name'])
                    # Father session_id and record_id from folder structure since it's not contained in the file name
                    folder_child = Folder().load(item['folderId'], force=True)
                    folder_name = folder_child['name']
                    session_id = folder_name.split('_')[0]
                    parent_folder = Folder().load(folder['parentId'], force=True)
                    parent_folder_name = parent_folder['name']
                    record_id = parent_folder['name'].split('_')[0]

                    imgsrc_files = os.path.join(args.datadir, args.foldername, parent_folder_name, folder_name, 'imgsrc')
                    json_files = os.path.join(args.datadir, args.foldername, parent_folder_name, folder_name, 'json')
                    mask_files = os.path.join(args.datadir, args.foldername, record_id, parent_folder_name, 'masks')
                    annotated_files = imgsrc_files = os.path.join(args.datadir, args.foldername, parent_folder_name, folder_name, 'annotated')
                    [make_dir_if_not_exists(f) for f in [imgsrc_files, json_files, mask_files, annotated_files]]
                    # return os.path.join(args.datadir, 'natiens_pilot', parent_folder['name'], folder['name'], 'json', item['name'] + '.json')
                    with open(os.path.join(args.datadir, 'natiens_pilot', parent_folder['name'], folder['name'], 'json', item['name'] + '.json'), 'wb') as f:
                        item['annotations'] = [anno for anno in annotations_within_range]
                        f.write(json.dumps(item, cls=JsonEncoder))
                else:
                    try:
                        os.mkdir(os.path.join(args.datadir, args.foldername, 'json'))
                    except OSError:
                        pass  # if the directory exists, just add to it
                    with open(os.path.join(args.datadir, args.foldername, 'json', item['name'] + '.json'), 'wb') as f:
                        item['annotations'] = [anno for anno in annotations_within_range]
                        f.write(json.dumps(item, cls=JsonEncoder))
    if startdate and enddate:
        range_str = '-' + str(startdate.date()) + '--' + str(enddate.date())
    elif startdate:
        range_str = '-before-' + str(startdate.date())
    elif enddate:
        range_str = '-after-' + str(enddate.date())
    else:
        range_str = ''
    if args.zip:
        tar_obj = tarfile.open(os.path.join(args.datadir, args.foldername, folder['name'] + '-' + str(item['folderId']) + range_str + '.tar.gz'), 'w:gz')
        json_files = glob.glob(os.path.join(args.datadir, args.foldername, 'json', '*.json'))
        [tar_obj.add(json_file) for json_file in json_files]
        tar_obj.close()
        [os.remove(json_file) for json_file in json_files]


def render_annotations():
    # json_files = get_all_files(os.path.join(args.datadir, args.foldername, 'json'))
    for record_id in os.listdir(os.path.join(args.datadir, args.foldername)):
        for session_id in os.listdir(os.path.join(args.datadir, args.foldername, record_id)):
            imgsrc_files = os.path.join(args.datadir, args.foldername, record_id, session_id, 'imgsrc')
            json_files = os.path.join(args.datadir, args.foldername, record_id, session_id, 'json')
            mask_files = os.path.join(args.datadir, args.foldername, record_id, session_id, 'masks')
            annotated_files = os.path.join(args.datadir, args.foldername, record_id, session_id, 'annotated')
            [make_dir_if_not_exists(f) for f in [imgsrc_files, json_files, mask_files, annotated_files]]
            cmd = 'JSON_FOLDER={json}/ BASELINE_FOLDER={imgsrc}/ ANNOTATED_IMAGES_FOLDER={annotated}/ MASKS_FOLDER={masks}/ /opt/histomicstk/HistomicsTK/histomicstk/utils/run_step1_main_read_json_mask.sh /home/ubuntu/matlab/r2021b/mcr'.format(imgsrc=imgsrc_files, json=json_files, masks=mask_files, annotated=annotated_files)
            print(cmd)
            os.system(cmd)


def send_to_redcap():
    fields_records_upload = {
        'token': args.redcaptoken,
        'content': 'file',
        'action': 'import',
        'returnFormat': 'json',
    }
    try:
        annotated_files
    except NameError:
        for record_id in os.listdir(os.path.join(args.datadir, args.foldername)):
            for session_id in os.listdir(os.path.join(args.datadir, args.foldername, record_id)):
                annotated_files = os.path.join(args.datadir, args.foldername, record_id, session_id, 'annotated')
                for filename in annotated_files:
                    record_id_errata, session_id, field_name, errata = filename.split('-')
                    record_id = re.findall(r'\d+$', record_id_errata)[0]
                    username = errata.split('_')[-2]
                    fields_records_upload['record'] = record_id
                    fields_records_upload['data'] = record_id
                    req_records = requests.post(API_URL_REDCAP, data=fields_records_upload)
    # os.environ.get('GIRDER_TOKEN', 'DID_NOT_SUPPLY_GIRDER_TOKEN')


def get_items_from_folder(folder=args.folder):
    pilot_ids = set()
    items = []
    user = None
    if set(args.operation) & set([
           PROCESS_OP, PROCESS_BASELINE_OP, PROCESS_NATIENS_OP, EXPORT_OP, EXPORT_NATIENS_OP, STATUS_OP, POLL_ANNOTATIONS_NATIENS_OP
       ]):
        item_url = args.url + ITEM_API_URL + '?folderId=' + folder + ITEM_QUERY_STRING
        items = requests.get(item_url, headers=item_headers)
        items = json.loads(items.content)
        if 'message' in items:
            sys.stderr.write(items['message'] + "\n")
    if set(args.operation) & set([INGEST_FOLDER_OP, GET_FROM_REDCAP_OP, SEND_TO_REDCAP_OP, POLL_ANNOTATIONS_NATIENS_OP]):
        current_token = Token().load(args.token, force=True, objectId=False)
        user = User().load(current_token['userId'], force=True)

    return items, user


def remove_all_except_last(string, char):
    last_index = string.rfind(char)
    if last_index == -1:
        return string
    return string[:last_index].replace(char, '') + char + string[last_index+1:]


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


if __name__ == "__main__":
    items, user = get_items_from_folder()
    # Get status of annotation layers from SkinApp
    if STATUS_OP in args.operation:
        get_status(items)
    # Check if new annotations are available in NATIENS to process
    if POLL_ANNOTATIONS_NATIENS_OP in args.operation:
        pilot_ids, new_last_redcap_pull = poll_annotations_natiens(user)
        if pilot_ids:
            get_from_redcap(user)
            Setting().set(LAST_REDCAP_PULL_KEY, new_last_redcap_pull)
            for pilot_id in pilot_ids:
                # grabbing new items from ingested folder
                items = ingest_folder(user, pilot_id)
                group_by_name, annotations_dict, access_dict = process_natiens_create_annotation_layers_update_links(items)
                process_generate_thumbnails_and_permissions(items, group_by_name, annotations_dict, access_dict)
    # Download files from REDCap into an OS folder
    if GET_FROM_REDCAP_OP in args.operation:
        get_from_redcap(user)
    # Ingest OS folder into Girder collection folder
    if INGEST_FOLDER_OP in args.operation:
        ingest_folder(user)
    # creates annotation layers
    if PROCESS_OP in args.operation or PROCESS_BASELINE_OP in args.operation:
        group_by_name, annotations_dict, access_dict = process_access_helper()
    # Permissions for annotation layers is different for NATIENS
    if PROCESS_NATIENS_OP in args.operation:
        group_by_name, annotations_dict, access_dict = process_natiens_create_annotation_layers_update_links(items)
    if PROCESS_BASELINE_OP in args.operation:
        process_baseline_helper(access_dict)
    # if any kind of processing needs to be done, set permissions
    if any(['process' in op for op in args.operation]):
        process_generate_thumbnails_and_permissions(items, group_by_name, annotations_dict, access_dict)
    # Exports geoJSON-like files if any kind of export to be done
    if any(['export' in op for op in args.operation]):
        export(items, args)
    # Output annotated PNG files using MATLAB from json annotation and input file
    if RENDER_ANNOTATIONS_OP in args.operation:
        render_annotations()
    # Send the outputted annotated PNGs to REDCap
    if SEND_TO_REDCAP_OP in args.operation:
        send_to_redcap()
