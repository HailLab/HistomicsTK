from girder.api import access
from girder.api.v1.item import Folder as FolderResource
from girder.api.v1.item import Item as ItemResource
from girder.api.describe import autoDescribeRoute, Description
from girder.constants import AccessType
from girder.models.folder import Folder as FolderModel

import random


def _isLargeImageItem(item):
    return item.get('largeImage', {}).get('fileId') is not None


class FolderFirstImageResource(FolderResource):
    """Extends the "folder" resource to get the first image."""

    def __init__(self, apiRoot):
        # Don't call the parent (Item) constructor, to avoid redefining routes,
        # but do call the grandparent (Resource) constructor
        super(FolderResource, self).__init__()

        self.resourceName = 'folder'
        self._model = FolderModel()
        apiRoot.item.route('GET', (':id', 'first_image'), self.getFirstImage)

    @access.public
    @autoDescribeRoute(
        Description('Get the first image in the folder for this user.')
        .modelParam('id', 'The (virtual) folder ID the image is located in',
                    model='folder', destName='folder', paramType='query', level=AccessType.READ,
                    required=True)
        .errorResponse()
        .errorResponse('Image is empty or does not exist', code=404)
    )
    def getFirstImage(self, folder):
        user = ItemResource().getCurrentUser()
        groups = [str(g) for g in user.get('groups', [])]
        expert_group = '5f0dc574c9f8c18253ae949e'
        expert_group_natiens = '629ff512234d56ac7568f286'

        folderModel = FolderResource()
        #folder = folderModel.load(folder, user=user, level=AccessType.READ)

        if folder.get('isVirtual'):
            children = folderModel.childItems(folder, includeVirtual=True)
        else:
            children = folderModel.childItems(folder)

        allImages = [item for item in children if _isLargeImageItem(item)]
        if expert_group not in groups and expert_group_natiens not in groups:
            random.seed(user.get('_id'))
            random.shuffle(allImages)
        return allImages[0]

