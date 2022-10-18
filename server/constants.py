#!/usr/bin/env python
# -*- coding: utf-8 -*-


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
SKIN_APP_IMAGE_BASE_URL = 'https://skin.app.vumc.org/histomicstk#?image='
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


# Constants representing the setting keys for this plugin
class PluginSettings(object):
    HISTOMICSTK_DEFAULT_DRAW_STYLES = 'histomicstk.default_draw_styles'
    HISTOMICSTK_WEBROOT_PATH = 'histomicstk.webroot_path'
    HISTOMICSTK_BRAND_NAME = 'histomicstk.brand_name'
    HISTOMICSTK_BRAND_COLOR = 'histomicstk.brand_color'
    HISTOMICSTK_BANNER_COLOR = 'histomicstk.banner_color'
    HISTOMICSTK_ANALYSIS_ACCESS = 'histomicstk.analysis_access'
    HISTOMICSTK_QUARANTINE_FOLDER = 'histomicstk.quarantine_folder'
