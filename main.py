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
from picker import CircularTimePicker
from kivy.uix.button import Button
from datetime import datetime,time
import time as tt

import json

app = None

class PopupMessage(Label):
    def __init__(self,**kwargs):
        super(PopupMessage,self).__init__(**kwargs)
        
        Clock.schedule_once(self.fade_out,2)
        Clock.schedule_once(self.delete_self,5)
        Animation(opacity=0.5,duration=1).start(self)
        
    def fade_out(self,val):
        Animation(opacity=0,duration=2).start(self)
        
    def delete_self(self,val):
        app.root.remove_widget(self)
        
class AlarmWidget(BoxLayout):
    alarm_time = ObjectProperty(None)
    
    def __init__(self,**kwargs):
        super(AlarmWidget,self).__init__(**kwargs)
        self.alarm = SoundLoader.load('3.wav')
        self.alarm.loop = True
        
        self.animation_fade_out = Animation(opacity=0,duration=4)
        self.animation_fade_in = Animation(opacity=1,duration=1)
        
        self.alarm_volumes = [0.01,0.05,0.1,0.25,0.4,0.6,0.8,1]
        self.alarm_volumes_snooze = [0.2,0.4,0.7,1]
        self.alarm_volume_index = 0
        self.alarm.volume = self.alarm_volumes[self.alarm_volume_index]
        self.volume_clock = None
        self.alarm_clock = None
        
        self.alarm_time = None #time
        self.in_snooze = False
        self.snooze_time = 300
        
        self.enabled = False
        
        self.stopped = True
    
        self.touch_down_time = 0
        
    def set_alarm_time(self,value):
        self.alarm_time = value;
        self.alarm_label.label.text = value.strftime('%H:%M') if self.enabled else "__:__"
        
    def fade_out(self):
        self.animation_fade_out.start(self)
        
    def fade_in(self):
        self.animation_fade_in.start(self)
    
    def update_volume(self,val):
        volumes = self.alarm_volumes_snooze if self.in_snooze else self.alarm_volumes
        
        self.alarm.volume = volumes[self.alarm_volume_index]
        
        app.root.show_popup("Volume:{}".format(self.alarm.volume))
        
        if self.alarm_volume_index < len(volumes) - 1:
            self.alarm_volume_index += 1
            
            if not self.stopped:
                self.volume_clock = Clock.schedule_once(self.update_volume,10)
        
    def alarm_now(self,val):
        if app.root.current_alarm is None or app.root.current_alarm.stopped:
            app.root.show_popup("alarm now:")
            app.root.current_alarm = self
            app.root.in_alarm = True
            app.root.fade_in_self()
            self.fade_in()
            #TODO: need to control the volume
            self.alarm_volume_index = 0
            self.alarm.play()
            self.stopped = False

            self.volume_clock = Clock.schedule_once(self.update_volume,10)
            
            #when alarm finished, change current_alarm of root widget to None
        
    def stop(self,newScheduleTime):
        if (not self.stopped or self.in_snooze):
            self.alarm_clock.cancel()
        
        self.alarm.stop()
        self.stopped = True
        
        if newScheduleTime > 0:
            self.alarm_clock = Clock.schedule_once(self.alarm_now,newScheduleTime)
        elif newScheduleTime == 0:
            app.root.show_popup("alarm stopped:0")
            self.schedule_alarm()
        elif newScheduleTime < 0:
            app.root.show_popup("alarm stopped:<0")
            pass
        
        if self.volume_clock is not None:
            self.volume_clock.cancel()
        
        
    def schedule_alarm(self):
        if not self.stopped:
            self.stop(0)
              
        elif self.alarm_time is not None and self.enabled:
            now = datetime.now()
            alarm_time = now.replace(hour=self.alarm_time.hour,minute=self.alarm_time.minute,second=self.alarm_time.second)
                            
            delta = (alarm_time - now).seconds

            self.alarm_clock = Clock.schedule_once(self.alarm_now,delta)

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

        self.alarm.set_alarm_time(self.time_picker.time)
        self.alarm.schedule_alarm()
        app.set_alarm_to_store(self.alarm.id, {
                                               "enable":1 if self.button_enable.active else 0,
                                               "time":[self.alarm.alarm_time.hour,self.alarm.alarm_time.minute],
                                               "snooze":300,
                                                "alarm_volumes":[0.01,0.05,0.1,0.25,0.4,0.6,0.8,1],
                                                "alarm_volumes_snooze":[0.2,0.4,0.7,1]
                                               })
        self.button_cancel_down()
        
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
        self.animation_fade_out = Animation(opacity=0.4,duration=5)
        self.animation_fade_in = Animation(opacity=1,duration=1)
        self.in_alarm = False
        self.current_alarm = None
        
        
    def init_alarms(self):
        for i in range(1,5):
            info = app.get_alarm_from_store("{}".format(i))
            alarm = eval("self.alarm_{}".format(i))
            alarm.id="{}".format(i)
            
            if info is not None:   
                alarm.enabled = True if info["enable"]  == 1 else False           
                alarm.set_alarm_time(time(info["time"][0],info["time"][1]))
                alarm.snooze = info["snooze"]
                alarm.volumes = info["alarm_volumes"]
                alarm.volumes_snooze = info["alarm_volumes_snooze"]
            
        
    def on_touch_down(self,event):
        alarm = None
        if self.alarm_1.collide_point(event.ox, event.oy):
            alarm = self.alarm_1
        elif self.alarm_2.collide_point(event.ox, event.oy):
            alarm = self.alarm_2
        elif self.alarm_3.collide_point(event.ox, event.oy):
            alarm = self.alarm_3
        elif self.alarm_4.collide_point(event.ox, event.oy):
            alarm = self.alarm_4
            
        if alarm is not None:
            alarm.touch_down_time = tt.time()
        else:
            self.alarm_1.touch_down_time = 0
            self.alarm_2.touch_down_time = 0
            self.alarm_3.touch_down_time = 0
            self.alarm_4.touch_down_time = 0
            
        return super(ClockWidget,self).on_touch_down(event)
    
    def on_touch_up(self,event):   
        if event.is_touch:
            alarm = None
            if self.alarm_1.collide_point(event.ox, event.oy):
                alarm = self.alarm_1
            elif self.alarm_2.collide_point(event.ox, event.oy):
                alarm = self.alarm_2
            elif self.alarm_3.collide_point(event.ox, event.oy):
                alarm = self.alarm_3
            elif self.alarm_4.collide_point(event.ox, event.oy):
                alarm = self.alarm_4
            
            if alarm is not None:
                if (not alarm.stopped or alarm.in_snooze) and alarm.touch_down_time > 0 and (tt.time() - alarm.touch_down_time) > 3:
                    alarm.stop(0)
                    alarm.in_snooze = False
                
                if event.is_double_tap:
                    #edit alarms
                    if self.alarm_editor_openned == False:
                        self.opacity_old = self.opacity
                        self.opacity = 1
    
                        self.hide_alarm_clock()
                        
                        self.alarm_editor.opacity = 1
                        self.alarm_editor.edit(alarm)
                        self.add_widget(self.alarm_editor)
                        self.alarm_editor_openned = True
            
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
                self.show_popup("snooze...")
                self.current_alarm.in_snooze = True
                self.current_alarm.stop(self.current_alarm.snooze)
        
        return super(ClockWidget,self).on_touch_up(event)
    
    
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
     
    def show_popup(self,txt):
        print txt
        pop = PopupMessage(text=txt)
        self.add_widget(pop)
        

class ClockApp(App):
    clearcolor = (0,0,0,1)
    
    def __init__(self,**kwargs):
        super(ClockApp,self).__init__(**kwargs)
        from os.path import join
        self.store = JsonStore(join(self.user_data_dir,"clockalarm.json"))
    
    def build(self):
        root = ClockWidget()
        
        root.init_alarms()
        
        self.root=root
        return self.root
    
    def on_pause(self):
        return True
    
    def on_resume(self):
        pass
    
    def get_alarm_from_store(self,id):
        if self.store.exists("alarms"):
            try:
                return self.store.get("alarms")["a{}".format(id)]
            except:
                return None
        
    def set_alarm_to_store(self,id,alarm):
        allAlarms = {}
        for i in range(1,5):
            if i == int(id):
                allAlarms["{}".format(i)]=alarm
            else:
                allAlarms["{}".format(i)]=app.get_alarm_from_store("{}".format(i))
                                                       
        self.store.put("alarms",a1=allAlarms["1"],a2=allAlarms["2"],a3=allAlarms["3"],a4=allAlarms["4"])
        
    
app = ClockApp()
    
if __name__ == '__main__':
    app.run()
