bl_info = {
    "name": "Addon Development Tool",
    "description": "Removes redundancy and repetition in the creating and testing of Blender addons",
    "author": "Nathan Craddock",
    "version": (0, 1),
    "blender": (2, 75, 0),
    "location": "Properties shelf of the text editor",
    "warning": "",
    "support": "COMMUNITY",
    "category": "Text Editor"
}

import bpy
from bpy.types import Panel, AddonPreferences, PropertyGroup, UIList, Operator
from bpy.props import StringProperty, CollectionProperty, IntProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.app.handlers import persistent

import os
import zipfile
import json

#######################################################################################
# FUNCTIONS
#######################################################################################

@persistent
def get_projects(scene):
    # Import projects from JSON file
    projects_file = bpy.utils.script_path_user() + os.sep + "ADTProjects.json"
    project_list = bpy.context.scene.project_list
    names = [p.name for p in project_list]
    
    with open(projects_file) as readfile:
        projects = json.load(readfile)
    
    print("Imported", projects)
    
    for p in projects:
        if p[0] not in names:
            bpy.context.scene.project_list.add()
            bpy.context.scene.project_list_index = len(bpy.context.scene.project_list) - 1
            bpy.context.scene.project_list[bpy.context.scene.project_list_index].name = p[0]
            bpy.context.scene.project_list[bpy.context.scene.project_list_index].location = p[1]
            bpy.context.scene.project_list[bpy.context.scene.project_list_index].is_addon = True
    
def save_projects(scene):
    # Save project list to a JSON file
    projects_file = bpy.utils.script_path_user() + os.sep + "ADTProjects.json"
    project_list = bpy.context.scene.project_list
    
    projects = []
    
    for p in project_list:
        project = []
        project.append(p.name)
        project.append(p.location)
        project.append(p.is_addon)
        
        projects.append(project)
    
    print("Exported", projects)
    
    with open(projects_file, 'w') as savefile:
        json.dump(projects, savefile)        
        
def update_file_list(context):
    # Update the list of files for the current project
    if len(context.scene.project_list) > 0:
        project = context.scene.project_list[context.scene.project_list_index]
        
        # Make sure there is a valid location chosen first
        if os.path.exists(project.location):
            path = bpy.path.abspath(project.location)
            
            # For single-file addons
            if os.path.isfile(path):
                file = os.path.basename(path)
                if file.endswith('.py') and file not in project.project_files:
                    project.project_files.append(file)
                    print(file)

                # Remove the other file/s
                for p in project.project_files:
                    if p != file:
                        project.project_files.remove(p)
            
            # Multi-file addons
            else:
                # Make sure all files are in the project list
                for file in os.listdir(path):
                    if file.endswith('.py'):
                        if os.path.isfile(path + file) and file not in project.project_files:
                            project.project_files.append(file)
                        
                # Remove unneeded files from the project
                for p in project.project_files:
                    if p not in os.listdir(path):
                        project.project_files.remove(p)
                        
def close_files(context, all):    
    sce = context.scene
    item = sce.project_list[sce.project_list_index]
    
    for area in bpy.context.screen.areas:
        if area.type == 'TEXT_EDITOR':
            if all:
                for file in bpy.data.texts:
                    # Make the file the active file in the text editor
                    area.spaces[0].text = file
                    
                    bpy.ops.text.unlink()
            else:
                for file in bpy.data.texts:
                    if file.name in item.project_files:
                        # Make the file the active file in the text editor
                        area.spaces[0].text = file
                        
                        bpy.ops.text.unlink()
            break
                        
#######################################################################################
# UI
#######################################################################################            

class AddonDevelopmentProjectPanel(Panel):
    """ Creates a panel in the text editor """
    bl_label = "Addon Development Tool"
    bl_idname = "TEXT_PT_addon_dev"
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    
    def draw(self, context):
        project_list = context.scene.project_list
        list_index = context.scene.project_list_index
        
        layout = self.layout
        
        row = layout.row()
        row.template_list("AddonProjectUIList", "", context.scene, "project_list", context.scene, "project_list_index", rows=5)
        
        
        row = layout.row(align=True)
        row.operator('addon_dev_tool.new_addon')
        #row.operator('addon_dev_tool.new_script')
        row.operator('addon_dev_tool.delete_project')
        
        # Only if a valid project is selected
        if list_index >= 0 and len(project_list) > 0:
            item = project_list[list_index]
            
            if not item.location == "" and os.path.exists(bpy.path.abspath(item.location)):
                layout.separator()
                
                col = layout.column(align=True)                
                row = col.row(align=True)
                row.operator('addon_dev_tool.open_files')
                row.operator('addon_dev_tool.close_files')
                
                row=col.row(align=True)
                row.operator('addon_dev_tool.new_project_file')
                row.operator('addon_dev_tool.close_all_files')
                
                row = col.row(align=True)
                row.operator('addon_dev_tool.refresh_files', icon='FILE_REFRESH')
                
                layout.separator()
                col = layout.column(align=True)
                if item.is_addon:
                    col.operator('addon_dev_tool.install_addon')
                    col.operator('addon_dev_tool.remove_addon')
                else:
                    row.operator('addon_dev_tool.run_script')
                
                # Info Box
                if os.path.isdir(item.location):
                    if "__init__.py" not in os.listdir(item.location):
                        box = layout.box()
                        box.label(text="Package Missing __init__.py file")
                
        
        
    
    def draw_header(self, context):
        """ Just for fun """
        layout = self.layout
        obj = context.object
        #layout.label(icon='FILE_TEXT')
        
        
class AddonDevelopmentProjectSettingsPanel(Panel):
    """ Settings for the currently opened project """
    bl_label = "Project Settings"
    bl_idname = "TEXT_PT_addon_dev_project_settings"
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    
    def draw(self, context):
        layout = self.layout
        
        project_list = context.scene.project_list
        list_index = context.scene.project_list_index
        
        if list_index >= 0 and len(project_list) > 0:
            item = project_list[list_index]
            
            layout.prop(item, 'name')
            
                
            if not os.path.exists(item.location):              
                layout.prop(item, 'location', icon='ERROR')
            else:
                layout.prop(item, 'location')
     
        elif len(project_list) == 0:
            layout.label(text="No Projects")

        

class Project(PropertyGroup):
    """ Holds location, name, etc of each project """
    
    name = StringProperty(name="Name", description="The name of the current project", default="untitled")
    
    location = StringProperty(name="Location", description="The location of the project on the users machine", default="", subtype='FILE_PATH')
    
    is_addon = BoolProperty(name="Addon", description="Is the project a script or an addon?", default=True)
    
    project_files = []


class AddonProjectUIList(UIList):
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        addon_icon = 'FILE_TEXT'
        script_icon = 'FILE_SCRIPT'        
        
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            
            if item.is_addon:
                layout.label(item.name, icon=addon_icon)
            else:
                layout.label(item.name, icon=script_icon)
        
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label("", icon=text_icon)


class AddAddon(Operator):
    bl_label = "New Addon"
    bl_idname = "addon_dev_tool.new_addon"
    bl_description = "Create a new blank addon"
    
    def execute(self, context):
        context.scene.project_list.add()
        context.scene.project_list_index = len(context.scene.project_list) - 1
        
        context.scene.project_list[context.scene.project_list_index].is_addon = True        
        
        return {'FINISHED'}
    
    
class AddScript(Operator):
    bl_label = "New Script"
    bl_idname = "addon_dev_tool.new_script"
    bl_description = "Create a new blank script"
    
    def execute(self, context):
        context.scene.project_list.add()
        context.scene.project_list_index = len(context.scene.project_list) - 1
        
        context.scene.project_list[context.scene.project_list_index].is_addon = False
        
        return {'FINISHED'}
    

class RemoveItem(Operator):
    bl_label = "Delete Project"
    bl_idname = "addon_dev_tool.delete_project"
    bl_description = "Delete the current project (will not remove from computer)"
    
    @classmethod
    def poll(self, context):
        """ You can only delete if there is something in the list!"""
        return len(context.scene.project_list) > 0
    
    def execute(self, context):
        list = context.scene.project_list
        index = context.scene.project_list_index
        
        list.remove(index)
        
        if index > 0:
            context.scene.project_list_index = index - 1
        
        return {'FINISHED'}
    
    
class ADTOpenFiles(Operator):
    bl_label = "Open Files"
    bl_idname = 'addon_dev_tool.open_files'
    bl_description = "Open files from current project in the text editor"
    
    @classmethod
    def poll(self, context):
        sce = context.scene
        item = sce.project_list[sce.project_list_index]
        
        update_file_list(context)
        
        unopened = False

        for file in item.project_files:
            if file not in bpy.data.texts:
                unopened = True
                
        return unopened
    
    def execute(self, context):
        project = bpy.context.scene.project_list[bpy.context.scene.project_list_index]
        path = bpy.path.abspath(project.location)
        
        # Open files in the text editor from the current project
        update_file_list(context)
        
        for file in project.project_files:
            if file not in bpy.data.texts:
                if os.path.isdir(path):
                    bpy.ops.text.open(filepath=path + file)
                elif os.path.isfile(path):
                    bpy.ops.text.open(filepath=path)

        return {'FINISHED'}
    
    
class ADTNewProjectFile(Operator, ExportHelper):
    bl_label = "New File"
    bl_idname = 'addon_dev_tool.new_project_file'
    bl_description = "Create a new file for the project and open it in the editor"
    
    filename_ext = ".py"
    
    # Set the filepath to the project location
    def invoke(self, context, event):
        location = context.scene.project_list[context.scene.project_list_index].location
        
        if self.filepath == "":
            self.filepath = location
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):        
        # Create the file
        print("Creating", self.filepath)
        f = open(self.filepath, 'w', encoding='utf-8')
        f.close()
        
        # Open the file in the text editor
        text = bpy.data.texts.load(self.filepath)

        for area in bpy.context.screen.areas:
            if area.type == 'TEXT_EDITOR':
                area.spaces[0].text = text
                break

        return {'FINISHED'}     


class ADTCloseFiles(Operator):
    bl_label = "Close Files"
    bl_idname = 'addon_dev_tool.close_files'
    bl_description = "Close files from current project in the text editor"
    
    @classmethod
    def poll(self, context):
        sce = context.scene
        item = sce.project_list[sce.project_list_index]
        
        files_open = False

        for file in bpy.data.texts:
            if file.name in item.project_files:
                files_open = True
                
        return files_open
                
    
    def execute(self, context):
        close_files(context, False)
        
        return {'FINISHED'}
    
class ADTCloseAllFiles(Operator):
    bl_label = "Close All Files"
    bl_idname = 'addon_dev_tool.close_all_files'
    bl_description = "Close all files in the text editor"
    
    @classmethod
    def poll(self, context):
        return len(bpy.data.texts) > 0
    
    def execute(self, context):
        close_files(context, True)
        
        return {'FINISHED'}
    
    
class ADTRefreshFiles(Operator):
    bl_label = "Refresh Files"
    bl_idname = 'addon_dev_tool.refresh_files'
    bl_description = "Refresh all open project files in the text editor"
    
    @classmethod
    def poll(self, context):
        return True
    
    def execute(self, context):
        sce = context.scene
        item = sce.project_list[sce.project_list_index]
        
        # Find all modified files from the project and update them
        for area in bpy.context.screen.areas:
            if area.type == 'TEXT_EDITOR':
                for file in bpy.data.texts:
                    if file.name in item.project_files:
                        # Make the file the active file in the text editor
                        area.spaces[0].text = file
                        
                        if file.is_modified:
                            bpy.ops.text.reload()
        
        return {'FINISHED'}
    
    
class ADTInstallAddon(Operator):
    bl_label = "Install Addon"
    bl_idname = 'addon_dev_tool.install_addon'
    bl_description = "Install the addon"
    
    def execute(self, context):
        project = context.scene.project_list[context.scene.project_list_index]
        path = project.location
        temp = bpy.utils.script_path_user()

        # If it is a multi-file addon get the folder
        if os.path.isdir(path):
            if path.endswith(os.sep):               
                addon_name = os.path.basename(path.rstrip(os.sep))         

                zip = zipfile.ZipFile(temp + os.sep + addon_name + ".zip", 'w')
                
                for file in project.project_files:
                    zip.write(path + file, addon_name + os.sep + file)
                    
                zip.close()
                
                bpy.ops.wm.addon_install(overwrite=True, filepath=temp + os.sep + addon_name + ".zip")
                
                bpy.ops.wm.addon_enable(module=addon_name)
                print("NAME", addon_name)
                
                #remove the temporary zip file
                os.remove(temp + os.sep + addon_name + ".zip")
                
        # Otherwise, get the name of the file
        elif os.path.isfile(path):
            addon_name = os.path.basename(path)
            
            bpy.ops.wm.addon_install(overwrite=True, filepath=path)
            bpy.ops.wm.addon_enable(module=os.path.splitext(addon_name)[0])       

        return {'FINISHED'}
    
    
class ADTRemoveAddon(Operator):
    bl_label = "Uninstall Addon"
    bl_idname = 'addon_dev_tool.remove_addon'
    bl_description = "Remove the addon"
    
    @classmethod
    def poll(self, context):
        project = context.scene.project_list[context.scene.project_list_index]
        path = project.location
        if os.path.isdir(path):
            addon_name = os.path.basename(path.rstrip(os.sep))
        elif os.path.isfile(path):
            addon_name = os.path.basename(path)
        
        return addon_name in bpy.context.user_preferences.addons.keys()
    
    def execute(self, context):
        project = context.scene.project_list[context.scene.project_list_index]
        path = project.location
        addon_name = os.path.basename(path.rstrip(os.sep))
        
        bpy.ops.wm.addon_remove(module=addon_name)
        
        return {'FINISHED'}

def register():
    bpy.utils.register_module(__name__)
    
    bpy.types.Scene.project_list = CollectionProperty(type=Project)
    bpy.types.Scene.project_list_index = IntProperty(name="Index for project_list", default=0)
    
    bpy.app.handlers.load_post.append(get_projects)
    bpy.app.handlers.save_post.append(save_projects)
    
def unregister():
    bpy.utils.unregister_module(__name__)
    
    del bpy.types.Scene.project_list
    del bpy.types.Scene.project_list_index
    
    bpy.app.handlers.load_post.remove(get_projects)
    bpy.app.handlers.save_post.remove(save_projects)