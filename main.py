import kivy
from random import Random
kivy.require('1.9.0')

from kivy.app import App

class ClockApp(App):
    
    def alarm_touch_down(self,id):
        pass



if __name__ == '__main__':
    app = ClockApp()
    app.run()
