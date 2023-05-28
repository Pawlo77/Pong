# Pong Game

Pong Game is a classic arcade game implemented using the Python library Kivy. It offers an interactive gaming experience where players can compete against each other or against a computer-controlled opponent. The game features various settings and options to customize the gameplay.

## How It Works
The game follows the traditional rules of Pong, where players control paddles to hit the ball and prevent it from crossing their side of the screen. The objective is to score points by making the ball pass the opponent's paddle while defending against incoming shots.

Here's a step-by-step breakdown of how the game works:
1. The game starts with a ball placed at the center of the screen and two paddles positioned on each side.
2. Players control their respective paddles using keyboard inputs or touch gestures on supported devices.
3. The ball moves across the screen, and players use their paddles to hit it back toward the opponent's side.
4. When the ball collides with a paddle, it changes direction based on the angle of impact.
5. If a player fails to hit the ball and it crosses their side of the screen, the opposing player scores a point.
6. The game continues until one player reaches the specified number of points to win the match.
7. Players can pause and resume the game at any time, allowing for breaks or interruptions.

## Keymap
The keymap for controlling the paddles is as follows:
- Single Player Mode:
  - Arrow Up: Move the paddle up
  - Arrow Down: Move the paddle down
- Two Player Mode:
  - Player 1 (Right Paddle):
    - Arrow Up: Move the paddle up
    - Arrow Down: Move the paddle down
  - Player 2 (Left Paddle):
    - 'W' Key: Move the paddle up
    - 'S' Key: Move the paddle down

## Network Description
The game supports multiplayer gameplay over a LAN network. Here are some details about the network functionality:
- By default, the game scans for servers only on the local network. You can modify the code in `internet.py`, line 99, to change this behavior.
- The game allows hosting multiple servers on the same computer using different ports. If the specified ports are already in use, an error message will be displayed.
- Special error pop-ups will appear in case of any network errors or if a player leaves the game.
- Both players have the ability to pause and resume the game, regardless of who initiated the pause.

## Advanced Options
The game provides advanced options that can be customized in the settings:
- "Show logs in console": When enabled, important game events and connection-related information will be displayed in the console of the respective players' devices.
- "Developer mode": When enabled, detailed error messages will be shown for any errors that occur during gameplay.

Pong Game offers a fun and engaging gaming experience, allowing players to enjoy the classic Pong gameplay with customizable settings and multiplayer capabilities.
