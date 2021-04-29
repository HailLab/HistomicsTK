import events from './events';
import ImageView from './views/body/ImageView';

import Router from './router';

import { restRequest } from 'girder/rest';

function bindRoutes() {
    Router.route('', 'index', function () {
        let firstImage = '5f0f2da097cefa564329547b';
        let firstFolder = '5f0dc45cc9f8c18253ae949b';
        console.log('routes.js, bindRoutes --> ');
        restRequest({
            url: `item/5f0dc45cc9f8c18253ae949b/first_image?folder=5f0dc45cc9f8c18253ae949b`
        }).done(function (first) {
            console.log('routes.js, bindRoutes --> done , first._id ', first._id, (typeof first));
            console.log('routes.js, bindRoutes <-- done, firstImage: ', firstImage);
            firstImage = typeof first !== 'undefined' ? first._id : firstImage;
            firstFolder = typeof first !== 'undefined' && first.folderId ? first.folderId : firstFolder;
            console.log('routes.js, bindRoutes <-- done, firstImage: ', firstImage);
            //events.trigger('g:navigateTo', ImageView, {'modelId': firstImage});
            events.trigger('g:navigateTo', ImageView, {'modelId': firstImage, 'folderId': firstFolder});
            //events.trigger('g:navigateTo', ImageView, {'modelId': '123456'});     
            console.log('routes.js, bindRoutes <-- done ');
        });
        /*
        var first = restRequest({
            url: 'item/5f0dc45cc9f8c18253ae949b/first_image?folder=5f0dc45cc9f8c18253ae949b'
        });
        firstImage = typeof first !== 'undefined' ? first._id : firstImage;
        events.trigger('g:navigateTo', ImageView, {'modelId': firstImage});
        */
    });
    return Router;
}

export default bindRoutes;
