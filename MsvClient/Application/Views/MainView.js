var LightStick = LightStick || {};

LightStick.MainView = Backbone.View.extend({
    template: "",

    initialize: function() {
        this.commandModel = new LightStick.CommandModel();
        this.initEvents();
        this.startUpdateTimer();

        this.showFrames = null;

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
        this.showFrames = this.commandModel.get("FRAME_LIST");
        var message = this.commandModel.get("data");

        this.playback.setNewSceneShow(message);
    },

    render: function() {
       //this.$el.html("<h1>Render OK</h1>");
       return this;
    }
});


LightStick.PlayBack = function() {
    this.init = function(readyCB, $el)  {
        this.updatesPerBeat = 64;

        this.$el = $el;
        this.playbackTimer = null;
        this.initPlaybackTimer(readyCB, this.updatesPerBeat);

        this.showFrames = null;
        this.currentFrame = null;
        this.msvTime = 0.0;

        this.nextSceneShow = null;

        this.initEffects();
    };

    this.initEffects = function() {
        // Effects
        this.beatTextEffect = new LightStick.BeatTextEffect(this.$el);
        this.colorEffect = new LightStick.ColorEffect(this.$el, this.updatesPerBeat);
        //this.strobeEffect = new LightStick.StrobeEffect(this.$el, this.updatesPerBeat)
    };

    this.initPlaybackTimer = function(readyCB, updatesPerBeat) {
        this.playbackTimer = new LightStick.PlayBackTimer(updatesPerBeat);

        var that = this;
        this.playbackTimer.init(function() {
            that.playbackTimerReadyCallback();
            readyCB();
        });
    };

    this.playbackTimerReadyCallback = function() {
        var that = this;
        this.playbackTimer.addIntervalUpdateCallback(function(currentTime, msvTime, isReset){
            that.updateCallback(currentTime, msvTime, isReset);
        });
        this.playbackTimer.start();
    };

    this.updateCallback = function(currentTime, msvTime, isReset) {
        this.$el.find("#msv").html(currentTime.toFixed(2) + " beats");

        this.msvTime = msvTime;

        var frame = this.getCurrentFrame(currentTime);
        var currentFrameTime = frame.currentFrameTime;

        if (frame !== this.currentFrame || isReset){
            this.onFrameChange(frame);
        }

        if (this.nextSceneShow != null) {
            this.setNewSceneShow(this.nextSceneShow);
        }

        this.colorEffect.onUpdate(currentFrameTime);
    };

    this.onFrameChange = function(frame) {
        this.currentFrame = frame;

        var sceneTime = frame["SCENE_TIME"];
        var fadeTime = frame["FADE_TIME"];

        var that = this;

        // TODO Refactor to set each effect
        _.each(this.currentFrame["EFFECTS"], function(effect) {
            var fxName = effect["FX_NAME"];

            // COLOR EFFECT
            if (fxName == "COLOR") {
                that.colorEffect.setNewColor(effect, sceneTime, fadeTime);
            }

            // TEXT EFFECT
            if (fxName == "TEXT") {
                that.beatTextEffect.setText(effect);
            } else {
                that.beatTextEffect.clearEffect();
            }

            // TODO STROBE EFFECT
        });
    };

    this.setNewSceneShow = function(sceneShow) {
        var showStartTime = sceneShow["MSV_TIME"];

        if (showStartTime < this.msvTime) {
            this.nextSceneShow = null;
            this.triggerNewSceneShow(sceneShow);
        } else {
            this.nextSceneShow = sceneShow;
        }
    };

    this.triggerNewSceneShow = function(sceneShow) {
        this.showFrames = sceneShow["FRAME_LIST"];

        var showStartTime = sceneShow["MSV_TIME"];
        this.playbackTimer.setPlaybackStartTime(showStartTime);

        var showTime = this._calcTotalShowTime(sceneShow["FRAME_LIST"]);
        this.playbackTimer.setPlaybackLength(showTime);
    };

    this._calcTotalShowTime = function(show) {
        var showTime = 0.0;
        _.each(show, function(scene){
            showTime += scene["SCENE_TIME"];
        });
        return showTime;
    };

    this.getCurrentFrame = function(currentTime) {
        // TODO fix offset so do not need to iter trough prev frames if time is higher than before

        var frameShowTime = 0.0;

        return _.find(this.showFrames, function(scene){
            var currentFrameTime = currentTime - frameShowTime;
            frameShowTime += scene["SCENE_TIME"];
            if (frameShowTime > currentTime) {
                scene.currentFrameTime = currentFrameTime;
                return scene;
            }
        });
    };
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

    this.currentTime = 0.0;
    this.lastUpdateTime = new Date().getTime();

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
            //return (1.0 / (this.bpm) / 60.0) / this.updatesPerBeat;
            // TODO this one seems correct also fix this one in the playbackHandler.py
            return 60.0 * this.updatesPerBeat / this.bpm;
        }
        return 0.0
    };

    this.scheduleNextUpdate = function() {
        this.updateFromMsv();
        var currTime = new Date().getTime();

        var elapsed = ((currTime - this.lastUpdateTime) / 100);
        this.lastUpdateTime = currTime;
        //var interval = this.updateInterval - (elapsed - this.updateInterval);

        //if ((interval < 0.0) && (this.updateInterval > 0.0)) {
        //    console.log("WARNING TO FAST!!!, CANT MAKE ALL FRAMES");
        //    interval = 0.0;
        //}

        console.log(elapsed, 1.0/25);

        var that = this;
        if (this.updateInterval > 0.0) {
            this.timer = setTimeout(function() {
                that.scheduleNextUpdate();
            }, 1.0 / 25);
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
        var prevTime = this.currentTime;

        var timeAfterStart = this.msvPosition - this.playbackStartTime;
        this.currentTime = timeAfterStart % this.playbackLength;

        var timerReset = (prevTime > this.currentTime);

        var that = this;
        _.each(this.callbacks, function(callback) {
            callback(that.currentTime, that.msvPosition, timerReset);
        });
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


LightStick.StrobeEffect = function($el, updatesPerBeat) {
    this.$el = $el.find("#strobe");
    this.updatesPerBeat = updatesPerBeat;

    this.onUpdate = function(isWholeBeat) {
        if (isWholeBeat)
            this.flash();
    };

    this.flash = function() {
        this.$el.show();
        var that = this;
        setTimeout(function(){
            that.$el.hide();
        }, 10);
    };
};


// EFFECTS ! ! ! TODO extract to its own file
LightStick.BeatTextEffect = function($el) {
    this.$el = $el.find("#beat");

    this.setText = function(effect) {
        this.$el.text(effect["TEXT"]);
        this.$el.show();
    };

    this.clearEffect = function() {
        this.$el.text("")
    };

    this.flash = function() {
        this.$el.show();
        var that = this;
        setTimeout(function(){
            that.$el.hide();
        }, 100);
    }
};


LightStick.ColorEffect = function($el, updatesPerBeat)  {
    this.$el = $el.find("#color");
    this.fadeTime = 0.0;

    this.updatesPerBeat = updatesPerBeat;

    this.currRed = 0.0;
    this.currGreen = 0.0;
    this.currBlue = 0.0;

    this.setNewColor = function(colorEffect, sceneTime, FadeTime) {
        this.fadeTime = FadeTime;

        this.oldRed = this.currRed;
        this.oldGreen = this.currGreen;
        this.oldBlue = this.currBlue;

        var newColor = colorEffect["COLOR_HEX"];

        this.newRed = this.getRedFromHex(newColor);
        this.newGreen = this.getGreenFromHex(newColor);
        this.newBlue = this.getBlueFromHex(newColor);

        this.$el.find("#demo").text(this.numSteps);

        if (this.fadeTime == 0.0) {
            this.redColorDiff = 0.0;
            this.greenColorDiff = 0.0;
            this.blueColorDiff = 0.0;
            this.setScreenColor(this.newRed, this.newGreen, this.newBlue);

        } else {
            this.redColorDiff = (this.newRed - this.currRed);
            this.greenColorDiff = (this.newGreen - this.currGreen);
            this.blueColorDiff = (this.newBlue - this.currBlue);
        }
    };

    this.onUpdate = function(currentFrameTime) {
        if (currentFrameTime < this.fadeTime) {
            var currentFadePos = currentFrameTime / this.fadeTime;
            this.currRed = this.oldRed + this.redColorDiff * currentFadePos;
            this.currGreen = this.oldGreen + this.greenColorDiff * currentFadePos;
            this.currBlue = this.oldBlue + this.blueColorDiff * currentFadePos;
        } else {
            this.currRed = this.newRed;
            this.currGreen = this.newGreen;
            this.currBlue = this.newBlue;
        }
        this.setScreenColor(this.currRed, this.currGreen, this.currBlue);

        this.numSteps -= 1;
    };

    this.setScreenColor = function(r, g, b) {
        this.$el.css("background-color", this.toCssRGB(r, g, b));
    };

    this.getRedFromHex = function(color) {
        return parseInt("0x"+color.substr(1, 2));
    };

    this.getGreenFromHex = function(color) {
        return parseInt("0x"+color.substr(3, 2));
    };

    this.getBlueFromHex = function(color) {
        return parseInt("0x"+color.substr(5, 2));
    };

    this.toCssRGB = function(r, g, b) {
        return "rgb(" + parseInt(r) + ", " + parseInt(g) + ", " + parseInt(b) + ")";
    };

    this.fromCssRgb2Hex = function(rgb){
        rgb = rgb.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
        return "#" +
            ("0" + parseInt(rgb[1],10).toString(16)).slice(-2) +
            ("0" + parseInt(rgb[2],10).toString(16)).slice(-2) +
            ("0" + parseInt(rgb[3],10).toString(16)).slice(-2);
    }
};
