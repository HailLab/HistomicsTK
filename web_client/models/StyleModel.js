import Backbone from 'backbone';

const StyleModel = Backbone.Model.extend({
    defaults: {
        lineWidth: 2,
        lineColor: 'rgba(0,212,186,0.82)',
        fillColor: 'rgba(74,204,181,0.29)',
        closed: true
    }
});

export default StyleModel;
