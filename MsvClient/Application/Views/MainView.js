var LightStick = LightStick || {};

LightStick.MainView = Backbone.View.extend({
    template: "",

    initialize: function() {

    },

    render: function() {
       this.$el.html("<h1>Render OK</h1>");
       return this;
    }
});
