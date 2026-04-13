
# write game logic for Asteroids game using thorvg-cython for UI, and pymunk for physics

some inspiration for it, and just replace pygame logic with ours...

thor-ballbreaker/.venv/lib/python3.13/site-packages/pymunk
http://www.pymunk.org/en/latest/pymunk.html
thor-ballbreaker/.venv/lib/python3.13/site-packages/thorvg_cython
https://github.com/Py-Swift/thorvg-cython

if reading is needed..

kivy-thor/src/kivy_thor/thor_screen.py
(just for understanding where we get glcanvas from, but dont use any kivy / kivy-thor, should not be needed)
(kivy will provide keyboard input, so Game class just need key_event input function)



```
# ThorScreen once loaded in kivy will provide 
class AsteroidsGame

    canvas: GlCanvas

    def __init__(self, canvas: GlCanvas):
        self.canvas = canvas

        # Add game start up code ect
        # PyMunk Engine startup ect

    def tick(self, dt: float):
        ...



# in kivy
game = AsteroidsGame(canvas)
Clock.schedule_interval(game.tick, 0)
```


try break everything up into classes since we both got pymunk logic and thorvg handling, and more classes just makes it easier
i dont want to see this pattern of one class 20000 functions... 

so we got Player / Enemies / Other Objects ect...

