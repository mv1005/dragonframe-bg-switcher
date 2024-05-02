# Dragonframe Background Switcher
Switches the image on a screen in sync with Dragonframe events. The
screen can be used as dynamic background during stop-motion recordings.

-----

**Table of Contents**

- [Status](#status)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Status

This project is still under initial development.

## Installation

Recommenced instalation method is using `pipx`. This will automatically
install the application inside an isolated virtualenv and populate the
provided executables via your `PATH`.

```console
pipx install git+https://github.com/mv1005/dragonframe-bg-switcher.git
```

When installing manually with pip, using a virtualenv is recommened as
well.
```console
pip install git+https://github.com/mv1005/dragonframe-bg-switcher.git
```

## Usage

### Run the application

Run the program and specify an image directory:

```console
dragonframe-bg-switcher /my/image/dir/
```

### Connect with Dragonframe

Connect your Dragonframe instance to the server on port 8888 using the
so called "Simple Interface". See Dragonframe documentation for details.

The program waits for events of type "Position Frame (Move to
Frame)" received from Dragonframe, which according to the docs looks
like:

```
PF [FRAME] [EXPOSURE] [EXPOSURE NAME] [STEREO INDEX][\r\n]
```

The third argument named `EXPOSURE NAME` will be used as image name
beeing looked up in the directory you specified when starting
`dragonframe-bg-switcher`. That image will be loaded and served
via a dynamic web page.

### Display dynamic image in browser

To display that page, open a browser and connect to the webserver on port
5000 on the machine running `dragonframe-bg-switcher`.

The URL looks like `http://<IP or HOST>:5000`.

Once opened in your browser, subsequent PF-events will trigger an
automatic update of the image shown on your screen without further
action of the user.

To use this display as background for shooting stop motion frames,
switch your browser to full screen mode.

### Play around without Dragonframe

You can emulate the behaviour of Dragonframe with any program that is
capable of sending text via a TCP socket.

The following shows an example using netcat (`nc`), assuming that
`dragonframe-bg-switcher` is running on the same host.

```console
nc localhost 8888
```

In netcat prompt, type any Dragaonframe event you like, e.g.
```
PF 1 1 test.jpg
```


## License

Dragonframe Background Switcher is distributed under the terms of the
[MIT](https://spdx.org/licenses/MIT.html) license.
