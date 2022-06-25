# Pong Game
<b>Pong game</b> using python's liblary kivy.<br>
Allows playing against a simple bot, other player on the same PC or via an LAN network.<br>
Game can be paused<br>
Game has some in-build flexible settings, like adjusting speed of both bot and player,<br>
number of rounds it takes to win or how fast the ball moves.<br><br><br>
<hr>
<b>Keymap</b><br>
If only one player is playing physicaly on the computer, it moves using arrow up / down<br>
moving paddle on the right side of screen. In case of 2 - left paddle is being moved<br>
by w (for up) and s (for down). <br>
<hr>
<b>Network description</b><br>
By default it scannes for servers only on physical local network (tweak internet.py, line 99 to change),<br>
having ability to host 2 servers on the same PC and using for that ports 8000-8001 (if they are used,<br>
the error telling that game was unable to create a server will be shown on the screen.<br>
In case of any network errors / player leaving etc special error-popups will be raised.<br>
Both player are able to unpause the game, regardless of whom paused it.<br>
<hr>
<b>Advanved options</b><br>
In settings by ticking "Show logs in consol" all important events of the game will be reported on<br>
the computer making calculations (in online - the server) and on every one all connection-related informations.<br>
Choosing "Developer mode" will show every error bypassed by try...except python statement.<br>