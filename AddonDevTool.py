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

import os
import shutil
import zipfile
import xml.etree.ElementTree as ET

#######################################################################################
# FUNCTIONS
#######################################################################################

def xml_new_project(root, p):
    # Take the input project and then create the tree   
    list = root
    
    project = ET.SubElement(list, 'project', name=p.name)
    
    loc = ET.SubElement(project, 'location').text = p.location
    
    if p.is_addon:
        addon = ET.SubElement(project, 'is_addon').text = "True"
    else:
        addon = ET.SubElement(project, 'is_addon').text = "False"
    
    files = ET.SubElement(project, 'project_files')
    
    for file in p.project_files:
        ET.SubElement(files, 'file').text = file
    
    return list
    
def update_xml(context):
    # Make sure there is a ADTProjects.xml file
    # If not then create one
    # Then update the tree to include all current projects
    #update the current projects to include all from the tree
    # Makes sure that no matter what the addon will have all the projects you have made
    
    NAME = "ADTProjects.xml"
    
    scripts_path = bpy.utils.script_path_user()
    projects_file = scripts_path + os.sep + NAME
    projects = context.scene.project_list
    
    
    if NAME in os.listdir(scripts_path):
        # Compare both lists

        pass
        
    else:
        # Create ADTProjects.xml
        # Add all current projects to the tree
        
        # Write the projects to the tree
        root = ET.Element('project_list')

        for project in projects:
            # We don't like unfinished projects definitions here :)
            if not project.location == "":
                root = xml_new_project(root, project)

        tree = ET.ElementTree(root)
        tree.write(projects_file)
        
        
def update_file_list(context):
    if len(context.scene.project_list) > 0:
        project = context.scene.project_list[context.scene.project_list_index]
        path = bpy.path.abspath(project.location)
        
        # Make sure there is a location chosen first
        if project.location != "":
            if os.path.isfile(path):
                file = os.path.basename(path)
                if file.endswith('.py') and file not in project.project_files:
                    project.project_files.append(file)

                for p in project.project_files:
                    if p != file:
                        project.project_files.remove(item)
            else:
                # Make sure all files are in the project list
                for file in os.listdir(path):
                    if file.endswith('.py') or file.endswith('.txt') or file.endswith('.xml'):
                        if os.path.isfile(path + file) and file not in project.project_files:
                            project.project_files.append(file)
                        
                # Remove unneeded files from the project
                for item in project.project_files:
                    if item not in os.listdir(path):
                        project.project_files.remove(item)
                        
def close_files(context, all):    
    sce = context.scene
    item = sce.project_list[sce.project_list_index]
    
    for area in bpy.context.screen.areas:
        if area.type == 'TEXT_EDITOR':
            if all:
                if file.name in item.project_files:
                    # Make the file the active file in the text editor
                    area.spaces[0].text = file
                    
                    bpy.ops.text.unlink()
            else:
                for file in bpy.data.texts:
                    if file.name in item.project_files:
                        # Make the file the active file in the text editor
                        area.spaces[0].text = file
                        
                        bpy.ops.text.unlink()
                        
#######################################################################################
# UI
#######################################################################################

class AddonDevelopmentPreferences(AddonPreferences):
    """ Holds the project path for the addon """
    bl_idname = __name__
    
    projects_path = StringProperty(
        name = "Default Project Folder",
        description = "Define the default project folder",
        default = "",
        subtype = 'DIR_PATH'
    )
    
    def draw(self, context):
        layout = self.layout
        #layout.label(text = "Define the default project folder for addons")
        layout.prop(self, 'projects_path')
            

class AddonDevelopmentProjectPanel(Panel):
    """ Creates a panel in the text editor """
    bl_label = "Addon Development Tool"
    bl_idname = "TEXT_PT_addon_dev"
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    
    def draw(self, context):
        project_list = context.scene.project_list
        list_index = context.scene.project_list_index
        
        # Make sure the files and xml are always updated
        update_file_list(context)
        update_xml(context)
        
        layout = self.layout
        
        addon_preferences = context.user_preferences.addons[__name__].preferences
        
        projects_path = bpy.path.abspath(addon_preferences.projects_path)
        
        row = layout.row()
        row.template_list("AddonProjectUIList", "", context.scene, "project_list", context.scene, "project_list_index", rows=5)
        
        
        row = layout.row()
        row.operator('addon_dev_tool.new_addon')
        row.operator('addon_dev_tool.new_script')
        row.operator('addon_dev_tool.delete_project')
        
        layout.separator()
        
        if list_index >= 0 and len(project_list) > 0:
            item = project_list[list_index]
            
            if not item.location == "" and os.path.exists(bpy.path.abspath(item.location)):
                
                split = layout.split()
                col = split.column()
                col.operator('addon_dev_tool.open_files')
                col = split.column()
                col.operator('addon_dev_tool.close_files')
                col.operator('addon_dev_tool.close_all_files')
                
                layout.separator()
                
                row = layout.row()
                if item.is_addon:
                    row.operator('addon_dev_tool.install_addon')
                    row = layout.row()
                    row.operator('addon_dev_tool.remove_addon')
                else:
                    row.operator('addon_dev_tool.run_script')
        
        
    
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
        file_types = ['.py', '.txt', '.xml']
        
        project_list = context.scene.project_list
        list_index = context.scene.project_list_index
        
        if list_index >= 0 and len(project_list) > 0:
            item = project_list[list_index]
            
            layout.prop(item, 'name')
            layout.prop(item, 'location')
                
            if not item.location == "":                
                path = bpy.path.abspath(item.location)
                
                if os.path.exists(path):
                
                    #Display files
                    for file in item.project_files:
                        layout.label(text=file)
                    
                else:
                    layout.label(text="Invalid Path")
            else:
                layout.label(text="Choose a location")
     
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
    
    def execute(self, context):
        project = bpy.context.scene.project_list[bpy.context.scene.project_list_index]
        path = bpy.path.abspath(project.location)
        
        # Open files in the text editor from the current project
        update_file_list(context)
        
        for file in project.project_files:
            if file not in bpy.data.texts:
                bpy.ops.text.open(filepath=path + file)

        return {'FINISHED'}     


class ADTCloseFiles(Operator):
    bl_label = "Close Files"
    bl_idname = 'addon_dev_tool.close_files'
    bl_description = "Close files from current project in the text editor"
    
    def execute(self, context):
        close_files(context, False)
        
        return {'FINISHED'}
    
class ADTCloseAllFiles(Operator):
    bl_label = "Close All Files"
    bl_idname = 'addon_dev_tool.close_all_files'
    bl_description = "Close all files in the text editor"
    
    def execute(self, context):
        close_files(context, True)
        
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
                
                #bpy.ops.wm.addon_enable(module=addon_name)
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
        addon_name = os.path.splitext(os.path.basename(path))[0]
        
        return addon_name in bpy.context.user_preferences.addons.keys()
    
    def execute(self, context):
        project = context.scene.project_list[context.scene.project_list_index]
        path = project.location
        addon_name = os.path.splitext(os.path.basename(path))[0]
        
        bpy.ops.wm.addon_remove(module=addon_name)
        
        return {'FINISHED'}

def register():
    bpy.utils.register_class(AddonDevelopmentProjectPanel)
    bpy.utils.register_class(AddonDevelopmentPreferences)
    bpy.utils.register_class(AddonProjectUIList)
    bpy.utils.register_class(Project)
    bpy.utils.register_class(AddAddon)
    bpy.utils.register_class(ImportAddon)
    bpy.utils.register_class(AddScript)
    bpy.utils.register_class(ImportScript)
    bpy.utils.register_class(RemoveItem)
    bpy.utils.register_class(AddonDevelopmentProjectSettingsPanel)
    bpy.utils.register_class(ADTOpenFiles)
    bpy.utils.register_class(ADTCloseFiles)
    bpy.utils.register_class(ADTCloseAllFiles)
    bpy.utils.register_class(ADTInstallAddon)
    bpy.utils.register_class(ADTRemoveAddon)
    
    bpy.types.Scene.project_list = CollectionProperty(type=Project)
    bpy.types.Scene.project_list_index = IntProperty(name="Index for project_list", default=0)
    
    
def unregister():
    bpy.utils.unregister_class(AddonDevelopmentProjectPanel)
    bpy.utils.unregister_class(AddonDevelopmentPreferences)
    bpy.utils.unregister_class(AddonProjectUIList)
    bpy.utils.unregister_class(Project)
    bpy.utils.unregister_class(AddAddon)
    bpy.utils.unregister_class(ImportAddon)
    bpy.utils.unregister_class(AddScript)
    bpy.utils.unregister_class(ImportScript)
    bpy.utils.unregister_class(RemoveItem)
    bpy.utils.unregister_class(AddonDevelopmentProjectSettingsPanel)
    bpy.utils.unregister_class(ADTOpenFiles)
    bpy.utils.unregister_class(ADTCloseFiles)
    bpy.utils.unregister_class(ADTCloseAllFiles)
    bpy.utils.unregister_class(ADTInstallAddon)
    bpy.utils.unregister_class(ADTRemoveAddon)
    
    del bpy.types.Scene.project_list
    del bpy.types.Scene.project_list_index