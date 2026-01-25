from kivy.app import App
from kivy.uix.label import Label
from kivy.core.window import Window
class SovereignAI(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        return Label(text='[color=FFD700][b]SOVEREIGN AI: READY[/b][/color]\n[size=20]Wait for Battle...[/size]', markup=True, font_size='32sp')
if __name__ == '__main__': SovereignAI().run()