# Unreal Engine Custom Collision Blender Addon Tool (UCX)

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

## Object mode

![image](https://github.com/user-attachments/assets/67eb663c-f566-4e32-82cb-062810bc542f)

### Select or Create Collection for Collision profiles
- This is required

### Creating Collisions base on Selected Object
- if your mesh/object is a simple box or low poly without holes or complex geometry you can use this feature

### Creating from Existing Vertex groups
- if you have existing vertex groups

### Choose only vertex groups with prefix `UCX_`

### Clean Object names
- This clears or remove `.000` suffix of collision profiles the names should be `UCX_meshname_00`
- so if you have multiple collision profiles for meshname it needs to be `UCX_meshname_001` `UCX_meshname_01` and so on

## Edit mode

![image](https://github.com/user-attachments/assets/d4af691b-27b9-44b3-8dd8-2213fe70b26c)

### Creating from Selected Vertices
- Must select atleast 3 Vertex

### Add Selected Vertices to Vertex Group
- This will create a Vertex Group rename for later use

![image](https://github.com/user-attachments/assets/1611b12c-7572-4d09-bdfc-d8f66c207699)

### Fetch Vertex Groups
- Check `Choose only group with prefix UCX_` or fetch all
- It only fetches valid groups with more than 3 vertices selected

![image](https://github.com/user-attachments/assets/ee63f09f-4f0f-47e2-9a48-2aa33fbc676b)

### Finally Create from VG List
- You can remove VG from the current list using the X button
- Automatically creates all collision profiles base on vertex groups




