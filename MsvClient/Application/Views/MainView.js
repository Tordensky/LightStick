var LightStick = LightStick || {};

LightStick.MainView = Backbone.View.extend({
    template: "",

    initialize: function() {
        this.commandModel = new LightStick.CommandModel();
        this.initEvents();
        this.startUpdateTimer();

        this.show = null;

        this.playback = null;
        this.initPlayback();
    },

    initEvents: function() {
        this.commandModel.on("change:cmdNum", this.handleCommand, this);
    },

    initPlayback: function() {
        this.playback = new LightStick.PlayBack();

        var that = this;
        this.playback.init(function() {
            that.playbackReadyCallback();
        }, this.$el);
    },

    playbackReadyCallback: function() {
        console.log("Playback ready")
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
        var message = this.commandModel.get("data");

        this.playback.setNewSceneShow(message);
        //this.playbackHandler.setPlaybackStartTime(startTime);
    },

    render: function() {
       //this.$el.html("<h1>Render OK</h1>");
       return this;
    },

    setScreenColor: function(color) {
        this.$el.css("background-color", color);
    }
});


LightStick.PlayBack = function() {
    this.init = function(readyCB, $el)  {
        this.$el = $el;
        this.playbackTimer = null;
        this.initPlaybackTimer(readyCB);

        this.beatText = new LightStick.BeatTextTest(this.$el);
    };

    this.initPlaybackTimer = function(readyCB) {
        this.playbackTimer = new LightStick.PlayBackTimer(50);

        var that = this;
        this.playbackTimer.init(function() {
            that.playbackTimerReadyCallback();
            readyCB();
        });
    };

    this.playbackTimerReadyCallback = function() {
        var that = this;
        this.playbackTimer.addIntervalUpdateCallback(function(currentTime, isWholeBeat){
            that.updateCallback(currentTime, isWholeBeat);
        });
        this.playbackTimer.start();
    };

    this.updateCallback = function(currentTime, isWholeBeat) {
        this.$el.find("#msv").html(currentTime.toFixed(2) + " beats, " + isWholeBeat);

        if (isWholeBeat) {
            this.beatText.flash();
        }
    };

    this.setNewSceneShow = function(sceneShow) {
        console.log("showData", sceneShow);

        this.playbackTimer.setPlaybackStartTime(sceneShow["MSV_TIME"]);
        var showTime = this._calcTotalShowTime(sceneShow["FRAME_LIST"]);
        this.playbackTimer.setPlaybackLength(showTime);
    };

    this._calcTotalShowTime = function(show) {
        var showTime = 0.0;
        _.each(show, function(scene){
            showTime += scene["SCENE_TIME"];
        });
        return showTime;
    }
};

LightStick.BeatTextTest = function($el) {
    this.$el = $el;
    this.flash = function() {
        this.$el.find("#beat").show();
        var that = this;
        setInterval(function(){
            that.$el.find("#beat").hide();
        }, 500);
    }
};

LightStick.PlayBackTimer = function(updatesPerBeat) {
    this.bpm = 60.0;
    this.updatesPerBeat = 1.0 / (typeof updatesPerBeat !== 'undefined' ? updatesPerBeat : 10);

    this.msvPosition = 0.0;
    this.updateInterval = 0.0;
    this.timer = null;

    this.playbackStartTime = 0.0;
    this.playbackLength = 0.0;

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
    };

    this.setPlaybackLength = function(showLength) {
        this.playbackLength = showLength;
    };

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
            this.timer = setTimeout(function() {
                that.scheduleNextUpdate();
            }, this.updateInterval * 1000);
            // SHOW IS RUNNING
            this.onUpdate();
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
        var isWholeBeat = this.isWholeBeat(currentTime);
        _.each(this.callbacks, function(callback) {
            callback(currentTime, isWholeBeat);
        });
    };

    this.isWholeBeat = function(currentTime) {
        var tmpTime = Math.floor(currentTime);
        var beatPos = currentTime - tmpTime;

        if (tmpTime != this.lastTime) {
            if ((beatPos < 0.05)) {
                return true;
            }
        }
        this.lastTime = tmpTime;
        return false;
    }
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
