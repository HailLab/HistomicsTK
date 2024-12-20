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
import subprocess
import tarfile

from render_annotations import render_annotations


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
        imaging_session = None
        imaging_device_and_vectra = None
        fidelity = 'lo'

        try:
            if len(name_constituents) == 3:
                pilot_id, imaging_session, imaging_device_and_vectra = name_constituents
            elif len(name_constituents) == 4:
                pilot_id, site_id, imaging_session, imaging_device_and_vectra = name_constituents
            elif len(name_constituents) == 5:
                pilot_id, site_id, imaging_session, fidelity, imaging_device_and_vectra = name_constituents
                imaging_session = imaging_session + '_' + fidelity  # @TODO: Not positive if session name should include fidelity
            else:
                return None, None, None, None, None  # Return None for all if parsing fails
        except Exception as e:
            print("Error parsing filename: " + filename + ". Error: " + str(e))

        try:
            imaging_device_and_vectra = os.path.splitext(imaging_device_and_vectra)[0]
        except TypeError as e:
            print("Error parsing imaging_device_and_vectra: " + str(e))
            imaging_device_and_vectra = None

        return pilot_id, site_id, imaging_session, imaging_device_and_vectra, fidelity

    def _render_annotations(self, item, folder):
        # URL = 'http://ec2-54-152-138-170.compute-1.amazonaws.com/api/v1/'
        URL = 'https://skin.app.vumc.org/api/v1/'
        MULTIPLE_ANNOTATIONS = 'annotation/item/'
        GIRDER_TOKEN = getCurrentToken()['_id']
        item_id = str(item['_id'])
        item_headers = {'Girder-Token': GIRDER_TOKEN, 'Accept': 'application/json'}
        base_dir = '/opt/histomicstk_data/'

        updated = item['updated']
        localtz = pytz.timezone("America/Chicago")
        annotations_access_url = URL + MULTIPLE_ANNOTATIONS + item_id
        annotations_blob = requests.get(annotations_access_url, headers=item_headers)
        # @TODO: I'm not sure why there are some \n, characters showing up in output
        #        but removing them seems to solve the issue 
        try:
            annotations = json.loads(annotations_blob.content.replace(",\n", "").replace("\n", ""), strict=False)
        except ValueError:
            annotations = json.loads(annotations_blob.content, strict=False)
        meta_annotations_only = dict()
        project_folder_name = ''
        if annotations and item and 'meta' in item:
            for m in item['meta']:
                for annotator in annotations:
                    if annotator['annotation']['name'] in m:
                         meta_annotations_only[m] = item['meta'][m]
            item['meta'] = meta_annotations_only
            record_id, site_id, imaging_session, imaging_device_and_vectra, fidelity = self._parse_filename(item['name'])
            # Father session_id and record_id from folder structure since it's not contained in the file name
            folder_child = FolderResource().load(str(item['folderId']), force=True)
            folder_name = folder_child['name']
            session_id = folder_name.split('_')[0]
            parent_folder = FolderResource().load(folder['parentId'], force=True)
            parent_folder_name = parent_folder['name']
            # record_id = parent_folder['name'].split('_')[0]
            if not project_folder_name:  # Only need to set project folder once
                project_folder = FolderResource().load(parent_folder['parentId'], force=True)
                project_folder_name = project_folder['name']
                export_path = os.path.join(base_dir, project_folder_name)
                try:
                    os.mkdir(export_path)
                except OSError:
                    pass  # if the directory exists, just add to it
            parent_folder = os.path.join(base_dir, project_folder_name, parent_folder_name)
            item_folder = os.path.join(parent_folder, folder_name)
            imgsrc_files = os.path.join(item_folder, 'imgsrc')
            json_files = os.path.join(item_folder, 'json')
            mask_files = os.path.join(item_folder, 'masks')
            annotated_files = os.path.join(item_folder, 'annotated')
            [self._make_dir_if_not_exists(f) for f in [parent_folder, item_folder, imgsrc_files, json_files, mask_files, annotated_files]]
            # with open(os.path.join(base_dir, export_dir, parent_folder_name, folder_name, 'json', str(item['name']) + '.json'), 'wb') as f:
            #     item['annotations'] = [anno for anno in annotations]
            #     f.write(json.dumps(item, default=str))
            # Previously was using MATLAB to render annotations
            # cmd = 'JSON_FOLDER={json}/ BASELINE_FOLDER={imgsrc}/ ANNOTATED_IMAGES_FOLDER={annotated}/ MASKS_FOLDER={masks}/ /opt/histomicstk/HistomicsTK/histomicstk/utils/run_step1_main_read_json_mask.sh /home/ubuntu/matlab/r2021b/v911/mcr'.format(imgsrc=imgsrc_files, json=json_files, masks=mask_files, annotated=annotated_files)
            # return cmd, '', ''
            # os.system(cmd)
            (annotated_filename, annotated_extension) = os.path.splitext(item['name'])
            current_user = getCurrentUser()
            annotated_filename = os.path.join(annotated_files, annotated_filename + '_' + current_user['login']) + annotated_extension
            imgsrc = os.path.join(imgsrc_files, item['name'])
            jsonsrc = os.path.join(json_files, item['name'] + '.json')
            try:
                # result = subprocess.run(["identify", "-format", "%Q", img_src_path], capture_output=True, text=True, check=True)
                output = subprocess.check_output(["identify", "-format", "%Q", imgsrc])
                quality = int(output.strip())
            except BaseException as e:
                quality = 92  # Default to high quality

            rendered = render_annotations(
                imgsrc,
                jsonsrc,
                os.path.join(annotated_files, annotated_filename),
                quality
            )

            #return 1, item
            #return 1, annotated_path_extenionless + annotated_extension, 1
            #return annotated_path_extenionless + '.jpg'
            if rendered:
                return record_id, annotated_filename, jsonsrc
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
        from histomicstk import API_URL_REDCAP
        req_users = requests.post(API_URL_REDCAP, data=data)
        for u in json.loads(req_users.text):
            # Grab the list from the annotator field
            if u['field_name'] == 'annotator':
                return {a.split(', ')[1]: a.split(', ')[0] for a in u['select_choices_or_calculations'].split(' | ')}

    def _get_instance_number(self, redcaptoken, record, user, session_id=None):
        data = {
            'token': redcaptoken,
            'content': 'record',
            'action': 'export',
            'format': 'json',
            'type': 'flat',
            'csvDelimiter': '',
            'records[0]': record,
            'fields[0]': 'record_id',
            'fields[1]': 'imaging_session',
            'forms[0]': 'annotation',
            'returnFormat': 'json',
        }

        filter_logic = []
        if user:
            users = self.get_redcap_annotation_users(redcaptoken)
            if user not in users:
                return None
            user_id = users[user]
            filter_logic.append("[annotator] = '" + user_id + "'")

        if session_id:
            filter_logic.append("[imaging_session] = '" + session_id + "'")

        if filter_logic:
            data['filterLogic'] = " and ".join(filter_logic)

        from histomicstk import API_URL_REDCAP
        req_anno = requests.post(API_URL_REDCAP, data=data)

        return json.loads(req_anno.text)

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
        GIRDER_TOKEN = getCurrentToken()['_id']
        # study name is not passed in, so walk up folder directory to get it
        folder = FolderResource().load(str(item['folderId']), force=True)
        session_folder = FolderResource().load(folder['parentId'], force=True)
        study_folder = FolderResource().load(session_folder['parentId'], force=True)
        study_name = study_folder['name']
        vectra = item['name'].split('_')[-1][1:3]  # parse filename for vectra
        try:
            record_name = item['meta']['record_id']
        except KeyError:
            record_name = item['name'].split('_')[0]  # parse filename for record name
        user = ItemResource().getCurrentUser()
        user_name = user['firstName'] + ' ' + user['lastName']
        # Simulating arguments from manage_skin script
        # from histomicstk.utils.manage_skin import EXPORT_NATIENS_OP, VECTRA_FILE_FIELDS, export
        from histomicstk.utils import manage_skin
        args = type('obj', (object,), {
            'folder': item['folderId'],
            'foldername': study_name,
            'startdate': None,
            'enddate': None,
            'annotator': [user['login']],
            'url': 'https://skin.app.vumc.org/api/v1/',
            # 'url': 'http://ec2-54-152-138-170.compute-1.amazonaws.com/api/v1/',
            'operation': [manage_skin.EXPORT_NATIENS_OP],
            'datadir': '/opt/histomicstk_data',
            'token': GIRDER_TOKEN,
            'zip': True,
        })
        manage_skin.export([item], args)  # generate json files so annotation images can be rendered
        # -return self._render_annotations(item, folder)
        (record_id, annotated_path_jpg, json_path) = self._render_annotations(item, folder)
        # return vars(args)
        session_id = folder['lowerName'].rsplit('_', 1)[0]
        instance_number = self._get_instance_number(redcaptoken, record_name, user_name, session_id)
        try:
            single_annotation = [i for i in instance_number if i['redcap_repeat_instrument'] == 'annotation'][0]
        except IndexError:
            single_annotation = None
        try:
            repeat_instance = single_annotation['redcap_repeat_instance']
        except KeyError:
            return "Failed to parse annotation repeat instance."

        field_annotation = manage_skin.VECTRA_FILE_FIELDS[vectra] + '1'  # Annotation fields end with a 1
        fields_records_upload = {
            'token': redcaptoken,
            'record': record_name,
            'content': 'file',
            'action': 'import',
            'returnFormat': 'json',
            'field': field_annotation,
            'repeat_instance': repeat_instance,
        }
        # if 'meta' in item and 'record_id' in item['meta']:
        from histomicstk import API_URL_REDCAP
        # upload annotation jpg
        with open(annotated_path_jpg, 'rb') as f:
            # return (annotated_path_jpg, API_URL_REDCAP, fields_records_upload, f)
            req = requests.post(API_URL_REDCAP, data=fields_records_upload, files={'file': f})
            # return fields_records_upload
        field_components = manage_skin.VECTRA_FILE_FIELDS[vectra].split('_')
        # JSON fields start with json_ and don't delimit field components
        fields_records_upload['field'] = 'json_' + ''.join(field_components[:-1]) + '_' + field_components[-1]
        # upload annotation json
        #raise Exception(json_path)
        with open(json_path, 'rb') as f:
            req = requests.post(API_URL_REDCAP, data=fields_records_upload, files={'file': f})
            return req.text
        # groups = [str(g) for g in user.get('groups', [])]
        # expert_group = '5f0dc574c9f8c18253ae949e'
        # expert_group_natiens = '629ff512234d56ac7568f286'

        #folder = folderModel.load(folder, user=user, level=AccessType.READ)

