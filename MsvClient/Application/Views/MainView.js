var LightStick = LightStick || {};

LightStick.MainView = Backbone.View.extend({
    initialize: function() {
        this.el = this.options.el;
        console.log("View", this.el);
    },

    render: function() {
        console.log("Call render in main view");
    }
});
