import events from './events';
import ImageView from './views/body/ImageView';

import Router from './router';

import { getCurrentUser } from 'girder/auth';
import { restRequest } from 'girder/rest';

function bindRoutes() {
    Router.route('', 'index', function () {
        const user = getCurrentUser();
        const cgvhdGroupId = '5f0dc554c9f8c18253ae949d';
        let firstImage = '5f0e188697cefa5643295388';
        let firstFolder = '5f0dc45cc9f8c18253ae949b';
        if (user.attributes.groups.indexOf(cgvhdGroupId)) {
            firstImage = '5f0e192a97cefa5643295397';
            firstFolder = '5f0dc449c9f8c18253ae949a';
        }
        restRequest({
            url: `item/${firstFolder}/first_image?folder=${firstFolder}`
        }).done(function (first) {
            firstImage = typeof first !== 'undefined' ? first._id : firstImage;
            firstFolder = typeof first !== 'undefined' && first.folderId ? first.folderId : firstFolder;
            events.trigger('g:navigateTo', ImageView, {'modelId': firstImage, 'folderId': firstFolder});
        });
    });
    return Router;
}

export default bindRoutes;
