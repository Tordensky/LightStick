var LightStick = LightStick || {};

LightStick.Controller = {
    ds: null,

    load: function () {
        console.log('Setting up MSV');

        this.msv = MSV.msv("msv://mcorp.no:8091/18");
        this.msv.add_error_handler(this.msvErrorHandler);
        this.msv.add_ready_handler(this.msvReadyHandler);
    },

    msvErrorHandler: function () {
        alert("Failed to load MSV");
    },

    msvReadyHandler: function () {
        LightStick.Controller.setupMsvControllerBar();
        LightStick.Controller.ds = new TM.DataSet(
            "ds://mcorp.no:8080/2013",
            LightStick.Controller.msv, {
                tail: 300, head: 100, live_window: 1},
            null,
            LightStick.Controller.dsReadyHandler);
        setInterval(LightStick.Controller.updateLoop, 10);
    },

    setupMsvControllerBar: function () {
        var controllerBar = new TM.ControlBar(
            LightStick.Controller.msv,
            {
                play: function () {
                    console.log('play');
                    LightStick.Controller.msv.update(null, 1, null);
                },
                beginning: function () {
                    console.log('beginning');
                    LightStick.Controller.msv.update(0, 1, null);
                },
                pause: function () {
                    console.log('pause');
                    LightStick.Controller.msv.update(null, 0, null);
                }
                ,
                live: function () {
                    console.log('live');
                    var liveTime = (LightStick.Controller.ds.alive_at.getTime() +
                        (Math.abs(LightStick.Controller.ds.alive_at.getTimezoneOffset())*60000)) / 1000;
                    console.log(liveTime);
                    LightStick.Controller.msv.update(
                        50000.0, 1, null);
                }
            }
        );
        controllerBar.attach(
            $("#ctrl"),
            controllerBar.default_formatter,
            "Control",
            true
        );
    },

    dsUpdateHandler: function (newEntries) {
        console.log('num: ', _.size(newEntries));
        console.log(newEntries);
/*        _.each(newEntries, function (entry) {
            console.log('entry', entry);
        });*/
    },

    dsReadyHandler: function () {
        console.log("Ready!");
        LightStick.Controller.ds.addTimedHandler(
            LightStick.Controller.dsUpdateHandler);
    },

    updateLoop: function () {
        ;
    },

    post: function () {
        console.log("Hello button");
        var ts = Math.round(LightStick.Controller.msv.query()[MSV.P]);
        var msg = {'data' : 'Test Msg'};
        console.log(ts, msg);

        LightStick.Controller.ds.addAt(ts, JSON.stringify(msg), null, null, 1);
    }
};