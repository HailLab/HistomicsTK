import _ from 'underscore';

import events from 'girder/events';
import Panel from 'girder_plugins/slicer_cli_web/views/Panel';
import { getCurrentUser } from 'girder/auth';
import { restRequest } from 'girder/rest';

import StyleCollection from '../collections/StyleCollection';
import StyleModel from '../models/StyleModel';
import editElement from '../dialogs/editElement';
import editStyleGroups from '../dialogs/editStyleGroups';
import drawWidget from '../templates/panels/drawWidget.pug';
import '../stylesheets/panels/drawWidget.styl';

/**
 * Create a panel with controls to draw and edit
 * annotation elements.
 */
var DrawWidget = Panel.extend({
    events: _.extend(Panel.prototype.events, {
        'click .h-edit-element': 'editElement',
        'click .h-delete-element': 'deleteElement',
        'click .h-draw': 'drawElement',
        'click .h-pan': 'drawElement',
        'click .h-nogvhd': 'nogvhd',
        'click .h-unconfident': 'unconfident',
        'click .h-skin-survey': 'skin_survey',
        'change .h-style-group': '_setStyleGroup',
        'click .h-configure-style-group': '_styleGroupEditor',
        'mouseenter .h-element': '_highlightElement',
        'mouseleave .h-element': '_unhighlightElement'
    }),

    /**
     * Create the panel.
     *
     * @param {object} settings
     * @param {ItemModel} settings.image
     *     The associate large_image "item"
     */
    initialize(settings) {
        this.image = settings.image;
        this.annotation = settings.annotation;
        this.collection = this.annotation.elements();
        this.viewer = settings.viewer;
        this._drawingType = settings.drawingType || 'line';

        this._highlighted = {};
        this._groups = new StyleCollection();
        this._style = new StyleModel({id: 'default'});
        this.listenTo(this._groups, 'update', this.render);
        this.listenTo(this.collection, 'add remove reset', this._recalculateGroupAggregation);
        this.listenTo(this.collection, 'change update reset', this.render);
        this._groups.fetch().done(() => {
            // ensure the default style exists
            if (this._groups.has('default')) {
                this._style.set(this._groups.get('default').toJSON());
            } else {
                this._groups.add(this._style.toJSON());
                this._groups.get(this._style.id).save();
            }
        });
        this.on('h:mouseon', (model) => {
            if (model && model.id) {
                this._highlighted[model.id] = true;
                this.$(`.h-element[data-id="${model.id}"]`).addClass('h-highlight-element');
            }
        });
        this.on('h:mouseoff', (model) => {
            if (model && model.id) {
                this._highlighted[model.id] = false;
                this.$(`.h-element[data-id="${model.id}"]`).removeClass('h-highlight-element');
            }
        });
    },

   render() {
        this.$('[data-toggle="tooltip"]').tooltip('destroy');
        if (!this.viewer) {
            this.$el.empty();
            delete this._skipRenderHTML;
            return;
        }
        const name = (this.annotation.get('annotation') || {}).name || 'Untitled';
        this.trigger('h:redraw', this.annotation);
        var nogvhd = false;
        var unconfident = false;
        var item = $.ajax({
            url: '/api/v1/item/' + this.image.attributes._id,
            beforeSend: function(request) {
                var getCookie = function(name) {
                    var value = "; " + document.cookie;
                    var parts = value.split("; " + name + "=");
                    if (parts.length == 2)
                        return parts.pop().split(";").shift();
                };
                request.setRequestHeader('girder-token', getCookie('girderToken'));
            },
            type: 'GET',
            cache: false,
            timeout: 5000,
            success: function(data) {
                console.log(data.meta);
            }, error: function(jqXHR, textStatus, errorThrown) {
                alert('error ' + textStatus + " " + errorThrown);
            },
            async: false
        });
        if ('meta' in item.responseJSON && 'unconfident-' + this.annotation.attributes.annotation.name.replace(/\./g, '') in item.responseJSON.meta) {
            unconfident = !!item.responseJSON.meta['unconfident-' + this.annotation.attributes.annotation.name.replace(/\./g, '')];
        }
        if ('meta' in item.responseJSON && 'nogvhd-' + this.annotation.attributes.annotation.name.replace(/\./g, '') in item.responseJSON.meta) {
            nogvhd = !!item.responseJSON.meta['nogvhd-' + this.annotation.attributes.annotation.name.replace(/\./g, '')];
        }
        var survey_submit = false;
        const user = getCurrentUser();
        const NATIENS_GROUP = '61684cd6b782047b732b842c';
        // const skin_survey_folder = '60f600aa40582164e9ac5f25';
        // if (this.image && this.image.attributes && this.image.attributes.folderId && this.image.attributes.folderId == skin_survey_folder) {
        //     survey_submit = true;
        // }
        console.log('GROUP STUFF');
        console.log(user);
        console.log(user.attributes.groups);
        console.log(NATIENS_GROUP);
        if (user.attributes.groups.indexOf(NATIENS_GROUP) > -1) {
            survey_submit = true;
        }
        // console.log(JSON.stringify(JSON.decycle(this)));
        if (this._skipRenderHTML) {
            delete this._skipRenderHTML;
        } else {
            this.$el.html(drawWidget({
                title: 'Draw',
                elements: this.collection.models,
                groups: this._groups,
                style: this._style.id,
                highlighted: this._highlighted,
                nogvhd: nogvhd,
                unconfident: unconfident,
                survey_submit: survey_submit,
                name
             }));
        }
        if (this._drawingType) {
            this.$('button.h-draw[data-type="' + this._drawingType + '"]').addClass('active');
            this.$('button.h-pan').removeClass('active');
            this.drawElement(undefined, this._drawingType);
        }
        this.$('.s-panel-content').collapse({toggle: false});
        this.$('[data-toggle="tooltip"]').tooltip({container: 'body'});
        if (this.viewer.annotationLayer && !this.viewer.annotationLayer._boundHistomicsTKModeChange) {
            this.viewer.annotationLayer._boundHistomicsTKModeChange = true;
            this.viewer.annotationLayer.geoOn(window.geo.event.annotation.mode, (event) => {
                this.$('button.h-draw').removeClass('active');
                this.$('button.h-draw[data-type="' + this._drawingType + '"]').addClass('active');
                if (event.mode !== this._drawingType && this._drawingType) {
                    /* This makes the draw modes stay on until toggled off.
                     * To turn off drawing after each annotation, add
                     *  this._drawingType = null;
                     */
                    this.drawElement(undefined, this._drawingType);
                }
            });
        }
        return this;
    },

    /**
     * When a region should be drawn that isn't caused by a drawing button,
     * toggle off the drawing mode.
     *
     * @param {event} Girder event that triggered drawing a region.
     */
    _widgetDrawRegion(evt) {
        this._drawingType = null;
        this.$('button.h-draw').removeClass('active');
        this.$('button.h-pan').addClass('active');
    },

    /**
     * Set the image "viewer" instance.  This should be a subclass
     * of `large_image/imageViewerWidget` that is capable of rendering
     * annotations.
     */
    setViewer(viewer) {
        this.viewer = viewer;
        // make sure our listeners are in the correct order.
        this.stopListening(events, 's:widgetDrawRegion', this._widgetDrawRegion);
        if (viewer) {
            this.listenTo(events, 's:widgetDrawRegion', this._widgetDrawRegion);
            viewer.stopListening(events, 's:widgetDrawRegion', viewer.drawRegion);
            viewer.listenTo(events, 's:widgetDrawRegion', viewer.drawRegion);
        }
        return this;
    },

    /**
     * Respond to a click on the "edit" button by rendering
     * the EditAnnotation modal dialog.
     */
    editElement(evt) {
        var dialog = editElement(this.collection.get(this._getId(evt)));
        this.listenTo(dialog, 'h:editElement', (obj) => {
            // update the html immediately instead of rerendering it
            let id = obj.element.id,
                label = (obj.data.label || {}).value,
                elemType = obj.element.get('type');
            label = label || (elemType === 'polyline' ? (obj.element.get('closed') ? 'polygon' : 'line') : elemType);
            this.$(`.h-element[data-id="${id}"] .h-element-label`).text(label).attr('title', label);
            this._skipRenderHTML = true;
        });
    },

    /**
     * Respond to a click on the "delete" button by removing
     * the element from the element collection.
     */
    deleteElement(evt) {
        let id = this._getId(evt);
        this.$(`.h-element[data-id="${id}"]`).remove();
        this._skipRenderHTML = true;
        this.collection.remove(id);
    },

    /**
     * Respond to clicking an element type by putting the image
     * viewer into "draw" mode.
     *
     * @param {jQuery.Event} [evt] The button click that triggered this event.
     *      `undefined` to use a passed-in type.
     * @param {string|null} [type] If `evt` is `undefined`, switch to this draw
     *      mode.
     */
    drawElement(evt, type) {
        var $el;
        if (evt) {
            $el = this.$(evt.currentTarget);
            $el.tooltip('hide');
            type = $el.hasClass('active') ? null : $el.data('type');
        } else {
            $el = this.$('button.h-draw[data-type="' + type + '"]');
            this.$('button.h-pan').removeClass('active');
        }
        if (this.viewer.annotationLayer.mode() === type && this._drawingType === type) {
            return;
        }
        if (this.viewer.annotationLayer.mode()) {
            this._drawingType = null;
            this.viewer.annotationLayer.mode(null);
            this.viewer.annotationLayer.geoOff(window.geo.event.annotation.state);
            this.viewer.annotationLayer.removeAllAnnotations();
        }
        if (type) {
            // always show the active annotation when drawing a new element
            this.$('button.h-pan').removeClass('active');
            this.annotation.set('displayed', true);

            this._drawingType = type;
            this.viewer.startDrawMode(type)
                .then((element) => {
                    this.collection.add(
                        _.map(element, (el) => _.extend(el, _.omit(this._style.toJSON(), 'id')))
                    );
                    return undefined;
                });
        } else {
            this.$('button.h-pan').addClass('active');
        }
    },

    /**
     * Mark image as not containing any GVHD by storing in metadata.
     *
     * @param {jQuery.Event} [evt] The button click that triggered this event.
     *      `undefined` to use a passed-in type.
     */
    nogvhd(evt) {
        var $el;
        var active = false;
        if (evt) {
            $el = this.$(evt.currentTarget);
            $el.tooltip('hide');
            active = $el.hasClass('active');
        }
        if (this.viewer.annotationLayer.mode()) {
            this._drawingType = null;
            this.viewer.annotationLayer.mode(null);
            this.viewer.annotationLayer.geoOff(window.geo.event.annotation.state);
            this.viewer.annotationLayer.removeAllAnnotations();
        }
        var data = {};
        data["nogvhd-" + this.annotation.attributes.annotation.name.replace(/\./g, '')] = !active;
        var item = $.ajax({
            url: '/api/v1/item/' + this.image.attributes._id + '/metadata',
            beforeSend: function(request) {
                var getCookie = function(name) {
                    var value = "; " + document.cookie;
                    var parts = value.split("; " + name + "=");
                    if (parts.length == 2)
                        return parts.pop().split(";").shift();
                };
                request.setRequestHeader('girder-token', getCookie('girderToken'));
            },
            data: JSON.stringify(data),
            contentType: "application/json; charset=utf-8",
            type: 'PUT',
            cache: false,
            timeout: 5000,
            success: function(data) {
                $el.toggleClass('active');
            }, error: function(jqXHR, textStatus, errorThrown) {
                alert('error ' + textStatus + " " + errorThrown);
            }
        });
    },

    /**
     * Mark annotation as not being confident by storing in metadata.
     *
     * @param {jQuery.Event} [evt] The button click that triggered this event.
     *      `undefined` to use a passed-in type.
     */
    unconfident(evt) {
        var $el;
        var active = false;
        if (evt) {
            $el = this.$(evt.currentTarget);
            $el.tooltip('hide');
            active = $el.hasClass('active');
        }
        if (this.viewer.annotationLayer.mode()) {
            this._drawingType = null;
            this.viewer.annotationLayer.mode(null);
            this.viewer.annotationLayer.geoOff(window.geo.event.annotation.state);
            this.viewer.annotationLayer.removeAllAnnotations();
        }
        var data = {};
        data["unconfident-" + this.annotation.attributes.annotation.name.replace(/\./g, '')] = !active;
        var item = $.ajax({
            url: '/api/v1/item/' + this.image.attributes._id + '/metadata',
            beforeSend: function(request) {
                var getCookie = function(name) {
                    var value = "; " + document.cookie;
                    var parts = value.split("; " + name + "=");
                    if (parts.length == 2)
                        return parts.pop().split(";").shift();
                };
                request.setRequestHeader('girder-token', getCookie('girderToken'));
            },
            data: JSON.stringify(data),
            contentType: "application/json; charset=utf-8",
            type: 'PUT',
            cache: false,
            timeout: 5000,
            success: function(data) {
                $el.toggleClass('active');
            }, error: function(jqXHR, textStatus, errorThrown) {
                alert('error ' + textStatus + " " + errorThrown);
            }
        });
    },

    /**
     * Returns the parent folder ID
     *
     * @param {string} The folder ID of the parent.
     */
    getParentFolder(folderId) {
        console.log('InsideGetParentFolder:', folderId);
        return new Promise(function(resolve, reject) {
            restRequest({
                url: 'folder/' + folderId,
                type: 'GET'
            }).done(function (parentFolder) {
                resolve(parentFolder);
            }).fail(function (err) {
                console.error('Error getting parent folder:', err);
                reject(err);
            });
        });
    },

    /**
     * Submit images to survey using API, only for Skin Survey
     *
     * @param {jQuery.Event} [evt] The button click that triggered this event.
     *      `undefined` to use a passed-in type.
     */
    async skin_survey(evt) {
        var $el;
        var active = false;
        if (evt) {
            $el = this.$(evt.currentTarget);
            $el.tooltip('hide');
            active = $el.hasClass('active');
            // get folder
            var folderImage = await this.getParentFolder(this.image.parent.id);
            console.log('parent.id: ', this.image.parent.id);
            // get all parent folders until one has a redcaptoken
            while (folderImage && (!folderImage.hasOwnProperty('meta') || !folderImage.meta.hasOwnProperty('redcaptoken'))) {
                console.log('Folderloop: ', folderImage.parentId);
                folderImage = await this.getParentFolder(folderImage.parentId);
            }

            const redcaptoken = folderImage.meta.redcaptoken ? folderImage.meta.redcaptoken : 'DEFAULT_REDCAP_TOKEN';
            console.log('send_to_redcap!');
            console.log(folderImage);
            console.log(this.image);
            const imageId = this.image.attributes._id;
            var item = $.ajax({
                url: '/api/v1/item/%7Bid%7D/%7Bredcaptoken%7D/send_to_redcap?id=' + imageId + '&redcaptoken=' + redcaptoken,
                beforeSend: function(request) {
                    var getCookie = function(name) {
                        var value = "; " + document.cookie;
                        var parts = value.split("; " + name + "=");
                        if (parts.length == 2)
                            return parts.pop().split(";").shift();
                    };
                    request.setRequestHeader('girder-token', getCookie('girderToken'));
                },
                contentType: "application/json; charset=utf-8",
                type: 'POST',
                cache: false,
                timeout: 500000,
                async: true,
                success: function(data) {
                    $el.toggleClass('active');
                    console.log('Skin Survey submitted.');
                }, error: function(jqXHR, textStatus, errorThrown) {
                    alert('error ' + textStatus + " " + errorThrown);
                }
            });
        }
    },

    cancelDrawMode() {
        this.drawElement(undefined, null);
        this.viewer.annotationLayer._boundHistomicsTKModeChange = false;
        this.viewer.annotationLayer.geoOff(window.geo.event.annotation.state);
        this.$('button.h-pan').addClass('active');
    },

    drawingType() {
        return this._drawingType;
    },

    _onKeyDown(evt) {
        if (evt.key === 'd') {
            if (this.$('.h-draw.active[data-type="line"]')) {
                this.drawElement(undefined, 'line');
            } else {
                this.cancelDrawMode();
            }
        }
    },

    /**
     * Get the element id from a click event.
     */
    _getId(evt) {
        return this.$(evt.currentTarget).parent('.h-element').data('id');
    },

    _setStyleGroup() {
        this._style.set(
            this._groups.get(this.$('.h-style-group').val()).toJSON()
        );
        if (!this._style.get('group') && this._style.id !== 'default') {
            this._style.set('group', this._style.id);
        }
    },

    _styleGroupEditor() {
        var dlg = editStyleGroups(this._style, this._groups);
        dlg.$el.on('hidden.bs.modal', () => {
            this.render();
            this.parentView.trigger('h:styleGroupsEdited', this._groups);
        });
    },

    _highlightElement(evt) {
        const id = $(evt.currentTarget).data('id');
        this.parentView.trigger('h:highlightAnnotation', this.annotation.id, id);
    },

    _unhighlightElement() {
        this.parentView.trigger('h:highlightAnnotation');
    },

    _recalculateGroupAggregation() {
        const groups = _.invoke(
            this.collection.filter((el) => el.get('group')),
            'get', 'group'
        );
        this.annotation.set('groups', groups);
    }
});

export default DrawWidget;
