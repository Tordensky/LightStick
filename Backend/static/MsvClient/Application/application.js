var LightStick = LightStick || {};

LightStick.Application = {
    run: function () {
        var mainView = new LightStick.MainView({
            el: $("#app")
        });
        mainView.render();
    }
};
