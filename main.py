import kivy
kivy.require('1.9.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from datetime import datetime
from kivy.uix.label import Label
from kivy.uix.bubble import Bubble
from kivy.uix.textinput import TextInput
from kivy.animation import Animation
from kivy.properties import ObjectProperty
from kivy.storage import jsonstore

app = None
alarm_volume = [0.01,0.05,0.1,0.25,0.4,0.6,0.8,1]

class AlarmWidget(BoxLayout):
    alarm_time = ObjectProperty(None)
    
    def __init__(self,**kwargs):
        super(AlarmWidget,self).__init__(**kwargs)
        self.alarm = SoundLoader.load('3.mp3')
        self.alarm.bind(on_start=self.on_alarm_start)
        self.alarm.bind(on_stop=self.on_alarm_stop)
        
        self.animation_fade_out = Animation(opacity=0,duration=4)
        self.animation_fade_in = Animation(opacity=1,duration=1)
        self.alarm_volume_index = 0
        self.alarm.volume = alarm_volume[self.alarm_volume_index]
        
        self.alarm_time = None #datetime
        self.in_snooze = False
        
    def on_alarm_start(self):
        self.alarm.volume = alarm_volume[self.alarm_volume_index]
        self.alarm_volume_index += 1
    
    def on_alarm_stop(self,v):
        if self.alarm.volume < 1 and not self.in_snooze:
            self.alarm.play()
        else:
            self.alarm_volume_index = 0
    
    def on_alarm_time(self,instance,value):
        self.alarm_label.label.text = value.strftime('%H:%M')
        
    def fade_out(self):
        self.animation_fade_out.start(self)
        
    def fade_in(self):
        self.animation_fade_in.start(self)
        
    def alarm_now(self,dt):
        app.root.current_alarm = self
        app.root.in_alarm = True
        app.root.fade_in_self()
        self.fade_in()
        #TODO: need to control the volume
        self.alarm.play()
        
    def schedule_alarm(self):
        if self.alarm_time is not None:
            delta = (self.alarm_time - datetime.now()).seconds
            Clock.schedule_once(self.alarm_now,delta)

class NowWidget(Label):
    def __init__(self,**kwargs):
        super(NowWidget,self).__init__(**kwargs)
        Clock.schedule_interval(self.update_now,1)
        
    def update_now(self,dt):
        self.text = datetime.now().strftime('%H:%M')
        
    def on_touch_down(self, touch):
        if touch.is_double_tap:
            opacity = self.opacity + 0.1
            
            if opacity > 1:
                opacity = 0
                
            self.opacity = opacity

class AlarmEditor(Bubble):
    def edit(self,alarm):
        if alarm is not None:
            self.alarm = alarm
            
            if alarm.alarm_time is not None:
                self.input_hour.text = alarm.alarm_time.strftime("%H")
                self.input_minute.text = alarm.alarm_time.strftime("%M")
            else:
                self.input_hour.text = "0"
                self.input_minute.text = "0"

    def button_ok_down(self):
        now = datetime.now()
        y = now.year
        m = now.month
        d = now.day
        
        self.alarm.alarm_time = datetime(year = y, month=m,day=d,hour=int(self.input_hour.text),minute=int(self.input_minute.text))
        self.alarm.schedule_alarm()
        #Animation(x=0,y=0,size=(1,1),duration=5).start(self)
        app.root.opacity = app.root.opacity_old
        app.root.alarm_editor_openned = False
        app.root.remove_widget(self)
        

class ClockWidget(RelativeLayout):
    def __init__(self,**kwargs):
        super(ClockWidget,self).__init__(**kwargs)
        self.alarm_fade_clock = None
        self.fade_clock = None
        self.alarm_editor = AlarmEditor()
        self.opacity_old = 0
        self.alarm_editor_openned = False
        self.animation_fade_out = Animation(opacity=0,duration=5)
        self.animation_fade_in = Animation(opacity=.8,duration=1)
        self.in_alarm = False
        self.current_alarm = None
        
    def on_touch_up(self,event):
        if event.is_touch:            
            if event.is_triple_tap:
                #edit alarms
                alarm = None
                if self.alarm_1.collide_point(event.ox, event.oy):
                    alarm = self.alarm_1
                if self.alarm_2.collide_point(event.ox, event.oy):
                    alarm = self.alarm_2
                if self.alarm_3.collide_point(event.ox, event.oy):
                    alarm = self.alarm_3
                if self.alarm_4.collide_point(event.ox, event.oy):
                    alarm = self.alarm_4

                if alarm is not None and self.alarm_editor_openned == False:
                    self.opacity_old = self.opacity
                    self.opacity = 0.8
                    self.alarm_editor.edit(alarm)
                    self.add_widget(self.alarm_editor)
                    self.alarm_editor_openned = True

            if self.fade_clock is not None:
                self.fade_clock.cancel()
                
            if self.alarm_fade_clock is not None:
                self.alarm_fade_clock.cancel()

            self.fade_in_alarms()
            self.fade_in_self()
            
            if not self.in_alarm:
                self.alarm_fade_clock = Clock.schedule_once(self.fade_out_alarms,10)   
                self.fade_clock = Clock.schedule_once(self.fade_out_self,180)
            elif self.current_alarm is not None:
                #snooze
                self.current_alarm.in_snooze = True
                self.alarm.stop()
                self.current_alarm.in_snooze = False
                Clock.schedule_once(self.current_alarm.alarm_now,300)
            
    def fade_out_self(self,dt):
        self.animation_fade_out.start(self)
    
    def fade_in_self(self):
        self.animation_fade_in.start(self)

    def fade_in_alarms(self):
        self.alarm_1.fade_in()
        self.alarm_2.fade_in()
        self.alarm_3.fade_in()
        self.alarm_4.fade_in()
        
    
    def fade_out_alarms(self,dt):
        self.alarm_1.fade_out()
        self.alarm_2.fade_out()
        self.alarm_3.fade_out()
        self.alarm_4.fade_out()
                

class ClockApp(App):
    clearcolor = (0,0,0,1)
    
    def build(self):
        root = ClockWidget()
        self.root=root
        return self.root

app = ClockApp()
    
if __name__ == '__main__':
    app.run()
