# Addon Development Tool
*A Blender addon to aid in the development of addons by providing quick access to repetitive operations*

### [Download the addon](https://raw.githubusercontent.com/natecraddock/AddonDevelopmentTool/master/AddonDevTool.py)
![Example GIF](https://raw.githubusercontent.com/natecraddock/AddonDevelopmentTool/master/resources/ADTv1.0.gif)

## Use
The Addon Development Tool is located on the toolshelf in the text editor. 

I prefer to use the scripting layout of Blender's UI when using the ADT, but thats just personal preference.

Operators:
- New Addon: Creates a new addon. You need to specify the name and location before working on it.
- Delete Project: Deletes the addon from the JSON file. Will not be deleted from the disk.
- Open Files: Opens all the files from the current project in Blender's text editor
- Close Files: Closes all of the files from the current project.
- New File: Adds a new file to the project
- Close All Files: Closes every text file
- Refresh Files: Refreshes files from outside changes
- Install Addon: If the addon is valid, install it.
- Uninstall Addon: If the addon is installed, uninstall it.
