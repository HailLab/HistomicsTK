import events from './events';
import ImageView from './views/body/ImageView';

import Router from './router';

import { restRequest } from 'girder/rest';

function bindRoutes() {
    Router.route('', 'index', function () {
        var firstImage = '5f0f2da097cefa564329547b';
        var folderId = '5f0dc45cc9f8c18253ae949b';
	console.log('routes.js, bindRoutes --> ');

        restRequest({
            url: `item/5f0dc45cc9f8c18253ae949b/first_image?folder=5f0dc45cc9f8c18253ae949b`
        }).done(function (first) {
	    console.log('routes.js, bindRoutes --> done , first._id ', first._id, (typeof first));
	    console.log('routes.js, bindRoutes <-- done, firstImage: ', firstImage);	    	    
            firstImage = typeof first !== 'undefined' ? first._id : firstImage;
	    console.log('routes.js, bindRoutes <-- done, firstImage: ', firstImage);	    	    	    
            //events.trigger('g:navigateTo', ImageView, {'modelId': firstImage});
	    events.trigger('g:navigateTo', ImageView, {'modelId': firstImage, 'debug': 'YES'});	    
	    //events.trigger('g:navigateTo', ImageView, {'modelId': '123456'});	    
	    console.log('routes.js, bindRoutes <-- done ');	    
        });
    });
    return Router;
}

export default bindRoutes;
