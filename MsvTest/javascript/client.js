var LightStick = LightStick || {};

LightStick.client = {
    ds: null,

    load: function () {
        console.log('Setting up MSV');

        this.msv = MSV.msv("msv://mcorp.no:8091/18");
        this.msv.add_error_handler(this.msvErrorHandler);
        this.msv.add_ready_handler(this.msvReadyHandler);
    },

    msvErrorHandler: function ()  {
        alert("Failed to load MSV");
    },

    msvReadyHandler: function () {
        console.log('MSV ready');
        LightStick.client.ds = new TM.DataSet(
            "ds://mcorp.no:8080/2013",
            LightStick.client.msv, {
            tail: 10, head: 10},
            null,
            LightStick.client.dsReadyHandler);
        setInterval(LightStick.client.updateLoop, 10);
    },

    dsReadyHandler: function () {
        console.log("DS Ready");
        LightStick.client.ds.addTimedHandler(
            LightStick.client.dsUpdateHandler);
    },

    dsUpdateHandler: function (newEntries) {
        console.log('Updates from ds', newEntries);
    },

    updateLoop: function () {
        LightStick.client.setValuesToScreen();
    },

    getCurrentMsvTime: function () {
        return LightStick.client.msv.query()[MSV.P];
    },

    getCurrentMsvVelocity: function () {
        return LightStick.client.msv.query()[MSV.V];
    },

    getCurrentMsvAcceleration: function () {
        return LightStick.client.msv.query()[MSV.A];
    },

    setValuesToScreen: function () {
        var thisVar = LightStick.client;
        var currentMsvTime = thisVar.getCurrentMsvTime();
        $('#currentTime').html("MSV-P: " + currentMsvTime);

        var currentMsvVelocity = thisVar.getCurrentMsvVelocity();
        $('#currentSpeed').html("MSV-V: " + currentMsvVelocity);

        var currentMsvAcceleration = thisVar.getCurrentMsvAcceleration();
        $('#currentAcceleration').html("MSV-A: " + currentMsvAcceleration);
    }
};
