import kivy
kivy.require('1.9.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.animation import Animation
from kivy.properties import ObjectProperty
from kivy.storage.jsonstore import JsonStore
from kivy.garden.circulardatetimepicker import CircularTimePicker
from kivy.uix.button import Button
from datetime import datetime

app = None

class AlarmWidget(BoxLayout):
    alarm_time = ObjectProperty(None)
    
    def __init__(self,**kwargs):
        super(AlarmWidget,self).__init__(**kwargs)
        self.alarm = SoundLoader.load('3.mp3')
        self.alarm.loop = True
        
        self.animation_fade_out = Animation(opacity=0,duration=4)
        self.animation_fade_in = Animation(opacity=1,duration=1)
        
        self.alarm_volumes = [0.01,0.05,0.1,0.25,0.4,0.6,0.8,1]
        self.alarm_volumes_snooze = [0.2,0.4,0.7,1]
        self.alarm_volume_index = 0
        self.alarm.volume = self.alarm_volumes[self.alarm_volume_index]
        
        self.alarm_time = None #time
        self.in_snooze = False
        self.snooze_time = 300
        
        self.enabled = False
        
        self.stopped = True
        
    def on_alarm_time(self,instance,value):
        self.alarm_label.label.text = value.strftime('%H:%M') if self.enabled else "__:__"
        
    def fade_out(self):
        self.animation_fade_out.start(self)
        
    def fade_in(self):
        self.animation_fade_in.start(self)
    
    def update_volume(self,val):
        volumes = self.alarm_volumes_snooze if self.in_snooze else self.alarm_volumes
        
        self.alarm.volume = volumes[self.alarm_volume_index]
        
        print "Volume:{}".format(self.alarm.volume)
        
        if self.alarm_volume_index < len(volumes) - 1:
            self.alarm_volume_index += 1
            
            if not self.stopped:
                Clock.schedule_once(self.update_volume,10)
        
    def alarm_now(self,val):
        if app.root.current_alarm is None or app.root.current_alarm.stopped:
            print "alarm now:{}".format(datetime.now().strftime("%H:%M"))
            app.root.current_alarm = self
            app.root.in_alarm = True
            app.root.fade_in_self()
            self.fade_in()
            #TODO: need to control the volume
            self.alarm_volume_index = 0
            self.alarm.play()
            self.stopped = False

            Clock.schedule_once(self.update_volume,10)
            
            #when alarm finished, change current_alarm of root widget to None
        
    def stop(self):
        print "alarm stopped:{}".format(datetime.now().strftime("%H:%M"))
        self.alarm.stop()
        self.stopped = True
        
    def schedule_alarm(self):
        if self.alarm_time is not None and self.enabled:
            now = datetime.now()
            
            delta = 0
            if self.alarm_time.hour < now.hour:
                delta = (self.alarm_time.hour + 24 - now.hour)*60 
            else:
                delta = (self.alarm_time.hour - now.hour)*3600
            
            delta += (self.alarm_time.minute - now.minute) * 60

            Clock.schedule_once(self.alarm_now,delta)

class NowWidget(Label):
    def __init__(self,**kwargs):
        super(NowWidget,self).__init__(**kwargs)
        Clock.schedule_interval(self.update_now,1)
        
    def update_now(self,dt):
        self.text = datetime.now().strftime('%H:%M')


class AlarmEditor(BoxLayout):
    def edit(self,alarm):
        if alarm is not None:
            self.alarm = alarm
            
            if alarm.alarm_time is not None:
                self.time_picker.time = alarm.alarm_time

    def button_ok_down(self):
        if self.button_enable.active:
            self.alarm.enabled = True
        else:
            self.alarm.enabled = False

        self.alarm.alarm_time = self.time_picker.time
        self.button_cancel_down()
        self.alarm.schedule_alarm()
        
        #self.save_alarm()
        
    '''
    def save_alarm(self):
        if app.store.exists("alarms") == False:
            app.store.put("alarms",{self.alarm.id:{"time":self.alarm.alarm_time}})
        else:
            alarms = app.store.get("alarms")
            alarms[self.id] = {"time":self.alarm.alarm_time}
            
            app.store.put("alarms",alarms)
    '''
        
    def button_cancel_down(self):
        app.root.opacity = app.root.opacity_old
        app.root.show_alarm_clock()
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
        self.animation_fade_out = Animation(opacity=1,duration=5)
        self.animation_fade_in = Animation(opacity=1,duration=1)
        self.in_alarm = False
        self.current_alarm = None
        
    def on_touch_up(self,event):
        if event.is_touch:            
            if event.is_double_tap:
                #edit alarms
                alarm = None
                if self.alarm_1.collide_point(event.ox, event.oy):
                    alarm = self.alarm_1
                elif self.alarm_2.collide_point(event.ox, event.oy):
                    alarm = self.alarm_2
                elif self.alarm_3.collide_point(event.ox, event.oy):
                    alarm = self.alarm_3
                elif self.alarm_4.collide_point(event.ox, event.oy):
                    alarm = self.alarm_4
                elif self.clock.collide_point(event.ox,event.oy):
                    pass
                    #opacity = self.clock.opacity + 0.1
                
                    #if opacity > 0.8:
                    #    opacity = 0.1
                        
                    #self.clock.opacity = opacity

                if alarm is not None and self.alarm_editor_openned == False:
                    self.opacity_old = self.opacity
                    self.opacity = 1

                    self.hide_alarm_clock()
                    
                    self.alarm_editor.opacity = 1
                    self.alarm_editor.edit(alarm)
                    self.add_widget(self.alarm_editor)
                    self.alarm_editor_openned = True
                else:
                    self.fade_in_alarms()
                    self.fade_in_self()

            if self.fade_clock is not None:
                self.fade_clock.cancel()
                
            if self.alarm_fade_clock is not None:
                self.alarm_fade_clock.cancel()
            
            if not self.in_alarm:
                self.alarm_fade_clock = Clock.schedule_once(self.fade_out_alarms,10)   
                self.fade_clock = Clock.schedule_once(self.fade_out_self,180)
            elif not self.current_alarm.stopped:
                if event.is_triple_tap:
                    print "stop..."
                    #TODO: never get here as always go to snooze
                    self.current_alarm.in_snooze = False
                    self.current_alarm.stop()
                else:
                    print "snooze..."
                    self.current_alarm.in_snooze = True
                    self.current_alarm.stop()
                    Clock.schedule_once(self.current_alarm.alarm_now,300)
    
    def hide_alarm_clock(self):                    
        self.clock.opacity = 0
        self.alarm_1.opacity = 0
        self.alarm_2.opacity = 0
        self.alarm_3.opacity = 0
        self.alarm_4.opacity = 0
        
    def show_alarm_clock(self):                    
        self.clock.opacity = 0.6
        self.alarm_1.opacity = 0.8
        self.alarm_2.opacity = 0.8
        self.alarm_3.opacity = 0.8
        self.alarm_4.opacity = 0.8
        
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
    
    def __init__(self,**kwargs):
        super(ClockApp,self).__init__(**kwargs)
        from os.path import join
        self.store = JsonStore(join(self.user_data_dir,"clockalarm.json"))
        
    def build(self):
        root = ClockWidget()
        self.root=root
        return self.root
    
    def on_pause(self):
        return True
    
    def on_resume(self):
        pass
        
    
app = ClockApp()
    
if __name__ == '__main__':
    app.run()
