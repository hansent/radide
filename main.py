import os
import inspect

import kivy
kivy.require('1.0.7')

from kivy.graphics import *
from kivy.properties import *
from kivy.core.window import Window
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.treeview import TreeViewLabel, TreeViewNode
from kivy.uix.filechooser import FileChooserListView


class WidgetProxyNode(TreeViewLabel):
    widget = ObjectProperty(None)

    def on_widget(self, *args):
        if not self.widget.id:
            classname = self.widget.__class__.__name__
            self.widget.id = "%s <uid:%s>"%(classname, self.widget.uid)


class PropertyDialog(GridLayout):
    widget = ObjectProperty(None)

    def on_widget(self, *args):
        clsname = self.widget.__class__.__name__
        for name in sorted(self.widget._Widget__properties):
            title = Label(text=name+":", size_hint=(None,1), width=150, halign='left')
            textval = TextInput(text=str(getattr(self.widget, name)))
            self.add_widget(title)
            self.add_widget(textval)


class AppEditor(FloatLayout):
    app = ObjectProperty(None)
    widget_tree = ObjectProperty(None)
    widget_container = ObjectProperty(None)
    highlight_box = ListProperty([0,0, 0,0, 0,0, 0,0])
    property_popup = ObjectProperty(None, allownone=True)

    def on_app(self, *args):
        if not self.app.built:
            self.app.load_kv()
            self.app.root = self.app.build()
        Clock.schedule_once(self.update_widget_tree,-1)

    def create_tree_node(self, widget, parent_node=None):
        node = WidgetProxyNode(widget=widget)
        self.widget_tree.add_node(node, parent_node)
        for c in widget.children:
            c.bind(x=self.update_highlight_box, right= self.update_highlight_box,
                   y=self.update_highlight_box, top=self.update_highlight_box)
                   
            self.create_tree_node(c, node)

    def update_widget_tree(self, *args):
        self.widget_container.clear_widgets()
        self.widget_container.add_widget(self.app.root)

        self.widget_tree.root.nodes = []
        self.create_tree_node(self.app.root)
        self.widget_tree.bind(selected_node=self.update_highlight_box)

    def update_highlight_box(self, *args):
        try:
            w = self.widget_tree.selected_node.widget
            self.highlight_box = ( w.to_window(w.x, w.y) +
                                   w.to_window(w.right, w.y) +
                                   w.to_window(w.right, w.top) +
                                   w.to_window(w.x, w.top) )
        except:
            self.highlight_box = [0,0, 0,0, 0,0, 0,0]

    def show_property_popup(self, *args):
        if self.property_popup == None and self.widget_tree.selected_node:

            w = self.widget_tree.selected_node.widget
            props = PropertyDialog(widget=w)

            def on_dismiss(*args):
                self.property_popup = None

            self.property_popup = Popup(
                    title = "Propertis:", 
                    size_hint=(.8,.9),
                    content=props,
                    on_dismiss=on_dismiss )

            self.property_popup.open()
        elif self.property_popup:
            self.property_popup.dismiss()



class TestScreen(FloatLayout):
    pass

class TestApp(App):
    title = "Test App"
    def build(self):
        return TestScreen()


class RadideApp(App):
    title = "Fly little Ratite! Fly!"

    def handle_keypress(self, win, key, scancode, uncidode, modifiers):
        print key
        if key == 293: #F12
            self.app_editor.show_property_popup()

    def build(self):
        Window.bind(on_key_down=self.handle_keypress)
        self.app_editor =  AppEditor(app=TestApp())
        return self.app_editor


if __name__ in ('__android__', '__main__'):
    app = RadideApp()
    app.run()
