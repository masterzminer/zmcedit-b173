"""Copyright (c) 2010-2012 David Rio Vierra

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""

import re

from .toolbasics import *
from albow.dialogs import wrapped_label
from albow import *
import importlib
from pathlib import Path
from config import LastDir, Settings, LastFilter, HiddenFilters, save_config

from pymclevel.box import BoundingBox
import arguments
import log
import mcplatform

DEFAULT_FILTER_SEARCH_TEXT = "RandomBlocks_py"

ALL_FILTER_DIRS = []

def reload_filter_dirs():
    """
    Find all relevant filter directories
    """
    log.debug("Reloading filter directories")
    filter_dirs = []

    # Add the base filters directory
    filter_dirs.append(directories.STOCK_FILTERS)

    # Add the directories from the arguments
    filter_dirs.extend(arguments.FILTER_DIRS)

    # Add the directory from user configuration
    user_dir = Settings.user_filters_dir.v
    if user_dir is not None and user_dir != "":
        filter_dirs.append(user_dir)

    # Replace the contents of the reference for the list of dirs
    global ALL_FILTER_DIRS
    ALL_FILTER_DIRS.clear()
    ALL_FILTER_DIRS.extend([Path(p) for p in filter_dirs])

    log.debug("Loaded filter directories", [str(s) for s in filter_dirs])


ALL_FILTER_MODULES = {}

def reload_filter_modules():
    log.debug("Reloading filter modules from dirs", [str(s) for s in ALL_FILTER_DIRS])

    # Find all filters
    all_modules = []
    for filters_dir in ALL_FILTER_DIRS:
        log.debug("Reloading filters at", filters_dir)
        
        # Add all filter directories to the path
        if filters_dir not in [s if isinstance(s, str) else s for s in sys.path]:
            sys.path.append(str(filters_dir))

        # Find all files
        filter_files = os.listdir(filters_dir)

        # Add each file to the list of filters
        for x in filter_files:
            # Skip anything that isn't a py file
            if not x.endswith(".py"): continue

            p = Path(filters_dir) / Path(x)
            log.debug("Loading filter", p)

            # Build a unique module name based on the path, replacing non alphanumerics with underscores
            path_name = str(p)
            module_name = "_mcedit_filter_" + re.sub(r'\W+', '_', path_name)

            log.debug("Creating filter with module name:", module_name)

            # Reload the filter
            spec = importlib.util.spec_from_file_location(module_name, p)
            module = importlib.util.module_from_spec(spec)

            # Give the module a unique name for mapping
            module._mcedit_name = module_name

            # Add the path for later lookup
            module._filter_file_path = path_name

            # Import the module
            spec.loader.exec_module(module)

            # Add the module to sys
            sys.modules[module_name] = module

            # Give the module a friendly name, or use the given one if needed
            module._mcedit_name_display = module.displayName if hasattr(module, 'displayName') else (p.stem.capitalize())

            # Track the module
            all_modules.append(module)

        
    # Only load modules that are valid filters
    filter_modules = []
    for m in all_modules:
        if hasattr(m, "perform"):
            filter_modules.append(m)
        else:
            log.warn(f"Invalid filter: {m}, missing perform function")
    
    # Map all filters by their id
    filter_modules = dict((m._mcedit_name, m) for m in filter_modules)

    log.debug("loaded", len(filter_modules), "filters")

    # Save all the modules to the global dict
    global ALL_FILTER_MODULES
    ALL_FILTER_MODULES.clear()
    ALL_FILTER_MODULES.update(filter_modules)

    log.debug(f"Reloaded {len(filter_modules)} filters")


def reload_filters():
    reload_filter_dirs()
    reload_filter_modules()
    global filterToolPanel
    if filterToolPanel:
        if filterToolPanel.panel:
            filterToolPanel.panel.reload()

filterToolPanel = None
"""The panel that holds the current filters for the editor"""

# Init filter directories and filters
reload_filters()


def alertFilterException(func):
    def _func(*args, **kw):
        try:
            func(*args, **kw)
        except Exception as e:
            log.error("Exception during filter")
            alert(f"Exception during filter operation. See console for details.\n\n{e}")

    return _func

def addNumField(page, optionName, val, min=None, max=None):
        if isinstance(val, float):
            f_type = FloatField
        else:
            f_type = IntField

        if min == max:
            min = None
            max = None

        field = f_type(value=val, width=100, min=min, max=max)
        page.optionDict[optionName] = AttrRef(field, 'value')

        row = Row([Label(optionName), field])
        return row

class FilterModuleOptions(Widget):
    is_gl_container = True

    def __init__(self, tool, module, *args, **kw):
        Widget.__init__(self, *args, **kw)
        self.tool = ToolOptions
        self.pages = None
        self.optionDict = {}
        self.module = module
        self.init_options()

    def init_options(self):
        if self.pages is not None:
            self.remove(self.pages)

        self.pages = pages = TabPanel()
        pages.is_gl_container = True
        module = self.module
        log.debug("Creating options for ", module)
        if hasattr(module, "inputs"):
            if isinstance(module.inputs, list):
                for tabData in module.inputs:
                    title, page, pageRect = self.makeTabPage(self.tool, tabData)
                    pages.add_page(title, page)
                    pages.set_rect(pageRect.union(pages._rect))           
            elif isinstance(module.inputs, tuple):
                title, page, pageRect = self.makeTabPage(self.tool, module.inputs)
                pages.add_page(title, page)
                pages.set_rect(pageRect)
        else:
            self.size = (0, 0)

        pages.shrink_wrap()
        self.add(pages)
        self.shrink_wrap()
        if len(pages.pages):
            if(pages.current_page != None):
                pages.show_page(pages.current_page)
            else:
                pages.show_page(pages.pages[0])                

        for eachPage in pages.pages:
            self.optionDict = dict(list(self.optionDict.items()) + list(eachPage.optionDict.items()))

    def makeTabPage(self, tool, inputs):
        page = Widget()
        page.is_gl_container = True
        rows = []
        cols = []
        height = 0
        max_height = 550
        page.optionDict = {}
        page.tool = tool
        title = "Tab"

        for optionName, optionType in inputs:
            if isinstance(optionType, tuple):
                if isinstance(optionType[0], (int, int, float)):
                    if len(optionType) > 2:
                        val, min, max = optionType
                    elif len(optionType) == 2:
                        min, max = optionType
                        val = min

                    rows.append(addNumField(page, optionName, val, min, max))

                if isinstance(optionType[0], str):
                    isChoiceButton = False
                    if len(optionType) == 3:
                        a,b,c = optionType
                        if a == "strValSize":
                            field = TextField(value=b, width=c)
                            page.optionDict[optionName] = AttrRef(field, 'value')
                            
                            row = Row((Label(optionName), field))
                            rows.append(row)
                        else:
                            isChoiceButton = True
                    elif len(optionType) == 2:
                        a,b = optionType
                        if a == "strVal":
                            field = TextField(value=b, width=200)
                            page.optionDict[optionName] = AttrRef(field, 'value')

                            row = Row((Label(optionName), field))
                            rows.append(row)
                        elif a == "strSize":
                            field = TextField(value="Input String Here", width=b)
                            page.optionDict[optionName] = AttrRef(field, 'value')

                            row = Row((Label(optionName), field))
                            rows.append(row)
                        else:
                            isChoiceButton = True
                    else:
                        isChoiceButton = True

                    if isChoiceButton:
                        choiceButton = ChoiceButton(list(map(str, optionType)))
                        page.optionDict[optionName] = AttrRef(choiceButton, 'selectedChoice')

                        rows.append(Row((Label(optionName), choiceButton)))

            elif isinstance(optionType, bool):
                c_box = CheckBox(value=optionType)
                page.optionDict[optionName] = AttrRef(c_box, 'value')

                row = Row((Label(optionName), c_box))
                rows.append(row)
          
            elif isinstance(optionType, (int, float)):
                rows.append(addNumField(self, optionName, optionType))

            elif optionType == "blocktype" or isinstance(optionType, material.Block):
                blockButton = BlockButton()
                if isinstance(optionType, material.Block):
                    blockButton.blockInfo = optionType

                row = Column((Label(optionName), blockButton))
                page.optionDict[optionName] = AttrRef(blockButton, 'blockInfo')

                rows.append(row)
            elif optionType == "label":
                rows.append(wrapped_label(optionName, 50))

            elif optionType == "string":
                field = TextField(value="Input String Here", width=200)
                page.optionDict[optionName] = AttrRef(field, 'value')
                
                row = Row((Label(optionName), field))
                rows.append(row)

            elif optionType == "title":
                title = optionName

            else:
                raise ValueError(("Unknown option type", optionType))

        height = sum(r.height for r in rows)

        if height > max_height:
            h = 0
            for i, r in enumerate(rows):
                h += r.height
                if h > height / 2:
                    break

            cols.append(Column(rows[:i]))
            rows = rows[i:]

        if len(rows):
            cols.append(Column(rows))

        if len(cols):
            page.add(Row(cols))
        page.shrink_wrap()

        return (title, page, page._rect)

    @property
    def options(self):
        return dict((k, v.get()) for k, v in self.optionDict.items())

    @options.setter
    def options(self, val):
        for k in val:
            if k in self.optionDict:
                self.optionDict[k].set(val[k])


class FilterToolPanel(Panel):
    def __init__(self, tool):
        Panel.__init__(self)

        self.savedOptions = {}
        self.file_controls = None
        self.show_file_controls = False

        self.tool = tool

        # Select the last selected filter if one was selected and it exists
        self.selectedFilterName = None
        self.load_last_filter()

        if len(ALL_FILTER_MODULES):
            self.reload()

    def reload(self):
        log.debug("Reloading filters panel")

        for i in list(self.subwidgets):
            self.remove(i)

        tool = self.tool
        
        hidden_filter_paths = HiddenFilters.get_list()
        enabled_filters = [id for id in tool.filter_identifiers if ALL_FILTER_MODULES[id]._filter_file_path not in hidden_filter_paths]

        select_row = Row((
            self.build_reload_button(),
            Button("Visibility", action=self.open_hide_filters_panel),
        ))

        open_files_row = Row((
            Button("Template", action=self.create_template),
            Button("Guide", action=self.open_filter_guide),
        ))

        self.file_controls = Column((
            select_row,
            open_files_row
        ))

        if len(ALL_FILTER_MODULES) == 0:
            lab = Label("No filter modules found")
            reload_button = self.build_reload_button()
            self.add(Column((lab, reload_button, self.file_controls)))
            self.shrink_wrap()
            return

        if len(enabled_filters) == 0:
            lab = Label("No filter modules enabled")
            reload_button = self.build_reload_button()
            self.add(Column((lab, reload_button, self.file_controls)))
            self.shrink_wrap()
            return

        if (self.selectedFilterName is None) or (self.selectedFilterName not in enabled_filters) or (self.selectedFilterName not in ALL_FILTER_MODULES):
            # Try to use the default filter
            to_select = None
            for f in enabled_filters:
                if DEFAULT_FILTER_SEARCH_TEXT in f:
                    to_select = f
                    break

            # Otherwise, use the first one in the list
            if to_select is None:
                to_select = enabled_filters[0]

            self.select_filter(to_select)

        self.filterOptionsPanel = None
        while self.filterOptionsPanel is None:
            module = ALL_FILTER_MODULES[self.selectedFilterName]
            try:
                self.filterOptionsPanel = FilterModuleOptions(self.tool, module)
            except Exception as e:
                alert("Error creating filter inputs for {0}: {1}".format(module, e))
                traceback.print_exc()
                ALL_FILTER_MODULES.pop(self.selectedFilterName)
                if not self.selectedFilterName:
                    self.select_filter(enabled_filters[0])

            if len(enabled_filters) == 0:
                raise ValueError("No filters loaded!")

        self.filterSelect = ChoiceButton(enabled_filters, choice_display=dict(tool.filter_identifiers_and_names), choose=self.filterChanged)
        self.filterSelect.selectedChoice = self.selectedFilterName

        self.confirmButton = Button("Confirm", action=self.tool.confirm)

        filterLabel = Label("Filter:", fg_color=(177, 177, 255, 255))
        filterSelectRow = Row((filterLabel, self.filterSelect))

        self.input_columns = None

        self.load_last_filter()

        class ShowControlsUpdate:
            def __init__(self):
                self.value = None

            def set(control_self, value):
                self.value = value
                self.update_file_controls(value)
            def get(control_Self):
                return self.value

        show_controls_button = CheckBoxLabel("Show File Controls", ref=ShowControlsUpdate())
        show_controls_button.value = self.show_file_controls

        load_defaults_button = Button("Default Options", action=self.load_default_options)

        input_columns = Column((
            # Input rows
            filterSelectRow, self.filterOptionsPanel, self.confirmButton,
            load_defaults_button,
            show_controls_button,
        ))

        self.add(input_columns)
        self.input_columns = input_columns

        self.shrink_wrap()
        if self.parent:
            self.centery = self.parent.centery

        if self.selectedFilterName in self.savedOptions:
            self.filterOptionsPanel.options = self.savedOptions[self.selectedFilterName]

        self.update_file_controls(self.show_file_controls)


    def load_default_options(self):
        if self.filterOptionsPanel is not None:
            self.filterOptionsPanel.init_options()
        self.saveOptions()


    def update_file_controls(self, show):
        c = self.file_controls
        if c is None:
            return
        if self.input_columns is None:
            return

        showing = c.parent is self
    
        if show:
            if not showing:
                self.add(c)
        else:
            if showing:
                self.remove(c)

        c.top = self.input_columns.bottom
        self.shrink_wrap()

        self.show_file_controls = show
                

    def build_reload_button(self):
        return Button("Reload Filters", action=self.reload_filters_and_ui)
    
    def reload_filters_and_ui(self):
        reload_filter_modules()
        self.reload()

    def create_template(self):
        # Get the template text
        template_text = None
        with open(directories.FILTER_TEMPLATE_FILE, "r") as f:
            template_text = "\n".join(f.readlines())

        # Failed to get the template text
        if not template_text:
            log.warn("Failed to load filter template")
            return
        
        # Select a file to save
        path = mcplatform.askSaveFile(LastDir.filter, "Choose filter name", "new filter", "py")
        if not path: return

        # Write the contents of the template filter
        with open(path, "w") as f:
            f.write(template_text)

        # Reload filters after adding a new one
        self.reload_filters_and_ui()

    def open_hide_filters_panel(self):
        FilterConfigModal().present()

    def open_filter_guide(self):
        mcplatform.platform_open(directories.FILTER_GUIDE_FILE)

    def filterChanged(self):
        self.saveOptions()
        self.select_filter(self.filterSelect.selectedChoice)
        self.reload()

    filterOptionsPanel = None

    def saveOptions(self):
        if self.filterOptionsPanel:
            self.savedOptions[self.selectedFilterName] = self.filterOptionsPanel.options
        self.save_last_filter_options()


    def select_filter(self, f):
        # Save the last used filter
        self.selectedFilterName = f
        if f is not None and f != "":
            # Update the filter
            LastFilter.selected.set(f)
            self.save_last_filter_options()

    def save_last_filter_options(self):
         if self.selectedFilterName in self.savedOptions:
            options = self.savedOptions[self.selectedFilterName]
            all_settings = LastFilter.all_settings.get()
            all_settings[self.selectedFilterName] = self._options_to_dict(options)
            LastFilter.all_settings.set(all_settings)
            save_config()


    def _options_to_dict(self, options):
        # If it's a block, must convert it to just the id and block data
        if isinstance(options, Block):
            return {
                "ID": options.ID,
                "blockData": options.blockData,
                "json_type": "Block"
            }

        # For a dict, convert each key
        if isinstance(options, dict):
            return {
                key: self._options_to_dict(value)
                for key, value in options.items()
            }

        # For a list, convert each value
        if isinstance(options, list):
            return [self._options_to_dict(value) for value in options]

        # Otherwise, return the original object
        return options


    def load_last_filter(self):
        last_filter = LastFilter.selected.v
        if last_filter is not None and last_filter != "":
            if last_filter in ALL_FILTER_MODULES:
                self.select_filter(last_filter)
                
                # Load the last known settings
                options = LastFilter.all_settings.get()
                options = self._dict_to_options(options)
                if last_filter in options:
                    self.savedOptions[last_filter] = options[last_filter]

    def _dict_to_options(self, d):
        # If it's a dict, check for custom types
        if isinstance(d, dict):
            # For a block, convert it
            if "json_type" in d and d["json_type"] == "Block":
                return materials.blockWithID(d["ID"], d["blockData"])

            # For a dict, convert each value 
            return {
                key: self._dict_to_options(value)
                for key, value in d.items()
            }

        # For a list, convert each value
        if isinstance(d, list):
            return [self._dict_to_options(value) for value in d]

        # Otherwise return the value directory
        return d

class FilterOperation(Operation):
    def __init__(self, level, box, filter, options):
        self.box = box
        self.level = level
        self.filter = filter
        self.options = options

    def perform(self, recordUndo=True):
        if recordUndo:
            self.recordUndo()

        self.filter.perform(self.level, BoundingBox(self.box), self.options)

        pass

    def recordUndo(self):
        self.undoSchematic = self.extractUndoSchematicFrom(self.level, self.box)

    def undo(self):
        if self.undoSchematic:
            self.level.removeEntitiesInBox(self.box)
            self.level.removeTileEntitiesInBox(self.box)
            self.level.copyBlocksFrom(self.undoSchematic, BoundingBox((0, 0, 0), self.box.size), self.box.origin)

    def dirtyBox(self):
        return self.box


class FilterTool(EditorTool):
    tooltipText = "Filter"
    toolIconName = "filter"

    def __init__(self, editor):
        EditorTool.__init__(self, editor)

        self.panel = FilterToolPanel(self)

        # Rather hacky to do this, but keep a global reference to the last filter tool so the ui can be updated
        global filterToolPanel
        filterToolPanel = self

    def all_tool_icons(self):
        return ["filter"]

    @property
    def statusText(self):
        return f"Choose a filter, then click Confirm or press {Keys.confirm_construction.v.upper()} to apply it."

    def toolEnabled(self):
        return not (self.selectionBox() is None)

    def toolSelected(self):
        self.showPanel()

    @alertException
    def showPanel(self):
        if self.panel.parent:
            self.editor.remove(self.panel)

        self.panel.reload()

        self.panel.left = self.editor.left
        self.panel.centery = self.editor.centery

        self.editor.add(self.panel)

    def hidePanel(self):
        self.panel.saveOptions()
        if self.panel.parent:
            self.panel.parent.remove(self.panel)
    
    @property
    def filter_identifiers(self):
        return [m[0] for m in self.filter_identifiers_and_names]

    @property
    def filter_identifiers_and_names(self):
        names = [(module._mcedit_name, module._mcedit_name_display) for module in ALL_FILTER_MODULES.values()]
        # Sort by display name
        names.sort(key=lambda n: n[1])
        return names

    @alertFilterException
    def confirm(self):

        with setWindowCaption("APPLYING FILTER - "):
            filterModule = ALL_FILTER_MODULES[self.panel.filterSelect.selectedChoice]

            op = FilterOperation(self.editor.level, self.selectionBox(), filterModule, self.panel.filterOptionsPanel.options)

            self.editor.level.showProgress = showProgress
            self.performWithRetry(op)

            self.editor.addOperation(op)
            self.editor.addUnsavedEdit()

            self.editor.invalidateBox(self.selectionBox())

        self.panel.saveOptions()

class FilterConfigModal(Dialog):
    def __init__(self):
        super().__init__()
        # Base table
        table_view = TableView(columns=[TableColumn("Hide?", 50, "l"), TableColumn("Filter", 250, "l"), TableColumn("Path", 400, "l")])
        table_widget = Widget()

        # Displaying modules alphabetically by name
        filter_modules = [f for f in ALL_FILTER_MODULES.values()]
        filter_modules.sort(key=lambda m: m._mcedit_name_display)

        # Setup rows of the table
        def build_row(i):
            title = filter_modules[i]._mcedit_name_display
            path = filter_modules[i]._filter_file_path
            path = filter_modules[i]._filter_file_path
            max_path = 40
            if len(path) > max_path:
                path = f"...{path[-max_path:]}"

            return ("hide", title, path)
        table_view.num_rows = lambda: len(filter_modules)
        table_view.anchor = "lrbt"
        table_view.row_data = build_row
        table_view.click_row = lambda i, e: self.refs[i].toggle()

        # Find which filters are hidden
        hidden_filter_paths = HiddenFilters.get_list()

        # Keeping track of which filters are enabled
        self.enabled_map = {}
        class EnabledRef:
            def __init__(e_self, m):
                e_self.module = m
                e_self.key = m._filter_file_path
                e_self.hidden = e_self.key in hidden_filter_paths
                e_self.update_enabled_map()

            def update_enabled_map(e_self):
                self.enabled_map[e_self.key] = e_self.hidden

            def get(e_self):
                return e_self.hidden
            def set(e_self, h):
                e_self.hidden = h
                e_self.update_enabled_map()
            
            def toggle(e_self):
                e_self.set(not e_self.get())

        # Build check boxes for hiding or unhiding filters
        self.refs = []
        for m in filter_modules:
            ref = EnabledRef(m)
            self.refs.append(ref)

        # Setup drawing custom elements
        draw_table_cell = table_view.draw_table_cell
        def draw_block_table_cell(surf, i, data, cell_rect, column):
            # For the hide row, instead, draw depending on if the filter is hidden or not
            if data == "hide":
                r = self.refs[i]
                draw_table_cell(surf, i, "X" if self.refs[i].get() else "", cell_rect, column)
            # Draw the normal content for the other columns
            else:
                draw_table_cell(surf, i, data, cell_rect, column)
        table_view.draw_table_cell = draw_block_table_cell

        # Add contents 
        table_widget.add(table_view)
        table_widget.shrink_wrap()

        # Add a button to exit
        exit_button = Button("Return", action=lambda: self.dismiss(True))

        # Setup layout to allow for scrolling properly
        content_col = Column((table_widget, exit_button))

        # Add the table to the modal
        self.add(content_col)
        self.shrink_wrap()

    # On modal close, update a config for which filters are enabled and reload the filters
    def dismiss(self, value=True):
        result = super().dismiss(value)

        hidden = []
        for f, enabled in self.enabled_map.items():
            if enabled:
                hidden.append(f)

        # Update the config
        HiddenFilters.set_list(hidden)
        save_config()

        # Reload filters for the ui
        reload_filters()

        return result
    
