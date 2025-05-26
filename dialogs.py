
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

def confirm_dialog(parent, message, callback):
    layout = BoxLayout(orientation='vertical', spacing=10, padding=15)
    layout.add_widget(Label(text=message, halign='center', valign='middle'))
    button_layout = BoxLayout(orientation='horizontal', spacing=15, size_hint_y=None, height=50)
    btn_yes = Button(text="Yes")
    btn_no = Button(text="No")
    button_layout.add_widget(btn_yes)
    button_layout.add_widget(btn_no)
    layout.add_widget(button_layout)
    popup = Popup(title="Confirm", content=layout, size_hint=(0.6, 0.4), auto_dismiss=False)
    def on_yes(instance):
        popup.dismiss()
        callback(True)
    def on_no(instance):
        popup.dismiss()
        callback(False)
    btn_yes.bind(on_release=on_yes)
    btn_no.bind(on_release=on_no)
    popup.open()

def confirm_dialog_error(parent, message, callback=None):
    layout = BoxLayout(orientation='vertical', spacing=10, padding=15)
    layout.add_widget(Label(text=message, halign='center', valign='middle'))
    btn_ok = Button(text="OK", size_hint_y=None, height=50)
    layout.add_widget(btn_ok)
    popup = Popup(title="Error", content=layout, size_hint=(0.6, 0.4), auto_dismiss=False)
    def on_ok(instance):
        popup.dismiss()
        if callback:
            callback()
    btn_ok.bind(on_release=on_ok)
    popup.open()
