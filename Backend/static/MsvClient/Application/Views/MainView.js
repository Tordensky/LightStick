var LightStick = LightStick || {};

LightStick.MainView = Backbone.View.extend({
    template: "",

    initialize: function() {
        this.commandModel = new LightStick.CommandModel();
        this.initEvents();
        this.startUpdateTimer();

        this.frameList = null;

        this.playback = null;
        this.initPlayback();

        // HANDLE INCOMING NOTIFICATIONS OF NEW SHOWS
        this.pullNotificationMsv = new LightStick.MsvClient(22, "msv://t0.mcorp.no:8091/");
        var that = this;
        this.pullNotificationMsv.init(function() {
            that.pullMsvReady()
        });

        // GENERATE UNIQUE ID FOR USER
        this.myID = null;
        var cookie = $.cookie('my_id');
        if (cookie == undefined) {
            this.myID = uuid.v4();
            $.cookie('my_id', String(this.myID), {expires: 365, path: "/"});
        } else {
            this.myID = $.cookie('my_id');
        }
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

    pullMsvReady: function() {
        var that = this;
        this.pullNotificationMsv.add_update_handler(function(){
            that.updateModels();
            console.log("NOTIFICATION OF NEW SHOW");
        });
    },

    playbackReadyCallback: function() {
        console.log("Playback ready")
    },

    updateModels: function () {
        this.commandModel.fetch({data: {id: this.myID}});
    },

    startUpdateTimer: function() {
        var heartbeatLongPollTime = 10000;

        var that = this;
        setInterval(function(){
            that.updateModels();
        }, heartbeatLongPollTime);
    },

    handleCommand: function() {
        this.frameList = this.commandModel.get("FRAME_LIST");
        var message = this.commandModel.get("data");
        this.playback.setNewSceneShow(message);
    },

    render: function() {
       // RENDER FUNCTION FOR BACKBONE VIEW
       return this;
    }
});


LightStick.PlayBack = function() {
    this.init = function(readyCB, $el)  {
        this.$el = $el;
        this.playbackTimer = null;
        this.initPlaybackTimer(readyCB, this.updatesPerBeat);

        this.frameList = null;
        this.currentFrame = null;
        this.msvTime = 0.0;

        this.nextShow = null;

        this.initEffects();
    };

    this.initEffects = function() {
        this.beatTextEffect = new LightStick.BeatTextEffect(this.$el);
        this.colorEffect = new LightStick.ColorEffect(this.$el, this.updatesPerBeat);
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
        var currentFrameTime;
        var frame = this.getCurrentFrame(currentTime);

        if (this.nextShow != null) {
            this.setNewSceneShow(this.nextShow);
        }

        try {
            currentFrameTime = frame.currentFrameTime;
            if (frame !== this.currentFrame || isReset){
                this.onFrameChange(frame);
            }
            this.colorEffect.onUpdate(currentFrameTime);

        } catch (TypeError) {
            console.log("No frame");
        }
    };

    this.onFrameChange = function(frame) {
        this.currentFrame = frame;

        var fadeTime = frame["FADE_TIME"];

        // SET COLOR EFFECT
        var newColorEffect = _.findWhere(this.currentFrame["EFFECTS"], {FX_NAME: "COLOR"});
        if (newColorEffect != undefined) {
            this.colorEffect.setNewColor(newColorEffect, fadeTime);
        } else {
            this.colorEffect.clearColorEffect();
        }

        // SET TEXT EFFECT
        var newTextEffect = _.findWhere(this.currentFrame["EFFECTS"], {FX_NAME: "TEXT"});
        if (newTextEffect != undefined) {
            this.beatTextEffect.setText(newTextEffect);
        } else {
            this.beatTextEffect.clearEffect();
        }
    };

    this.setNewSceneShow = function(sceneShow) {
        var showStartTime = sceneShow["MSV_TIME"];

        // TRIGGER NEW SCENE SHOW
        if (showStartTime < this.msvTime) {
            this.nextShow = null;
            this.triggerNewShow(sceneShow);

        // WAIT FOR START TIME TO TRIGGER SHOW
        } else {
            this.nextShow = sceneShow;
        }
    };

    this.triggerNewShow = function(sceneShow) {
        this.frameList = sceneShow["FRAME_LIST"];

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
        var frameShowTime = 0.0;

        return _.find(this.frameList, function(scene){
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
    this.updatesPerBeat = 1.0 / (typeof updatesPerBeat !== 'undefined' ? updatesPerBeat : 10);

    this.timer = null;
    this.msvPosition = 0.0;

    this.currentTime = 0.0;
    this.playbackStartTime = 0.0;
    this.playbackLength = 0.0;

    this.callbacks = [];

    this.FPS = 24.0;

    this.init = function(readyCallback) {
        this.msvClient = new LightStick.MsvClient(18, "msv://t0.mcorp.no:8091/");

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
        this.msvPosition = this.msvClient.getCurrentMsvTime();
    };

    this.addIntervalUpdateCallback = function(callback) {
        this.callbacks.push(callback);
    };

    this.start = function() {
        this.scheduleNextUpdate();
    };

    this.stop = function() {
        this.unScheduleNextUpdate();
    };

    this.scheduleNextUpdate = function() {
        this.onUpdate();

        var that = this;
        this.timer = setTimeout(function() {
            that.scheduleNextUpdate();
        }, 1000.0 / this.FPS);
    };

    this.unScheduleNextUpdate = function() {
        if (this.timer != null) {
            clearTimeout(this.timer);
        }
    };

    this.onUpdate = function() {
        this.updateFromMsv();
        var prevTime = this.currentTime;

        var timeAfterStart = this.msvPosition - this.playbackStartTime;
        this.currentTime = timeAfterStart % this.playbackLength;

        var timerReset = (prevTime > this.currentTime);

        var that = this;
        _.each(that.callbacks, function(callback) {
            callback(that.currentTime, that.msvPosition, timerReset);
        });
    };
};


LightStick.MsvClient = function(id, host) {
    this.msv = null;
    this.id = id;
    this.host = host;

    this.init = function (msvReadyCallback) {
        this.msv = MSV.msv(this.host+ this.id);

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

    this.add_update_handler = function (callback){
        this.msv.add_update_handler(callback);
    };

    this.msvErrorHandler = function ()  {
        alert("Failed to load MSV");
    };

    this.msvReadyHandler = function () {
        console.log('MSV ready:');
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


// EFFECTS ! ! !
LightStick.BeatTextEffect = function($el) {
    this.$el = $el.find("#text");
    this.$holder = $el;

    this.setText = function(effect) {
        var text = effect["TEXT"];
        this.$el.text(text);

        this.$el.fitText(Math.min(0.1 * text.length, 0.5), {maxFontSize: this.$holder.height()});

        this.$el.position({
            my: "center center",
            at: "center center",
            of: this.$holder
        });
        this.$el.show();
    };

    this.clearEffect = function() {
        this.$el.text("");
    };
};


LightStick.ColorEffect = function($el, updatesPerBeat)  {
    this.$el = $el.find("#color");
    this.fadeTime = 0.0;

    this.updatesPerBeat = updatesPerBeat;

    this.currRed = 0.0;
    this.currGreen = 0.0;
    this.currBlue = 0.0;

    this.glowMax = 0.0;
    this.glowMin = 0.0;
    this.interval = 0.0;


    var offsets = [0.0, 0.25, 0.5, 0.75];
    this.glowOffset = offsets[Math.floor(Math.random() * offsets.length)];
    console.log("glowOffset: ", this.glowOffset);

    this.clearColorEffect = function(){
        this.setNewColor({GLOW_MAX: 100, GLOW_MIN: 0, GLOW_INT: 0, COLOR_HEX: "#000000", GLOW_OFFSET: false}, 0)
    };

    this.setNewColor = function(colorEffect, FadeTime) {
        this.glowMax = colorEffect["GLOW_MAX"];
        this.glowMin = colorEffect["GLOW_MIN"];
        this.interval = colorEffect["GLOW_INT"];
        this.offsetGlow = colorEffect["GLOW_OFFSET"];

        this.fadeTime = FadeTime;

        this.oldRed = this.currRed;
        this.oldGreen = this.currGreen;
        this.oldBlue = this.currBlue;

        var newColor = colorEffect["COLOR_HEX"];

        this.newRed = this.getRedFromHex(newColor);
        this.newGreen = this.getGreenFromHex(newColor);
        this.newBlue = this.getBlueFromHex(newColor);

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
        this.intensityUpdate(currentFrameTime);
        var r, g, b;
        if (currentFrameTime < this.fadeTime) {
            var currentFadePos = currentFrameTime / this.fadeTime;
            r = this.oldRed + this.redColorDiff * currentFadePos;
            g = this.oldGreen + this.greenColorDiff * currentFadePos;
            b = this.oldBlue + this.blueColorDiff * currentFadePos;
        } else {
            r = this.newRed;
            g = this.newGreen;
            b = this.newBlue;
        }
        this.setScreenColor(r, g, b);
    };

    this.intensityUpdate = function(currentFrameTime){
        if (this.interval > 0.0) {
            // ADD GLOW OFFSET
            if (this.offsetGlow){
                currentFrameTime += this.interval * this.glowOffset;
            }

            var pos = (currentFrameTime % this.interval) / (this.interval / 2.0);
            if (pos > 1.0) {
                pos = 2.0 - pos;
            }
            this.intensity = this.glowMin + (this.glowMax - this.glowMin) * pos;
        } else {
            this.intensity = this.glowMax;
        }
    };

    this.setScreenColor = function(r, g, b) {
        this.currRed = r;
        this.currGreen = g;
        this.currBlue = b;
        this.$el.css("background-color", this.toCssRGB(r*this.intensity, g*this.intensity, b*this.intensity));
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
