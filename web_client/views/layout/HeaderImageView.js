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
        }
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
        const analysis = router.getQuery('analysis') ? `&analysis=${router.getQuery('analysis')}` : '';
        const folder = router.getQuery('folder') ? `&folder=${router.getQuery('folder')}` : '&folder=5e471b311c7080564deb44fa';
        let nextImageLink = this._nextImage;
        if (this._nextImage && this._nextImage.indexOf('https://') < 0) {
            nextImageLink = this._nextImage ? `#?image=${this._nextImage}${folder}${analysis}` : null;
        }
        const previousImageLink = this._previousImage ? `#?image=${this._previousImage}${folder}${analysis}` : null;
        console.log('headerImage');
        console.log(folder);
        console.log(nextImageLink);
        this.$el.html(headerImageTemplate({
            image: this.imageModel,
            parentChain: this.parentChain,
            nextImageLink: nextImageLink,
            previousImageLink: previousImageLink
        }));
        return this;
    },

    _setNextPreviousImage() {
        const model = this.imageModel;
        const folder = router.getQuery('folder') ? `?folderId=${router.getQuery('folder')}` : '';
        if (!model) {
            this._nextImage = null;
            this._previousImage = null;
            this.render();
            return;
        }

        $.when(
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
