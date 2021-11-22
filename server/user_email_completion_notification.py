from girder.api import access
from girder.api.v1.user import User as UserResource
from girder.api.describe import autoDescribeRoute, Description
from girder.constants import AccessType
from girder.models.user import User as UserModel
from girder.utility import mail_utils


class UserEmailCompletionNotificationResource(UserResource):
    """Extends the "folder" resource to get the first image."""

    def __init__(self, apiRoot):
        # Don't call the parent (Item) constructor, to avoid redefining routes,
        # but do call the grandparent (Resource) constructor
        super(UserResource, self).__init__()

        self.resourceName = 'user'
        self._model = UserModel()
        apiRoot.item.route('GET', (':email', ':project', 'notify_completion'), self.emailCompletionNotification)

    @access.public
    @autoDescribeRoute(
        Description('Email project lead to inform them of work completion.')
        .param('email', 'The email address of the recipient.',
               dataType='string', required=True)
        .param('project', 'The project which was completed.',
               dataType='string', required=True)
        .errorResponse()
        .errorResponse('Email address invalid.', code=404)
    )
    def emailCompletionNotification(self, email, project):
        user = self.getCurrentUser()
        mail_utils.sendEmail(
            to=email, subject='Skin {project} completion: {email_addr}'.format(email_addr=user.get('email', 'unknown_user').lower(), project=project),
            text='The user {email_addr} completed {project}.'.format(email_addr=user.get('email', 'unknown_user').lower(), project=project),
        )
        return {'message': 'Emailed.'}

