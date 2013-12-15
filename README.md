================================================================
==              LightStick system README file                 ==
==        by Simon Nistad - simon.nistad@hotmail.com          ==
================================================================

.____    .___  ________  ___ ______________   ____________________.____________  ____  __.
|    |   |   |/  _____/ /   |   \__    ___/  /   _____/\__    ___/|   \_   ___ \|    |/ _|
|    |   |   /   \  ___/    ~    \|    |     \_____  \   |    |   |   /    \  \/|      <
|    |___|   \    \_\  \    Y    /|    |     /        \  |    |   |   \     \___|    |  \
|_______ \___|\______  /\___|_  / |____|    /_______  /  |____|   |___|\______  /____|__ \
        \/           \/       \/                    \/                        \/        \/
  ______________.___. _______________________________   _____
 /   _____/\__  |   |/   _____/\__    ___/\_   _____/  /     \
 \_____  \  /   |   |\_____  \   |    |    |    __)_  /  \ /  \
 /        \ \____   |/        \  |    |    |        \/    Y    \
/_______  / / ______/_______  /  |____|   /_______  /\____|__  /
        \/  \/              \/                    \/         \/

################################################################
##     The folder structure is organized as follows:          ##
################################################################


> LightStick                    # source for the light stick system
    > Backend                   # Code for the light stick server and the light stick client (static folder)
       > Config                 # server config
       > log                    # Generated folder for log files from server
       > static                 # Code for the light stick client
            > Application           # Backbone application (light stick client)
                > models            # command model
                > Router            # backbone router
                > Views             # main view
            > CSS                   # styling for Light stick client and mobile BPM controller
            > HTML                  # HTML files for light stick client and BPM controller
            > external              # External javascript libs
            > images                # images used by clients
   > LightStick Controller  # Code for the light stick controller
        > KivyFiles             # .kv files for the light stick controller (Layout and bindings)
        > Source                # Source code for the light stick controller
            > BpmCounter            # Code BPM widget
            > ColorMixer            # Code color mixer and glow mixer
            > Config                # widget config
            > HttpWebClient         # web client
            > MSvController         # msv controller
            > SceneMixer            # code scene mixer
            > TextEffect            # code text widget
            > WidgetElements        # some widget elements
   > libs                   # External libs. WebPy and MSV lib
   > logsFromFestival       # files from the insomnia festival


###################################################################
##                     SETUP AND USAGE                           ##
###################################################################

    NOTE: There could be some problems running the light stick system on a personal computer. The Kivy framework need some
    time to be set up correctly, and the MSV service is still under development. The following steps are needed to setup
    the light stick controller.

*Run the system is this order:
    1. The server need to be started first
    2. light stick controller


*** LIGHT STICK SERVER ***
    Dependencies:
        The light stick server uses the WebPy library and the MSV library both of these libraries are included in
        the "libs" folder

    To run the server:

        python \LightStick\Backend\server.py


*** LIGHT STICK CONTROLLER ***
    To Run the light stick client:

    Dependencies:
        1. kivy must be installed to run the service:
            installation instruction can be found on (The controller has only been tested for windows):
                - http://kivy.org/#download

        2. There could be some problems with setting up the python interpreter to find the kivy installation. The
           stack overflow post gives a solution used during the development of the project:

                http://stackoverflow.com/questions/9768489/kivy-eclipse-and-pydev-also-pypy


        An environment variable needs to be set for the light stick controller to find the .kv files on launch:
        The variable FILE_PATH = the full path to the LightStick/LightStickController/KivyFiles must be set

        When kivy and the env_var is set correctly the light stick controller should be able to be launched with:

            python \LightStick\LightStickController\Source\main.py


When the server and light stick controller are up and running the service should be available from local host.

To access the light stick client:
    http://localhost:8080

To access the mobile bpm controller
    http://localhost:8080/beatControl