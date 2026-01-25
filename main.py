from kivy.app import App
from kivy.uix.label import Label
from kivy.core.window import Window
class Kajitan(App):
    def build(self):
        Window.clearcolor = (0,0,0,1)
        return Label(text='[color=FFD700][b]KAJITAN SOVEREIGN[/b][/color]', markup=True, font_size='40sp')
Kajitan().run()