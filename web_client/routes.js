import events from './events';
import ImageView from './views/body/ImageView';

import Router from './router';

import { restRequest } from 'girder/rest';

function bindRoutes() {
    Router.route('', 'index', function () {
        var firstImage = '5f0f2da097cefa564329547b';
        var folderId = '5f0dc45cc9f8c18253ae949b';
        restRequest({
            url: `item/5f0dc45cc9f8c18253ae949b/first_image?folder=5f0dc45cc9f8c18253ae949b`
        }).done(function (first) {
            firstImage = typeof first !== 'undefined' ? first._id : firstImage;
            events.trigger('g:navigateTo', ImageView, {'modelId': firstImage});
        });
    });
    return Router;
}

export default bindRoutes;
