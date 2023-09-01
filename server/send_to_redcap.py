from girder.api import access
from girder.api.rest import getCurrentToken, getCurrentUser
from girder.api.v1.item import Folder as FolderResource
from girder.api.v1.item import Item as ItemResource
from girder.api.describe import autoDescribeRoute, Description
from girder.constants import AccessType
from girder.exceptions import RestException
# from girder.models.folder import Folder as FolderModel
from girder.models.item import Item as ItemModel

from dateutil import parser
from PIL import Image
import glob
import json
import os
import pytz
import random
import requests
import tarfile


class SendToRedcapItemResource(ItemResource):
    """Extends the "item" resource to send an image to REDCap."""

    def __init__(self, apiRoot):
        # Don't call the parent (Item) constructor, to avoid redefining routes,
        # but do call the grandparent (Resource) constructor
        super(ItemResource, self).__init__()

        self.resourceName = 'item'
        self._model = ItemModel()
        apiRoot.item.route('POST', (':id', ':redcaptoken', 'send_to_redcap'), self.send_to_redcap)

    def _parse_filename(self, filename):
        name_constituents = filename.split('_')
        pilot_id = None
        site_id = None
        if len(name_constituents) == 3:
            pilot_id, imaging_session, imaging_device_and_vectra = name_constituents
        elif len(name_constituents) == 4:
            _, site_id, imaging_session, imaging_device_and_vectra = name_constituents
        imaging_device_and_vectra = os.path.splitext(imaging_device_and_vectra)[0]
        return pilot_id, site_id, imaging_session, imaging_device_and_vectra

    def _render_annotations(self, item, folder):
        URL = 'https://skin.app.vumc.org/api/v1/'
        # URL = 'https://skin.app.vumc.org/api/v1/'
        MULTIPLE_ANNOTATIONS = 'annotation/item/'
        TOKEN = getCurrentToken()['_id']
        item_id = str(item['_id'])
        item_headers = {'Girder-Token': TOKEN, 'Accept': 'application/json'}
        base_dir = '/opt/histomicstk_data/'
        export_dir = 'natiens_pilot'
        # export_dir = 'export-annotated'
        export_path = os.path.join(base_dir, export_dir)
        try:
            os.mkdir(export_path)
        except OSError:
            pass  # if the directory exists, just add to it

        updated = item['updated']
        localtz = pytz.timezone("America/Chicago")
        annotations_access_url = URL + MULTIPLE_ANNOTATIONS + item_id
        annotations_blob = requests.get(annotations_access_url, headers=item_headers)
        annotations = json.loads(annotations_blob.content)
        meta_annotations_only = dict()
        if annotations and item and 'meta' in item:
            for m in item['meta']:
                for annotator in annotations:
                    if annotator['annotation']['name'] in m:
                         meta_annotations_only[m] = item['meta'][m]
            item['meta'] = meta_annotations_only
            pilot_id, site_id, imaging_session, imaging_device_and_vectra = self._parse_filename(item['name'])
            # Father session_id and record_id from folder structure since it's not contained in the file name
            folder_child = FolderResource().load(str(item['folderId']), force=True)
            folder_name = folder_child['name']
            session_id = folder_name.split('_')[0]
            parent_folder = FolderResource().load(folder['parentId'], force=True)
            parent_folder_name = parent_folder['name']
            record_id = parent_folder['name'].split('_')[0]

            parent_folder = os.path.join(base_dir, export_dir, parent_folder_name)
            item_folder = os.path.join(base_dir, export_dir, parent_folder_name, folder_name)
            imgsrc_files = os.path.join(base_dir, export_dir, parent_folder_name, folder_name, 'imgsrc')
            json_files = os.path.join(base_dir, export_dir, parent_folder_name, folder_name, 'json')
            mask_files = os.path.join(base_dir, export_dir, parent_folder_name, folder_name, 'masks')
            annotated_files = os.path.join(base_dir, export_dir, parent_folder_name, folder_name, 'annotated')
            [self._make_dir_if_not_exists(f) for f in [parent_folder, item_folder, imgsrc_files, json_files, mask_files, annotated_files]]
            # with open(os.path.join(base_dir, export_dir, parent_folder_name, folder_name, 'json', str(item['name']) + '.json'), 'wb') as f:
            #     item['annotations'] = [anno for anno in annotations]
            #     f.write(json.dumps(item, default=str))
            cmd = 'JSON_FOLDER={json}/ BASELINE_FOLDER={imgsrc}/ ANNOTATED_IMAGES_FOLDER={annotated}/ MASKS_FOLDER={masks}/ /opt/histomicstk/HistomicsTK/histomicstk/utils/run_step1_main_read_json_mask.sh /home/ubuntu/matlab/r2021b/mcr'.format(imgsrc=imgsrc_files, json=json_files, masks=mask_files, annotated=annotated_files)
            # print(cmd)
            os.system(cmd)
            (annotated_filename, _) = os.path.splitext(item['name'])
            annotated_extension = '.png'
            current_user = getCurrentUser()
            annotated_path_extenionless = os.path.join(annotated_files, annotated_filename + '_' + current_user['login'])
            # return 1, item
            # return 1, annotated_path_extenionless + annotated_extension
            return record_id, annotated_path_extenionless + annotated_extension
            try:
                annotated_im = Image.open(annotated_path_extenionless + annotated_extension)
                annotated_rgb_im = annotated_im.convert("RGB")  # convert to jpg
                annotated_rgb_im.save(annotated_path_extenionless + '.jpg')
            except IOError:
                raise RestException('Image not found.', 404)
            return record_id, annotated_path_extenionless + '.jpg'
            # tar_obj = tarfile.open(os.path.join(base_dir, export_dir, item_id, item_id + '.tar.gz'), 'w:gz')
            # json_files = glob.glob(os.path.join(base_dir, export_dir, item_id, 'json', '*.json'))
            # [tar_obj.add(json_file) for json_file in json_files]
            # tar_obj.close()
            # [os.remove(json_file) for json_file in json_files]

    def get_redcap_annotation_users(self, redcaptoken):
        data = {
            'token': redcaptoken,
            'content': 'metadata',
            'format': 'json',
            'returnFormat': 'json',
            'fields': 'annotator',
            'forms[0]': 'annotation'
        }
        # req_users = requests.post('https://redcap.vanderbilt.edu/api/', data=data)
        from histomicstk import utils
        req_users = requests.post(utils.manage_skin.API_URL_REDCAP, data=data)
        for u in json.loads(req_users.text):
            # Grab the list from the annotator field
            if u['field_name'] == 'annotator':
                return {a.split(', ')[1]: a.split(', ')[0] for a in u['select_choices_or_calculations'].split(' | ')}

    def _get_instance_number(self, redcaptoken, record, user):
        users = self.get_redcap_annotation_users(redcaptoken)
        if user not in users:
            return None
        user_id = users[user]
        data = {
            'token': redcaptoken,
            'content': 'record',
            'action': 'export',
            'format': 'json',
            'type': 'flat',
            'csvDelimiter': '',
            'records[0]': record,
            'fields[0]': 'record_id',
            'forms[0]': 'annotation',
            'returnFormat': 'json',
            'filterLogic': '[annotator] = ' + user_id,
        }
        # req_anno = requests.post('https://redcap.vanderbilt.edu/api/', data=data)
        from histomicstk import utils
        req_anno = requests.post(utils.manage_skin.API_URL_REDCAP, data=data)
        for a in json.loads(req_anno.text):
            return a

    def _make_dir_if_not_exists(self, path):
        try:
            return os.mkdir(path)
        except OSError:
            return False

    @access.public
    @autoDescribeRoute(
        Description('Send this annotation to REDCap.')
        .modelParam('id', 'The item ID of the annotated image to be uploaded',
                    model='item', destName='item', paramType='query', level=AccessType.READ,
                    required=True)
        .param('redcaptoken', 'The REDCap token to upload this image to..')
        .errorResponse()
        .errorResponse('Item is empty or does not exist', code=404)
    )
    def send_to_redcap(self, item, redcaptoken):
        folder = FolderResource().load(str(item['folderId']), force=True)
        (record_id, annotated_path_jpg) = self._render_annotations(item, folder)
        vectra = item['name'].split('_')[-1][1:3]  # parse filename for vectra
        record_name = item['name'].split('_')[0]  # parse filename for record name
        user = ItemResource().getCurrentUser()
        user_name = user['firstName'] + ' ' + user['lastName']
        # Simulating arguments from manage_skin script
        from histomicstk import utils
        args = type('obj', (object,), {
            'folder': item['folderId'],
            'foldername': folder['name'],
            'startdate': None,
            'enddate': None,
            'annotator': [user['login']],
            'url': 'https://skin.app.vumc.org/api/v1/',
            'operation': 'export_natiens',
            'operation': utils.manage_skin.EXPORT_NATIENS_OP,
            'datadir': '/opt/histomicstk_data',
            'token': 'bR1i41zmW301Vu8vR6DA76bzTHUz3CbT6BisLH5CX4B4Fmy65GwaxuyPkYaLbKBd',  # @TODO: I'm sure this can be pulled
            'zip': True,
        })
        utils.manage_skin.export([item], args)
        instance_number = self._get_instance_number(redcaptoken, record_name, user_name)

        field = utils.manage_skin.VECTRA_FILE_FIELDS[vectra] + '1'  # Annotation fields end with a 1
        fields_records_upload = {
            'token': redcaptoken,
            'content': 'file',
            'action': 'import',
            'returnFormat': 'json',
            'field': field,
            'repeat_instance': instance_number['redcap_repeat_instance'],
        }
        # if 'meta' in item and 'record_id' in item['meta']:
        fields_records_upload['record'] = record_name
        with open(annotated_path_jpg, 'rb') as f:
            # return (annotated_path_jpg, utils.manage_skin.API_URL_REDCAP, fields_records_upload, f)
            req = requests.post(utils.manage_skin.API_URL_REDCAP, data=fields_records_upload, files={'file': f})
            # return fields_records_upload
            return req.text
        # groups = [str(g) for g in user.get('groups', [])]
        # expert_group = '5f0dc574c9f8c18253ae949e'
        # expert_group_natiens = '629ff512234d56ac7568f286'

        #folder = folderModel.load(folder, user=user, level=AccessType.READ)
