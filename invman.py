#!/usr/bin/env python3

""" README README README README README README
This program manages inventories
It was written in one night
I hope there are z4r0 b00gz!

Also a special feature:
You can select items by double clicking them in the list box. 
Then their infos are automagically put into the text entries. 
Ain't that something? 
"""

from tkinter import *
from tkinter import ttk
import tkinter.filedialog as tkFileDialog
import tkinter.messagebox as tkMessageBox
from heapq import merge

###
### Misc
###

# Enable console logging by default
LOG = True 
def log(msg):
    global LOG
    if LOG: print(msg)

# Implement merge sort
def merge_sort(lst):
    """ Merge sort function """
    if len(lst) <= 1:
        return lst
 
    middle = len(lst) // 2
    left = lst[:middle]
    right = lst[middle:]
 
    left = merge_sort(left)
    right = merge_sort(right)

    return list(merge(left, right))


# Overwrite default sort function to use mergesort
def sorted(n): 
    return merge_sort(list(n))

# Exceptions
class GUIException(Exception):
    pass

class ProductException(Exception):
    pass

###
### Inventory Management
###

def add_to_inventory(invt, prod):
    """Adds a product to the inventory set"""
    if find_in_inventory(invt, prod.pid) is None:
        log("add_to_inventory: %s" % prod.pid)
        invt.append(prod)
        return list(sorted(invt))
    else:
        raise ProductException("Item with id '{}' already exists".format(prod.pid))

def delete_from_inventory(invt, pid):
    """ Deletes a product with specified ID from inventory """
    log("delete_from_inventory: %s" % pid)
    index = find_in_inventory_index(invt, pid)
    invt.pop(index)
    return invt

def delete_from_inventory_index(invt, index):
    return delete_from_inventory(invt, invt[index].pid)

def find_in_inventory_index(invt, pid):
    """ Returns the index from inventory item matching pid """

    def binary_search(invt, value):
        low = 0
        high = len(invt)-1
        while low <= high: 
            mid = (low + high)//2
            if invt[mid].pid > value: high = mid-1
            elif invt[mid].pid < value: low = mid+1
            else: return mid
        return -1

    return binary_search(invt, pid)

def find_in_inventory(invt, pid):
    """Returns the product from inventory matching pid"""
    found_index = find_in_inventory_index(invt, pid)
    log("find_in_inventory: %s -> %s" % (pid, found_index))
    if found_index == -1: return None
    return invt[found_index]

def set_inventory_item(invt, new_item, index):
    """ Sets inventory item at inedx to be new_item """
    invt = delete_from_inventory_index(invt, index)
    return add_to_inventory(invt, new_item)

def save_inventory_to_file(invt, filepath):
    """ Saves the inventory to a file specified by a path """
    log("save_inventory_to_file: len(invt) = %s -> %s" % (len(invt), filepath))
    with open(filepath, "w") as wf:
        wf.writelines(map(lambda x: str(x) + "\n", invt))

def read_inventory_from_file(filepath):
    """ Reads the inventory in from a file specified by a path. Every line of
    the file must contain comma seperated values with exactly 5 fields """
    def product_from_string(line):
        toks = [t.strip() for t in line.split(",")]
        if len(toks) != 5: raise ProductException("Invalid field count from data file")
        return Product(*toks)

    log("read_inventory_from_file: %s " % filepath)
    with open(filepath, "r") as rf:
        lines = rf.readlines()
        return list(sorted(map(product_from_string, lines)))

###
### Helpter functions + Data Structures
###

def cast_or_except(data, typefn, exn, msg):
    """ Raise exception exn with argument msg if data is not of type typefn """
    def str_type(t): return str(t).split("'")[1]
    try: return typefn(data)
    except: raise exn("{} must be valid {}".format(msg, str_type(typefn)))

class Product:
    """ A Product represents a single item in the inventory """
    def clean(self):
        """ Scrub the input data for evil delimiters """
        self.name = self.name.replace(",", "")
        self.location = self.location.replace(",", "")
        self.description = self.description.replace(",", "")

    def column_format(self):
        """ Format it to look kinda like a table """
        return str(self).replace(",", " | ")

    def __init__(self, pid, quant, name, loc, descr):
        self.pid = cast_or_except(pid, int, ProductException, "Item number")
        self.quantity =  cast_or_except(quant, int, ProductException, "Quantity")
        self.name = cast_or_except(name, str, ProductException, "Name")
        self.location = cast_or_except(loc, str, ProductException, "Location")
        self.description = cast_or_except(descr, str, ProductException, "Description")

        if self.pid < 0: raise ProductException("Item number cannot be negative")

        self.clean()

    def __str__(self):
        s = "{},{},{},{},{}"
        return s.format(self.pid, self.quantity, self.name,
                        self.location, self.description)

    def __lt__(self, other):
        return self.pid < other.pid

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash((self.pid, self.quantity,
                    self.name, self.location,
                    self.description))

###
### All GUI Code in MainGUI
###

class MainGUI():

    def warning(self, e):
        """ Alertbox helper """
        tkMessageBox.showwarning("Warning", str(e))

    def info(self, e):
        """ Alertbox helper """
        tkMessageBox.showinfo("Info", str(e))

    def get_selected(self):
        """ Gets the index of the currently selected item in the listbox """
        try: return self.listbox.curselection()[0]
        except IndexError: raise GUIException("Please select a valid entry")

    def focus_item(self, at):
        """ Scrolls and activates the item with index 'at' in the scrollbox """
        self.listbox.select_clear(0, last=len(self.inventory))
        self.listbox.activate(at)
        self.listbox.selection_set(at)
        self.listbox.see(at)
        self.update_input_entries(None)

    def product_from_entries(self):
        """ Generate a Product object from the TK entry boxes in the GUI """

        zero_length_entries = [len(ge.get()) == 0 for ge in self.gui_entries]

        if any(zero_length_entries):
            raise GUIException("Entries cannot be empty")

        log("gui:product_from_entries")
        return Product(
            self.gui_number.get(),
            self.gui_quantity.get(),
            self.gui_name.get(),
            self.gui_location.get(),
            self.gui_description.get())

    def clear_entries(self):
        """ Callback that fires when clicking outside the Listbox, compliments
        the callback immediately below """
        self.gui_number.set("")
        self.gui_quantity.set("")
        self.gui_name.set("")
        self.gui_location.set("")
        self.gui_description.set("")

    def update_input_entries(self, event):
        """ Callback that fires when clicking anything in the Listbox, used to
        automatically fill in data in the entry boxes (for convenience)"""
        selected = self.listbox.curselection()
        if len(selected) == 0:
            self.clear_entries()
            return

        log("gui:update_input_entries")
        prod = self.inventory[selected[0]]
        self.gui_number.set(prod.pid),
        self.gui_quantity.set(prod.quantity),
        self.gui_name.set(prod.name),
        self.gui_location.set(prod.location),
        self.gui_description.set(prod.description)

    def update_selected_entry(self):
        """ Callback to the "Update" Button """
        try:
            to_search_pid = cast_or_except(self.gui_number.get(), int, GUIException, "Item Number")
            prod_index = find_in_inventory_index(self.inventory, to_search_pid)

            if prod_index == -1:
                self.info("No entry with id '{}' was found".format(to_search_pid))
                return

            log("gui:update_selected_entry: {}".format(prod_index))
            new_item = self.product_from_entries()

            self.inventory = set_inventory_item(self.inventory, new_item, prod_index)
            self.listbox_refresh(self.inventory)
            self.focus_item(prod_index)

        except (ProductException,GUIException) as e: self.warning(e)
        except Exception as e: self.warning(e)

    def add_new_entry(self):
        """ Callback to the "New" Button """
        try:
            new_item = self.product_from_entries()
            log("gui:add_new_entry: %s" % new_item)
            self.inventory = add_to_inventory(self.inventory, new_item)
            self.listbox_refresh(self.inventory)
            at = find_in_inventory_index(self.inventory, new_item.pid)
            self.focus_item(at)
        except (ProductException, GUIException, Exception) as e: self.warning(e)

    def delete_selected_entry(self):
        """ Callback to the "Delete" Button """
        try:
            entry_index = self.get_selected()
            log("gui:delete_selected_entry: %s" % entry_index)
            self.inventory = delete_from_inventory_index(self.inventory, entry_index)
            self.listbox_refresh(self.inventory)
            self.focus_item(entry_index)
        except (GUIException,ProductException,Exception) as e: self.warning(e)

    def load_data(self):
        """ Callback to the "Load Data" Button """
        try:
            log("gui:load_data")
            path = tkFileDialog.askopenfilename()
            if len(path) == 0: raise FileNotFoundError
            self.inventory = read_inventory_from_file(path)
            self.listbox_refresh(self.inventory)
        except ProductException as e: self.warning(e)
        except FileNotFoundError: self.warning("File not found")


    def save_data(self):
        """ Callback to the "Save Data" Button """
        try:
            log("gui:save_data")
            path = tkFileDialog.asksaveasfilename()
            if len(path) == 0: raise FileNotFoundError
            save_inventory_to_file(self.inventory, path)
            self.info("File saved to {}".format(path))
        except ProductException as e: self.warning(e)
        except FileNotFoundError: self.warning("File not found")


    def search_entries(self):
        """ Callback to the "Search" Button """
        try: 
            log("gui:search_entries")
            to_search_pid = cast_or_except(self.gui_number.get(), int, GUIException, "Item Number")
            prod_index = find_in_inventory_index(self.inventory, to_search_pid)

            if prod_index == -1:
                self.info("No entry with id '{}' found".format(to_search_pid))
                return

            prod = self.inventory[prod_index]

            self.gui_quantity.set(prod.quantity)
            self.gui_name.set(prod.name)
            self.gui_description.set(prod.description)
            self.gui_location.set(prod.location)

            self.focus_item(prod_index)

        except GUIException as e: self.warning(e)
        except Exception as e: self.warning(e)

    def listbox_refresh(self, inventory):
        """ Refresh the listbox with items currently in inventory """
        self.listbox.delete(0,last=self.listbox.size())
        for item in inventory:
            self.listbox.insert(END, item.column_format())

    def __init__(self, master, inventory):
        """ Setup GUI and internal variables """

        self.inventory = inventory

        # Setup the top section (Save and Load buttons)
        top_frame = ttk.Frame(master, relief=SUNKEN, padding="3 3 3 3")
        top_frame.pack( fill=BOTH)

        def set_command_button(btn):
            btn.pack_configure( fill=Y, side=LEFT, padx = 2, pady = 1)

        command_buttons = \
          [ ttk.Button(top_frame, text = 'Load Data', command = self.load_data),
            ttk.Button(top_frame, text = 'Save Data', command = self.save_data), ]

        for btn in command_buttons:
            set_command_button(btn)

        # Setup the middle section (the Listbox)
        middle_frame = ttk.Frame(master, relief=SUNKEN, padding="3 3 3 3")
        middle_frame.pack(fill=BOTH)
        scrollbar = Scrollbar(middle_frame)
        scrollbar.pack(side=RIGHT, fill=Y)
        listbox = Listbox(middle_frame, selectmode=SINGLE, height=25, width=80, yscrollcommand=scrollbar.set)
        listbox.pack(side=LEFT, expand=True, fill=BOTH)
        listbox.bind(sequence = "<Button>", func=self.update_input_entries)
        scrollbar.config(command=listbox.yview)

        # Setup the lower section (Buttons and Labels)
        lower_frame = ttk.Frame(master, relief=SUNKEN, padding="3 3 3 3")
        lower_frame.pack(fill=BOTH)

        entry_frame = ttk.Frame(lower_frame, relief=SUNKEN, padding="3 3 3 3")
        entry_frame.pack(side=RIGHT, expand=True, fill=BOTH)

        def init_entry_label_pair(label_text):
            sv = StringVar()
            l = ttk.Label(entry_frame, text = label_text).pack(anchor=W)
            e = ttk.Entry(entry_frame, textvariable = sv)
            e.pack(fill=X)
            return sv

        self.gui_number = init_entry_label_pair("Item Number")
        self.gui_quantity = init_entry_label_pair("Item Quantity")
        self.gui_name = init_entry_label_pair("Item Name")
        self.gui_location = init_entry_label_pair("Item Location")
        self.gui_description = init_entry_label_pair("Item Description")

        self.gui_entries = [
                self.gui_number,
                self.gui_quantity,
                self.gui_name,
                self.gui_location,
                self.gui_description]

        # Setup and configure the 4 action buttons

        def set_action_pack(btn):
            btn.pack_configure (
                expand=True,
                padx = 2, pady = 2,
                side=LEFT, fill=X, 
            )

        action_frame = ttk.Frame(entry_frame, padding="0 0 0 0")
        action_frame.pack(side=LEFT, expand=True, fill=BOTH)

        update_buttons = \
          [ ttk.Button(action_frame, text = 'New', command = self.add_new_entry),
            ttk.Button(action_frame, text = 'Search', command = self.search_entries),
            ttk.Button(action_frame, text = 'Delete', command = self.delete_selected_entry),
            ttk.Button(action_frame, text = 'Update', command = self.update_selected_entry) ]

        for btn in update_buttons: 
            set_action_pack(btn)

        self.listbox = listbox
        self.listbox_refresh(inventory)

def main():
    master = Tk()
    MainGUI(master, list())
    master.title("Inventory Manager")
    master.mainloop()

if __name__ == "__main__":
    main()
