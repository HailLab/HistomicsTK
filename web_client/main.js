import events from 'girder/events';
import router from 'girder/router';
import { getCurrentUser } from 'girder/auth';

import { registerPluginNamespace } from 'girder/pluginUtils';
import { exposePluginConfig } from 'girder/utilities/PluginUtils';

// expose symbols under girder.plugins
import * as histomicstk from 'girder_plugins/HistomicsTK';

// import modules for side effects
import './views/itemList';
import './views/itemPage';

import ConfigView from './views/body/ConfigView';
import UsersView from '@girder/core/views/body/UsersView';
import UserView from '@girder/core/views/body/UserView';

const pluginName = 'HistomicsTK';
const configRoute = `plugins/${pluginName}/config`;

registerPluginNamespace(pluginName, histomicstk);

exposePluginConfig(pluginName, configRoute);

router.route(configRoute, 'HistomicsTKConfig', function () {
    events.trigger('g:navigateTo', ConfigView);
});

// Restrict access to users page - require admin access
router.route('users', 'users', function (params) {
    const user = getCurrentUser();
    if (!user || !user.get('admin')) {
        // Redirect to home if not authenticated or not an admin
        router.navigate('', {trigger: true});
        return;
    }
    // Allow access to original users route for admins
    events.trigger('g:navigateTo', UsersView, params || {});
    events.trigger('g:highlightItem', 'UsersView');
});

router.route('user/:id', 'user', function (userId, params) {
    const user = getCurrentUser();
    if (!user || !user.get('admin')) {
        // Redirect to home if not authenticated or not an admin
        router.navigate('', {trigger: true});
        return;
    }
    // Allow access to original user route for admins
    UserView.fetchAndInit(userId, {
        folderCreate: params.dialog === 'foldercreate',
        dialog: params.dialog
    });
});
