# bpy.ucx_tool
Unreal Engine Custom Collision Tool (UCX)

Automatically creates profile collision for UE FBX Import

# PLEASE ⭐STAR⭐ THE REPO IF YOU LIKE IT! THANKS!

## Installations:
1. Navigate to top left `Menus > Edit > Preferrences > Add-ons`
2. Click the button at the top right (down icon)
3. Click `Install from disk...`
4. Locate the zip 
5. Enjoy

## How to use it
### Check the official docs regarding UCX [visit](https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-static-mesh-pipeline?application_version=4.27)

Object mode
![image](https://github.com/user-attachments/assets/67eb663c-f566-4e32-82cb-062810bc542f)

### Select or Create Collection for Collision profiles
- This is required

### Creating Collisions base on Selected Object
- if your mesh/object is a simple box or low poly without holes or complex geometry you can use this feature

### Creating from Existing Vertex groups
- if you have existing vertex groups

### Choose only vertex groups with prefix `UCX_`

### Clean Object names
- This clears or remove .000 suffix of collision profiles the names should be 1UCX_meshname_001
- so if you have multiple collision profiles for meshname it needs to be 1UCX_meshname_001 1UCX_meshname_011 and so on


