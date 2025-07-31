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

const pluginName = 'HistomicsTK';
const configRoute = `plugins/${pluginName}/config`;

registerPluginNamespace(pluginName, histomicstk);

exposePluginConfig(pluginName, configRoute);

router.route(configRoute, 'HistomicsTKConfig', function () {
    events.trigger('g:navigateTo', ConfigView);
});

// Restrict access to users page - require login
router.route('users', 'users', function () {
    const user = getCurrentUser();
    if (!user) {
        // Redirect to login if not authenticated
        router.navigate('', {trigger: true});
        return;
    }
    // Allow access to original users route
    events.trigger('g:navigateTo', girder.views.UsersView);
});

router.route('users/:id', 'user', function (id) {
    const user = getCurrentUser();
    if (!user) {
        // Redirect to login if not authenticated
        router.navigate('', {trigger: true});
        return;
    }
    // Allow access to original user route
    events.trigger('g:navigateTo', girder.views.UserView, {id: id});
});
