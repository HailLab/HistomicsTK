import Backbone from 'backbone';

import GirderApp from 'girder/views/App';
import eventStream from 'girder/utilities/EventStream';
import { getCurrentUser } from 'girder/auth';
import { splitRoute } from 'girder/misc';

import router from './router';
import HeaderView from './views/layout/HeaderView';
import bindRoutes from './routes';

import layoutTemplate from './templates/layout/layout.pug';
import './stylesheets/layout/layout.styl';

var App = GirderApp.extend({
    initialize(settings) {
        /*
            cycle.js
            2018-05-15
        
            Public Domain.
        
            NO WARRANTY EXPRESSED OR IMPLIED. USE AT YOUR OWN RISK.
        
            This code should be minified before deployment.
            See http://javascript.crockford.com/jsmin.html
        
            USE YOUR OWN COPY. IT IS EXTREMELY UNWISE TO LOAD CODE FROM SERVERS YOU DO
            NOT CONTROL.
        */
        
        // The file uses the WeakMap feature of ES6.
        
        /*jslint eval */
        
        /*property
            $ref, decycle, forEach, get, indexOf, isArray, keys, length, push,
            retrocycle, set, stringify, test
        */
        
        if (typeof JSON.decycle !== "function") {
            JSON.decycle = function decycle(object, replacer) {
                "use strict";
        
        // Make a deep copy of an object or array, assuring that there is at most
        // one instance of each object or array in the resulting structure. The
        // duplicate references (which might be forming cycles) are replaced with
        // an object of the form
        
        //      {"$ref": PATH}
        
        // where the PATH is a JSONPath string that locates the first occurance.
        
        // So,
        
        //      var a = [];
        //      a[0] = a;
        //      return JSON.stringify(JSON.decycle(a));
        
        // produces the string '[{"$ref":"$"}]'.
        
        // If a replacer function is provided, then it will be called for each value.
        // A replacer function receives a value and returns a replacement value.
        
        // JSONPath is used to locate the unique object. $ indicates the top level of
        // the object or array. [NUMBER] or [STRING] indicates a child element or
        // property.
        
                var objects = new WeakMap();     // object to path mappings
        
                return (function derez(value, path) {
        
        // The derez function recurses through the object, producing the deep copy.
        
                    var old_path;   // The path of an earlier occurance of value
                    var nu;         // The new object or array
        
        // If a replacer function was provided, then call it to get a replacement value.
        
                    if (replacer !== undefined) {
                        value = replacer(value);
                    }
        
        // typeof null === "object", so go on if this value is really an object but not
        // one of the weird builtin objects.
        
                    if (
                        typeof value === "object"
                        && value !== null
                        && !(value instanceof Boolean)
                        && !(value instanceof Date)
                        && !(value instanceof Number)
                        && !(value instanceof RegExp)
                        && !(value instanceof String)
                    ) {
        
        // If the value is an object or array, look to see if we have already
        // encountered it. If so, return a {"$ref":PATH} object. This uses an
        // ES6 WeakMap.
        
                        old_path = objects.get(value);
                        if (old_path !== undefined) {
                            return {$ref: old_path};
                        }
        
        // Otherwise, accumulate the unique value and its path.
        
                        objects.set(value, path);
        
        // If it is an array, replicate the array.
        
                        if (Array.isArray(value)) {
                            nu = [];
                            value.forEach(function (element, i) {
                                nu[i] = derez(element, path + "[" + i + "]");
                            });
                        } else {
        
        // If it is an object, replicate the object.
        
                            nu = {};
                            Object.keys(value).forEach(function (name) {
                                nu[name] = derez(
                                    value[name],
                                    path + "[" + JSON.stringify(name) + "]"
                                );
                            });
                        }
                        return nu;
                    }
                    return value;
                }(object, "$"));
            };
        }
        
        
        if (typeof JSON.retrocycle !== "function") {
            JSON.retrocycle = function retrocycle($) {
                "use strict";
        
        // Restore an object that was reduced by decycle. Members whose values are
        // objects of the form
        //      {$ref: PATH}
        // are replaced with references to the value found by the PATH. This will
        // restore cycles. The object will be mutated.
        
        // The eval function is used to locate the values described by a PATH. The
        // root object is kept in a $ variable. A regular expression is used to
        // assure that the PATH is extremely well formed. The regexp contains nested
        // * quantifiers. That has been known to have extremely bad performance
        // problems on some browsers for very long strings. A PATH is expected to be
        // reasonably short. A PATH is allowed to belong to a very restricted subset of
        // Goessner's JSONPath.
        
        // So,
        //      var s = '[{"$ref":"$"}]';
        //      return JSON.retrocycle(JSON.parse(s));
        // produces an array containing a single element which is the array itself.
        
                var px = /^\$(?:\[(?:\d+|"(?:[^\\"\u0000-\u001f]|\\(?:[\\"\/bfnrt]|u[0-9a-zA-Z]{4}))*")\])*$/;
        
                (function rez(value) {
        
        // The rez function walks recursively through the object looking for $ref
        // properties. When it finds one that has a value that is a path, then it
        // replaces the $ref object with a reference to the value that is found by
        // the path.
        
                    if (value && typeof value === "object") {
                        if (Array.isArray(value)) {
                            value.forEach(function (element, i) {
                                if (typeof element === "object" && element !== null) {
                                    var path = element.$ref;
                                    if (typeof path === "string" && px.test(path)) {
                                        value[i] = eval(path);
                                    } else {
                                        rez(element);
                                    }
                                }
                            });
                        } else {
                            Object.keys(value).forEach(function (name) {
                                var item = value[name];
                                if (typeof item === "object" && item !== null) {
                                    var path = item.$ref;
                                    if (typeof path === "string" && px.test(path)) {
                                        value[name] = eval(path);
                                    } else {
                                        rez(item);
                                    }
                                }
                            });
                        }
                    }
                }($));
                return $;
            };
        }
        this.settings = settings;
        return GirderApp.prototype.initialize.apply(this, arguments);
    },

    render() {
        this.$el.html(layoutTemplate());

        this.histomicsHeader = new HeaderView({
            el: this.$('#g-app-header-container'),
            parentView: this,
            settings: this.settings
        }).render();

        return this;
    },

    /**
     * On login we re-render the current body view; whereas on
     * logout, we redirect to the front page.
     */
    login() {
        var route = splitRoute(Backbone.history.fragment).base;
        Backbone.history.fragment = null;
        eventStream.close();

        if (getCurrentUser()) {
            eventStream.open();
            router.navigate(route, {trigger: true});
        } else {
            router.navigate('/', {trigger: true});
        }
    },

    navigateTo(view) {
        if (this.bodyView instanceof view) {
            return this;
        }
        return GirderApp.prototype.navigateTo.apply(this, arguments);
    },

    bindRoutes: bindRoutes
});

export default App;
