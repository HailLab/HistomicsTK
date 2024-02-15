from girder.api import access
from girder.api.v1.token import Token as TokenResource
from girder.api.describe import autoDescribeRoute, Description
from girder.constants import AccessType
# from girder.models.folder import Folder as FolderModel
from girder.models.token import Token as TokenModel
from dateutil import parser


class UpdateTokenExpirationTokenResource(TokenResource):
    """Extends the "token" resource to allow updating Token expirations."""

    def __init__(self, apiRoot):
        # Don't call the parent (Token) constructor, to avoid redefining routes,
        # but do call the grandparent (Resource) constructor
        super(TokenResource, self).__init__()

        self.resourceName = 'token'
        self._model = TokenModel()
        self.route('POST', (':id', ':expiration', 'update_token_expiration'), self.update_token_expiration)
        apiRoot.token.route('POST', (':id', ':expiration', 'update_token_expiration'), self.update_token_expiration)
        #apiRoot.token.route('GET', ('update_token_expiration'), self.update_token_expiration)

    @access.public
    @autoDescribeRoute(
        Description('Update the expiration date for a given token')
        .modelParam('id', 'The token ID of a particular user',
                    model='token', destName='token', paramType='query', level=AccessType.READ,
                    required=True)
        .param('expiration', 'The expiration date in the form of YYYY-MM-DD')
        .errorResponse()
        .errorResponse('Token is empty or does not exist', code=404)
    )
    def update_token_expiration(self, token, expiration):
        token['expires'] = parser.parse(expiration)
        #from girder.api.rest import getCurrentToken
        #token = getCurrentToken()
        #import datetime
        #token['expires'] = (datetime.datetime.utcnow() + datetime.timedelta(days=365*7))
        return TokenModel().save(token)

