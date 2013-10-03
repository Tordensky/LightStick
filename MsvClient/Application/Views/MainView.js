var LightStick = LightStick || {};

LightStick.MainView = Backbone.View.extend({
    template: "",

    initialize: function() {
        this.commandModel = new LightStick.CommandModel();
        this.initEvents();
        this.startUpdateTimer();

        this.show = null;

        this.playbackHandler = null;
        this.initPlayBackHandler();
    },

    initEvents: function() {
        this.commandModel.on("change:cmdNum", this.handleCommand, this);
    },

    initPlayBackHandler: function() {
        this.playbackHandler = new LightStick.PlayBackHandler();

        var that = this;
        this.playbackHandler.init(function() {
            that.playbackReadyCallback();
        });
    },

    playbackReadyCallback: function() {
        var that = this;
        this.playbackHandler.addIntervalUpdateCallback(function(currentTime){
            that.updateCallback(currentTime);
        });
        this.playbackHandler.start();
    },

    updateCallback: function(currentTime) {
        this.$el.find("#msv").html(currentTime);
    },

    updateModels: function () {
        this.commandModel.fetch();
    },

    startUpdateTimer: function() {
        var that = this;
        setInterval(function(){
            that.updateModels();
        }, 2000);
    },

    handleCommand: function() {
        this.show = this.commandModel.get("FRAME_LIST");
        var startTime = this.commandModel.get("MSV_TIME");
        this.playbackHandler.setPlaybackStartTime(startTime);
    },

    render: function() {
       //this.$el.html("<h1>Render OK</h1>");
       return this;
    },

    setScreenColor: function(color) {
        this.$el.css("background-color", color);
    }
});


LightStick.PlayBackHandler = function(updatesPerBeat) {
    this.bpm = 60.0;
    this.updatesPerBeat = 1.0 / (typeof updatesPerBeat !== 'undefined' ? updatesPerBeat : 40);

    this.msvPosition = 0.0;
    this.updateInterval = 0.0;
    this.timer = null;

    this.playbackStartTime = 0.0;
    this.playbackLength = 10.0;

    this.callbacks = [];

    this.init = function(readyCallback) {
        this.msvClient = new LightStick.MsvClient();

        var that = this;
        this.msvClient.init(function() {
            that.onMsvReady();
            readyCallback();
        });
    };

    this.setPlaybackStartTime = function(startTime) {
        this.playbackStartTime = startTime;
    }

    this.onMsvReady = function() {
        this.updateFromMsv();
    };

    this.updateFromMsv = function() {
        this.bpm = 60.0 * this.msvClient.getCurrentMsvVelocity();
        this.msvPosition = this.msvClient.getCurrentMsvTime();

        this.updateInterval = this.getIntervalTime();
    };

    this.addIntervalUpdateCallback = function(callback) {
        this.callbacks.push(callback);
    };

    this.start = function() {
        this.scheduleNextUpdate();
    };

    // should not be used
    this.stop = function() {
        this.unScheduleNextUpdate();
    };

    this.getIntervalTime = function() {
        if (this.bpm > 0.0) {
            return 60.0 * this.updatesPerBeat / this.bpm;
        }
        return 0.0
    };

    this.scheduleNextUpdate = function() {
        this.updateFromMsv();
        var that = this;
        if (this.updateInterval > 0.0) {
            // SHOW IS RUNNING
            this.timer = setTimeout(function() {
                that.onUpdate();
            }, this.updateInterval * 1000);
        } else {
            // BPM IS ZERO AND THE SHOW IS PAUSED, CHECK FOR UPDATES IN BPM each 100ms
            setTimeout(function() {
                that.scheduleNextUpdate();
            }, 100);
        }
    };

    this.unScheduleNextUpdate = function() {
        if (this.timer != null) {
            clearTimeout(this.timer);
        }
    };

    this.onUpdate = function() {
        var timeAfterStart = this.msvPosition - this.playbackStartTime;
        var currentTime = timeAfterStart % this.playbackLength;
        _.each(this.callbacks, function(callback) {
            callback(currentTime);
        });
        this.scheduleNextUpdate();
    };
};


LightStick.MsvClient = function() {
    this.ds = null;
    this.msv = null;

    this.init = function (msvReadyCallback) {
        this.msv = MSV.msv("msv://mcorp.no:8091/18");

        var that = this;
        this.msv.add_error_handler(
            function(){
                that.msvErrorHandler();
            });

        this.msv.add_ready_handler(
            function(){
                msvReadyCallback();
                that.msvReadyHandler();
            });
    };

    this.msvErrorHandler = function ()  {
        alert("Failed to load MSV");
    };

    this.msvReadyHandler = function () {
        //console.log('MSV ready: ', this.getCurrentMsvTime());
    };

    this.getCurrentMsvTime = function () {
        return this.msv.query()[MSV.P];
    };

    this.getCurrentMsvVelocity = function () {
        return this.msv.query()[MSV.V];
    };

    this.getCurrentMsvAcceleration = function () {
        return this.msv.query()[MSV.A];
    };
};
