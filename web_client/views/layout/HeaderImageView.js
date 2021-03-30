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
        'click [href="https://redcap.vanderbilt.edu/surveys/?s=HH3D3PMNM8"]': function (evt) {
            if (!confirm("You've completed the baseline entries. To make changes, select 'Cancel' and navigate back to the images you would like to review. To proceed, select 'Ok' and complete the experience survey.")) {
                evt.preventDefault();
            }
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
	console.log('HeaderImageView render -->');			
        const analysis = router.getQuery('analysis') ? `&analysis=${router.getQuery('analysis')}` : '';
        const folder = router.getQuery('folder') ? `&folder=${router.getQuery('folder')}` : '&folder=5f0dc45cc9f8c18253ae949b';
        const folderId = router.getQuery('folder') || '5f0dc45cc9f8c18253ae949b';
        let nextImageLink = this._nextImage;
        if (this._nextImage && this._nextImage.indexOf('https://') < 0) {
            nextImageLink = this._nextImage ? `#?image=${this._nextImage}${folder}${analysis}` : null;
        }
        const previousImageLink = this._previousImage ? `#?image=${this._previousImage}${folder}${analysis}` : null;
        console.log(this._firstImage);
        console.log('HeaderImageView.js, debug: Should have been first image!');
        restRequest({
            url: `item/${folderId}/first_image?folder=${folderId}`
        }).done((first) => {
            this._firstImage = first._id;
            const firstImageLink = this._firstImage ? `#?image=${this._firstImage}${folder}` : '#?image=5f0f2da097cefa564329547b&folder=5f0dc45cc9f8c18253ae949b';
            this.$el.html(headerImageTemplate({
                image: this.imageModel,
                parentChain: this.parentChain,
                nextImageLink: nextImageLink,
                previousImageLink: previousImageLink,
                firstImageLink: firstImageLink
            }));
        })
	console.log('HeaderImageView render <--');				
        return this;
    },

    _setNextPreviousImage() {
        const model = this.imageModel;
        const folder = router.getQuery('folder') ? `?folderId=${router.getQuery('folder')}` : '';
        const folderId = router.getQuery('folder') || '5f0dc45cc9f8c18253ae949b';
        if (!model) {
            console.log('HeaderImageView.js: No model!');
            this._nextImage = null;
            this._previousImage = null;
            this._firstImage = null;
            this.render();
            return;
        }

        $.when(
            restRequest({
                url: `item/${folderId}/first_image${folder}`
            }).done((first) => {
                this._firstImage = (first._id !== model.id) ? first._id : null;
                console.log('HeaderImageView.js, Debug: FIRST!!!!11!!!');
                console.log(first);
            }),
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
