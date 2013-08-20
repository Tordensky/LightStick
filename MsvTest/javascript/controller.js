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
        console.log('MSV ready');
        LightStick.Controller.setupMsvControllerBar();
        LightStick.Controller.ds = new TM.DataSet(
            "ds://mcorp.no:8080/2013",
            LightStick.Controller.msv, {
                tail: 10, head: 10, live_window: 1},
            null,
            LightStick.Controller.dsReadyHandler);
        setInterval(LightStick.Controller.updateLoop, 10);
    },

    setupMsvControllerBar: function () {
        console.log("test", LightStick.Controller.msv);
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
                },
                live: function () {
                    console.log('live');
                    LightStick.Controller.msv.update(
                        LightStick.Controller.msv.query()[3], 1, null);
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
        console.log('Updates from ds', newEntries);
    },

    dsReadyHandler: function () {
        console.log("DS READY. . .");
        LightStick.Controller.ds.addTimedHandler(
            LightStick.Controller.dsUpdateHandler);
    },

    updateLoop: function () {
        ;
    }
};