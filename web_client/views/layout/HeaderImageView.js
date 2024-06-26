import { getCurrentUser } from 'girder/auth';
import { restRequest } from 'girder/rest';

import events from '../../events';
import router from '../../router';
import View from '../View';

import headerImageTemplate from '../../templates/layout/headerImage.pug';
import '../../stylesheets/layout/headerImage.styl';

var HeaderImageView = View.extend({
    events: {
        'click .h-open-image': function (evt) {
            events.trigger('h:openImageUi');
        },
        'click .h-open-annotated-image': function (evt) {
            events.trigger('h:openAnnotatedImageUi');
        },
        'click .h-open-help-modal': function (evt) {
            console.log('help modal trigger');
            events.trigger('h:openHelpModalUi');
        },
        'click [href*="https://redcap.vanderbilt.edu/surveys/?s=HH3D3PMNM8"]': '_alertBeforeFinishedAnnotatingBaseline',
        'click [href*="https://redcap.vanderbilt.edu/surveys/?s=RARCDR4N443KDYHR"]': '_alertBeforeFinishedAnnotatingRCT'
    },

    initialize() {
        this.imageModel = null;
        this.parentChain = null;
        this.listenTo(events, 'h:analysis:rendered', this.render);
        this.listenTo(events, 'h:imageOpened', (model) => {
            this.imageModel = model;
            this.parentChain = null;
            this._setNextPreviousImage();
            if (model) {
                this.imageModel.getRootPath((resp) => {
                    this.parentChain = resp;
                    this.render();
                });
            }
            this.render();
        });
    },

    render() {
        const user = getCurrentUser();
        const cgvhdGroupId = '5f0dc554c9f8c18253ae949d';
        const baselineGroupId = '5f0dc532c9f8c18253ae949c';
        let firstFolder;
        if (user.attributes.groups.indexOf(cgvhdGroupId) >= 0) {
            firstFolder = '5f0dc449c9f8c18253ae949a';
        } else if (user.attributes.groups.indexOf(baselineGroupId) >= 0) {
            firstFolder = '5f0dc45cc9f8c18253ae949b';
        }
        const analysis = router.getQuery('analysis') ? `&analysis=${router.getQuery('analysis')}` : '';
        const folder = router.getQuery('folder') ? `&folder=${router.getQuery('folder')}` : `&folder=${firstFolder}`;
        const folderId = router.getQuery('folder') || firstFolder;
        let nextImageLink = this._nextImage;
        if (this._nextImage && this._nextImage.indexOf('https://') < 0) {
            nextImageLink = this._nextImage ? `#?image=${this._nextImage}${analysis}` : null;
        }
        const previousImageLink = this._previousImage ? `#?image=${this._previousImage}${analysis}` : null;
        if (typeof firstFolder !== 'undefined') {
            restRequest({
                url: `item/${folderId}/first_image?folder=${folderId}`
            }).done((first) => {
                this._firstImage = first._id;
                this._firstFolder = typeof first !== 'undefined' && typeof first.folderId !== 'undefined'  ? '&folder=' + first.folderId : folder;
                var firstImageLink = null;
                if (router.getQuery('image') != this._firstImage) {
                    firstImageLink = this._firstImage ? `#?image=${this._firstImage}${this._firstFolder}` : `#?image=${firstImage}&folder=$(firstFolder)`;
                }
                this.$el.html(headerImageTemplate({
                    image: this.imageModel,
                    parentChain: this.parentChain,
                    nextImageLink: nextImageLink,
                    previousImageLink: previousImageLink,
                    firstImageLink: firstImageLink
                }));
            });
        }
        return this;
    },

    _alertBeforeFinishedAnnotatingBaseline(evt) {
        this._alertBeforeFinishedAnnotating('baseline', evt);
    },

    _alertBeforeFinishedAnnotatingRCT(evt) {
        this._alertBeforeFinishedAnnotating('rct', evt);
    },

    _alertBeforeFinishedAnnotating(groupName, evt) {
        const cont = confirm("You've completed the " + groupName + " entries. To make changes, " +
                             "select cancel and navigate back to the images you would like to review. " +
                             "To proceed, select Go to survey and complete the experience survey.");
        if (cont) {
            this.writeAnnotatorImageMetadata();
            var item = $.ajax({
                url: '/api/v1/item/SkinStudy%40vumc.org/' + groupName + '/notify_completion',
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
                timeout: 2000,
                success: function(data) {
                    console.log('emailed');
                }, error: function(jqXHR, textStatus, errorThrown) {
                    console.log('failed email notification');
                }
            });
        } else {
            evt.preventDefault();
        }
    },

    _setNextPreviousImage() {
        const model = this.imageModel;
        const folder = router.getQuery('folder') ? `?folderId=${router.getQuery('folder')}` : '';
        const folderId = router.getQuery('folder') || '5f0dc45cc9f8c18253ae949b';
        const user = getCurrentUser();
        const cgvhdGroupId = '5f0dc554c9f8c18253ae949d';
        const baselineGroupId = '5f0dc532c9f8c18253ae949c';
        console.log('router query string' + router.getQuery('folder'));
        if (!model) {
            this._nextImage = null;
            this._previousImage = null;
            this._firstImage = null;
            this.render();
            return;
        }

        $.when(
            function() {
                if (user.attributes.groups.indexOf(cgvhdGroupId) >= 0 || user.attributes.groups.indexOf(baselineGroupId) >= 0) {
                    console.log('inside when');
                    restRequest({
                        url: `item/${folderId}/first_image${folder}`
                    }).done((first) => {
                        this._firstImage = (first._id !== model.id) ? first._id : null;
                    })
                }
            },
            restRequest({
                url: `item/${model.id}/previous_image${folder}`
            }).done((previous) => {
                this._previousImage = (previous._id !== model.id) ? previous._id : null;
            }),
            restRequest({
                url: `item/${model.id}/next_image${folder}`
            }).done((next) => {
                this._nextImage = (next._id !== model.id) ? next._id : null;
                // if (next._id == '5d9f9829e6291400c45dbbe1') {
                //     this.nextImage = 'https://redcap.vanderbilt.edu/surveys/?s=HH3D3PMNM8';
                // }
            })
        ).done(() => this.render());
    }
});

export default HeaderImageView;
