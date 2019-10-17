from girder.api import access
from girder.api.v1.item import Item as ItemResource
from girder.api.describe import autoDescribeRoute, Description
from girder.constants import AccessType
from girder.exceptions import RestException
from girder.models.folder import Folder

import random


def _isLargeImageItem(item):
    return item.get('largeImage', {}).get('fileId') is not None


class ImageBrowseResource(ItemResource):
    """Extends the "item" resource to iterate through images im a folder."""

    def __init__(self, apiRoot):
        # Don't call the parent (Item) constructor, to avoid redefining routes,
        # but do call the grandparent (Resource) constructor
        super(ItemResource, self).__init__()

        self.resourceName = 'item'
        apiRoot.item.route('GET', (':id', 'next_image'), self.getNextImage)
        apiRoot.item.route('GET', (':id', 'previous_image'), self.getPreviousImage)

    def getAdjacentImages(self, currentImage):
        user = self.getCurrentUser()
        groups = [str(g) for g in user.get('groups', [])]
        expert_group = '5bef3897e6291400ba908ab3'
        folderModel = Folder()
        folder = folderModel.load(
            currentImage['folderId'], user=user, level=AccessType.READ)
        allImages = [item for item in folderModel.childItems(folder) if _isLargeImageItem(item)]
        if expert_group not in groups:
            random.seed(user.get('_id'))
            random.shuffle(allImages)
        try:
            index = allImages.index(currentImage)
        except ValueError:
            raise RestException('Id is not an image', 404)

        return {
            'previous': allImages[index - 1],
            'next': allImages[(index + 1) % len(allImages)]
        }

    @access.public
    @autoDescribeRoute(
        Description('Get the next image in the same folder as the given item.')
        .modelParam('id', 'The current image ID',
                    model='item', destName='image', paramType='path', level=AccessType.READ)
        .errorResponse()
        .errorResponse('Image not found', code=404)
    )
    def getNextImage(self, image):
        return self.getAdjacentImages(image)['next']

    @access.public
    @autoDescribeRoute(
        Description('Get the previous image in the same folder as the given item.')
        .modelParam('id', 'The current item ID',
                    model='item', destName='image', paramType='path', level=AccessType.READ)
        .errorResponse()
        .errorResponse('Image not found', code=404)
    )
    def getPreviousImage(self, image):
        return self.getAdjacentImages(image)['previous']
