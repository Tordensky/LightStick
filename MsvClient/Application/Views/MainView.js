var LightStick = LightStick || {};

LightStick.MainView = Backbone.View.extend({
    template: "",

    initialize: function() {
        this.commandModel = new LightStick.CommandModel();
        this.initEvents();
        this.startUpdateTimer();
    },

    initEvents: function() {
        this.commandModel.on("change:cmdNum", this.handleCommand, this);
    },

    updateModels: function () {
        this.commandModel.fetch();
    },

    startUpdateTimer: function() {
        var that = this;
        setInterval(function(){
            that.updateModels();
        }, 500);
    },

    handleCommand: function() {
        console.log(this.commandModel.get("command")["color"]);
        this.$el.css("background-color", this.commandModel.get("command")["color"]);

    },

    render: function() {
       this.$el.html("<h1>Render OK</h1>");
       return this;
    }
});
