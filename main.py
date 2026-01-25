from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock
class KajitanUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        Window.clearcolor = (0, 0, 0, 1)
        self.add_widget(Label(text='[b][color=FFD700]KAJITAN SOVEREIGN[/color][/b]', markup=True, font_size='40sp'))
        self.status = Label(text='Scanning Field...', font_size='18sp')
        self.add_widget(self.status)
        Clock.schedule_interval(self.update, 0.1)
    def update(self, dt):
        self.status.text = 'Calculating 5 Trillion Cycles... [color=FF0000]AIM LOCKED[/color]'
        self.status.markup = True
class KajitanApp(App):
    def build(self):
        return KajitanUI()
if __name__ == '__main__': KajitanApp().run()