from typing import Any, cast, Dict, List, Optional, Set, Union
from typing_extensions import Protocol

from collections import OrderedDict
from enum import Enum
from types import DynamicClassAttribute

import glfw
import OpenGL.GL as gl

import imgui
from imgui.integrations.glfw import GlfwRenderer

from _pyntcore import NetworkTable, NetworkTableEntry, NetworkTables, NetworkTableType
from networktables.util import ChooserControl


class EntryType(Enum):
    Unknown = 0

    Boolean = 1
    Double = 2
    String = 3

    Chooser = 10

    @staticmethod
    def from_nt_type(tipe: NetworkTableType) -> 'EntryType':
        if tipe == NetworkTableType.kBoolean:
            return EntryType.Boolean
        elif tipe == NetworkTableType.kDouble:
            return EntryType.Double
        elif tipe == NetworkTableType.kString:
            return EntryType.String
        else:
            return EntryType.Unknown
    
    def is_entry(self):
        return self.value < 10


class Widget:
    tipe: EntryType
    key: str

    show_indicator: bool = True

    def __init__(self, entry: Union[NetworkTable, NetworkTableEntry], tipe: EntryType = EntryType.Unknown):
        if isinstance(entry, NetworkTable):
            self.tipe = tipe
            self.key = entry.getPath()
        else:
            self.tipe = EntryType.from_nt_type(entry.getType())
            self.key = entry.getName()
    
    @DynamicClassAttribute
    def entry(self) -> Optional[NetworkTableEntry]:
        entries = NetworkTables.getEntries(self.key, 0)
        if len(entries) == 0:
            return None
        else:
            return entries.pop()
    
    @DynamicClassAttribute
    def table(self) -> Optional[NetworkTable]:
        table = NetworkTables.getTable(self.key)
        if len(table.getKeys()) == 0:
            return None
        return table
    
    # @staticmethod
    # def fromdict(d: Dict[str, Any]) -> Widget:
    #     w = Widget()

    #     for k, v in d.items():
    #         w[k] = v


show_sendable_debug = True
show_demo = False
active_widgets: Dict[str, Widget] = {}


def init():
    NetworkTables.startClient('localhost')
    # NetworkTables.startClientTeam(2175)
    
    def listen(connected, _):
        if not connected:
            NetworkTables.deleteAllEntries()
    NetworkTables.addConnectionListener(listen, False)


def draw(imgui) -> None:
    global show_sendable_debug
    global show_demo
    global active_widgets

    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("Help"):
            clicked, _ = imgui.menu_item("Hide Demo" if show_demo else "Show Demo")
            if clicked:
                show_demo = not show_demo
            imgui.end_menu()
        imgui.end_main_menu_bar()

    if show_demo:
        imgui.show_test_window()

    if imgui.begin('All Entries'):
        if imgui.begin_popup_context_window():
            clicked, do_debug = imgui.checkbox('Show Chooser Debug Info', show_sendable_debug)
            if clicked:
                show_sendable_debug = do_debug
            imgui.end_popup()

        def table_tree(table: EntryGroup):
            for key, entry in table.items():
                if isinstance(entry, NetworkTableEntry):
                    imgui.text(entry_name(key) + ': ' + str(entry.value))
                    
                    imgui.same_line()
                    imgui.push_id(key)
                    if imgui.button('Add'):
                        active_widgets[key] = Widget(entry)
                    imgui.pop_id()
                else:
                    t = NetworkTables.getTable(key)
                    if '.type' in t.getKeys():
                        name = t.getString('.name', '')

                        imgui.text(name)
                        
                        imgui.same_line()
                        imgui.push_id(key)
                        if imgui.button('Add'):
                            active_widgets[key] = Widget(t, EntryType.Chooser)
                        imgui.pop_id()

                        if show_sendable_debug:
                            if imgui.tree_node('Chooser Debug (' + key + ')'):
                                table_tree(entry)
                                imgui.tree_pop()
                    elif imgui.tree_node(entry_name(key), imgui.TREE_NODE_DEFAULT_OPEN):
                        # nothing fancy, just a subtable
                        table_tree(entry)
                        imgui.tree_pop()

        entries = buildList(sorted(NetworkTables.getEntries('', 0), key=lambda e: e.getName()))
        table_tree(entries)
    imgui.end()

    to_close: List[str] = []
    for key, widget in active_widgets.items():
        expanded, opened = imgui.begin(entry_name(key), True)
        if not opened:
            to_close.append(key)

        if (
            (widget.tipe.is_entry() and widget.entry is None)
            or (not widget.tipe.is_entry() and widget.table is None)
        ):
            imgui.text_colored('WARNING! Disconnected!', 1, 0, 0)
            imgui.end()
            continue

        if widget.tipe == EntryType.Boolean:
            assert widget.entry is not None

            if widget.show_indicator:
                imgui.push_item_width(-1)
                r, g, b = (0, 1, 0) if widget.entry.value else (1, 0, 0)
                imgui.color_button(key + '/indicator', r, g, b, width=imgui.get_window_width(), height=100)

            clicked, new_val = imgui.checkbox('on', widget.entry.value)
            if clicked:
                widget.entry.setValue(new_val)
        elif widget.tipe == EntryType.Double:
            assert widget.entry is not None

            val = str(widget.entry.getDouble(0))
            changed, new_val = imgui.input_text('', val, 64, imgui.INPUT_TEXT_CHARS_DECIMAL)
            if changed:
                try:
                    widget.entry.setDouble(float(new_val))
                except ValueError:
                    pass
        elif widget.tipe == EntryType.String:
            assert widget.entry is not None

            changed, new_val = imgui.input_text('', widget.entry.getString(''), 256)
            if changed:
                widget.entry.setString(new_val)
        elif widget.tipe == EntryType.Chooser:
            assert widget.table is not None

            values = widget.table.getStringArray('options', [])
            try:
                selected = values.index(widget.table.getString('active', ''))
            except ValueError:
                selected = 0

            changed, current = imgui.combo('', selected, values)
            if changed:
                widget.table.putString('active', values[current])
        else:
            try:
                assert widget.entry is not None
                imgui.text(str(widget.entry.value))
            except AttributeError:
                imgui.text('Could not view contents.')
        
        if imgui.begin_popup_context_window():
            if widget.tipe == EntryType.Boolean:
                clicked, new_val = imgui.checkbox('Show Indicator', widget.show_indicator)
                if clicked:
                    widget.show_indicator = new_val
            imgui.end_popup()

        # imgui.button('Options')
        
        imgui.end()
    
    for key in to_close:
        active_widgets.pop(key)


EntryGroup = Dict[str, Union[NetworkTableEntry, Dict[str, Any]]]

def buildList(entries: List[NetworkTableEntry]):
    nested: EntryGroup = OrderedDict()
    for entry in entries:
        segments = entry.getName().split('/')

        currentKey = ''
        currentDict = nested

        for i, segment in enumerate(segments):
            if segment == '':
                continue
                
            currentKey = currentKey + '/' + segment

            if i < len(segments) - 1:
                # table
                if not currentKey in currentDict:
                    currentDict[currentKey] = OrderedDict()
                currentDict = cast(EntryGroup, currentDict[currentKey])
            else:
                # value
                currentDict[currentKey] = entry
    
    return nested


def entry_name(key: str) -> str:
    return key.split('/').pop()


# -------------------------------------------------------

def main():
    init()

    imgui.create_context()
    window = impl_glfw_init()
    impl = GlfwRenderer(window)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        imgui.new_frame()

        draw(imgui)

        gl.glClearColor(1., 1., 1., 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


def impl_glfw_init():
    width, height = 1280, 720
    window_name = "minimal ImGui/GLFW3 example"

    if not glfw.init():
        print("Could not initialize OpenGL context")
        exit(1)

    # OS X supports only forward-compatible core profiles from 3.2
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

    # Create a windowed mode window and its OpenGL context
    window = glfw.create_window(
        int(width), int(height), window_name, None, None
    )
    glfw.make_context_current(window)

    if not window:
        glfw.terminate()
        print("Could not initialize Window")
        exit(1)

    return window


if __name__ == "__main__":
    main()
