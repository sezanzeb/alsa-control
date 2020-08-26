# ALSA Control

**This is in a very early stage of development!**

Making ALSA easy to use.

Since ALSA provides dmix for soundcards that don't support multiplexing, it is not necessary to run pulseaudio for that.
Pulseaudio can have issues with sample rates of USB devices, which will be avoided by not using it.
Furthermore, pure ALSA should have the lowest possible audio latency.

## Usage

You can't configure your soundcard yet, so it won't work for you at this point.

```
pip3 install pyalsaaudio
python3 setup.py install
```

Start the daemon. You can put this into your autostart.

```
alsacontrol-notify-daemon-gtk
```

Change the volume. For convenience, bind this to your multimedia keys in your user interface

```
alsacontrol -v +10
alsacontrol -v -10
```

<p align="center">
    <img src="data/notifications.png"/>
</p>


## Goals

Basically provide everything that is needed to comfortably use ALSA in a GUI

Features
- Show a volume meter as notification on volume changes or mute toggling
- Change the volume of soundcards without Master controls with softvol
- Add a GUI slider and mute button for the volume of both input and output
- Add button to test the speaker setup
- Provide .deb files and get it into the AUR
- Add an example implementation of a GUI in gnome
- Add a dropdown to change input and output pcm devices (which modifies softvols pcm device) and also make jack selectable if available
- Notify about new detected audio devices with a button to open the GUI to select it
- Input and output meter

Quality
- Provide tooltips for anything that is not easily self explanatory
- Show when the user is supposed to restart their applications for it to take effect
- Make it easy to write GUIs for this in alternative libraries by properly separating code
- Provide well written docstrings
- Don't just grey out stuff, provide proper error messages and log outputs to debug problems
- Don't automatically switch devices when the current device is not available. But maybe add user defined fallback devices
- Be verbose with logs, provide debug logs

