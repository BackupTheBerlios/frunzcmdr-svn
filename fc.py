#!/usr/bin/python2.3
import sys
import os

import pygtk
pygtk.require('2.0')

import gobject
import gtk
import gtk.glade
import gnome.zvt
import gnome.vfs
import gnome.ui

import profile

import time

LEFT = 0
RIGHT = 1

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

class DirCacheEntry(gtk.ListStore):
    def __init__(self, uri):
        self.uri = uri
        self.path = "0"
        gtk.ListStore.__init__(self,
                               gobject.TYPE_PYOBJECT, # 0-fi
                               gobject.TYPE_STRING,   # 1-name for displaying
                               gobject.TYPE_STRING,   # 2-name for sorting
                               gtk.gdk.Pixbuf,        # 3-icon
                               'gboolean',            # 4-selected
                               str)                   # 5-selection bg color
        pass

    def append(self, fi):
        disp_name = fi.name.replace("&", "&amp;")
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

        gtk.ListStore.append(self,
                             (fi,
                              disp_name,
                              sort_name,
                              None,
                              False,
                              "LightBlue"))
        
        pass

    def sort(self):
        gtk.ListStore.set_sort_column_id(self, 2, gtk.SORT_ASCENDING)
        pass
        

class Panel:
    def __init__(self, tv, cmb, lbl, dir_cache):
        self.tv = tv
        self.cmb = cmb
        self.lbl = lbl
        self.dir_cache = {} #dir_cache

        self.tv.get_selection().set_mode(gtk.SELECTION_NONE)

        cwd = os.getcwd()
        self.curr_path = 0
        self.curr_iter = None

        renderer = gtk.CellRendererPixbuf()
        clmn = gtk.TreeViewColumn("Icon", renderer, pixbuf=3)
        self.tv.append_column(clmn)
        renderer = gtk.CellRendererText()
        clmn = gtk.TreeViewColumn("Name", renderer, markup=1,
                                  background_set=4, background=5)
        self.tv.append_column(clmn)

        self.tv.connect("key_press_event", self.on_tv_key_press_event)
        self.tv.connect("cursor_changed", self.on_tv_cursor_changed)
        self.tv.connect("row_activated", self.on_tv_row_activated)
        self.tv.connect("select_cursor_parent", self.on_tv_select_cursor_parent)
        
        self.cmb.connect("activate", self.on_cmb_activate)

        self.__load_list(gnome.vfs.URI("file://"+cwd))

        self.tv.show()
        pass

    def on_tv_key_press_event(self, widget, event):
        if event.keyval == gtk.gdk.keyval_from_name("Left"):
            self.__chdir_up()
            return gtk.TRUE
        elif event.keyval == gtk.gdk.keyval_from_name("Right"):
            self.__chdir_down()
            return gtk.TRUE
        elif event.keyval == gtk.gdk.keyval_from_name("F2"):
            print "F2"
            self.tv.set_cursor(self.curr_path, start_editing=gtk.TRUE)
            return gtk.TRUE
        elif event.keyval == gtk.gdk.keyval_from_name("F3"):
            print "F3"
            return gtk.TRUE
        elif event.keyval == gtk.gdk.keyval_from_name("F4"):
            print "F4"
            return gtk.TRUE
        elif event.keyval == gtk.gdk.keyval_from_name("F5"):
            print "F5"
            return gtk.TRUE
        elif event.keyval == gtk.gdk.keyval_from_name("F6"):
            print "F6"
            return gtk.TRUE
        elif event.keyval == gtk.gdk.keyval_from_name("F7"):
            print "F7"
            return gtk.TRUE
        elif event.keyval == gtk.gdk.keyval_from_name("F8"):
            print "F8"
            return gtk.TRUE
        elif event.keyval == gtk.gdk.keyval_from_name("F9"):
            print "F9"
            return gtk.TRUE
        elif event.keyval == gtk.gdk.keyval_from_name("Insert"):
            print "Insert"
            bg_set = not self.model.get_value(self.curr_iter, 4)
            self.model.set_value(self.curr_iter, 4, bg_set)
            self.tv.set_cursor(self.curr_path[0] + 1)
            return gtk.TRUE
        return gtk.FALSE

    def on_tv_cursor_changed(self, widget):
        (self.curr_path, column) = self.tv.get_cursor()
        self.curr_iter = self.model.get_iter(self.curr_path)
        fi = self.model.get_value(self.curr_iter, 0)

        #name
        name = "<b>"+fi.name+"</b>"
        #determine permissions
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

        #determine size
        if fi.size < 1024:
            size = str(fi.size)+"B"
        elif fi.size < 1024*1024:
            size = str(fi.size/1024)+"kB"
        elif fi.size < 1024*1024*1024:
            size = str(fi.size/1024/1024)+"MB"
        else:
            size = str(fi.size/1024/1024/1024)+"GB"
            pass

        #determine modification time
        t = time.strftime("%b %d %H:%M", time.gmtime(fi.mtime))

        #set label
        sep = "  <span foreground='blue' weight='bold'>/</span>  "
        self.lbl.set_markup(name + sep + t + sep + size + sep + perm)
        pass

    def on_tv_row_activated(self, treeview, path, view_column):
        self.__activate(path)
        pass

    def on_tv_select_cursor_parent(self, widget):
        self.__chdir_up()
        pass

    def on_cmb_activate(self, widget):
        self.__chdir_to()
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
            dir_cache_entry = DirCacheEntry(dir_uri)
            self.dir_cache[str(dir_uri)] = dir_cache_entry
            cached = False
        else:
            cached = True
            dir_cache_entry = self.dir_cache[str(dir_uri)]
            pass

        listitem = gtk.ListItem(str(dir_uri))
        self.cmb.list.append_items([listitem])
        listitem.show()        
        self.cmb.entry.set_text(str(dir_uri))
        
        if not cached:
            print "from disc"
            entries = []
            while True:
                try:
                    fi = dh.next()
                    dir_cache_entry.append(fi)
                except StopIteration:
                    break
                pass
            dir_cache_entry.sort()
            pass
        self.model = dir_cache_entry
        self.tv.set_model(dir_cache_entry)

        #model.set_sort_column_id(1, gtk.SORT_ASCENDING)
        self.tv.show()
        pass

    def __fe_goto_entry(self, model, path, iter, dir):
        d = model.get_value(iter, 1)
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
    
    def __chdir_up(self):
        dir = str(self.model.uri).strip("/").split("/")[-1]
        self.__load_list(self.model.uri.append_path(".."))
        self.__goto_entry(dir)
        pass

    def __chdir_down(self):
        fi = self.model.get_value(self.curr_iter, 0)
        self.__load_list(self.model.uri.append_path(fi.name))
        self.__goto_entry("..")
        pass

    def __chdir_to(self):
        self.__load_list(gnome.vfs.URI(self.cmb.entry.get_text()))
        self.__goto_entry("..")
        pass

    def __activate(self, path):
        model = self.model
        iter = model.get_iter(path)
        fi = model.get_value(iter, 0)
        uri = model.uri.append_path(fi.name)

        if fi.type == gnome.vfs.FILE_TYPE_DIRECTORY:
            self.__load_list(uri)
            self.__goto_entry("..")
        elif fi.type == gnome.vfs.FILE_TYPE_REGULAR:
            mime_type = gnome.vfs.get_mime_type(str(uri))
            app = gnome.vfs.mime_get_default_application(mime_type)
            file = str(uri).replace("file://", "")
            os.spawnlp(os.P_NOWAIT, app[2], app[2], file)
            pass
        pass

class Fc:

    def child_died_event(self, zvt):
        gtk.main_quit()
        pass

    def on_switch_to_shell_panels_activate(self, widget):
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
        self.current = 1 - self.current
        self.panel[self.current].tv.grab_focus()
        pass

    def on_app_key_press_event(self, widget, event):
        #print event.keyval
        if event.keyval == gtk.gdk.keyval_from_name("Tab"):
            self.current = 1 - self.current
            self.panel[self.current].tv.grab_focus()
            return gtk.TRUE
        elif event.keyval == gtk.gdk.keyval_from_name("F1"):
            print "F1"
            return gtk.TRUE
        elif event.keyval == gtk.gdk.keyval_from_name("F10"):
            print "F10"
            gtk.main_quit()
            return gtk.TRUE
        return gtk.FALSE

    def __init__(self):
        #self.gnomeApp = gnome.ui.GnomeApp(self, 'pygnome-hello-world', 'pygnome_hello')
	#self.gnomeApp.set_wmclass('pygnome_hello', 'pygnome_hello')
        gnome.init("FC", "FC")
        
        self.switch_shell_panels = 0
        self.current = LEFT
        
        font_name = "-misc-fixed-medium-r-normal--20-200-75-75-c-100-*-*"
        xml = gtk.glade.XML('fc.glade')
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

        term = gnome.zvt.Term(80, 25)
        term.set_scrollback(50)
        term.set_font_name(font_name);
        term.connect("child_died", self.child_died_event)
        self.hbox.pack_start(term)
        term.show()

        self.vbox.show()

        charwidth = term.charwidth
        charheight = term.charheight

        app.set_geometry_hints(geometry_widget=term,
                            min_width=2*charwidth, min_height=2*charheight,
                            base_width=charwidth,  base_height=charheight,
                            width_inc=charwidth,   height_inc=charheight)

        self.dir_cache = {}

        self.panel = []
        self.panel.append(Panel(xml.get_widget('tv_left'),
                                xml.get_widget('cmb_left'),
                                xml.get_widget('lbl_left'),
                                self.dir_cache))
        self.panel.append(Panel(xml.get_widget('tv_right'),
                                xml.get_widget('cmb_right'),
                                xml.get_widget('lbl_right'),
                                self.dir_cache))


        app.show()
        self.panel[self.current].tv.grab_focus()

        pid = term.forkpty()
        if pid == -1:
            print "Couldn't fork"
            sys.exit(1)
        if pid == 0:
            os.execv('/bin/bash', ['/bin/bash'])
            #os.execv('/usr/bin/env', ['/usr/bin/env', 'python'])
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
