import wx
from os.path import isdir, basename, join
from dicomeditor.data_table import DataTable
from dicomeditor.dicom_editor import DICOMEditor, Tag
from dicomeditor.utilities import set_msw_background_color, get_file_paths, get_type, get_selected_listctrl_items


class MainFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.ds = {}

        # Create GUI widgets
        keys =['in_dir', 'tag_group', 'tag_element', 'value', 'out_dir']
        self.input = {key: wx.TextCtrl(self, wx.ID_ANY, "") for key in keys}
        self.input['value_type'] = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.input_obj = [self.input[key] for key in keys]

        keys = ['save', 'quit', 'in_browse', 'out_browse', 'add', 'delete', 'select_all', 'deselect_all']
        self.button = {key: wx.Button(self, wx.ID_ANY, key.replace('_', ' ').title()) for key in keys}

        columns = ['Tag', 'Description', 'Value', 'Value Type']
        data = {c: [''] for c in columns}
        self.list_ctrl = wx.ListCtrl(self, wx.ID_ANY, style=wx.BORDER_SUNKEN | wx.LC_REPORT)
        self.data_table = DataTable(self.list_ctrl, data=data, columns=columns, widths=[100, 200, 150, 100])

        self.label = {key: wx.StaticText(self, wx.ID_ANY, key.replace('_', ' ').title() + ':')
                      for key in ['tag_group', 'tag_element', 'value', 'value_type', 'files_found', 'description']}

        self.file_paths = []
        self.update_files_found()
        
        self.__set_properties()
        self.__do_bind()
        self.__do_layout()
    
    def __set_properties(self):
        set_msw_background_color(self)

        self.button['in_browse'].SetLabel(u"Browse…")
        self.button['out_browse'].SetLabel(u"Browse…")

        self.button['add'].Disable()
        self.button['delete'].Disable()
        self.button['save'].Disable()

        self.input['value_type'].SetItems(['str', 'float', 'int'])
        self.input['value_type'].SetValue('str')
    
    def __do_bind(self):
        for key, button in self.button.items():
            self.Bind(wx.EVT_BUTTON, getattr(self, "on_" + key), id=button.GetId())

        for widget in self.input_obj:
            widget.Bind(wx.EVT_KEY_DOWN, self.on_key_down)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.update_delete_enable, id=self.list_ctrl.GetId())

    def __do_layout(self):
        # Create GUI sizers
        sizer_wrapper = wx.BoxSizer(wx.VERTICAL)
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_input_dir_wrapper = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, "Directory"), wx.VERTICAL)
        sizer_input_dir = wx.BoxSizer(wx.HORIZONTAL)
        sizer_edit_wrapper = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, "Tag Editor"), wx.VERTICAL)
        sizer_edit = wx.BoxSizer(wx.HORIZONTAL)
        sizer_edit_widgets = {key: wx.BoxSizer(wx.VERTICAL)
                              for key in ['tag_group', 'tag_element', 'value', 'value_type', 'add']}
        sizer_edit_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_output_dir_wrapper = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, "Output Directory"), wx.VERTICAL)
        sizer_output_dir = wx.BoxSizer(wx.HORIZONTAL)
        sizer_app_buttons = wx.BoxSizer(wx.HORIZONTAL)

        # Directory Browser
        sizer_input_dir.Add(self.input['in_dir'], 1, wx.EXPAND | wx.ALL, 5)
        sizer_input_dir.Add(self.button['in_browse'], 0, wx.ALL, 5)
        sizer_input_dir_wrapper.Add(sizer_input_dir, 0, wx.ALL | wx.EXPAND, 5)
        sizer_input_dir_wrapper.Add(self.label['files_found'], 0, wx.ALL, 10)
        sizer_main.Add(sizer_input_dir_wrapper, 0, wx.EXPAND | wx.ALL, 5)

        # Input Widgets
        for key in ['tag_group', 'tag_element', 'value', 'value_type']:
            sizer_edit_widgets[key].Add(self.label[key], 0, 0, 0)
            sizer_edit_widgets[key].Add(self.input[key], 0, wx.EXPAND, 0)
            sizer_edit.Add(sizer_edit_widgets[key], 0, wx.EXPAND | wx.ALL, 5)
        sizer_edit_widgets['add'].Add((5, 13), 0, wx.EXPAND, 0)  # Align Button
        sizer_edit_widgets['add'].Add(self.button['add'], 0, wx.EXPAND, 0)
        sizer_edit.Add(sizer_edit_widgets['add'], 0, wx.EXPAND | wx.ALL, 5)
        sizer_edit_wrapper.Add(sizer_edit, 0, wx.EXPAND | wx.ALL, 5)

        sizer_edit_wrapper.Add(self.label['description'], 0, wx.LEFT | wx.BOTTOM, 10)

        sizer_edit_wrapper.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 10)

        for key in ['delete', 'select_all', 'deselect_all']:
            sizer_edit_buttons.Add(self.button[key], 0, wx.EXPAND | wx.RIGHT | wx.LEFT, 5)
        sizer_edit_wrapper.Add(sizer_edit_buttons, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        sizer_main.Add(sizer_edit_wrapper, 1, wx.EXPAND | wx.ALL, 5)

        # Output Directory Browser
        sizer_output_dir.Add(self.input['out_dir'], 1, wx.EXPAND | wx.ALL, 5)
        sizer_output_dir.Add(self.button['out_browse'], 0, wx.ALL, 5)
        sizer_output_dir_wrapper.Add(sizer_output_dir, 0, wx.ALL | wx.EXPAND, 5)
        sizer_main.Add(sizer_output_dir_wrapper, 0, wx.EXPAND | wx.ALL, 5)

        sizer_app_buttons.Add(self.button['save'], 0, wx.ALL, 5)
        sizer_app_buttons.Add(self.button['quit'], 0, wx.ALL, 5)
        sizer_main.Add(sizer_app_buttons, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        sizer_wrapper.Add(sizer_main, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer_wrapper)
        self.Fit()
        self.Center()

    def on_key_down(self, event):
        self.update_description()

        keycode = event.GetKeyCode()
        if keycode == wx.WXK_TAB:
            widget = event.GetEventObject()
            index = self.input_obj.index(widget)
            index = index + 1 if index + 1 < len(self.input_obj) else 0
            self.input_obj[index].SetFocus()
        event.Skip()

    def get_files(self):
        dir_path = self.input['in_dir'].GetValue()
        if isdir(dir_path):
            self.file_paths = get_file_paths(dir_path)
        else:
            self.file_paths = []
        self.update_files_found()

    def update_files_found(self):
        found = len(self.file_paths)
        label = "Files Found: %s" % found
        self.label['files_found'].SetLabel(label)
        self.button['add'].Enable(found > 0)

    @property
    def group(self):
        return self.input['tag_group'].GetValue().replace('(', '').replace(')', '').strip()

    @property
    def element(self):
        return self.input['tag_element'].GetValue().replace('(', '').replace(')', '').strip()

    @property
    def tag(self):
        return Tag(self.group, self.element)

    @property
    def value(self):
        value = self.input['value'].GetValue()
        type_ = get_type(self.input['value_type'].GetValue())
        return type_(value)

    def on_save(self, *evt):
        self.apply_edits()
        self.save_files()

    def on_quit(self, *evt):
        self.Close()

    def on_in_browse(self, *evt):
        starting_dir = self.input['in_dir'].GetValue()
        if not isdir(starting_dir):
            starting_dir = ""

        dlg = wx.DirDialog(self, "Select directory", starting_dir, wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.input['in_dir'].SetValue(dlg.GetPath())
            self.get_files()

        self.ds = {}
        new_file_paths = []
        for f in self.file_paths:
            try:
                self.ds[f] = DICOMEditor(f)
                new_file_paths.append(f)
            except Exception:
                pass
        self.file_paths = new_file_paths

    def on_out_browse(self, *evt):
        starting_dir = self.input['out_dir'].GetValue()
        if not isdir(starting_dir):
            starting_dir = ""

        dlg = wx.DirDialog(self, "Select directory", starting_dir, wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.input['out_dir'].SetValue(dlg.GetPath())
            self.button['save'].Enable()

    def on_add(self, *evt):
        description = self.ds[self.file_paths[0]].get_tag_name(self.tag.tag)
        row = [str(self.tag), description, self.input['value'].GetValue(), self.input['value_type'].GetValue()]
        if self.data_table.has_data and self.data_table.get_row(0)[0]:
            self.data_table.append_row(row)
        else:
            columns = self.data_table.columns
            data = {columns[i]: [value] for i, value in enumerate(row)}
            self.data_table.set_data(data, columns)

        for key in ['tag_group', 'tag_element', 'value']:
            self.input[key].SetValue('')

        self.input['tag_group'].SetFocus()
        self.update_description()

    def on_delete(self, *evt):
        for index in self.selected_indices[::-1]:
            self.data_table.delete_row(index)
        self.update_delete_enable()

    def on_select_all(self, *evt):
        self.data_table.apply_selection_to_all(True)
        self.button['delete'].Enable()

    def on_deselect_all(self, *evt):
        self.data_table.apply_selection_to_all(False)
        self.button['delete'].Disable()

    def update_delete_enable(self, *evt):
        self.button['delete'].Enable(len(self.data_table.selected_row_data))

    @property
    def selected_indices(self):
        return get_selected_listctrl_items(self.list_ctrl)

    def apply_edits(self):
        for ds in self.ds.values():
            for row in range(self.data_table.row_count):
                row_data = self.data_table.get_row(row)
                group = row_data[0].split(',')[0][1:].strip()
                element = row_data[0].split(',')[1][:-1].strip()
                tag = Tag(group, element).tag

                value_str = row_data[2]
                value_type = get_type(row_data[3])
                value = value_type(value_str)

                try:
                    ds.edit_tag(tag, value)
                except Exception:
                    pass

    def save_files(self):
        output_dir = self.input['out_dir'].GetValue()
        prepend = 'copy_' if output_dir == self.input['in_dir'].GetValue() else ''
        for file_path, ds in self.ds.items():
            file_name = basename(file_path)
            if prepend:
                file_name = prepend + file_name
            output_path = join(output_dir, file_name)
            ds.save_as(output_path)

    def update_description(self):
        description = self.description if self.group and self.element else ''
        self.label['description'].SetLabel("Description: %s" % description)
        self.update_tag_type()

    def update_tag_type(self):
        tag = self.tag.tag
        tag_type = 'str'
        for file_path in self.file_paths:
            try:
                tag_type = self.ds[file_path].get_tag_type(tag)
                break
            except Exception:
                pass
        self.input['value_type'].SetValue(tag_type)

    @property
    def description(self):
        for file_path in self.file_paths:
            try:
                return self.ds[file_path].get_tag_name(self.tag.tag)
            except Exception:
                pass
        return 'Not Found'


class MainApp(wx.App):
    def OnInit(self):

        self.SetAppName('DVHA DICOM Editor')
        self.frame = MainFrame(None, wx.ID_ANY, "DVHA DICOM Editor v0.1")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True


def start():
    app = MainApp(0)
    app.MainLoop()