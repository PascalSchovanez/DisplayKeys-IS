# Image Splitter made by Neuffexx
# This image splitter was made to allow people to take images they want displayed across their Mountain DisplayPad keys.
# Who asked for this? Me. I did. Because it's a workaround to a problem that shouldn't exist in the first place.
# And I was too lazy to do this to each image manually.
# Was this more effort? Yes. You are welcome.

########################################################
#            Local Packaging Instructions
########################################################
# Command:
#       pyinstaller DisplayKeys-IS.py --onefile --noconsole --debug all --name DisplayKeys-IS --add-data "./path/to/DisplayKeys-IS.ico;." --add-data "./path/to/Preview.png;." --add-data "./path/to/Help.png;." --additional-hooks-dir=./path/to/hooks
# Note:
#       - Ensure that all paths referencing packaged files have 'sys._MEIPASS + ' in front of them,
#         otherwise they won't be found!
#         (i.e. sys._MEIPASS + "./DisplayKeys-IS.ico")
#       - '--additional-hooks-dir=' requires the path to the folder with any modules to be packaged
#         (i.e. Package tkinterdnd2, and its within './assets/modules/hook-tkinterdnd2.py',
#         then it will be '...hooks-dir=./assets/modules')

from typing import Literal, Callable, Union, Annotated
import os, sys
from PIL import Image, ImageTk, ImageSequence, ImageDraw
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Menu
import tkinterdnd2 as tkdnd
from tkinterdnd2 import *
import webbrowser
import json
from enum import Enum

####################################################################################################################
#                                                    App Paths
####################################################################################################################

# For Local Environments
#sys_icon_img = "./assets/images/DisplayKeys-IS.ico"
#sys_help_img = "./assets/images/Help.png"
#sys_preview_img = "./assets/images/Preview.png"

# For Packaging
sys_icon_img = sys._MEIPASS + "./DisplayKeys-IS.ico"
sys_help_img = sys._MEIPASS + "./Help.png"
sys_preview_img = sys._MEIPASS + "./Preview.png"


####################################################################################################################
#                                                    App Window
####################################################################################################################


# The Main Application Window
class DisplayKeys_GUI:
    """
        The Main Class of the Application.
        It Creates the Window and all of its UI Elements within it when Initialized.
    """

    def __init__(self):
        # Window Properties
        print("---Creating Window---")
        self.window = tkdnd.Tk()  # Use tkdnd to support drag & drop events
        self.window.title("DisplayKeys-IS")
        icon_path = sys_icon_img
        self.window.iconbitmap(icon_path)
        self.window.geometry("600x600")
        self.window.resizable(False, False)

        self.create_menu_bar()

        #########################

        print("---Creating Left Column---")
        # Create the Properties Frame
        self.properties_frame = tk.Frame(self.window, width=200, height=500, background="#343A40")
        self.properties_frame.grid(row=0, column=0, sticky="nsew")
        self.properties_frame.grid_columnconfigure(0, weight=1)
        # Populate the properties frame with widgets
        self.properties = []
        self.properties = self.populate_column(self.properties_frame, self.get_properties_widgets())

        print("---Creating Right Column---")
        # Create the Preview Frame
        self.preview_frame = tk.Frame(self.window, height=500, background="#212529")
        self.preview_frame.grid(row=0, column=1, sticky="nsew")  # Updated this line
        self.preview_frame.grid_columnconfigure(0, weight=1)
        # Create the Preview Widget and place it in the right column
        self.preview = DisplayKeys_Previewer(self.preview_frame, width=350, height=350)
        self.preview_reset = tk.Button(self.preview_frame, text="Reset", background="#E9ECEF", command=lambda: DisplayKeys_Previewer.reset_drag(self.preview), width=10)
        self.preview_reset.grid(sticky="n", row=1)
        self.previewer_reset_tooltip = DisplayKeys_Tooltip(self.preview_reset, "Reset the Preview Image to its original position.")
        # Create the Preview Statistics and place them in the right column
        self.previewer_help = DisplayKeys_Help(parent=self.preview_frame, row=1, alignment="nes", percentage_size=40,
                                               help_tooltip="Previewer is not 100% Accurate!\n\nPreviewer Legend:\n  - Red Lines: Image Split\n  - Red Line Thickness: Gap\n  - Black Stipped: Cell Cropping",
                                               tooltip_justification="left", tooltip_anchor="center")
        # TODO: Add Results Widget's and populate content (ie. cell resolution, % of lost pixels?, etc.)
        #       Also check if there is any actual meaningful information that can be shown.
        #self.preview_info = self.populate_column(self.preview_frame, self.get_preview_widgets())
        #self.previewer_info_help = DisplayKeys_Help(parent=self.preview_frame, row=10, alignment="se", percentage_size=40,
        #                                       help_tooltip="Further Information on the Results!")

        # Additional grid configuration for main window
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_columnconfigure(1, weight=2)

        #########################

        # Initially Create Object to hold reference to all Presets in the future.
        self.presets: list[PresetData] = []
        self.default_preset = PresetData(name="Default", rows=2, cols=6, gap=40)
        self.presets.append(self.default_preset)

        # Initially Hide Property Column Widget's Based on Dropdown Selection
        ButtonFunctions.property_options_visibility(self.properties)

        # Set focus to Application Window, to stop it being hidden behind others on launch
        self.window.focus_force()

    # Used to populate a column(Frame) with DisplayKeys_Composite_Widget's
    @staticmethod
    def populate_column(parent, widgets):
        """
            Adds [DisplayKeys_Composite_Widget]'s to a parent container.
            :param parent: The Container to fill with Widgets
            :param widgets: The list of widgets to add to the Parent
        """

        created_widgets = []
        for widget in widgets:
            created_widgets.append(DisplayKeys_Composite_Widget(parent, **widget))

        for i, widget in enumerate(created_widgets):
            widget.grid(row=i, column=0, sticky="nsew")

        return created_widgets

    @staticmethod
    def get_properties_widgets():
        """
            Returns an array of [DisplayKeys_Composite_Widget]'s, used to split Images.
        """

        # Example of a Blank Composite Widget, on how to define what type of sub-widget to be added:
        # {
        #     "composite_id": "",
        #     "widgets": [
        #         {
        #             "type": WidgetTypes.LABEL,
        #             "widget_id": "",
        #         },
        #         {
        #             "type": WidgetTypes.DROPDOWN,
        #             "widget_id": "",
        #         },
        #         {
        #             "type": WidgetTypes.TEXTBOX,
        #             "widget_id": "",
        #         },
        #         {
        #             "type": WidgetTypes.SPINBOX,
        #             "widget_id": "",
        #         },
        #         {
        #             "type": WidgetTypes.BUTTON,
        #             "widget_id": "",
        #         },
        #     ],
        # },

        ToolProperties = [
            {
                "composite_id": "Credits",
                "widgets": [
                    {
                        "type": CompWidgetTypes.LABEL,
                        "widget_id": "CreditsLabel",
                        "text": "Image Splitter made by Neuffexx",
                    },
                ],
            },
            {
                "composite_id": "GetImage",
                "widgets": [
                    {
                        "type": CompWidgetTypes.LABEL,
                        "widget_id": "GetImageLabel",
                        "text": "Choose Image:",
                    },
                    {
                        "type": CompWidgetTypes.TEXTBOX,
                        "widget_id": "GetImageTextbox",
                        "state": "readonly",
                        "dnd_type": "image",
                        "updates_previewer": True,
                    },
                    {
                        "type": CompWidgetTypes.BUTTON,
                        "widget_id": "GetImageButton",
                        "label": "Browse Image",
                        "command": ButtonFunctions.browse_image,
                        "tooltip": "Select the Image you want to be split.",
                    },
                ],
            },
            {
                "composite_id": "GetOutput",
                "widgets": [
                    {
                        "type": CompWidgetTypes.LABEL,
                        "widget_id": "GetOutputLabel",
                        "text": "Choose Output Location:",
                    },
                    {
                        "type": CompWidgetTypes.TEXTBOX,
                        "widget_id": "GetOutputTextbox",
                        "state": "readonly",
                        "dnd_type": "folder",
                    },
                    {
                        "type": CompWidgetTypes.BUTTON,
                        "label": "Browse Folder",
                        "command": ButtonFunctions.browse_directory,
                        "tooltip": "Select the Folder to save the split image to.",
                    },
                ],
            },
            {
                "composite_id": "TopDivider",
                "widgets": [
                    {
                        "type": CompWidgetTypes.LABEL,
                        "widget_id": "TopDividerLabel",
                        "text": "-------------------------------------",
                    },
                ],
            },
            {
                "composite_id": "GetParamsType",
                "widgets": [
                    {
                        "type": CompWidgetTypes.LABEL,
                        "widget_id": "GetParamsLabel",
                        "text": "Set Splitting Parameters:",
                    },
                    {
                        "type": CompWidgetTypes.DROPDOWN,
                        "widget_id": "GetParamsDropdown",
                        "options": ["Preset", "User Defined"],
                        "command": ButtonFunctions.property_options_visibility,
                        "tooltip": "Preset: Saved selection of Splitting Parameters.\nUser Defined: Or Enter your own.",
                        "update_previewer": True,
                    },
                ],
            },
            {
                "composite_id": "PresetList",
                "widgets": [
                    {
                        "type": CompWidgetTypes.DROPDOWN,
                        "widget_id": "PresetListDropdown",
                        "options": ["Default"],
                        "command": ButtonFunctions.placeholder,
                        "tooltip": "Default Values are: \n Rows         | 2 \nColumns   | 6 \n Gap            | 40",
                        "update_previewer": True,
                    },
                ],
            },
            {
                "composite_id": "PresetAdd",
                "widgets": [
                    {
                        "type": CompWidgetTypes.BUTTON,
                        "widget_id": "PressetAddButton",
                        "label": "       Add       ",
                        "command": ButtonFunctions.create_preset_popup,
                        "tooltip": "Create a new Preset.",
                        "fill": "vertical",
                    },
                ],
            },
            {
                "composite_id": "PresetEdit",
                "widgets": [
                    {
                        "type": CompWidgetTypes.BUTTON,
                        "widget_id": "PresetEditButton",
                        "label": "       Edit       ",
                        "command": ButtonFunctions.edit_preset_popup,
                        "tooltip": "Edit the currently selected Preset.",
                        "fill": "vertical",
                    },
                ],
            },
            {
                "composite_id": "PresetDelete",
                "widgets": [
                    {
                        "type": CompWidgetTypes.BUTTON,
                        "widget_id": "PresetDeleteButton",
                        "label": "     Delete     ",
                        "command": ButtonFunctions.delete_preset_popup,
                        "tooltip": "Delete the currently selected Preset.",
                        "fill": "vertical",
                    },
                ],
            },
            {
                "composite_id": "GetRows",
                "widgets": [
                    {
                        "type": CompWidgetTypes.LABEL,
                        "widget_id": "GetRowsLabel",
                        "text": "Rows:",
                    },
                    {
                        "type": CompWidgetTypes.SPINBOX,
                        "widget_id": "GetRowsSpinbox",
                        "default_value": DefaultSplitData.ROWS,
                        "dnd_type": "text",
                        "updates_previewer": True,
                    },
                ],
            },
            {
                "composite_id": "GetColumns",
                "widgets": [
                    {
                        "type": CompWidgetTypes.LABEL,
                        "widget_id": "GetColumnsLabel",
                        "text": "Columns:",
                    },
                    {
                        "type": CompWidgetTypes.SPINBOX,
                        "widget_id": "GetColumnsSpinbox",
                        "default_value": DefaultSplitData.COLS,
                        "dnd_type": "text",
                        "updates_previewer": True,
                    },
                ],
            },
            {
                "composite_id": "GetGap",
                "widgets": [
                    {
                        "type": CompWidgetTypes.LABEL,
                        "widget_id": "GetGapLabel",
                        "text": "Gap (in Pixels):",
                    },
                    {
                        "type": CompWidgetTypes.SPINBOX,
                        "widget_id": "GetGapSpinbox",
                        "default_value": DefaultSplitData.GAPPIX,
                        "dnd_type": "text",
                        "updates_previewer": True,
                    },
                ],
            },
            {
                "composite_id": "BottomDivider",
                "widgets": [
                    {
                        "type": CompWidgetTypes.LABEL,
                        "widget_id": "BottomDividerLabel",
                        "text": "-------------------------------------",
                    },
                ],
            },
            {
                "composite_id": "SplitImage",
                "widgets": [
                    {
                        "type": CompWidgetTypes.BUTTON,
                        "label": "Split Image",
                        "command": ButtonFunctions.process_image,
                    },
                ],
            },
        ]

        return ToolProperties

    @staticmethod
    def get_preview_widgets():
        """
            Returns an array of [DisplayKeys_Composit_Widgets]'s and the [DisplayKeys_Previewer].
            Used to Preview the changes done by the Property Widgets, along with some meaningful information.
        """
        PreviewWidgets = [
            {
                "widget_id": "PreviewDivider",
                "label_text": "",
                "label_colour": "#E9ECEF",
            },
            {
                "widget_id": "OutputDetails",
                "label_text": "Results :",
                "label_colour": "#E9ECEF",
            },
            {
                "widget_id": "",
                "label_text": "",
                "label_colour": "#E9ECEF",
            },
            {
                "widget_id": "",
                "label_text": "",
                "label_colour": "#E9ECEF",
            },
        ]

        return PreviewWidgets

    # Returns a specific widget of the Properties Frame
    def get_property_widget(self, widget_id: str):
        composite_widget = next((widget for widget in self.properties if widget.id == widget_id), None)
        return composite_widget

    # Returns a specific widget of the Properties Frame, if it has this child
    def get_property_widget_by_child(self, child_id: str):
        child_widget = next((widget for widget in self.properties if widget.get_child(child_id)), None)
        return child_widget

    # TODO: Create Prefernces menu
    #       - For now only to house colour settings for the Composite widgets and application backgrounds
    #       - In the future also for Previewer colours, etc.
    # To keep the code more encapsulated and clean
    def create_menu_bar(self):
        """
            Creates the Main Window Menu Bar.
            Will house Import/Export, Settings, Preferences, Help, etc. Menus.
        """

        # Main Window Menu Bar
        self.menu_bar = Menu()
        self.window.configure(menu=self.menu_bar)
        # --- File
        self.app_menu = Menu(self.menu_bar, tearoff=False)
        self.preset_menu = Menu(self.app_menu, tearoff=False)
        self.app_menu.add_cascade(label="Presets", menu=self.preset_menu)
        self.app_menu.add_separator()
        self.app_menu.add_command(label="Exit", command=ButtonFunctions.quit)
        # ---
        self.preset_menu.add_command(label="Load Presets File", command=lambda: ButtonFunctions.load_presets_file())
        self.preset_menu.add_command(label="Save Presets", command=lambda: ButtonFunctions.save_presets_file())
        self.preset_menu.add_separator()
        self.preset_menu.add_command(label="Delete Current Presets", command=lambda: PopUp_Dialogue(app.window, popup_type='warning', message="Delete ALL Presets?", buttons=[{'Yes': ButtonFunctions.delete_all_presets}, {'No': lambda: None}]))
        # --- Help
        self.help_menu = Menu(self.menu_bar, tearoff=False)
        self.help_menu.add_separator()
        self.help_menu.add_command(label="Help",
                                   command=lambda: webbrowser.open("https://www.github.com/Neuffexx/DisplayKeys-IS"))
        # Add to Menu Bar
        self.menu_bar.add_cascade(label="File", menu=self.app_menu)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)

    # Starts the Window loop
    def run(self):
        self.window.mainloop()


# The Widget that show's all changes done to the Image within the Application
class DisplayKeys_Previewer:
    """
        The Widget that show's all changes done to the Image within the Application.

        :param parent: The Widget Container holding this Previewer.
        :param width: The Width of the Previewer Canvas.
        :param height: The Height of the Previewer Canvas.
    """

    def __init__(self, parent, width, height):
        # Initialize Image
        self.width = width
        self.height = height
        self.placeholder_path = sys_preview_img
        self.image_path = None

        # Initialize canvas
        self.canvas = tk.Canvas(parent, width=self.width, height=self.height, background="#151515", highlightthickness=3, highlightbackground="#343A40")
        self.canvas.grid()
        self.canvas.tag_bind("preview_image", "<ButtonPress-1>", self.start_drag)
        self.canvas.tag_bind("preview_image", "<ButtonRelease-1>", self.end_drag)
        self.canvas.tag_bind("preview_image", "<B1-Motion>", self.do_drag)

        # Initialize Click-Drag / Offset Functionality
        self.drag_data = {"item": None, "x": 0.0, "y": 0.0}
        self.image_reset_position = {"x": 0.0, "y": 0.0}
        self.image_current_position = {"x": 0.0, "y": 0.0}
        self.allowed_drag_distance_cell = 0
        self.allowed_drag_distance_cropping = {"x": 0.0, "y": 0.0}
        self.drag_limit_type = False
        self.scale_factor = 1
        self.final_offset = {"x": 0.0, "y": 0.0}

        # Load and show the initial placeholder image
        self.display_preview_image(self.placeholder_path)

    def display_preview_image(self, image_path):
        """
        Simply gets the image, rescales it and renders it onto the canvas.
        :param image_path: The on Disk path to the Image to be Previewed
        """
        image = Image.open(image_path)

        # Rescaling image to fit within preview boundaries
        aspect_ratio = image.width / image.height
        if self.width / self.height >= aspect_ratio:
            # Constrained by height
            new_height = self.height
            new_width = int(self.height * aspect_ratio)
        else:
            # Constrained by width
            new_width = self.width
            new_height = int(self.width / aspect_ratio)
        self.scale_factor = new_width / image.width
        resized_image = image.resize((new_width, new_height))

        # Convert to PhotoImage to be used in TkInter Canvas
        self.tk_image = ImageTk.PhotoImage(resized_image)
        x_offset = (self.width - new_width) / 2
        y_offset = (self.height - new_height) / 2
        self.preview_image = self.canvas.create_image(x_offset if self.image_path != image_path else self.image_current_position["x"],
                                                      y_offset if self.image_path != image_path else self.image_current_position["y"],
                                                      image=self.tk_image, anchor=tk.NW, tags="preview_image")

        # Store initial position of Image for reset
        # (only if it's a new image)
        if self.image_path != image_path:
            self.image_reset_position["x"], self.image_reset_position["y"] = self.canvas.coords(self.preview_image)
            self.image_path = image_path
        # And make it the current position
        self.image_current_position["x"], self.image_current_position["y"] = self.canvas.coords(self.preview_image)

        # For Grid/Cropping Preview
        self.resized_image = resized_image
        self.x_offset = x_offset
        self.y_offset = y_offset

        # For click-drag offset input
        self.drag_data["x"] = x_offset
        self.drag_data["y"] = y_offset

    def update_preview(self, image_path, num_rows, num_columns, gap):
        """
            This calculates an approximate representation of the split_image function,
            to preview the Splitting and Cropping of an image provided.
            Also calls the 'display_preview_image' to refresh the image.
        """

        # Clear the canvas to prepare for new content
        self.canvas.delete("all")

        # Display the image after rescaling
        self.display_preview_image(image_path)

        # Calculate the dimensions of each image cell
        image_width, image_height = self.resized_image.size
        cell_width = image_width / num_columns
        cell_height = image_height / num_rows
        scaled_gap = gap * self.scale_factor

        # Define the size of the square to be cropped from each cell
        square_size = min(cell_width, cell_height) - scaled_gap
        # For Cell Clamping
        self.allowed_drag_distance_cell = square_size
        # For Cropping Clamping
        self.allowed_drag_distance_cropping["x"] = abs((cell_width - square_size)) / (self.scale_factor)
        self.allowed_drag_distance_cropping["y"] = abs((cell_height - square_size)) / (self.scale_factor)

        # Draw Cropping Stipple's
        for column_index in range(num_columns):
            for row_index in range(num_rows):

                # Initial position for cropping rectangle (centered in cell)
                crop_left = column_index * cell_width + (cell_width - square_size) / 2 + self.x_offset
                crop_top = row_index * cell_height + (cell_height - square_size) / 2 + self.y_offset
                crop_right = crop_left + square_size
                crop_bottom = crop_top + square_size

                # Position adjustments for Outlier Image-Cells
                if row_index == 0:  # First Row
                    crop_bottom = (row_index + 1) * cell_height - scaled_gap / 2 + self.y_offset
                    crop_top = crop_bottom - square_size
                elif row_index == num_rows - 1:  # Last Row
                    crop_top = row_index * cell_height + scaled_gap / 2 + self.y_offset
                    crop_bottom = crop_top + square_size

                if column_index == 0:  # First Column
                    crop_right = (column_index + 1) * cell_width - scaled_gap / 2 + self.x_offset
                    crop_left = crop_right - square_size
                elif column_index == num_columns - 1:  # Last Column
                    crop_left = column_index * cell_width + scaled_gap / 2 + self.x_offset
                    crop_right = crop_left + square_size

                # Draw the adjusted Cropping Overlay
                self.canvas.create_rectangle(crop_left, crop_top, crop_right, crop_bottom, outline="blue")

                # Draw Cropping Overlays with stipple effect, adjusted for Outlier Image-Cells
                stipple_pattern = "gray25"
                overlay_left = self.x_offset if column_index == 0 else column_index * cell_width + self.x_offset
                overlay_right = self.x_offset + image_width if column_index == num_columns - 1 else (
                                                                                                            column_index + 1) * cell_width + self.x_offset
                overlay_top = self.y_offset if row_index == 0 else row_index * cell_height + self.y_offset
                overlay_bottom = self.y_offset + image_height if row_index == num_rows - 1 else (
                                                                                                        row_index + 1) * cell_height + self.y_offset

                self.canvas.create_rectangle(overlay_left, crop_top, crop_right, overlay_top, fill="gray",
                                             stipple=stipple_pattern)
                self.canvas.create_rectangle(overlay_left, crop_bottom, crop_right, overlay_bottom, fill="gray",
                                             stipple=stipple_pattern)
                self.canvas.create_rectangle(crop_left, overlay_top, overlay_left, overlay_bottom, fill="gray",
                                             stipple=stipple_pattern)
                self.canvas.create_rectangle(crop_right, overlay_top, overlay_right, overlay_bottom, fill="gray",
                                             stipple=stipple_pattern)

        # Draw the Grid Lines
        for column_index in range(1, num_columns):
            grid_x = column_index * cell_width + self.x_offset
            self.canvas.create_line(grid_x, self.y_offset, grid_x, image_height + self.y_offset, fill="#CC0000",
                                    width=scaled_gap)

        for row_index in range(1, num_rows):
            grid_y = row_index * cell_height + self.y_offset
            self.canvas.create_line(self.x_offset, grid_y, image_width + self.x_offset, grid_y, fill="#CC0000",
                                    width=scaled_gap)

        # Draw Blackout Lines (hides out-of-grid pixels)
        blackout_rectangles = [
            self.canvas.create_rectangle(0, 0, self.width + 15, self.y_offset, fill='black'),  # Top
            self.canvas.create_rectangle(0, self.y_offset + self.resized_image.height, self.width + 15,
                                         self.height + 15,
                                         fill='black'),  # Bottom
            self.canvas.create_rectangle(0, self.y_offset, self.x_offset, self.y_offset + self.resized_image.height,
                                         fill='black'),  # Left
            self.canvas.create_rectangle(self.x_offset + self.resized_image.width, self.y_offset, self.width + 15,
                                         self.y_offset + self.resized_image.height, fill='black'),  # Right
        ]

    # noinspection PyTypedDict
    def start_drag(self, event):
        """
            Record the position of the cursor.
        """

        # record the item and its location
        self.drag_data["item"] = self.canvas.find_closest(event.x, event.y)[0]
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        #print("Start Drag Position:", event.x, event.y)

    def end_drag(self, event):
        """
            Finalized the Drag event, storing / converting position coordinates, and calculating clamping.
        """

        # Save the end position of the drag
        self.image_current_position["x"], self.image_current_position["y"] = self.canvas.coords(self.preview_image)

        # Calculate the distance moved on Canvas
        canvas_delta_x = self.image_current_position["x"] - self.image_reset_position["x"]
        canvas_delta_y = self.image_current_position["y"] - self.image_reset_position["y"]
        # Convert to In-Canvas Image Space
        delta_x = canvas_delta_x / self.scale_factor
        delta_y = canvas_delta_y / self.scale_factor

        # Clamp the distance moved in Canvas Space
        if self.drag_limit_type:
            # Clamp the distance moved based on Cell Size
            if delta_x > 0:
                delta_x = min(delta_x, self.allowed_drag_distance_cell)
            else:
                delta_x = max(delta_x, -self.allowed_drag_distance_cell)

            if delta_y > 0:
                delta_y = min(delta_y, self.allowed_drag_distance_cell)
            else:
                delta_y = max(delta_y, -self.allowed_drag_distance_cell)
        else:
            # Clamp the distance moved based on Cropping Size
            if delta_x > 0:
                delta_x = min(delta_x, self.allowed_drag_distance_cropping["x"])
            else:
                delta_x = max(delta_x, -self.allowed_drag_distance_cropping["x"])

            if delta_y > 0:
                delta_y = min(delta_y, self.allowed_drag_distance_cropping["y"])
            else:
                delta_y = max(delta_y, -self.allowed_drag_distance_cropping["y"])

        # Update the position in Canvas Space, given the new delta_x and delta_y
        self.image_current_position["x"] = self.image_reset_position["x"] + delta_x * self.scale_factor
        self.image_current_position["y"] = self.image_reset_position["y"] + delta_y * self.scale_factor

        # move the image back to the new clamped position
        self.canvas.coords(self.preview_image, self.image_current_position["x"], self.image_current_position["y"])

        # Get / Store Offset in Original-Image Space
        delta_x = (self.image_current_position["x"] - self.image_reset_position["x"]) / self.scale_factor
        delta_y = (self.image_current_position["y"] - self.image_reset_position["y"]) / self.scale_factor
        self.final_offset = {"x": delta_x, "y": delta_y}
        print("Final Offset:", delta_x, delta_y)

        # reset the drag information
        self.drag_data["item"] = None
        self.drag_data["x"] = 0
        self.drag_data["y"] = 0

        # Update the Previewer - In the future it will show what cells will be discarded
        ButtonFunctions.process_image("DragPreviewImage")

    def do_drag(self, event):
        """
            Update the Preview Image to match the cursor position.
        """

        # compute how much the mouse has moved
        delta_x = event.x - self.drag_data["x"]
        delta_y = event.y - self.drag_data["y"]
        # move the object the appropriate amount
        self.canvas.move(self.drag_data["item"], delta_x, delta_y)
        # record the new position
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        #print("New Drag Position:", delta_x, delta_y)

    # Move the preview image back to its original position
    def reset_drag(self):
        """
            Set the preview image back to its original position.
        """

        # Reset Position / Save
        self.canvas.coords(self.preview_image, self.image_reset_position["x"], self.image_reset_position["y"])
        self.image_current_position["x"], self.image_current_position["y"] = self.canvas.coords(self.preview_image)
        delta_x = self.image_current_position["x"] - self.image_reset_position["x"]
        delta_y = self.image_current_position["y"] - self.image_reset_position["y"]
        self.final_offset = {"x": delta_x, "y": delta_y}
        print("Reset Offset:", delta_x, delta_y)

        # Update the Previewer
        ButtonFunctions.process_image("ResetPreviewer")


# TODO: Change class to check the order of widgets to be inside of the composite widget
#       Will split the widget construction into sub-functions, that will be called by a loop for each composite widget,
#       whenever the loop comes across the correct type of Widget to put inside of the composite widget.
#       Meaning there can now be multiple of the same type of widget inside a single composite widget at a time,
#       with Order being purely defined by the input array.
#       However, it will for now always be in a fixed linear centered top-to-bottom layout, maybe I will come up
#       with a way to work around that in the future. But not a priority for now.
#       - Need to figure out a way to keep each widget unique, meaning that if there are 3 textboxes used in a single
#         composite widget, then I need to be able to tell which one is which. But still needs to be easy to access.
# TODO: Get colours to display from Preferences menu/popup


# Widget Types used in the Composite Widget
class CompWidgetTypes(Enum):
    """
        The widget types supported by the 'DisplayKeys_Composite_Widget' class.
        Members are:
        [ LABEL, DROPDOWN, TEXTBOX, SPINBOX, BUTTON ]
    """
    LABEL = 1
    DROPDOWN = 2
    TEXTBOX = 3
    SPINBOX = 4
    BUTTON = 5


# Generic Widgets used throughout the Applications UI (i.e. Labels, Textboxes, Buttons, etc.)
class DisplayKeys_Composite_Widget(tk.Frame):
    """
        Generic Widgets used throughout the Applications UI (ie. Labels, Textboxes, Buttons, etc.)
        Designed to be used in a Vertical Layout.
    """

    def __init__(self, parent: tk.Frame, composite_id: str, widgets: list[list], layout: Literal['vertical', 'horizontal'] = 'vertical'):
        super().__init__(parent, bg="#343A40")
        self.grid(sticky="nsew", padx=5, pady=5)
        self.columnconfigure(0, weight=1)

        # The reference name by which to find this widget
        self.id = composite_id
        # Whether the widgets will be above or next to each other
        self.layout = layout

        self.child_container = tk.Frame(master=self)
        self.child_container.grid(row=0, column=0, sticky="nsew")
        self.child_container.grid_columnconfigure(0, weight=1)

        # The widgets contained by this Composite widget
        self.child_widgets = self.create_children(widgets)
        # Place child widgets (needed for rendering)
        self.populate_composite()

    def create_children(self, widgets):
        child_widgets = []

        for widget_dict in widgets:
            widget_type = widget_dict.get("type")
            widget_id = widget_dict.get("widget_id")
            # Remove keys that are not widget parameters
            widget_params = {k: v for k, v in widget_dict.items() if k not in ["type", "widget_id"]}

            match widget_type:
                case CompWidgetTypes.LABEL:
                    child_widgets.append(self.Comp_Label(master=self, widget_id=widget_id, **widget_params))
                case CompWidgetTypes.DROPDOWN:
                    child_widgets.append(self.Comp_Combobox(master=self, widget_id=widget_id, **widget_params))
                case CompWidgetTypes.TEXTBOX:
                    child_widgets.append(self.Comp_Entry(master=self, widget_id=widget_id, **widget_params))
                case CompWidgetTypes.SPINBOX:
                    child_widgets.append(self.Comp_Spinbox(master=self, widget_id=widget_id, **widget_params))
                case CompWidgetTypes.BUTTON:
                    child_widgets.append(self.Comp_Button(master=self, widget_id=widget_id, **widget_params))

        return child_widgets

    def populate_composite(self):
        for i, widget in enumerate(self.child_widgets):
            if widget.__class__ == self.Comp_Button:
                match self.layout:
                    case 'vertical':
                        match widget.fill:
                            case 'both':
                                widget.grid(sticky="nsew", row=i, column=0, pady=3)
                            case 'horizontal':
                                widget.grid(sticky="ew", row=i, column=0, pady=3)
                            case 'vertical':
                                widget.grid(sticky="ns", row=i, column=0, pady=3)
                            case "":
                                widget.grid(sticky="", row=i, column=0, pady=3)
                    case 'horizontal':
                        match widget.fill:
                            case 'both':
                                widget.grid(sticky="nsew", row=0, column=i, pady=3)
                            case 'horizontal':
                                widget.grid(sticky="ew", row=0, column=i, pady=3)
                            case 'vertical':
                                widget.grid(sticky="ns", row=0, column=i, pady=3)
                            case "":
                                widget.grid(sticky="", row=0, column=i, pady=3)
            else:
                match self.layout:
                    case 'vertical':
                        widget.grid(row=i, column=0, sticky="nsew")
                    case 'horizontal':
                        widget.grid(row=0, column=i, sticky="nsew")

    @staticmethod
    def get_composite_widget(widget_id: str, widgets: list):
        composite_widget = next((widget for widget in widgets if widget.id == widget_id), None)
        return composite_widget

    def get_child(self, child_id: str):
        child = next((widget for widget in self.child_widgets if widget.id == child_id), None)
        return child

    # Create child class widgets to hold all this information themselves, so as to not store it in arrays or anything
    # with some convoluted way to keeping track of what widget has what tooltip etc.
    class Comp_Label(tk.Label):
        def __init__(self, widget_id: str, text: str, tooltip: str = None,
                     master=None, **kwargs):
            super().__init__(master, text=text, **kwargs)
            self.id = widget_id
            if tooltip:
                self.tooltip = DisplayKeys_Tooltip(parent=self, text=tooltip)

    class Comp_Combobox(ttk.Combobox):
        def __init__(self, widget_id: str, options: list[str], tooltip: str = None,
                     command: Callable[[list['DisplayKeys_Composite_Widget']], None] = None,
                     update_previewer: bool = False,
                     master=None, **kwargs):
            self.dropdown_var = tk.StringVar()
            self.dropdown_var.set(options[0])  # Set default value

            super().__init__(master, textvariable=self.dropdown_var, state="readonly", justify="left",
                             values=options, **kwargs)
            self.id = widget_id
            self.bind("<<ComboboxSelected>>", lambda event: command(app.properties))
            if update_previewer:
                self.dropdown_trace = self.dropdown_var.trace('w', lambda *args: ButtonFunctions.process_image(self.id))
            if tooltip:
                self.tooltip = DisplayKeys_Tooltip(parent=self, text=tooltip)

    class Comp_Entry(tk.Entry):
        def __init__(self, widget_id: str, state: Literal["normal", "disabled", "readonly"] = "normal", default_value: str = None,
                     dnd_type: Literal['image', 'folder', 'text', 'any'] | None = None,
                     colour: str = "white", updates_previewer: bool = False,
                     master=None, **kwargs):
            self.textbox_var = tk.StringVar()
            if default_value:
                self.textbox_var.set(default_value)

            super().__init__(master, textvariable=self.textbox_var, state=state, bg=colour, **kwargs)
            self.id = widget_id
            if updates_previewer:
                self.textbox_trace = self.textbox_var.trace('w', lambda *args: ButtonFunctions.process_image(self.id))
            if dnd_type:
                self.dnd = DisplayKeys_DragDrop(self, drop_type=dnd_type, parent_widget=self,
                                                traced_callback=lambda *args: ButtonFunctions.process_image(
                                                    self.id) if updates_previewer else None)

    class Comp_Spinbox(tk.Spinbox):
        def __init__(self, widget_id: str, default_value: Union[int, float, 'DefaultSplitData'] = 0, dnd_type: Literal['image', 'folder', 'text', 'any'] | None = None,
                     colour: str = "white", updates_previewer: bool = False,
                     master=None, **kwargs):
            self.spinbox_var = tk.IntVar()

            # Get numeric value from Enum member
            if isinstance(default_value, DefaultSplitData):
                default_value = default_value.value

            if default_value:
                self.spinbox_var.set(default_value)

            super().__init__(master, from_=0, to=(int(default_value) + 1) * 100, textvariable=self.spinbox_var,
                             bg=colour, **kwargs)
            self.id = widget_id
            if updates_previewer:
                self.spinbox_trace = self.spinbox_var.trace('w', lambda *args: ButtonFunctions.process_image(self.id))
            if dnd_type:
                self.dnd = DisplayKeys_DragDrop(self, drop_type=dnd_type, parent_widget=self,
                                                traced_callback=lambda *args: ButtonFunctions.process_image(
                                                    self.id) if updates_previewer else None)

    class Comp_Button(tk.Button):
        def __init__(self, widget_id: str, label: str = None, command: Callable[[str], None] = None,
                     tooltip: str = None, colour: str = "white", border: int = 3, fill: str = 'both',
                     master=None, **kwargs):
            super().__init__(master, text=label, command=lambda: command(self.id), borderwidth=border, bg=colour, **kwargs)
            self.id = widget_id
            if tooltip:
                self.tooltip = DisplayKeys_Tooltip(parent=self, text=tooltip)
            self.fill = fill


# A custom Tooltip class based on tk.Toplevel
class DisplayKeys_Tooltip:
    """
        A Tooltip that can be assigned to any of the DisplayKeys_Composite_Widget sub widgets

        This tooltip will be stored within the actual Composite Widget, and will keep reference
        to the widget that will trigger it.

        :param parent: Widget that the Tooltip is Bound to.
        :param text: The Tooltip text to show.
        :param justify: The Relative Alignment of Text to itself when broken into a new line.
        :param anchor: The Alignment of Text in general Relative to the Tooltips Widget Space
        :param lifetime: How long the Tooltip should exist for while hovering over its Parent, in seconds.
    """

    def __init__(self, parent: tk.Label | tk.Entry | tk.Spinbox | tk.Button | ttk.Combobox, text: str,
                 justify: Literal["left", "center", "right"] = "center",
                 anchor: Literal["nw", "n", "ne", "w", "center", "e", "sw", "s", "se"] = "center",
                 lifetime: int = 5):
        self.parent = parent
        self.text = text
        self.text_justification = justify
        self.text_anchor = anchor
        self.tooltip = None
        self.tooltip_lifetime = lifetime * 1000
        self.tooltip_lifetime_id = None
        self.parent.bind("<Enter>", self.show_tooltip)
        self.parent.bind("<Leave>", self.hide_tooltip)
        self.parent.bind("<Button>", self.hide_tooltip)
        self.parent.bind("<Motion>", self.move_tooltip)

    def show_tooltip(self, event):
        """
            Creates the Tooltip whenever the Cursor hovers over its Parent Widget
        """
        # Create Window
        self.tooltip = tk.Toplevel(self.parent)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip_position(event)
        label = tk.Label(
            self.tooltip, text=self.text, background="#ffffe0", relief="solid", borderwidth=1,
            justify=self.text_justification, anchor=self.text_anchor
        )
        label.grid(sticky="n")

        # Start lifetime countdown to avoid tooltip getting bugged and not disappearing
        self.tooltip_lifetime_destructor()

    def move_tooltip(self, event):
        """
            Updates the Tooltips position based on mouse movement
        """

        if self.tooltip:
            self.tooltip_position(event)

    def tooltip_position(self, event):
        """
            Positions the Tooltip to the Bottom Right of the Cursor
        """

        x = self.parent.winfo_pointerx()
        y = self.parent.winfo_pointery()
        self.tooltip.wm_geometry(f"+{x + 20}+{y + 20}")

    # TODO:
    #       Tooltips dont disappear in some instances when used with Drop-down menus.
    #       When Clicking on the dropdown to open it, but then click on it again without moving the mouse off of it
    #       The dropdown remains until either a File Dialogue window is opened or a click-drag action is initiated.
    #       At which point the tooltip isn't destroyed, just moved beneath ALL windows. And remains on Desktop.
    #                           Need to find a way to destroy it when Dropdown is closed?
    def hide_tooltip(self, event=None):
        """
            Destroys the Tooltip whenever the Cursor leaves the region of the Parent Widget
        """
        if self.tooltip:
            if self._lifetime_id:
                self.tooltip.after_cancel(self._lifetime_id)

            # if event:
            #     print('Function called via event')
            # else:
            #     print('Function called via Timer')

            self.tooltip.destroy()
            self.tooltip = None

    def tooltip_lifetime_destructor(self):
        self._lifetime_id = self.tooltip.after(self.tooltip_lifetime, self.hide_tooltip)


class DisplayKeys_PopUp:
    """
        A custom Pop-Up Window Parent class built on tk.Toplevel.
    """

    def __init__(self, parent):
        # --- Create Window Setup ---
        self.popup_min_width = 225
        self.popup_min_height = 100

        self.parent = parent
        self.popup = tk.Toplevel(parent)
        self.popup.geometry(f"{self.popup_min_width}x{self.popup_min_height}")
        self.popup.resizable(False, False)

        # Makes the popup act as a modal dialog and focused
        self.popup.grab_set()
        self.popup.focus_force()
        # Disable parent window
        self.parent.attributes('-disabled', True)
        # Bind functionality to the creation of the window.
        self.popup.bind_class("Toplevel", "<Map>", self.on_open)
        # Bind functionality to the deletion of the window
        self.popup.bind("<Destroy>", self.on_close)

        # Primary Content Container ( will be used by all 'types' )
        self.container = tk.Frame(self.popup)
        self.container.pack(expand=True, fill=tk.BOTH)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

    def button_command_destructive(self, function):
        """
            Destructive version of the Button command execution.
            Use if popup is to close after Button usage.
        """

        def execute_function():
            print("---Destructive Popup Button---")
            function()
            # re-enable parent window
            self.popup.master.attributes('-disabled', False)
            # Close the popup when the function is done executing
            self.popup.destroy()

        return execute_function

    @staticmethod
    def button_command(function):
        """
            None-Destructive version of the Button command execution.
            Use if popup is to stay open after the button press.
            Useful simply for operations that may update the popup.
        """

        def execute_function():
            print("---Non-Destructive Popup Button---")
            function()

        return execute_function

    def center_window(self, parent):
        """
            Centers the Pop-Up to the Parent Window.
        """
        # Update the window to get correct measurements
        self.popup.update()

        # Get the window's width, height
        width = self.popup.winfo_width()
        height = self.popup.winfo_height()

        # Get the parent's width, height
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        # Get the parent's top-left coordinates
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()

        # Calculate the position to center the window
        x = parent_x + (parent_width / 2) - (width / 2)
        y = parent_y + (parent_height / 2) - (height / 2)

        self.popup.geometry(f'+{int(x)}+{int(y)}')

    # probably useless
    def center_content(self, content_parent: tk.Toplevel, content_child: tk.Frame):
        # Get the width and height of the screen
        screen_width = content_parent.winfo_screenwidth()
        screen_height = content_parent.winfo_screenheight()

        # Get the width and height of the child widget
        child_width = content_child.winfo_width()
        child_height = content_child.winfo_height()

        # Calculate the x and y coordinates of the child widget relative to the parent frame
        x = (screen_width - child_width) // 2
        y = (screen_height - child_height) // 2

        # Move the child widget to its new position
        content_parent.geometry(f"+{x}+{y}")

    # probably useless
    def center_row_content(self, content_parent: tk.Frame, buttons: list, items_per_row: int):
        # Configuring grid to center content
        for i in range(items_per_row):
            content_parent.columnconfigure(i, weight=1)
        for i in range(len(buttons) // items_per_row):
            content_parent.rowconfigure(i, weight=1)

    # Not yet needed, here as placeholder
    def on_open(self, event: tk.Event):
        """
            Custom Event function that is called when the pop-up window is opened.
            Can be extended in order to execute code on open time.
            Call this function at the start of the subclass version, in order to keep and extend the functionality.
        """
        print("Pop-up window created!")
        # Rescale popup to encompass all child widgets
        self.resize_popup_window(self.container)
        # Center the window
        self.center_window(self.parent)

    def on_close(self, event: tk.Event):
        """
            Custom Event function that is called when the pop-up window is closed.
            Can be extended in order to execute code on close time.
            Call this function at the start of the subclass version, in order to keep and extend the functionality.
        """
        # Custom code equivalent to 'cancel' to make sure nothing happens
        print("Pop-up window closed!")

        # unbind events to avoid any accidental function triggers
        self.popup.unbind_class("Toplevel", "<Map>")
        self.popup.unbind("<Destroy>")

        # Ensure main window becomes active after popup was closed
        self.popup.master.attributes('-disabled', False)

    def resize_popup_window(self, container: tk.Frame):
        """
            Resizes the pop-up window based on the screen size its content takes up.
            :param container: The parent of ALL the content inside the pop-up window.
        """
        self.popup.update_idletasks()
        width = self.popup.winfo_width()
        height = self.popup.winfo_height()
        x = self.popup.winfo_rootx()
        y = self.popup.winfo_rooty()

        # Get the total width and height of all child widgets
        total_width = 0
        total_height = 0
        for child in container.winfo_children():
            total_width = max(total_width, child.winfo_x() + child.winfo_width())
            total_height = max(total_height, child.winfo_y() + child.winfo_height())

        if total_width >= self.popup_min_width and total_height >= self.popup_min_height:  # Needs bigger window size
            # Resize the window to fit its contents
            self.popup.geometry(f"{total_width}x{total_height}+{x}+{y}")
        elif total_width < self.popup_min_width and total_height < self.popup_min_height:  # Too small both dimensions
            self.popup.geometry(f"{self.popup_min_width}x{self.popup_min_height}+{x}+{y}")
        elif total_width < self.popup_min_width:  # Not WIDE enough
            self.popup.geometry(f"{self.popup_min_width}x{total_height}+{x}+{y}")
        else:  # Not TALL enough
            self.popup.geometry(f"{total_width}x{self.popup_min_height}+{x}+{y}")


class PopUp_Dialogue(DisplayKeys_PopUp):
    def __init__(self, parent, popup_type: Literal['confirm', 'warning', 'error'], message: str,
                 buttons: list[dict[str, Callable[[], None]]] = [{'OK': lambda: None}, {'CANCEL': lambda: None}],
                 buttons_per_row: int = 2):
        super().__init__(parent)

        # Set / Determine Dialogue Type
        self.popup.resizable(True, False)
        self.type = popup_type
        self.popup.title(self.type.upper())

        self.buttons_per_row = buttons_per_row

        self.create_dialogue(message, buttons, buttons_per_row)
        self.resize_popup_window(self.container)

    # Extends the Parent class on_open function
    def on_open(self, event: tk.Event):
        DisplayKeys_PopUp.on_open(self, event)

    # Extends the Parent class on_close function
    def on_close(self, event: tk.Event):
        DisplayKeys_PopUp.on_close(self, event)

    # Creates the necessary pop-up content for this class
    def create_dialogue(self, message, buttons, buttons_per_row):
        """
            Creates all the widgets/content required for displaying and interaction
        """
        # The message to display
        self.popup_message = message

        self.message = tk.Label(self.container, text=self.popup_message, justify='left')  # , anchor='center')
        self.message.grid(sticky="nsew", row=1, column=1, columnspan=buttons_per_row, pady=15)

        # TODO:
        #       Figure out how to get the spacing between the buttons and the fillers to be correct
        #       + The offset with the text (see 'Folder' pop-up example)

        # Buttons left side white space filler
        self.left_placeholder = tk.Label(self.container)
        self.left_placeholder.grid(sticky='nsew', pady=15, row=2, column=0)
        self.container.grid_columnconfigure(0, weight=2)

        # Loop over the buttons to populate with as many as needed
        self.button_container = tk.Frame(self.container)
        self.button_container.grid(sticky="nsew", row=2, column=1)  # , columnspan=len(buttons))
        self.container.grid_columnconfigure(1, weight=1)

        self.buttons = buttons
        for i, button in enumerate(self.buttons):
            button_name, button_function = list(button.items())[0]
            tk.Button(self.button_container,
                      text=button_name,
                      command=self.button_command_destructive(button_function)).grid(sticky="nsew", pady=15,
                                                                                     row=(i // buttons_per_row),
                                                                                     column=i % buttons_per_row)
            self.button_container.grid_columnconfigure(i, weight=1)

        # Buttons right side white space filler
        self.right_placeholder = tk.Label(self.container)
        self.right_placeholder.grid(sticky='nsew', pady=15, row=0, column=2)
        self.container.grid_columnconfigure(2, weight=2)


class PopUp_Preset_Add(DisplayKeys_PopUp):
    def __init__(self, parent):
        super().__init__(parent)

        self.popup.title("Add Preset")
        self.popup.geometry("100x250")  # TODO: Remove once new UI has been finished, if already styled correctly.
                                        #       (should be visually fixed then)
        self.create_add_preset()

    # Extends the Parent class on_open function
    def on_open(self, event: tk.Event):
        DisplayKeys_PopUp.on_open(self, event)

    # Extends the Parent class on_close function
    def on_close(self, event: tk.Event):
        DisplayKeys_PopUp.on_close(self, event)

    def get_add_widgets(self):
        return [
            {
                "composite_id": "GetPresetName",
                "widgets": [
                    {
                        "type": CompWidgetTypes.LABEL,
                        "widget_id": "GetPresetNameLabel",
                        "text": "Preset Name:",
                    },
                    {
                        "type": CompWidgetTypes.TEXTBOX,
                        "widget_id": "GetPresetNameTextbox",
                        "default_value": "My Preset",
                    },
                ],
            },
            {
                "composite_id": "GetPresetRows",
                "widgets": [
                    {
                        "type": CompWidgetTypes.LABEL,
                        "widget_id": "GetPresetRowsLabel",
                        "text": "Rows:",
                    },
                    {
                        "type": CompWidgetTypes.SPINBOX,
                        "widget_id": "GetPresetRowsSpinbox",
                        "default_value": DefaultSplitData.ROWS,
                    },
                ],
            },
            {
                "composite_id": "GetPresetColumns",
                "widgets": [
                    {
                        "type": CompWidgetTypes.LABEL,
                        "widget_id": "GetPresetColumnsLabel",
                        "text": "Columns:",
                    },
                    {
                        "type": CompWidgetTypes.SPINBOX,
                        "widget_id": "GetPresetColumnsSpinbox",
                        "default_value": DefaultSplitData.COLS,
                    },
                ],
            },
            {
                "composite_id": "GetPresetGap",
                "widgets": [
                    {
                        "type": CompWidgetTypes.LABEL,
                        "widget_id": "GetPresetGapLabel",
                        "text": "Gap:",
                    },
                    {
                        "type": CompWidgetTypes.SPINBOX,
                        "widget_id": "GetPresetGapSpinbox",
                        "default_value": DefaultSplitData.GAPPIX,
                    },
                ],
            },
        ]

    def submit_preset(self):
        comp_class = DisplayKeys_Composite_Widget
        name_input_widget = comp_class.get_composite_widget("GetPresetName", self.preset_param_widgets).get_child("GetPresetNameTextbox")
        rows_input_widget = comp_class.get_composite_widget("GetPresetRows", self.preset_param_widgets).get_child("GetPresetRowsSpinbox")
        cols_input_widget = comp_class.get_composite_widget("GetPresetColumns", self.preset_param_widgets).get_child("GetPresetColumnsSpinbox")
        gap_input_widget = comp_class.get_composite_widget("GetPresetGap", self.preset_param_widgets).get_child("GetPresetGapSpinbox")
        if all(widget is not None for widget in [name_input_widget, rows_input_widget, cols_input_widget, gap_input_widget]):
            name = str(name_input_widget.get())
            rows = int(rows_input_widget.get())
            cols = int(cols_input_widget.get())
            gap = int(gap_input_widget.get())

            if not any(preset.name == name for preset in app.presets):
                ButtonFunctions.add_preset(name=name, rows=rows, cols=cols, gap=gap)
            else:
                PopUp_Dialogue(app.window, popup_type='error', message="Preset with this Name already exists!",
                               buttons=[{'OK': lambda: None}])
        else:
            PopUp_Dialogue(self.popup, popup_type='error', message="Missing a Field!", buttons=[{'OK': lambda: None}])

    # Creates the necessary pop-up content for this class
    def create_add_preset(self):
        """
            Creates all the widgets/content required to create a new Preset
        """
        self.preset_param_widgets = []

        # Display Instructions
        self.message = tk.Label(self.container, text="Set the Parameters for the new Preset.")  # , anchor='center', justify='left')
        self.message.grid(sticky="nsew", row=1, column=0, pady=15)

        # Create Necessary Edit Fields
        self.preset_param_widgets = app.populate_column(parent=self.container, widgets=self.get_add_widgets())

        # Interaction Buttons
        self.button_container = tk.Frame(self.container)
        self.button_container.grid(sticky="nsew", row=6, column=0)

        self.confirm_button = tk.Button(self.button_container, text="           Confirm          ", command=self.button_command_destructive(lambda: self.submit_preset()))
        self.confirm_button.grid(sticky="nsew", row=0, column=0)
        self.confirm_button.rowconfigure(0, weight=1)
        self.cancel_button = tk.Button(self.button_container, text="           Cancel           ", command=self.button_command_destructive(lambda: None))
        self.cancel_button.grid(sticky="nsew", row=0, column=1)
        self.cancel_button.rowconfigure(0, weight=1)

        # White Space Blank
        self.bottm_white_space = tk.Label(self.container)
        self.bottm_white_space.grid(sticky="nsew", row=7, column=0)


class PopUp_Preset_Edit(DisplayKeys_PopUp):
    def __init__(self, parent, preset_name):
        super().__init__(parent)

        self.popup.title(f"Edit {preset_name}")
        self.popup.geometry("100x250")  # TODO: Remove once new UI has been finished, if already styled correctly.
                                        #       (should be visually fixed then)

        self.current_preset = preset_name

        self.create_edit_preset()
        self.get_original_preset_values()

    # Extends the Parent class on_open function
    def on_open(self, event: tk.Event):
        DisplayKeys_PopUp.on_open(self, event)

    # Extends the Parent class on_close function
    def on_close(self, event: tk.Event):
        DisplayKeys_PopUp.on_close(self, event)

    def get_edit_widgets(self):
        return [
            {
                "composite_id": "GetPresetName",
                "widgets": [
                    {
                        "type": CompWidgetTypes.LABEL,
                        "widget_id": "GetPresetNameLabel",
                        "text": "Preset Name:",
                    },
                    {
                        "type": CompWidgetTypes.TEXTBOX,
                        "widget_id": "GetPresetNameTextbox",
                    },
                ],
            },
            {
                "composite_id": "GetPresetRows",
                "widgets": [
                    {
                        "type": CompWidgetTypes.LABEL,
                        "widget_id": "GetPresetRowsLabel",
                        "text": "Rows:",
                    },
                    {
                        "type": CompWidgetTypes.SPINBOX,
                        "widget_id": "GetPresetRowsSpinbox",
                    },
                ],
            },
            {
                "composite_id": "GetPresetColumns",
                "widgets": [
                    {
                        "type": CompWidgetTypes.LABEL,
                        "widget_id": "GetPresetColumnsLabel",
                        "text": "Columns:",
                    },
                    {
                        "type": CompWidgetTypes.SPINBOX,
                        "widget_id": "GetPresetColumnsSpinbox",
                    },
                ],
            },
            {
                "composite_id": "GetPresetGap",
                "widgets": [
                    {
                        "type": CompWidgetTypes.LABEL,
                        "widget_id": "GetPresetGapLabel",
                        "text": "Gap:",
                    },
                    {
                        "type": CompWidgetTypes.SPINBOX,
                        "widget_id": "GetPresetGapSpinbox",
                    },
                ],
            },
        ]

    def submit_preset(self):
        comp_class = DisplayKeys_Composite_Widget
        name_input_widget = comp_class.get_composite_widget("GetPresetName", self.preset_param_widgets).get_child("GetPresetNameTextbox")
        rows_input_widget = comp_class.get_composite_widget("GetPresetRows", self.preset_param_widgets).get_child("GetPresetRowsSpinbox")
        cols_input_widget = comp_class.get_composite_widget("GetPresetColumns", self.preset_param_widgets).get_child("GetPresetColumnsSpinbox")
        gap_input_widget = comp_class.get_composite_widget("GetPresetGap", self.preset_param_widgets).get_child("GetPresetGapSpinbox")
        if all(widget is not None for widget in[name_input_widget, rows_input_widget, cols_input_widget, gap_input_widget]):
            # Get Edited values
            name = str(name_input_widget.get())
            rows = int(rows_input_widget.get())
            cols = int(cols_input_widget.get())
            gap = int(gap_input_widget.get())

            # Save edited Preset
            if not any(preset.name == name for preset in app.presets):
                ButtonFunctions.edit_preset(current_preset=self.current_preset, new_name=name, rows=rows, cols=cols, gap=gap)
            else:
                PopUp_Dialogue(app.window, popup_type='error', message="Preset with this Name already exists!",
                               buttons=[{'OK': lambda: None}])
        else:
            PopUp_Dialogue(self.popup, popup_type='error', message="Missing a Field!", buttons=[{'OK': lambda: None}])

    def get_original_preset_values(self):
        original_preset = PresetData.get_preset(self.current_preset)

        comp_class = DisplayKeys_Composite_Widget
        self.name_input_widget = comp_class.get_composite_widget("GetPresetName", self.preset_param_widgets).get_child("GetPresetNameTextbox")
        self.rows_input_widget = comp_class.get_composite_widget("GetPresetRows", self.preset_param_widgets).get_child("GetPresetRowsSpinbox")
        self.cols_input_widget = comp_class.get_composite_widget("GetPresetColumns", self.preset_param_widgets).get_child("GetPresetColumnsSpinbox")
        self.gap_input_widget = comp_class.get_composite_widget("GetPresetGap", self.preset_param_widgets).get_child("GetPresetGapSpinbox")

        if all(widget is not None for widget in [self.name_input_widget, self.rows_input_widget, self.cols_input_widget, self.gap_input_widget]):
            self.name_input_widget.textbox_var.set(original_preset.name)
            self.rows_input_widget.spinbox_var.set(original_preset.rows)
            self.cols_input_widget.spinbox_var.set(original_preset.cols)
            self.gap_input_widget.spinbox_var.set(original_preset.gap)

    # Creates the necessary pop-up content for this class
    def create_edit_preset(self):
        """
            Creates all the widgets/content required to edit a Preset
        """
        self.preset_param_widgets = []

        # Display Instructions
        self.message = tk.Label(self.container,
                                text="Set the Parameters for the new Preset.")  # , anchor='center', justify='left')
        self.message.grid(sticky="nsew", row=1, column=0, pady=15)

        # Create Necessary Edit Fields
        self.preset_param_widgets = app.populate_column(parent=self.container, widgets=self.get_edit_widgets())

        # Interaction Buttons
        self.button_container = tk.Frame(self.container)
        self.button_container.grid(sticky="nsew", row=6, column=0)

        self.confirm_button = tk.Button(self.button_container, text="           Confirm          ",
                                        command=self.button_command_destructive(lambda: self.submit_preset()))
        self.confirm_button.grid(sticky="nsew", row=0, column=0)
        self.confirm_button.rowconfigure(0, weight=1)
        self.cancel_button = tk.Button(self.button_container, text="           Cancel           ",
                                       command=self.button_command_destructive(lambda: None))
        self.cancel_button.grid(sticky="nsew", row=0, column=1)
        self.cancel_button.rowconfigure(0, weight=1)

        # White Space Blank
        self.bottm_white_space = tk.Label(self.container)
        self.bottm_white_space.grid(sticky="nsew", row=7, column=0)


# TODO: Implement a Preferences Pop-Up to adjust colours, etc.
#       Main UI Structure should be:
#       -------------------------------------------------------
#       |                                                     |
#       | Colours  I        Colours         | Reset | Save |  |
#       | Option 2 I  --------------------------------------  |
#       | Option 3 I    Category                              |
#       | ...      I  Option                ['Hex' / String]  |
#       |          I  ...                                     |
#       |                                                     |
#       -------------------------------------------------------
class PopUp_Preferences(DisplayKeys_PopUp):
    pass


# A Drag&Drop latch-on class that can be used on any tk.Entry or tk.Spinbox widget
# noinspection PyUnresolvedReferences
class DisplayKeys_DragDrop:
    """
    Class that adds drag-and-drop functionality to a Tkinter widget.
    Any Data received will be passed along to the Widget to handle the input data.
    This simply ensures that you get the expected data.
    :param widget: The Widget to which to attach the Drag n Drop functionality.
    :param drop_type: Specifies the type of Data that is expected to be received and handled by this widget.
    """

    def __init__(self, widget: tk.Entry | tk.Spinbox, parent_widget,
                 drop_type: Literal["image", "folder", "text", "any"], traced_callback=None):
        self.widget = widget
        self.parent_widget = parent_widget
        self.trace_callback = traced_callback
        self.original_bg: str
        self.current_widget_state: str

        self.type_legend = {"image": DND_FILES, "folder": DND_FILES, "text": DND_TEXT, "any": DND_ALL}
        self.type = drop_type
        self.accept_type = self.type_legend[drop_type] if drop_type in self.type_legend else print("Incorrect drag type for:", widget)

        self.drag_pos_x, self.drag_pos_y = 0.0, 0.0

        self.enable_dnd()

    def enable_dnd(self):
        # Register widget with drag and drop functionality.
        self.widget.drop_target_register(self.accept_type)
        self.widget.dnd_bind('<<Drop>>', self.drop)
        self.widget.dnd_bind('<<DropEnter>>', self.drag_enter)
        self.widget.dnd_bind('<<DropLeave>>', self.drag_leave)
        self.widget.dnd_bind('<<DropPosition>>', self.drag_position)  # Doesnt trigger

    def disable_dnd(self):
        self.widget.dnd_bind('<<Drop>>', None)
        self.widget.dnd_bind('<<DragEnter>>', None)
        self.widget.dnd_bind('<<DragLeave>>', None)
        self.widget.dnd_bind('<<DropPosition>>', None)

    def drag_position(self, event):
        if not self.drag_pos_x == event.x_root or not self.drag_pos_y == event.y_root:
            print("---DnD Drag---")
            self.drag_pos_x = event.x_root
            self.drag_pos_y = event.y_root

            # For testing
            print('Dragging over widget: %s' % self.parent_widget.id)
        return event.action

    def drag_enter(self, event):
        print("---DnD Enter---")
        print('Entering widget: %s' % self.parent_widget.id)

        if event.data:
            if self.accept_type == (self.type_legend["image"] or self.type_legend["folder"]):
                # Remove brackets
                data_path = event.data[1:-1]
                print("The data path:", data_path)

                if self.type == "image":
                    try:
                        # Attempt to open image file, to ensure it is an image
                        Image.open(data_path)
                        # Show Can Drop
                        self.set_background(event.widget, 'green')
                    except IOError:
                        # Show Can't Drop
                        self.set_background(event.widget, 'red')
                        print("Not an Image DnD!")

                elif self.type == "folder":
                    # Ensure that dropped item is a folder
                    if os.path.isdir(event.data):
                        # Show Can Drop
                        self.set_background(event.widget, 'green')
                    else:
                        # Show Can't Drop
                        self.set_background(event.widget, 'red')
                        print("Not a Folder DnD!")
            elif self.accept_type == self.type_legend["text"]:
                try:
                    # Ensure that dropped item is text
                    event.data.encode('utf-8')
                    # Show Can Drop
                    self.set_background(event.widget, 'green')
                except UnicodeDecodeError:
                    # Show Can't Drop
                    self.set_background(event.widget, 'red')
                    print("Not a Text DnD!")
            elif self.accept_type == self.type_legend["any"]:
                # Show Can Drop
                self.set_background(event.widget, 'green')

        # self.set_background(event.widget)

        # print("Background was:", self.original_bg)

        return event.action

    def drag_leave(self, event):
        print("---DnD Leave---")
        print('Leaving widget: %s' % self.parent_widget.id)

        self.reset_background(event.widget)

        return event.action

    def drop(self, event):
        print("---Dropping File---")
        if event.data:
            # Check if a trace is attached to the widget
            widget_var = None
            trace_id = None
            if isinstance(self.widget, tk.Entry) and hasattr(self.parent_widget, 'textbox_var'):
                widget_var = self.parent_widget.textbox_var
                if hasattr(self.parent_widget, 'textbox_trace'):
                    trace_id = self.parent_widget.textbox_trace
            elif isinstance(self.widget, tk.Spinbox) and hasattr(self.parent_widget, 'spinbox_var'):
                widget_var = self.parent_widget.spinbox_var
                if hasattr(self.parent_widget, 'spinbox_trace'):
                    trace_id = self.parent_widget.spinbox_trace

            # Disable Trace if one exists
            if widget_var is not None and trace_id is not None:
                ButtonFunctions.disable_trace(widget_var, trace_id)

            # Store original widget state
            widget_original_state = self.widget.__getitem__('state')
            print("Original widget State: " + widget_original_state)

            # Set widget to editable
            self.widget.configure(state='normal')
            widget_current_text = self.widget.get()  # Backup if needed
            self.widget.delete(0, tk.END)

            # Re-Enable Trace if one existed
            if widget_var is not None and trace_id is not None:
                ButtonFunctions.enable_trace(widget_var, self.parent_widget, self.trace_callback)

            if self.accept_type == (self.type_legend["image"] or self.type_legend["folder"]):
                # Remove unnecessary brackets (beginning / end of string)
                data_path = event.data[1:-1]
                print("The data path:", data_path)

                if self.type == "image":
                    # Attempt to open image file, to ensure it is an image
                    try:
                        Image.open(data_path)
                        # Save path to widget
                        self.widget.insert(tk.END, data_path)
                    except IOError:
                        self.widget.insert(tk.END, widget_current_text)
                        PopUp_Dialogue(app.window, popup_type='error',
                                       message=f'Not an Image or supported Type!\nSupported Types are:\n- Static |  {split.get_supported_types()[0]}\n- Animated |  {split.get_supported_types()[1]}',
                                       buttons=[{'OK': lambda: None}])
                        print("Not an Image DnD!")

                elif self.type == "folder":
                    # Ensure that dropped item is a folder
                    if os.path.isdir(event.data):
                        self.widget.insert(tk.END, event.data)
                    else:
                        self.widget.insert(tk.END, widget_current_text)
                        PopUp_Dialogue(app.window, popup_type='error',
                                       message='Not an Folder!',
                                       buttons=[{'OK': lambda: None}, {'CANCEL': lambda: None}, ])
                        print("Not a Folder DnD!")

            elif self.accept_type == self.type_legend["text"]:
                # Ensure that dropped item is text
                try:
                    event.data.encode('utf-8')
                    self.widget.insert(tk.END, event.data)
                except UnicodeDecodeError:
                    PopUp_Dialogue(app.window, popup_type='error',
                                   message='Not Text!',
                                   buttons=[{'OK': lambda: None}])
                    print("Not a Text DnD!")

            elif self.accept_type == self.type_legend["any"]:
                self.widget.insert(tk.END, event.data)

            # Set widget back to its original state
            self.widget.configure(state=widget_original_state)

        else:
            print("COULDN'T GET DROP DATA!")

        # Reset background colour
        self.reset_background(event.widget)

        return event.action

    def set_background(self, widget, colour):
        self.current_widget_state = widget.cget('state')
        if self.current_widget_state == 'normal':
            self.original_bg = widget.cget("background")
            widget.configure(background=colour)
        elif self.current_widget_state == 'readonly':
            self.original_bg = widget.cget("readonlybackground")
            widget.configure(readonlybackground=colour)
        elif self.current_widget_state == 'disabled':
            self.original_bg = widget.cget("disabledbackground")
            widget.configure(disabledbackground=colour)

    def reset_background(self, widget):
        if self.current_widget_state == 'normal':
            widget.configure(background=self.original_bg)
        elif self.current_widget_state == 'readonly':
            widget.configure(readonlybackground=self.original_bg)
        elif self.current_widget_state == 'disabled':
            widget.configure(disabledbackground=self.original_bg)


# A Label holding an Image with a Tooltip attached to it, used to simply provide helpful information
class DisplayKeys_Help:
    """
        A Label with a Question Mark Image and a Tooltip used for General Hints/Support
        :param parent: The Widget that it will be contained in (usually a frame).
        :param row: Used to determine its Horizontal Position inside its parent Frame.
        :param col: Used to determine its Vertical Position inside its parent Frame.
        :param alignment: Determines the Positional Alignment in its row | col.
        :param percentage_size: Scales the size of the Image.
        :param help_tooltip: The tooltip text to display.
        :param tooltip_justification: See DisplayKeys_Tooltip for clarification.
        :param tooltip_anchor: See DisplayKeys_Tooltip for clarification.
    """

    def __init__(self, parent: tk.Frame, row: int = 0, col: int = 0, alignment: str = "nsew",
                 percentage_size: int = 100, help_tooltip: str = "Placeholder Help",
                 tooltip_justification: Literal["left", "center", "right"] = "center",
                 tooltip_anchor: Literal["nw", "n", "ne", "w", "center", "e", "sw", "s", "se"] = "center"):
        self.image = Image.open(sys_help_img)
        new_size = int(self.image.height * (percentage_size / 100))
        self.resized_image = ImageTk.PhotoImage(self.image.resize((new_size, new_size)))

        self.label = tk.Label(master=parent, image=self.resized_image, background=parent.cget("bg"))
        self.label.grid(sticky=alignment, column=col, row=row)

        self.h_tooltip = DisplayKeys_Tooltip(self.label, help_tooltip,
                                             justify=tooltip_justification,
                                             anchor=tooltip_anchor)


# A collection of button functions to be used throughout the UI
class ButtonFunctions:
    # ----- Debug: -----
    # For testing new UI without wanting any actual actions taken.
    @staticmethod
    def placeholder(widget_id):
        print("Placeholder Function")
        return

    @staticmethod
    # For Debugging the process_image function
    def placeholder_process(image_path, output_dir, rows, columns, gap):
        print("ImagePath: " + image_path)
        print("OutputPath: " + output_dir)
        print("Rows: " + rows)
        print("Columns: " + columns)
        print("Gap: " + gap)
        return

    # ----- Workarounds: -----
    # For temporary in code workaround solutions
    @staticmethod
    def disable_binding(widget, event_name, function_name):
        widget.unbind(event_name, function_name)

    @staticmethod
    def enable_binding(widget, event_name, function_name):
        widget.bind(event_name, function_name)

    @staticmethod
    def disable_trace(traced_variable: vars, trace_id: vars, event: str = "w"):
        """

            :param traced_variable: The Widget's Variable which holds the Trace to be destroyed.
            :param trace_id: The variable holding the stored Trace.
            :param event: The Type of Event to trigger the Trace.
        """
        # Ensure widget has a trace
        if ButtonFunctions.has_trace(traced_variable):
            traced_variable.trace_vdelete(event, trace_id)
            print("Deleted Trace:", trace_id)

    # Trace_variable_name (string) should be provided based on type of widget
    # (i.e. if textbox: textbox_trace, if spinbox: spinbox_trace, etc.)
    @staticmethod
    def enable_trace(variable_to_trace: vars, widget: DisplayKeys_Composite_Widget, function, event: str = "w"):
        """
        Will create a new Trace on a widget, that will fire a callback function whenever it is triggered.
        :param variable_to_trace: The Widget's Variable to enable the trace on.
        :param widget: The Parent widget to store the newly created Trace.
        :param function: The Function to Call when the Trace is triggered.
        :param event: The Event that will trigger this Trace.
        """
        # Create trace
        trace = variable_to_trace.trace(event, lambda *args: function(widget.id))
        widget.textbox_trace = trace
        print("Re-attached Trace:", type(widget.textbox_trace), widget.textbox_trace)
        return trace

    @staticmethod
    def has_trace(item: vars) -> bool:
        if item.trace_info():
            return True

        return False

    # ----- Main Window Functions: -----
    # --- Buttons ---

    # Grabs the Path to an Image, and if possible adds this into a widgets textbox
    @staticmethod
    def browse_image(widget_id: str) -> str:
        """
            Grabs the Path to an Image, and if possible adds this into a widgets textbox
            :param widget_id: The Unique ID of the Widget that Called this function
            :return: The Path on Disk to the Image
        """
        print("---Browsing for Image---")
        print("Widget ID: " + widget_id)
        # Get the Composite widget, if it contains the button that called this function
        widget: DisplayKeys_Composite_Widget = app.get_property_widget_by_child(widget_id)

        if widget:
            # Ask the user to select an Image
            file_path = filedialog.askopenfilename(
                filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.gif;*.bmp")]
            )
            # Put File Path into textbox if widget has a textbox
            if file_path and widget.textbox:
                widget_original_state = widget.textbox.__getitem__('state')
                print("Original Textbox State: " + widget_original_state)

                # Temporarily disable the trace (avoid calling process image with 'None' path)
                ButtonFunctions.disable_trace(widget.textbox_var, widget.textbox_trace)

                widget.textbox.configure(state='normal')
                widget.textbox.delete(0, tk.END)

                # Re-Enable the trace
                ButtonFunctions.enable_trace(widget.textbox_var, widget, ButtonFunctions.process_image)

                widget.textbox.insert(tk.END, file_path)
                widget.textbox.configure(state=widget_original_state)

            # Just in case its ever needed
            return file_path

    # Grabs the Path to a Directory, and if possible adds this into a widgets textbox
    @staticmethod
    def browse_directory(widget_id: str) -> str:
        """
            Grabs the Path to a Directory, and if possible adds this into a widgets textbox
            :param widget_id: The Unique ID of the Widget that Called this function
            :return: The Path on Disk to the Output Folder
        """
        print("---Browsing for Output Dir---")
        print("Widget ID: " + widget_id)
        widget = app.get_property_widget(widget_id)

        if widget:
            # Request the user to select a Directory
            output_path = filedialog.askdirectory()
            # Put Directory Path into textbox if widget has a textbox
            if output_path and widget.textbox:
                widget_original_state = widget.textbox.__getitem__('state')
                print("Original Textbox State: " + widget_original_state)

                widget.textbox.configure(state='normal')
                widget.textbox.delete(0, tk.END)
                widget.textbox.insert(tk.END, output_path)
                widget.textbox.configure(state=widget_original_state)

            # Just in case its ever needed
            return output_path

    # Grabs all required parameters and passes it to either the DisplayKeys_Previewer update or
    # Determine_Split_Type function.
    # Currently, defaults are provided for any of the required inputs that are missing.
    @staticmethod
    def process_image(widget_id: str):
        """
            Grabs all required parameters and passes it to either the DisplayKeys_Previewer update or
            Determine_Split_Type function.

            Currently, no defaults are provided for any of the required inputs that are missing.
            :param widget_id: The Unique ID of the Widget that Called this function
        """
        print("---Processing Image---")
        print("Widget ID: " + widget_id)
        calling_widget = app.get_property_widget(widget_id)
        widgets = app.properties
        previewer = app.preview

        # Get Image Properties Type
        get_params_type_widget = app.get_property_widget("GetParamsType").get_child("GetParamsDropdown")

        # Get Selected Preset
        get_preset_list_widget = app.get_property_widget("PresetList").get_child("PresetListDropdown")

        # Get Text boxes to process image
        get_image_widget = app.get_property_widget("GetImage").get_child("GetImageTextbox")
        get_output_widget = app.get_property_widget("GetOutput").get_child("GetOutputTextbox")
        get_rows_widget = app.get_property_widget("GetRows").get_child("GetRowsSpinbox")
        get_columns_widget = app.get_property_widget("GetColumns").get_child("GetColumnsSpinbox")
        get_gap_widget = app.get_property_widget("GetGap").get_child("GetGapSpinbox")

        if all(widget is not None for widget in
               [get_image_widget, get_output_widget, get_rows_widget, get_columns_widget, get_gap_widget,
                get_params_type_widget, previewer]):

            # Will always attempt to get the Image and Output Dir as it will ALWAYS be required
            # when saving to disk
            image_path = get_image_widget.get() if get_image_widget.get() else None
            output_dir = get_output_widget.get() if get_output_widget.get() else None
            if not image_path:
                image_path = sys_preview_img

                # Disable Trace temporarily to not call this function again mid-execution
                ButtonFunctions.disable_trace(get_image_widget.textbox_var, get_image_widget.textbox_trace)

                # Temporarily set the text entry widget to normal state to update its value
                get_image_widget.configure(state="normal")
                get_image_widget.delete(0, tk.END)

                get_image_widget.insert(tk.END, image_path)
                get_image_widget.configure(state="readonly")

                # Re-enable Trace
                ButtonFunctions.enable_trace(get_image_widget.textbox_var, get_image_widget,
                                             lambda *args: ButtonFunctions.process_image(get_image_widget.id))

            if not output_dir:
                output_dir = os.path.join(os.path.expanduser("~"), "Desktop")

                # Temporarily set the text entry widget to normal state to update its value
                get_output_widget.configure(state="normal")
                get_output_widget.delete(0, tk.END)
                get_output_widget.insert(tk.END, output_dir)
                get_output_widget.configure(state="readonly")

            # Determine if a Preset`s or User-Defined values should be used
            # Can later be expanded to Presets (i.e. 'CurrentPreset')
            if get_params_type_widget.dropdown_var.get() == "Preset":
                if get_preset_list_widget.dropdown_var.get() and app.presets:
                    preset_name = get_preset_list_widget.dropdown_var.get()
                    print(f"Selected Preset: {preset_name}")

                    # Find and Load Preset via function using name
                    selected_preset = PresetData.get_preset(preset_name)
                    rows = selected_preset.rows
                    columns = selected_preset.cols
                    gap = selected_preset.gap
                    x_offset = previewer.final_offset["x"] if previewer.final_offset else None
                    y_offset = previewer.final_offset["y"] if previewer.final_offset else None
                else:
                    PopUp_Dialogue(app.window, popup_type='error', message='Preset List was not found!', buttons=[{"OK": lambda: None}])
            elif get_params_type_widget.dropdown_var.get() == "User Defined":
                rows = int(get_rows_widget.get()) if get_rows_widget.get().isnumeric() else None
                columns = int(
                    get_columns_widget.get()) if get_columns_widget.get().isnumeric() else None
                gap = int(get_gap_widget.get()) if get_gap_widget.get().isnumeric() else None
                x_offset = previewer.final_offset["x"] if previewer.final_offset else None
                y_offset = previewer.final_offset["y"] if previewer.final_offset else None
                if not all(param is not None for param in [rows, columns, gap, x_offset, y_offset]):
                    # TODO: This occurs when you select all text, and enter the first digit no matter what!
                    #PopUp_Dialogue(app.window, popup_type="error", message="A Property was None!")
                    print("A Property was None!")
                    return
            else:
                return

            if widget_id == "SplitImage":
                # Split Image
                # Determine_Split_Type function then passes it to the appropriate Splitting function
                split.determine_split_type(image_path, output_dir, rows, columns, gap, x_offset, y_offset)
            else:
                # Update the preview
                app.preview.update_preview(image_path, rows, columns, gap)

                # TODO:
                #       The previewer will in the future to use 'Split.calculate_image_split()' function's output.
                #       Here is an example of how its intended:
                #       app.preview.update_preview(Split.calculate_image_split(...))
                #
                #       (This will directly pass the results to the update function,
                #       allowing me to rewrite the update function to directly use the output)

        else:
            print("One or more required widgets are missing.")

    # Calls the Popup class to Create a new Preset
    @staticmethod
    def create_preset_popup(widget_id: str):
        PopUp_Preset_Add(app.window)

    # Calls the Popup class to Edit an existing Preset
    @staticmethod
    def edit_preset_popup(widget_id: str):
        preset_list_widget = app.get_property_widget("PresetList").get_child("PresetListDropdown")
        current_preset_name = preset_list_widget.dropdown_var.get()
        if current_preset_name == "Default":
            PopUp_Dialogue(app.window, popup_type='error', message="Cannot Edit 'Default' Preset!", buttons=[{'OK': lambda: None}])
            return

        PopUp_Preset_Edit(app.window, current_preset_name)

    # Calls Dialogue Popup to confirm Preset Deletion
    @staticmethod
    def delete_preset_popup(widget_id: str):
        preset_list_widget = app.get_property_widget("PresetList").get_child("PresetListDropdown")
        current_preset = preset_list_widget.dropdown_var.get()
        if current_preset == "Default":
            PopUp_Dialogue(app.window, popup_type='error', message="Cannot Delete 'Default' Preset!",
                           buttons=[{'OK': lambda: None}])
            return

        PopUp_Dialogue(parent=app.window, popup_type='warning',
                       message=f"Do you want to delete the profile: {current_preset}?",
                       buttons=[{'Yes': ButtonFunctions.delete_preset}, {'No': lambda: None}])

    # --- Dropdowns: ---
    # Hides / Un-hides specific Widgets
    @staticmethod
    def property_options_visibility(properties: list[DisplayKeys_Composite_Widget]):
        """
            Hides / Un-hides specific Widgets
            (Will change in the future be changed to provide the list of Widgets it wants the visibility toggled for)
            :param properties: The list of Properties Widgets.
        """
        # option = app.get_property_widget("GetParamsType").get_child("GetParamsDropdown").dropdown_var.get()

        # Shortened Class Reference Name
        comp_class = DisplayKeys_Composite_Widget

        option = comp_class.get_composite_widget("GetParamsType", properties).get_child("GetParamsDropdown").dropdown_var.get()

        # Get the widgets to show/hide
        get_preset_list = comp_class.get_composite_widget("PresetList", properties)
        get_preset_create = comp_class.get_composite_widget("PresetAdd", properties)
        get_preset_edit = comp_class.get_composite_widget("PresetEdit", properties)
        get_preset_delete = comp_class.get_composite_widget("PresetDelete", properties)

        get_rows_widget = comp_class.get_composite_widget("GetRows", properties)
        get_columns_widget = comp_class.get_composite_widget("GetColumns", properties)
        get_gap_widget = comp_class.get_composite_widget("GetGap", properties)

        # Show/hide the widgets based on the selected option
        if all(widget is not None for widget in [get_rows_widget, get_columns_widget, get_gap_widget, get_preset_list,
                                                 get_preset_create, get_preset_edit, get_preset_delete]):
            if option == "Preset":
                for widget in (get_rows_widget, get_columns_widget, get_gap_widget):
                    if widget:
                        widget.grid_remove()
                for widget in (get_preset_list, get_preset_create, get_preset_edit, get_preset_delete):
                    if widget:
                        widget.grid(sticky="n")
            elif option == "User Defined":
                for widget in (get_preset_list, get_preset_create, get_preset_edit, get_preset_delete):
                    if widget:
                        widget.grid_remove()
                for widget in (get_rows_widget, get_columns_widget, get_gap_widget):
                    if widget:
                        widget.grid(sticky="n")
        else:
            print(f"Property Visibility: CANT GET OPTION!")

    # Populates the 'Preset' dropdown with preset options with currently available presets.
    # Then sets the Default preset as the selected one.
    @staticmethod
    def populate_property_presets_options(properties: list[DisplayKeys_Composite_Widget], presets: list['PresetData'], set_selection: [bool, str] = [False, ''], reset_selection: bool = True):
        properties_dropdown_widget = app.get_property_widget("PresetList").get_child("PresetListDropdown")

        preset_names = []
        for preset in presets:
            preset_names.append(preset.name)
            print(f"populate presets name: {preset_names}")
        properties_dropdown_widget['values'] = preset_names
        if set_selection[0]:
            properties_dropdown_widget.dropdown_var.set(set_selection[1])
        elif reset_selection:
            properties_dropdown_widget.dropdown_var.set(preset_names[0])

    # ----- Popup Windows: -----
    # Saves the Preset provided from the Popup_Preset_Add window
    @staticmethod
    def add_preset(name: str, rows: int, cols: int, gap: int):
        app.presets.append(PresetData(name, rows, cols, gap))
        ButtonFunctions.populate_property_presets_options(app.properties, app.presets, set_selection= [True, name])

    # Saves the Preset provided from the Popup_Preset_Edit window
    @staticmethod
    def edit_preset(current_preset: str, new_name: str, rows: int, cols: int, gap: int):
        for preset in app.presets:
            if preset.name == current_preset:
                preset.name = new_name
                preset.rows = rows
                preset.cols = cols
                preset.gap = gap

        ButtonFunctions.populate_property_presets_options(app.properties, app.presets, set_selection=[True, new_name])

    # Deletes the currently selected Preset
    @staticmethod
    def delete_preset():
        # Get name of currently selected preset
        current_preset = app.get_property_widget("PresetList").get_child("PresetListDropdown").dropdown_var.get()

        for preset in app.presets:
            if preset.name == current_preset:
                # delete the preset that currently exists...
                app.presets.remove(preset)
                continue
        ButtonFunctions.populate_property_presets_options(app.properties, app.presets, reset_selection=True)

    # ----- Menu Bar: -----
    # Closes Application
    @staticmethod
    def quit():
        app.window.destroy()

    # Load all presets from file with Default, replacing existing ones
    @staticmethod
    def load_presets_file():
        print("---Importing Presets---")
        app.presets = []
        app.presets.append(app.default_preset)
        app.presets.extend(PresetData.load_presets_from_file())
        ButtonFunctions.populate_property_presets_options(app.properties, app.presets)

    # Save all presets to file, excluding the Default Preset
    @staticmethod
    def save_presets_file():
        PresetData.save_presets_to_file()

    # Delete all currently existing Presets, excludes the Default Preset
    @staticmethod
    def delete_all_presets():
        app.presets = []
        app.presets.append(app.default_preset)
        ButtonFunctions.populate_property_presets_options(app.properties, app.presets, reset_selection=True)
        PopUp_Dialogue(app.window, popup_type='confirm', message="Deleted All Current Presets!",
                       buttons=[{'OK': lambda: None}])


# Defines the Data structure of Presets as well as contains all of its functionality.
# Each Preset is able to independently preform its necessary operations once created.
class PresetData:
    def __init__(self, name="", rows=0, cols=0, gap=1):
        self.name = name
        self.rows = rows
        self.cols = cols
        self.gap = gap

    # Serialize Data to JSON
    @staticmethod
    def to_json(preset: 'PresetData'):
        return {
            "name": preset.name,
            "rows": preset.rows,
            "cols": preset.cols,
            "gap": preset.gap,
        }

    # De-Serialize from JSON to Data Struct
    @classmethod
    def from_json(cls, data_dict):
        return cls(
            name=data_dict.get("name", "Placeholder"),
            rows=data_dict.get("rows", 1),
            cols=data_dict.get("cols", 1),
            gap=data_dict.get("gap", 1),
        )

    # Currently only saves itself to a selected/new file
    # Need to change to save all presets that are in the list to this file
    # and make this into a static method
    @staticmethod
    def save_presets_to_file():
        print("---Saving Preset---")
        file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                 filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not file_path:  # If user cancels the save dialog
            return
        with open(file_path, 'w') as file:
            if app.presets:
                if len(app.presets) > 1:
                    json_presets = []
                    for current_preset in app.presets[1:]:  # Start from the second preset, skipping the first
                        json_presets.append(PresetData.to_json(current_preset))
                    print(json_presets)
                    json.dump(json_presets, file)
                else:
                    PopUp_Dialogue(app.window, popup_type="error", message="No new Presets were found!", buttons=[{'OK': lambda: None}])

    # Currently only loads a single preset from a selected file
    # Need to change it to load all presets into a list
    @staticmethod
    def load_presets_from_file():
        print("---Loading Presets---")
        file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"),
                                                                                    ("All files", "*.*")])
        if not file_path:  # If user cancels the open dialog
            return []
        with open(file_path, 'r') as file:
            loaded_presets = []
            data_list = json.load(file)
            for data_dict in data_list:
                loaded_presets.append(PresetData.from_json(data_dict))

            for preset in loaded_presets:
                print(f"Imported Preset: {preset.name}")
            return loaded_presets

    # Retrieves a single Preset by name from the list of currently existing Presets
    @staticmethod
    def get_preset(preset_name: str):
        # Ensure there are Presets in array
        if len(app.presets) > 0:
            # Get Preset
            preset = next((preset for preset in app.presets if preset_name == preset.name), None)
            if preset:
                print(f"Retrieved Preset {preset}")
                return preset
            else:
                PopUp_Dialogue(app.window, popup_type='error', message=f"No Preset of the name '{preset_name}' found!", buttons=[{'OK': lambda: None}])
        else:
            PopUp_Dialogue(app.window, popup_type='error', message=f"Presets list is empty!", buttons=[{'OK': lambda: None}])


# The Default Values for the split functionality
class DefaultSplitData(Enum):
    """
        Default Values for Split Functionality
        Members are:
        [ ROWS, COLS, GAPPIX, GAPPER, GAPPERX, GAPPERY ]
        * GAPPIX = Pixels, GAPPER = Percentage, GAPPER X/Y = Percentage on Axis
    """
    ROWS: int = 2
    COLS: int = 6
    GAPPIX: int = 40
    GAPPER: float = 5.8  # Calculated per Axis, used result respectively
    GAPPERX: float = 3.7  # Calculated with X Axis, used on Both
    GAPPERY: float = 7.9  # Calculated with Y Axis, used on Both


####################################################################################################################
#                                                   Split Image
####################################################################################################################

class split:
    # Holds the list of currently supported Image Types,
    # Might look into extending this in the future if necessary.
    @staticmethod
    def get_supported_types():
        # The supported file formats:
        sup_image_formats = [".png", ".jpg", ".jpeg", ".bmp"]
        sup_animated_formats = [".gif"]
        return sup_image_formats, sup_animated_formats

    # Checks the provided image and determines whether it's a static or dynamic image format.
    # Also passes along rest of variables provided by ButtonFunctions.ProcessImage
    @staticmethod
    def determine_split_type(file_path: str, output_dir: str, rows: int, cols: int, gap: int | float, x_offset: float, y_offset: float):
        print("---Determining File Type---")

        # The supported file formats:
        image_formats = split.get_supported_types()[0]
        animated_formats = split.get_supported_types()[1]

        print("File Types are: ")
        print(split.get_supported_types()[0])
        print(split.get_supported_types()[1])

        try:
            # Check if Image Format is supported
            with Image.open(file_path) as image:
                print("Image can be opened: " + (
                    "True" if image else "False") + "\n   Image format is: " + "." + image.format.lower())
                # Is Static
                if "." + image.format.lower() in image_formats:
                    split.image_static(file_path, output_dir, rows, cols, gap, x_offset, y_offset)
                    return True
                # Is Animated
                elif "." + image.format.lower() in animated_formats:
                    split.image_animated(file_path, output_dir, rows, cols, gap, x_offset, y_offset)
                    return True
                else:
                    print("No formats matched")

        # Is not of a supported image format
        except TypeError as error_message:
            PopUp_Dialogue(app.window, 'error', f"File Format not supporte\nCurrenlty supported formats are:\n- Static     | {split.get_supported_types()[0]}\n- Animated  | {split.get_supported_types()[1]}")
            print("Wrong File Type: ", type(error_message).__name__, str(error_message))
            return None

    # TODO:
    #  1.) Replace the Previewer Drawing Functionality inside of the Previewer Update Function
    #      to use the calculate_image_split function's returned 'preview_coordinates'
    #       ( This may be too complicated now with the way the Offset input interacts with the Preview rendering )
    #       ( Will check when I am not sleep deprived to make sure it works when adapting to use external function )

    # Calls 'calculate_image_split' and saves its output 'image_cells'
    @staticmethod
    def image_static(image_path: str, output_dir: str, rows: int, cols: int, gap: int, x_offset: float, y_offset: float):
        # Open the image using PIL
        static_image = Image.open(image_path)

        # Split the Image
        split_image = split.calculate_image_split(static_image, rows, cols, gap, x_offset, y_offset)

        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Generate the output file path
        filename_without_extension = os.path.splitext(os.path.basename(static_image.filename))[0]

        # Save the image-cells
        cell: ImageTk.PhotoImage
        for cell in split_image["image_cells"]:
            output_path = os.path.join(output_dir, f"{filename_without_extension}_{cell.filename}.png")
            cell.save(output_path)

            print(f"Saved {output_path}")

    # Calls 'calculate_image_split' for each frame of an image
    # Recombines each image cell for each frame, before saving the combined Image-Cell
    # Preserves or adds Frame Timings in case Frame's are missing this information.
    # Discards 0ms Frame Times. Default Frame Timing is 100ms. If only some Frame's have timing, average will be used.
    # noinspection PyUnresolvedReferences
    @staticmethod
    def image_animated(gif_path: str, output_dir: str, rows: int, cols: int, gap: int, x_offset: float, y_offset: float):
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Open the image using PIL
        gif = Image.open(gif_path)
        print("GIF Frame Count: " + str(gif.n_frames))

        # Extract frames from .gif file
        frames = []
        for frame in ImageSequence.Iterator(gif):
            frames.append(frame.copy())

        # Get duration of each frame
        frame_durations = []
        for frame in range(0, gif.n_frames):
            gif.seek(frame)
            try:
                duration = int(gif.info['duration'])
                if duration > 0:
                    frame_durations.append(duration)
                else:
                    frame_durations.append(0)
            except(KeyError, TypeError):
                print("No frame durations present")

                # Add default time in case no frame duration is provided by .gif
                frame_durations.append(0)

        # Calculate average duration
        non_zero_durations = [d for d in frame_durations if d > 0]
        if len(non_zero_durations) > 0:
            default_duration = sum(non_zero_durations) // len(non_zero_durations)
        else:
            default_duration = 100

        # Replace missing values with average duration
        for i in range(len(frame_durations)):
            if frame_durations[i] == 0:
                frame_durations[i] = default_duration
        print("Frame Durations: \n" + frame_durations.__str__())

        # Takes the extracted frames from the gif and splits them individually
        modified_frame_cells = []
        for frame in frames:
            split_frame = split.calculate_image_split(frame, rows, cols, gap, x_offset, y_offset)
            modified_frame_cells.append(split_frame["image_cells"])

        combined_cells = []
        # Combine Image cell's into gif cell's (ie. [frame 0 cell 0] + [frame 1 cell 0] + [frame 2 cell 0] + etc.)
        num_cells = len(modified_frame_cells[0])
        for cell_index in range(num_cells):
            for frame_cells in modified_frame_cells:
                combined_cells.append(frame_cells[cell_index])

            # Generate the output file path
            filename_without_extension = os.path.splitext(os.path.basename(gif.filename))[0]

            # Use the filename of the cell image for creating the output_path

            cell_name = combined_cells[0].filename
            output_path = os.path.join(output_dir, f"{filename_without_extension}_{cell_name}.gif")

            # Save the combined cells as a .gif file
            combined_cells[0].save(output_path, save_all=True, append_images=combined_cells[1:],
                                   duration=frame_durations, loop=0)

            print(f"Saved {output_path}")
            combined_cells = []

    # Splits the provided Image into Image-Cell's based on provided parameters.
    # Will also crop the Image-Cells into a Square Format
    # Returns {preview_coordinates, image_cells}
    @staticmethod
    def calculate_image_split(image: ImageTk, rows: int, cols: int, gap: int, x_offset: float, y_offset: float) -> dict[str, list[dict] | str, list[ImageTk.PhotoImage]]:
        preview_grid = []
        cropped_cells = []

        # Calculate the width and height of each image-cell
        width, height = image.size
        print("Image Dimensions:", width, height)
        cell_width = (width - (cols - 1) * gap) // cols
        cell_height = (height - (rows - 1) * gap) // rows
        print("Cell Dimensions:", cell_width, cell_height)

        # Determine the maximum cell size (to maintain square shape)
        max_cell_size = min(cell_width, cell_height)
        print("Max Cell Size:", max_cell_size)

        # Calculate the horizontal and vertical gap offsets for cropping
        gap_horizontal_offset = (cell_width - max_cell_size) // 2
        gap_vertical_offset = (cell_height - max_cell_size) // 2

        print("Gap Offsets:", gap_horizontal_offset, gap_vertical_offset)

        # Determine the longest dimension (width or height)
        longest_dimension = "width" if cell_width > cell_height else "height"

        # Split the image and save each image-cell
        for row in range(rows):
            for col in range(cols):
                # Calculate the coordinates for cropping
                left = (col * (cell_width + gap) + gap_horizontal_offset) - x_offset
                upper = (row * (cell_height + gap) + gap_vertical_offset) - y_offset

                # Remove rows/columns only if they are part of the Outlier image-cells
                if row == 0:
                    upper += gap_vertical_offset
                elif row == rows - 1:
                    upper -= gap_vertical_offset
                if col == 0:
                    left += gap_horizontal_offset
                elif col == cols - 1:
                    left -= gap_horizontal_offset
                if longest_dimension == "width":
                    right = left + max_cell_size
                    lower = upper + cell_height
                else:
                    right = left + cell_width
                    lower = upper + max_cell_size

                # Crop all image-cells
                image_cell = image.crop((left, upper, right, lower))

                ########## Outputs ##########

                # Generate new Image-Cell Name
                image_cell.filename = f"{row}_{col}"
                # Save Image Cell
                cropped_cells.append(image_cell)

                # Store Coordinates of split image cells, for Previewer
                grid_cell = [{
                    "cell": f"{row}_{col}",
                    "Left_Coord": left,
                    "Right_Coord": right,
                    "Upper_Coord": upper,
                    "Lower_Coord": lower,
                }]
                preview_grid.append(grid_cell)

        return {"preview_coordinates": preview_grid, "image_cells": cropped_cells}


####################################################################################################################
#                                                    Create GUI
####################################################################################################################


if __name__ == "__main__":
    # For flow debugging
    print("---Code Start---")

    # Create/Start Application Window
    app = DisplayKeys_GUI()
    app.run()
