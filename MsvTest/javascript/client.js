var LightStick = LightStick || {};

LightStick.Client = {
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
        LightStick.Client.ds = new TM.DataSet(
            "ds://mcorp.no:8080/2013",
            LightStick.Client.msv, {
            tail: 10, head: 10},
            null,
            LightStick.Client.dsReadyHandler);
        setInterval(LightStick.Client.updateLoop, 10);
    },

    dsReadyHandler: function () {
        console.log("DS Ready");
        LightStick.Client.ds.addTimedHandler(
            LightStick.Client.dsUpdateHandler);
    },

    dsUpdateHandler: function (newEntries) {
        _.each(newEntries, function (entry) {
            console.log('entry', entry);
        });
    },

    updateLoop: function () {
        LightStick.Client.setValuesToScreen();
    },

    getCurrentMsvTime: function () {
        return LightStick.Client.msv.query()[MSV.P];
    },

    getCurrentMsvVelocity: function () {
        return LightStick.Client.msv.query()[MSV.V];
    },

    getCurrentMsvAcceleration: function () {
        return LightStick.Client.msv.query()[MSV.A];
    },

    setValuesToScreen: function () {
        var thisVar = LightStick.Client;
        var currentMsvTime = thisVar.getCurrentMsvTime();
        $('#currentTime').html("MSV-P: " + currentMsvTime);

        var currentMsvVelocity = thisVar.getCurrentMsvVelocity();
        $('#currentSpeed').html("MSV-V: " + currentMsvVelocity);

        var currentMsvAcceleration = thisVar.getCurrentMsvAcceleration();
        $('#currentAcceleration').html("MSV-A: " + currentMsvAcceleration);
    }
};
