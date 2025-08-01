from girder import events
from girder.api import access
from girder.exceptions import AccessException
from girder.models.user import User


def _checkUserAccess(event):
    """
    Event handler to restrict access to user-related endpoints.
    Only authenticated users can access user management features.
    """
    info = event.info
    
    # Check if this is a user-related endpoint
    if (hasattr(info, 'route') and 
        len(info['route']) > 0 and 
        info['route'][0] == 'user'):
        
        # Get current user
        currentUser = info.get('user')
        
        # If no user is logged in, deny access
        if not currentUser:
            raise AccessException('You must be logged in to access user information.')


def setup_user_access_control():
    """Setup user access control restrictions."""
    # Bind the access control check to API requests
    events.bind('rest.get.user.before', 'histomicstk', _checkUserAccess)
    events.bind('rest.post.user.before', 'histomicstk', _checkUserAccess)
    events.bind('rest.put.user.before', 'histomicstk', _checkUserAccess)
    events.bind('rest.delete.user.before', 'histomicstk', _checkUserAccess)

