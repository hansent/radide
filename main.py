import os
import inspect
import functools

import kivy
kivy.require('1.0.7')

from kivy.graphics import *
from kivy.properties import *
from kivy.core.window import Window
from kivy.app import App
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.factory import Factory
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
    editor = ObjectProperty
    widget = ObjectProperty(None)

    def on_widget(self, *args):
        if not self.widget.id:
            classname = self.widget.__class__.__name__
            self.widget.id = "%s <uid:%s>"%(classname, self.widget.uid)




class PropertyDialog(GridLayout):
    widget = ObjectProperty(None)

    def on_widget(self, *args):
        for name in sorted(self.widget._Widget__properties):
            title = Label(text=name+":", size_hint=(None,1), width=150, halign='left')
            textval = TextInput(text=str(getattr(self.widget, name)))
            validate = functools.partial(self.set_value, name, textval)
            textval.bind(text=validate)
            self.add_widget(title)
            self.add_widget(textval)

    def set_value(self, name, textval, *args):
        try:
            val = textval.text
            print "setting value:", val
            if type(getattr(self.widget, name)) == type('str'):
                val = eval("'%s'"%val)
            else:
                val = eval(val)
            setattr(self.widget, name, val)
        except Exception as e:
            print e



class AppContainer(FloatLayout):
    editor = ObjectProperty(None)

    def collide_children(self, root, pos, result ):
        p = root.to_local(*pos)
        for c in reversed(root.children):
            if c.collide_point(*p):
                result.append(c)
            self.collide_children(c, p, result)
        return result

    def on_touch_down(self, touch):
        hits = self.collide_children(self, touch.pos, [])
        if len(hits):
            self.editor.select_widget(hits[-1])
        else:
            self.editor.select_widget(None)
        
    def on_touch_move(self, touch):
        if self.collide_children(self, touch.pos, []):
            return True

    def on_touch_up(self, touch):
        if self.collide_children(self, touch.pos, []):
            return True


class AppEditor(FloatLayout):
    app = ObjectProperty(None)
    workspace = ObjectProperty(None)
    widget_tree = ObjectProperty(None)
    app_container = ObjectProperty(None)
    highlight_box = ListProperty([0,0, 0,0, 0,0, 0,0])
    property_popup = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.update_widget_tree = Clock.create_trigger(self._update_widget_tree)
        self.update_highlight_box = Clock.create_trigger(self._update_highlight_box)
        super(AppEditor, self).__init__(**kwargs)

    def on_app(self, *args):
        if not self.app.built:
            self.app.load_kv()
            self.app.root = self.app.build()
        self.update_widget_tree()

    def _create_tree_node(self, widget, parent_node=None):
        if parent_node == None:
            self.widget_tree.root.nodes = []
        
        node = WidgetProxyNode(widget=widget, editor=self)
        self.widget_tree.add_node(node, parent_node)
        for c in widget.children:
            c.bind(x=self.update_highlight_box, right=self.update_highlight_box,
                   y=self.update_highlight_box, top=self.update_highlight_box)
            self._create_tree_node(c, node)

    def _update_widget_tree(self, *args):
        self.app_container.clear_widgets()
        self.app_container.add_widget(self.app.root)
        self.workspace.bind(transform=self._update_highlight_box)

        self.widget_tree.bind(selected_node=self._update_highlight_box)
        self._create_tree_node(self.app.root)

    def _update_highlight_box(self, *args):
        try:
            w = self.widget_tree.selected_node.widget
            self.highlight_box = ( w.to_window(w.x, w.y) +
                                   w.to_window(w.right, w.y) +
                                   w.to_window(w.right, w.top) +
                                   w.to_window(w.x, w.top) )
        except:
            self.highlight_box = [0,0, 0,0, 0,0, 0,0]

    def _find_widget_in_tree(self, w, root):
        if isinstance(root, WidgetProxyNode) and root.widget == w:
            if not root.is_open:
                self.widget_tree.toggle_node(root)
            return root
        for n in root.nodes:
            node =  self._find_widget_in_tree(w, n)
            if node:
                if not root.is_open:
                    self.widget_tree.toggle_node(root)
                return node

    def select_widget(self, w):
        node = self._find_widget_in_tree(w, self.widget_tree.root)
        if node:
            self.widget_tree.select_node(node)
        else:
            self.widget_tree.select_node(self.widget_tree.root)

    def insert_new_widget(self, node):
        parent_widget = node.widget
        new_widget = Button(text='New Child')
        parent_widget.add_widget(new_widget)
        self._update_widget_tree()
        self.select_widget(parent_widget)

    def delete_widget(self, node):
        parent_widget = node.widget.parent
        parent_widget.remove_widget(node.widget)
        self._update_widget_tree()
        self.select_widget(parent_widget)

    def toggle_property_popup(self, *args):
        node = self.widget_tree.selected_node
        if self.property_popup == None and isinstance(node, WidgetProxyNode):
            w = node.widget
            props = PropertyDialog(widget=w)
            def on_dismiss(*args):
                self.property_popup = None
            self.property_popup = Popup(
                    title = "Properties:", 
                    size_hint=(.8,.9),
                    content=props,
                    on_dismiss=on_dismiss )

            self.property_popup.open()
        elif self.property_popup:
            self.property_popup.dismiss()

    def toggle_widget_tree(self, *args):
        new_x = 0
        if self.widget_tree.x > self.widget_tree.width* -0.5:
            new_x = - self.widget_tree.width
        Animation.stop_all(self.widget_tree, 'x')
        anim = Animation(x=new_x, t='out_expo', d=0.5)
        anim.start(self.widget_tree)





class AppScreen(FloatLayout):
    pass

class TestApp(App):
    title = "Test App"
    def build(self):
        return AppScreen()


class RadideApp(App):
    title = "Fly little Ratite! Fly!"

    def on_keyboard(self, win, key,*args):
        print key
        if key == 293: #F12
            self.app_editor.toggle_property_popup()
            return True           
        if key == 292: #F11
            self.app_editor.toggle_widget_tree()
            return True           

    def build(self):
        Window.bind(on_keyboard=self.on_keyboard)
        self.app_editor =  AppEditor(app=TestApp())
        return self.app_editor


if __name__ in ('__android__', '__main__'):
    Factory.register('AppContainer', AppContainer)
    app = RadideApp()
    #def load_self(*args):
    #    app.app_editor.app=RadideApp()
    #Clock.schedule_once(load_self,2)
    app.run()
