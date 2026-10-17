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


from .toolbasics import *
from albow.dialogs import wrapped_label
from albow import *
import importlib

from pymclevel.box import BoundingBox
from pymclevel.material import materials
import arguments

ALL_FILTER_DIRS = []

def reload_filter_dirs():
    """
    Find all relevant filter directories
    """
    print("Reloading filter directories")
    filter_dirs = []

    # Add the base filters directory
    filter_dirs.append(directories.STOCK_FILTERS)

    # Add the directories from the arguments
    filter_dirs.extend(arguments.FILTER_DIRS)

    # Add the directory from user configuration
    user_dir = config.get_user_filters_dir()
    if user_dir:
        filter_dirs.append(user_dir)

    # Replace the contents of the reference for the list of dirs
    global ALL_FILTER_DIRS
    ALL_FILTER_DIRS.clear()
    ALL_FILTER_DIRS.extend(filter_dirs)

    print("Loaded filter directories", [str(s) for s in filter_dirs])


def moduleDisplayName(module):
    return module.displayName if hasattr(module, 'displayName') else module.__name__.capitalize()

ALL_FILTER_MODULES = {}

def reload_filter_modules():
    print("Reloading filter modules from dirs", [str(s) for s in ALL_FILTER_DIRS])
    # Find all filter files
    all_py_files = []
    for filters_dir in ALL_FILTER_DIRS:
        # Add all filter directories to the path
        if filters_dir not in [s if isinstance(s, str) else s for s in sys.path]:              
            sys.path.append(str(filters_dir))
        # Add to the list of all files
        filter_files = os.listdir(filters_dir)
        all_py_files.extend([x for x in filter_files if x.endswith(".py")])
    # Import all filters
    all_modules = (__import__(m[:-3]) for m in all_py_files)
    # Only load modules that are valid filters
    filter_modules = []
    for m in all_modules:
        if hasattr(m, "perform"):
            filter_modules.append(m)
        else:
            print(f"Invalid filter: {moduleDisplayName(m)}, missing perform function")
    # Map all filters by their display name
    filter_modules = dict((moduleDisplayName(m), m) for m in filter_modules)
    # Force reload every filter
    [importlib.reload(m) for m in filter_modules.values()]
    
    global ALL_FILTER_MODULES
    ALL_FILTER_MODULES.clear()
    ALL_FILTER_MODULES.update(filter_modules)

    print(f"Reloaded {len(filter_modules)} filters")


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
            alert(u"Exception during filter operation. See console for details.\n\n{0}".format(e))
            print(traceback.format_exc())

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
        self.tool = tool
        pages = TabPanel()
        pages.is_gl_container = True
        self.pages = pages
        self.optionDict = {}
        pageTabContents = []
        
        print("Creating options for ", module)
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
        #cols.append(Column(rows))

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

        self.tool = tool
        self.selectedFilterName = None
        if len(ALL_FILTER_MODULES):
            self.reload()

    def reload(self):
        print("Reloading filters panel")

        for i in list(self.subwidgets):
            self.remove(i)

        tool = self.tool

        if len(ALL_FILTER_MODULES) == 0:
            self.add(Label("No filter modules found!"))
            reload_button = self.build_reload_button()
            reload_button.top = self.bottom
            self.add_centered(reload_button)
            self.shrink_wrap()
            return

        if self.selectedFilterName is None or self.selectedFilterName not in tool.filterNames:
            self.selectedFilterName = tool.filterNames[0]

        self.filterOptionsPanel = None
        while self.filterOptionsPanel is None:
            module = ALL_FILTER_MODULES[self.selectedFilterName]
            try:
                self.filterOptionsPanel = FilterModuleOptions(self.tool, module)
            except Exception as e:
                alert("Error creating filter inputs for {0}: {1}".format(module, e))
                traceback.print_exc()
                ALL_FILTER_MODULES.pop(self.selectedFilterName)
                self.selectedFilterName = tool.filterNames[0]

            if len(tool.filterNames) == 0:
                raise ValueError("No filters loaded!")

        self.filterSelect = ChoiceButton(tool.filterNames, choose=self.filterChanged)
        self.filterSelect.selectedChoice = self.selectedFilterName

        self.confirmButton = Button("Filter", action=self.tool.confirm)

        filterLabel = Label("Filter:", fg_color=(177, 177, 255, 255))
        # filterLabel.mouse_down = lambda x: mcplatform.platform_open(filtersDir)
        # filterLabel.tooltipText = "Click to open filters folder"
        filterSelectRow = Row((filterLabel, self.filterSelect))

        self.add(Column((
            # Input rows
            filterSelectRow, self.filterOptionsPanel, self.confirmButton,
            # Space and then the reload button
            Label(""), self.build_reload_button()
        )))
                 
        self.shrink_wrap()
        if self.parent:
            self.centery = self.parent.centery

        if self.selectedFilterName in self.savedOptions:
            self.filterOptionsPanel.options = self.savedOptions[self.selectedFilterName]

    def build_reload_button(self):
        reload_filters_button = Button("Reload Filters", action=self.reload_filters_and_ui)
        return reload_filters_button

    def reload_filters_and_ui(self):
        reload_filter_modules()
        self.reload()

    def filterChanged(self):
        self.saveOptions()
        self.selectedFilterName = self.filterSelect.selectedChoice
        self.reload()

    filterOptionsPanel = None

    def saveOptions(self):
        if self.filterOptionsPanel:
            self.savedOptions[self.selectedFilterName] = self.filterOptionsPanel.options


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

    @property
    def statusText(self):
        return "Choose a filter, then click Filter or press ENTER to apply it."

    def toolEnabled(self):
        return not (self.selectionBox() is None)

    def toolSelected(self):
        self.showPanel()

    @alertException
    def showPanel(self):
        if self.panel.parent:
            self.editor.remove(self.panel)

        reload_filter_modules()
        self.panel.reload()

        self.panel.left = self.editor.left
        self.panel.centery = self.editor.centery

        self.editor.add(self.panel)

    def hidePanel(self):
        self.panel.saveOptions()
        if self.panel.parent:
            self.panel.parent.remove(self.panel)


    @property
    def filterNames(self):
        names = [moduleDisplayName(module) for module in ALL_FILTER_MODULES.values()]
        names.sort()
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
