import View from 'girder/views/View';

export default View.extend({
    writeAnnotatorImageMetadata() {
        if (TimeMe.getTimeOnCurrentPageInSeconds() > 6) {
            if ('activeAnnotation' in this && 'attributes' in this.activeAnnotation && this.activeAnnotation.attributes.annotation.name) {
                const anno = this.activeAnnotation.attributes.annotation.name;
                // Seems to set even bedore navigating away if you move window to background 
                var data = {};
                if (typeof this.model.attributes.meta !== 'undefined' && ('time-' + anno) in this.model.attributes.meta && this.model.attributes.meta['time-' + anno]) {
                    data["time-" + anno] = TimeMe.getTimeOnCurrentPageInSeconds() + parseFloat(this.model.attributes.meta['time-' + anno]);
                } else {
                    data["time-" + anno] = TimeMe.getTimeOnCurrentPageInSeconds();
                }
                if (typeof this.model.attributes.meta !== 'undefined') {
                    data['zoom-' + anno] = this.model.attributes.meta['zoom-' + anno];
                }
                if (typeof this.model.attributes.meta !== 'undefined' && ('device-' + anno) in this.model.attributes.meta && this.model.attributes.meta['device-' + anno]) {
                    data['device-' + anno] = this.model.attributes.meta['device-' + anno];
                } else if (typeof this.model.attributes.meta !== 'undefined') {
                    data['device-' + anno] = WURFL.complete_device_name;
                }
                if (typeof this.model.attributes.meta !== 'undefined' && ('mobile-' + anno) in this.model.attributes.meta && this.model.attributes.meta['mobile-' + anno]) {
                    data['mobile-' + anno] = this.model.attributes.meta['mobile-' + anno];
                } else if (typeof this.model.attributes.meta !== 'undefined') {
                    data['mobile-' + anno] = WURFL.is_mobile;
                }
                if (typeof this.model.attributes.meta !== 'undefined' && ('formfactor-' + anno) in this.model.attributes.meta && this.model.attributes.meta['formfactor-' + anno]) {
                    data['formfactor-' + anno] = this.model.attributes.meta['formfactor-' + anno];
                } else if (typeof this.model.attributes.meta !== 'undefined') {
                    data['formfactor-' + anno] = WURFL.form_factor;
                }

                var item = $.ajax({
                    url: '/api/v1/item/' + this.model.attributes._id + '/metadata',
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
                        console.log('ImageView.js', data);
                    }, error: function(jqXHR, textStatus, errorThrown) {
                        alert('error ' + textStatus + " " + errorThrown);
                    }
                });
            }
        }
    }
});
