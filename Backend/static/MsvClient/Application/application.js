var LightStick = LightStick || {};

LightStick.Application = {
    run: function () {
        var router = new LightStick.Router();

        var mainView = new LightStick.MainView({
            el: $("#app")
        });
        mainView.render();
    }
};
