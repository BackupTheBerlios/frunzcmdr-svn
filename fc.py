#!/usr/bin/python2.3
import sys
import os
import profile
import time

import pygtk
pygtk.require('2.0')

import gobject
import gtk
import gtk.glade
import gnome
import gnome.vfs
import gnome.ui
import vte

import bonobo
import bonobo.ui

import threading

#import psyco
#psyco.full()

LEFT = 0
RIGHT = 1

GLADE_FILE = "fc.glade"

def bytes_to_human(bytes):
    if bytes < 1024:
        return str(bytes)+" B"
    elif bytes < 1024*1024:
        return str(bytes/1024)+" kB"
    elif bytes < 1024*1024*1024:
        return str(bytes/1024/1024)+" MB"
    else:
        return str(bytes/1024/1024/1024)+" GB"
    pass

class stock_list(gtk.TreeView):
    def __init__(self):
        gtk.TreeView.__init__(self)
        self.init_model()
        self.init_view_columns()
        
    def init_model(self):
        store = gtk.ListStore(gtk.gdk.Pixbuf, gobject.TYPE_STRING)
        for attr in dir(gtk):
            if attr.startswith('STOCK_'):
                store.append((self.get_icon_pixbuf(attr), 'gtk.%s' % attr))
        self.set_model(store)

    def get_icon_pixbuf(self, stock):
        # Use any technique you like to return a pixbuf to be stored
        # in the model.  We use render_icon() only because we want
        # stock icons for this example.
        return self.render_icon(stock_id=getattr(gtk, stock),
                                size=gtk.ICON_SIZE_MENU,
                                detail=None)

    def init_view_columns(self):
        cell = gtk.CellRendererPixbuf()
        col = gtk.TreeViewColumn('Icon', cell, pixbuf=0)
        self.append_column(col)
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn('Stock Item', cell, text=1)
        self.append_column(col)

class KeyBindings:
    # Key actions              Default key
    KEY_HELP          = 0    # F1
    KEY_EDIT_NAME     = 1    # F2
    KEY_VIEW          = 2    # F3
    KEY_EDIT          = 3    # F4
    KEY_COPY          = 4    # F5
    KEY_MOVE          = 5    # F6
    KEY_MKDIR         = 6    # F7
    KEY_DELETE        = 7    # F8
    KEY_OTHER1        = 8    # F9
    KEY_QUIT          = 9    # F10
    KEY_DOWN_DIR      = 10   # Right
    KEY_UP_DIR        = 11   # Left, Backspace
    KEY_SELECT        = 12   # Insert
    KEY_SWITCH_PANEL  = 13   # Tab
    
    def __init__(self):
        self.proc_bindings = {}
        self.key_bindings = {}

        self.key_bindings[gtk.gdk.keyval_from_name("F1")] = self.KEY_HELP
        self.key_bindings[gtk.gdk.keyval_from_name("F2")] = self.KEY_EDIT_NAME
        self.key_bindings[gtk.gdk.keyval_from_name("F3")] = self.KEY_VIEW
        self.key_bindings[gtk.gdk.keyval_from_name("F4")] = self.KEY_EDIT
        self.key_bindings[gtk.gdk.keyval_from_name("F5")] = self.KEY_COPY
        self.key_bindings[gtk.gdk.keyval_from_name("F6")] = self.KEY_MOVE
        self.key_bindings[gtk.gdk.keyval_from_name("F7")] = self.KEY_MKDIR
        self.key_bindings[gtk.gdk.keyval_from_name("F8")] = self.KEY_DELETE
        self.key_bindings[gtk.gdk.keyval_from_name("F9")] = self.KEY_OTHER1
        self.key_bindings[gtk.gdk.keyval_from_name("F10")] = self.KEY_QUIT
        self.key_bindings[gtk.gdk.keyval_from_name("Right")] = self.KEY_DOWN_DIR
        self.key_bindings[gtk.gdk.keyval_from_name("Left")] = self.KEY_UP_DIR
        self.key_bindings[gtk.gdk.keyval_from_name("Backspace")] = self.KEY_UP_DIR
        self.key_bindings[gtk.gdk.keyval_from_name("Insert")] = self.KEY_SELECT
        self.key_bindings[gtk.gdk.keyval_from_name("Tab")] = self.KEY_SWITCH_PANEL
        pass
    
    def def_proc_binding(self, key_action, key_func, chk_active_func):
        if self.proc_bindings.has_key(key_action):
            self.proc_bindings[key_action] = self.proc_bindings[key_action] + [(key_func, chk_active_func)]
        else:
            self.proc_bindings[key_action] = [(key_func, chk_active_func)]
        pass
     
    def process_key(self, key_val):
        if self.key_bindings.has_key(key_val):
            key_action = self.key_bindings[key_val]
            if self.proc_bindings.has_key(key_action):
                for (key_func, chk_active_func) in self.proc_bindings[key_action]:
                    if chk_active_func():
                        key_func()
                        return True
                    pass
                pass
            pass
        return False
    
    pass

TV_CLMN_FILE_INFO = 0
TV_CLMN_FILE = 1
TV_CLMN_PIX = 3
TV_CLMN_BG_SET = 4
TV_CLMN_BG = 5
class DirCacheEntry(gtk.ListStore):
    def __init__(self, dh, dir_uri):
        self.dh = dh
        self.dir_uri = dir_uri
        self.path = "0"
        gtk.ListStore.__init__(self,
                               gobject.TYPE_PYOBJECT, # 0-fi
                               gobject.TYPE_STRING,   # 1-name for displaying
                               gobject.TYPE_STRING,   # 2-name for sorting
                               gtk.gdk.Pixbuf,        # 3-icon
                               'gboolean',            # 4-selected
                               str)                   # 5-selection bg color

        while True:
            try:
                fi = dh.next()
                self.__append(fi)
            except StopIteration:
                break
            pass
        self.sort()

        gnome.vfs.monitor_add(str(dir_uri),
                              gnome.vfs.MONITOR_DIRECTORY,
                              self.__monitor_cb, 0)
        
        pass

    def __monitor_cb(self, monitor_uri, info_uri, event_type, data):
        print "monitor"
        
        if event_type == gnome.vfs.MONITOR_EVENT_CHANGED:
            pass
        elif event_type == gnome.vfs.MONITOR_EVENT_DELETED:
            print "monitor: removed directory entry: %s" % str(info_uri)
            self.__remove(info_uri)
            self.sort()
        elif event_type == gnome.vfs.MONITOR_EVENT_STARTEXECUTING:
            pass
        elif event_type == gnome.vfs.MONITOR_EVENT_STOPEXECUTING:
            pass
        elif event_type == gnome.vfs.MONITOR_EVENT_CREATED:
            print "monitor: added directory entry: %s" % str(info_uri)
            try:
                fi = gnome.vfs.get_file_info(info_uri)
            except gnome.vfs.NotFoundError:
                return
            self.__append(fi)
            self.sort()
        elif event_type == gnome.vfs.MONITOR_EVENT_METADATA_CHANGED:
            pass
        pass
    
    def __append(self, fi):
        disp_name = fi.name.replace("&", "&amp;")
        if fi.valid_fields & gnome.vfs.FILE_INFO_FIELDS_TYPE:
            if fi.type == gnome.vfs.FILE_TYPE_DIRECTORY:
                sort_name = "a" + fi.name
                disp_name = "<b>/" + disp_name + "</b>"
            elif fi.type == gnome.vfs.FILE_TYPE_REGULAR:
                sort_name = "b" + fi.name
            elif fi.type == gnome.vfs.FILE_TYPE_SYMBOLIC_LINK:
                sort_name = "c" + fi.name
                disp_name = "<b>~</b>" + disp_name
            elif fi.type == gnome.vfs.FILE_TYPE_FIFO:
                sort_name = "d" + fi.name
                disp_name = "<b>|</b>" + disp_name
            elif fi.type == gnome.vfs.FILE_TYPE_SOCKET:
                sort_name = "e" + fi.name
                disp_name = "<b>=</b>" + disp_name
            elif fi.type == gnome.vfs.FILE_TYPE_CHARACTER_DEVICE:
                sort_name = "f" + fi.name
                disp_name = "<b>-</b>" + disp_name
            elif fi.type == gnome.vfs.FILE_TYPE_BLOCK_DEVICE:
                sort_name = "g" + fi.name
                disp_name = "<b>+</b>" + disp_name
            else:
                sort_name = "h" + fi.name
                disp_name = "<b>?</b>" + disp_name
                pass
            pass
        else:
            sort_name = fi.name
            disp_name = disp_name
            pass

        gtk.ListStore.append(self,
                             (fi,
                              disp_name,
                              sort_name,
                              None,
                              False,
                              "LightBlue"))
        
        pass

    def __remove(self, uri):
        for row in self:
            if str(self.dir_uri)+"/"+row[0].name == uri:
                gtk.ListStore.remove(self, row.iter)
                break
            pass
        pass

    def sort(self):
        gtk.ListStore.set_sort_column_id(self, 2, gtk.SORT_ASCENDING)
        pass

class Dialog:
    pass

class CopyDialog(Dialog):
    def __init__(self):
        xml = gtk.glade.XML(GLADE_FILE, "dlg_cpy")
        self.xml = xml
        
        self.dlg_cpy = xml.get_widget('dlg_cpy')
        self.lbl_cpy_src = xml.get_widget('lbl_cpy_src')
        self.ent_cpy_dest = xml.get_widget('ent_cpy_dest')
        pass

    def run(self, file_list, dest_dir):
        self.lbl_cpy_src.set_markup("<i>Copy</i> <b>"+file_list+"</b>   ")
        self.ent_cpy_dest.set_text(dest_dir)
        response = self.dlg_cpy.run()
        self.dlg_cpy.hide()
        if response != gtk.RESPONSE_OK:
            return (False, None)
        return (True, self.ent_cpy_dest.get_text())
    pass

class ProgressDialog(Dialog):
    def __init__(self, title):
        xml = gtk.glade.XML(GLADE_FILE, "dlg_prgrs")
        self.xml = xml

        self.dlg_prgrs = xml.get_widget('dlg_prgrs')
        self.lbl_prgrs = xml.get_widget('lbl_prgrs')
        self.prgrs_bar = xml.get_widget("prgrs_bar")
        self.btn_prgrs_ok = xml.get_widget('btn_prgrs_ok')
        self.btn_prgrs_cancel = xml.get_widget('btn_prgrs_cancel')
        self.btn_prgrs_dock = xml.get_widget('btn_prgrs_dock')

        self.dlg_prgrs.set_title(title)

        self.step = 0.1
        self.start = time.time()
        pass

    def run(self):
        response = self.dlg_prgrs.run()
        self.dlg_prgrs.hide()
        if response == gtk.RESPONSE_CANCEL:
            return False
        elif response == gtk.RESPONSE_CLOSE:
            return False
        return True

    def progress(self, progress, txt):
        self.lbl_prgrs.set_text(txt)
        self.prgrs_bar.set_fraction(progress)
        pass

    def completed(self):
        self.btn_prgrs_ok.show()
        self.btn_prgrs_cancel.hide()
        pass        

class Panel:
    def __init__(self, tv, cmb, lbl, dir_cache, xml, key_bindings):
        self.tv = tv
        self.cmb = cmb
        self.lbl = lbl
        self.dir_cache = {} #dir_cache
        self.xml = xml

        self.key_bindings = key_bindings
        self.bind_keys()

        self.active = False

        self.appbar = xml.get_widget('appbar')
        self.dlg_mkdir = xml.get_widget('dlg_mkdir')
        self.ent_mkdir = xml.get_widget('ent_mkdir')

        self.tv.get_selection().set_mode(gtk.SELECTION_SINGLE)

        cwd = os.getcwd()
        self.curr_path = 0
        self.curr_iter = None

        renderer = gtk.CellRendererPixbuf()
        clmn = gtk.TreeViewColumn("Icon", renderer, pixbuf=TV_CLMN_PIX)
        self.tv.append_column(clmn)
        renderer = gtk.CellRendererText()
        clmn = gtk.TreeViewColumn("Name", renderer,
                                  markup=TV_CLMN_FILE,
                                  background_set=TV_CLMN_BG_SET,
                                  background=TV_CLMN_BG)
        self.tv.append_column(clmn)

        self.tv.connect("cursor_changed", self.on_tv_cursor_changed)
        self.tv.connect("row_activated", self.on_tv_row_activated)
        self.tv.connect("select_cursor_parent", self.on_tv_select_cursor_parent)
        
        self.cmb.connect("activate", self.on_cmb_activate)

        self.__load_list(gnome.vfs.URI("file://"+cwd))

        self.tv.show()
        pass

    def chk_active(self):
        return self.active

    def activate(self):
        self.active = True
        self.tv.grab_focus()
        pass

    def deactivate(self):
        self.active = False
        pass
    
    def bind_keys(self):
        self.key_bindings.def_proc_binding(KeyBindings.KEY_UP_DIR, self.act_chdir_up, self.chk_active)
        self.key_bindings.def_proc_binding(KeyBindings.KEY_DOWN_DIR, self.act_chdir_down, self.chk_active)
        self.key_bindings.def_proc_binding(KeyBindings.KEY_EDIT_NAME, self.act_edit_name, self.chk_active)
        self.key_bindings.def_proc_binding(KeyBindings.KEY_VIEW, self.act_view_file, self.chk_active)
        self.key_bindings.def_proc_binding(KeyBindings.KEY_MKDIR, self.act_mkdir, self.chk_active)
        self.key_bindings.def_proc_binding(KeyBindings.KEY_DELETE, self.act_delete, self.chk_active)
        self.key_bindings.def_proc_binding(KeyBindings.KEY_SELECT,  self.act_select, self.chk_active)
        pass

    def act_view_file(self):
        print "ACT: View"
        model = self.model
        iter = model.get_iter(self.curr_path)
        fi = model.get_value(iter, TV_CLMN_FILE_INFO)
        print "file "+fi.name
        uri = model.dir_uri.append_path(fi.name)
        print uri
        uic = bonobo.ui.Container()
        control = bonobo.ui.Widget("OAFIID:Nautilus_Text_View", uic.corba_objref())
        control.show()
        obj = control.get_objref().queryInterface("IDL:Nautilus/View:1.0")
        obj.load_location(str(uri))
        obj.unref()
        self.vbox = self.xml.get_widget('vbox')
        self.vbox1 = self.xml.get_widget('vbox1')
        self.vbox.remove(self.vbox1)
        self.vbox.pack_start(control)
        pass
    
    def act_edit_name(self):
        print "ACT: Edit name"
        self.tv.set_cursor(self.curr_path, start_editing=gtk.TRUE)
        pass

    def act_select(self):
        #print "ACT: Select"
        bg_set = not self.model.get_value(self.curr_iter, TV_CLMN_BG_SET)
        self.model.set_value(self.curr_iter, TV_CLMN_BG_SET, bg_set)
        try:
            self.tv.set_cursor(self.curr_path[0] + 1)
        except TypeError:
            pass
        pass

    def act_chdir_up(self):
        print "ACT: Chdir up"
        dir = str(self.model.dir_uri).strip("/").split("/")[-1]
        self.__load_list(self.model.dir_uri.append_path(".."))
        self.__goto_entry(dir)
        pass

    def act_chdir_down(self):
        print "ACT: Chdir down"
        fi = self.model.get_value(self.curr_iter, TV_CLMN_FILE_INFO)
        self.__load_list(self.model.dir_uri.append_path(fi.name))
        self.__goto_entry("..")
        pass

    def act_mkdir(self):
        print "ACT: Mkdir"
        response = self.dlg_mkdir.run()
        self.dlg_mkdir.hide()
        if response != gtk.RESPONSE_OK:
            return

        new_dir = self.ent_mkdir.get_text()
        if new_dir == "":
            return
        new_dir_uri = self.model.dir_uri.append_path(new_dir)
        gnome.vfs.make_directory(new_dir_uri, 0755)
        print new_dir_uri
        pass

    def act_delete(self):
        print "ACT: Delete"
        uri, fname = self.get_selected_entry()
        self.lbl_cpy_src.set_markup("<i>Copy</i> <b>"+str(s_uri)+"</b>   ")
        self.ent_cpy_dest.set_text(str(d_uri))
        response = self.dlg_cpy.run()
        self.dlg_cpy.hide()
        if response != gtk.RESPONSE_OK:
            return
        print "from "+str(s_uri)
        print "to "+str(d_uri)
        try:
            gnome.vfs.xfer_uri(s_uri, d_uri,
                               gnome.vfs.XFER_DEFAULT,
                               gnome.vfs.XFER_ERROR_ACTION_SKIP,
                               gnome.vfs.XFER_OVERWRITE_ACTION_ABORT,
                               self.progress_cb, 0)
        except gnome.vfs.InterruptedError:
            print "Cannot copy: " + str(gnome.vfs.InterruptedError)
            pass
        self.dlg_prgrs.set_title("Deleting")
        response = self.dlg_prgrs.run()
        if not ok:
            print "Cancel"
            pass
        pass
    
    def on_tv_cursor_changed(self, widget):
        (self.curr_path, column) = self.tv.get_cursor()
        if self.curr_path == None:
            return
        self.curr_iter = self.model.get_iter(self.curr_path)
        fi = self.model.get_value(self.curr_iter, TV_CLMN_FILE_INFO)

        #name
        name = "<b>"+fi.name+"</b>"
        
        #determine permissions
        if fi.valid_fields & gnome.vfs.FILE_INFO_FIELDS_PERMISSIONS:
            perm_u = ["-","-","-"]
            perm_g = ["-","-","-"]
            perm_o = ["-","-","-"]
            if fi.permissions & gnome.vfs.PERM_USER_READ:
                perm_u[0] = "r"
            if fi.permissions & gnome.vfs.PERM_USER_WRITE:
                perm_u[1] = "w"
            if fi.permissions & gnome.vfs.PERM_USER_EXEC:
                perm_u[2] = "x"
            perm_u = "".join(perm_u)
            if fi.permissions & gnome.vfs.PERM_GROUP_READ:
                perm_g[0] = "r"
            if fi.permissions & gnome.vfs.PERM_GROUP_WRITE:
                perm_g[1] = "w"
            if fi.permissions & gnome.vfs.PERM_GROUP_EXEC:
                perm_g[2] = "x"
            perm_g = "".join(perm_g)
            if fi.permissions & gnome.vfs.PERM_OTHER_READ:
                perm_o[0] = "r"
            if fi.permissions & gnome.vfs.PERM_OTHER_WRITE:
                perm_o[1] = "w"
            if fi.permissions & gnome.vfs.PERM_OTHER_EXEC:
                perm_o[2] = "x"
            perm_o = "".join(perm_o)
            
            if os.geteuid() == fi.uid:
                perm_u = "<b>"+perm_u+"</b>"
            elif os.getegid() == fi.gid:
                perm_g = "<b>"+perm_g+"</b>"
            else:
                perm_o = "<b>"+perm_o+"</b>"
                pass

            perm = perm_u + perm_g + perm_o
        else:
            perm = ""
            pass

        #determine size
        if fi.valid_fields & gnome.vfs.FILE_INFO_FIELDS_SIZE:
            size = bytes_to_human(fi.size)
            pass
        else:
            size = ""
            pass

        #determine modification time
        if fi.valid_fields & gnome.vfs.FILE_INFO_FIELDS_MTIME:
            t = time.strftime("%b %d %H:%M", time.gmtime(fi.mtime))
        else:
            t = ""
            pass

        #set label
        sep = "  <span foreground='blue' weight='bold'>/</span>  "
        self.lbl.set_markup(name + sep + t + sep + size + sep + perm)
        pass

    def on_tv_row_activated(self, treeview, path, view_column):
        self.__activate(path)
        pass

    def on_tv_select_cursor_parent(self, widget):
        self.act_chdir_up()
        pass

    def on_cmb_activate(self, widget):
        self.__chdir_to()
        pass

    def __chdir_to(self):
        self.__load_list(gnome.vfs.URI(self.cmb.entry.get_text()))
        #self.__goto_entry("..")
        pass

    def __load_list(self, dir_uri):
        try:
            dh = gnome.vfs.DirectoryHandle(dir_uri)
        except gnome.vfs.InvalidURIError:
            return
        except gnome.vfs.AccessDeniedError:
            self.appbar.set_status("Access denied")
            return

        if not self.dir_cache.has_key(str(dir_uri)):
            self.model = DirCacheEntry(dh, dir_uri)
            self.dir_cache[str(dir_uri)] = self.model
        else:
            self.model = self.dir_cache[str(dir_uri)]
            pass
        self.tv.set_model(self.model)

        listitem = gtk.ListItem(str(dir_uri))
        self.cmb.list.append_items([listitem])
        listitem.show()        
        self.cmb.entry.set_text(str(dir_uri))
        
        #model.set_sort_column_id(1, gtk.SORT_ASCENDING)
        self.tv.show()
        pass

    def __fe_goto_entry(self, model, path, iter, dir):
        d = model.get_value(iter, TV_CLMN_FILE)
        if len(d) < 9:
            return gtk.FALSE
        if d[4:-4] == dir:
            self.curr_path = path
            return gtk.TRUE
        return gtk.FALSE

    def __goto_entry(self, dir):
        self.model.foreach(self.__fe_goto_entry, dir)
        self.tv.set_cursor(self.curr_path)
        #self.tv.scroll_to_cell(self.curr_path)
        pass
    
    def __activate(self, path):
        model = self.model
        iter = model.get_iter(path)
        fi = model.get_value(iter, TV_CLMN_FILE_INFO)
        uri = model.dir_uri.append_path(fi.name)

        if fi.valid_fields & gnome.vfs.FILE_INFO_FIELDS_TYPE == 0:
            return

        if fi.type == gnome.vfs.FILE_TYPE_DIRECTORY:
            print uri
            self.__load_list(uri)
            self.__goto_entry("..")
        elif fi.type == gnome.vfs.FILE_TYPE_REGULAR:
            mime_type = gnome.vfs.get_mime_type(str(uri))
            app = gnome.vfs.mime_get_default_application(mime_type)
            file = str(uri).replace("file://", "")
            os.spawnlp(os.P_NOWAIT, app[2], app[2], file)
            pass
        pass

    def get_selected_entry(self):
        fi = self.model.get_value(self.curr_iter, TV_CLMN_FILE_INFO)
        return self.model.dir_uri.append_path(fi.name), fi.name

    def get_curr_dir(self):
        return self.model.dir_uri

class Thr(threading.Thread):
    def __init__(self, func, args):
        threading.Thread.__init__(self)
        self.func = func
        self.args = args
        pass

    def run(self):
        self.func(*self.args)
        pass

class Fc:

    def child_died_event(self, terminal):
        gtk.main_quit()
        pass

    def on_switch_to_shell_panels_activate(self, widget):
        print "aaa"
        if self.switch_shell_panels == 0:
            self.vbox.remove(self.vbox1)
            self.vbox.pack_start(self.hbox)
            self.switch_shell_panels = 1
        elif self.switch_shell_panels == 1:
            self.vbox.remove(self.hbox)
            self.vbox.pack_start(self.vbox1)
            self.switch_shell_panels = 0
        pass

    def on_switch_other_panel_activate(self, widget):
        self.act_switch_panel()
        pass

    def on_app_key_press_event(self, widget, event):
        #print event.keyval
        if self.key_bindings.process_key(event.keyval):
            return gtk.TRUE
        return gtk.FALSE

    def chk_active(self):
        return True

    def bind_keys(self):
        self.key_bindings.def_proc_binding(KeyBindings.KEY_SWITCH_PANEL, self.act_switch_panel, self.chk_active)
        self.key_bindings.def_proc_binding(KeyBindings.KEY_COPY, self.act_copy, self.chk_active)
        self.key_bindings.def_proc_binding(KeyBindings.KEY_QUIT, self.act_quit, self.chk_active)
        pass

    def act_switch_panel(self):
        #print "ACT: Switch panels"
        self.current = 1 - self.current
        self.panel_other = self.panel_curr
        self.panel_other.deactivate()
        self.panel_curr = self.panel[self.current]
        self.panel_curr.activate()

    def act_quit(self):
        print "ACT: Quit"
        gtk.main_quit()
        pass

    def progress_cb(self, info, dlg):
        #print "status: %d" % info.status

        if info.status == gnome.vfs.XFER_PROGRESS_STATUS_VFSERROR:
            print "Error"
            return 0

        #print "phase: %d" % info.phase

        if info.phase == gnome.vfs.XFER_PHASE_COPYING:
            progress = info.total_bytes_copied / float(info.bytes_total)
            if progress > dlg.step or progress == 1:
                if progress == 1:
                    stop = time.time()
                    elapsed = stop - dlg.start
                    speed = info.total_bytes_copied / elapsed
                    txt = "Copied %s in %f seconds (%s/s)" % (bytes_to_human(info.total_bytes_copied),
                                                              elapsed,
                                                              bytes_to_human(speed))
                else:
                    txt = "Copied %s/%s %d%%" % (bytes_to_human(info.total_bytes_copied),
                                                 bytes_to_human(info.bytes_total),
                                                 int(progress*100))
                    pass
                gtk.gdk.threads_enter()
                dlg.progress(progress, txt)
                gtk.gdk.threads_leave()
                dlg.step = dlg.step + 0.1
                pass
            pass
        elif info.phase == gnome.vfs.XFER_PHASE_COMPLETED:
            gtk.gdk.threads_enter()
            dlg.completed()
            gtk.gdk.threads_leave()
            pass
        
        return 1

    def __xfer_uri(self, s_uri, d_uri, opt, err_mode, ovwr_mode, cb, arg):
        print "start xfer_uri 1"
        try:
            print "start xfer_uri"
            gnome.vfs.xfer_uri(s_uri, d_uri, opt, err_mode, ovwr_mode,
                               cb, arg)
            print "xfer_uri done"
        except gnome.vfs.InterruptedError:
            print "Cannot copy: " + str(gnome.vfs.InterruptedError)
            pass
        pass

    def act_copy(self):
        print "ACT: Copy"
        s_uri, fname = self.panel_curr.get_selected_entry()
        d_uri = self.panel_other.get_curr_dir().append_path(fname)

        dlg = CopyDialog()
        (success, dest) = dlg.run(str(s_uri), str(d_uri))
        if not success:
            return

        print "%s %s" % (str(s_uri), str(gnome.vfs.URI(dest)))

        dlg = ProgressDialog("Copying")
        t = Thr(self.__xfer_uri,
                [s_uri, gnome.vfs.URI(dest),
                 gnome.vfs.XFER_DEFAULT,
                 gnome.vfs.XFER_ERROR_MODE_ABORT,
                 gnome.vfs.XFER_OVERWRITE_MODE_SKIP,
                 self.progress_cb, dlg])
        t.start()
        
        ok = dlg.run()
        if not ok:
            print "Cancel"
            pass
        t.join()
        
        pass
    
    def act_copy2(self):
        print "ACT: Copy"
        s_uri, fname = self.panel_curr.get_selected_entry()
        d_uri = self.panel_other.get_curr_dir().append_path(fname)

        self.lbl_cpy_src.set_markup("<i>Copy</i> <b>"+str(s_uri)+"</b>   ")
        self.ent_cpy_dest.set_text(str(d_uri))
        response = self.dlg_cpy.run()
        self.dlg_cpy.hide()
        if response != gtk.RESPONSE_OK:
            return
        print "from "+str(s_uri)
        print "to "+str(d_uri)
        try:
            gnome.vfs.xfer_uri(s_uri, d_uri,
                               gnome.vfs.XFER_DEFAULT,
                               gnome.vfs.XFER_ERROR_ACTION_SKIP,
                               gnome.vfs.XFER_OVERWRITE_ACTION_ABORT,
                               self.progress_cb, 0)
        except gnome.vfs.InterruptedError:
            print "Cannot copy: " + str(gnome.vfs.InterruptedError)
            pass
        self.dlg_prgrs.set_title("Copying")
        response = self.dlg_prgrs.run()
        if response == gtk.RESPONSE_CANCEL:
            print "Cancel"
        elif response == gtk.RESPONSE_CLOSE:
            print "Dock"
            pass
        pass

    def __init__(self):

        self.key_bindings = KeyBindings()
        self.bind_keys()

        
        #self.gnomeApp = gnome.ui.GnomeApp(self, 'pygnome-hello-world', 'pygnome_hello')
	#self.gnomeApp.set_wmclass('pygnome_hello', 'pygnome_hello')
        gnome.init("FC", "FC")
        
        self.switch_shell_panels = 0
        self.current = LEFT
        
        #font_name = "-misc-fixed-medium-r-normal--20-200-75-75-c-100-*-*"
        font_name = "fixed 12"
        xml = gtk.glade.XML(GLADE_FILE)
        self.xml= xml
        app = xml.get_widget('app')
        self.vbox = xml.get_widget('vbox')
        self.vbox1 = xml.get_widget('vbox1')
        self.appbar = xml.get_widget('appbar')
        
        xml.signal_autoconnect({
            'on_win_destroy': gtk.main_quit,
            'on_switch_to_shell_panels_activate': self.on_switch_to_shell_panels_activate,
            'on_switch_other_panel_activate': self.on_switch_other_panel_activate,
            'on_app_key_press_event': self.on_app_key_press_event
            })
        
        app.connect("delete_event", gtk.main_quit)
        app.set_title("Frunz Commander")
        app.set_resizable(gtk.TRUE);

        self.hbox = gtk.HBox()
        self.hbox.show()

        term = vte.Terminal()
        term.set_scrollback_lines(50)
        term.set_font_from_string(font_name);
        term.connect("child-exited", self.child_died_event)
        self.hbox.pack_start(term)
        term.show()

        self.vbox.show()

        #charwidth = term.charwidth
        #charheight = term.charheight

        #app.set_geometry_hints(geometry_widget=term,
        #                    min_width=2*charwidth, min_height=2*charheight,
        #                    base_width=charwidth,  base_height=charheight,
        #                    width_inc=charwidth,   height_inc=charheight)

        self.dir_cache = {}

        self.panel = []
        self.panel.append(Panel(xml.get_widget('tv_left'),
                                xml.get_widget('cmb_left'),
                                xml.get_widget('lbl_left'),
                                self.dir_cache,
                                xml,
                                self.key_bindings))
        self.panel.append(Panel(xml.get_widget('tv_right'),
                                xml.get_widget('cmb_right'),
                                xml.get_widget('lbl_right'),
                                self.dir_cache,
                                xml,
                                self.key_bindings))


        self.panel[self.current].activate()

        self.panel_curr = self.panel[self.current]
        self.panel_other = self.panel[1 - self.current]

        app.show()

        #pid = term.fork_command()
        #pid = term.fork_command("/bin/bash")
        #if pid == -1:
        #    print "Couldn't fork"
        #    sys.exit(1)
        #if pid == 0:
        #    os.execv('/bin/bash', ['/bin/bash'])
        #    #os.execv('/usr/bin/env', ['/usr/bin/env', 'python'])

        gtk.gdk.threads_init()
        gtk.main()
        pass


fc = Fc()


# setting icon
#             #mime_type = gnome.vfs.get_mime_type(str(uri))
#             #stock_icon = gnome.vfs.mime_get_icon(mime_type)
#             #if stock_icon != None and stock_icon != "":
#             #    stock_icon = "/usr/share/pixmaps/gnome-commander/mime-icons/"+stock_icon+".png"
#             #    print "mime: ", mime_type
#             #    print "stock: ", stock_icon
#             #    #icon = treeview.render_icon(gtk.STOCK_OPEN,
#             #    #                            size=gtk.ICON_SIZE_MENU,
#             #    #                            detail=None)
#             #    #icon = gtk.gdk.pixbuf_new_from_file(stock_icon)
#             #    icon = None
#             #else:
#             #    icon = None
#             icon = None    
#             model.set_value(iter, 3, icon)
