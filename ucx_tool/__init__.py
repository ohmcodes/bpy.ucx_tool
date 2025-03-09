# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy
import bmesh
import re
from mathutils import Vector
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, EnumProperty, BoolProperty, IntProperty, CollectionProperty, PointerProperty
from bpy.app.handlers import persistent

bl_info = {
    "name": "Unreal Engine Custom Collision Tool (UCX)",
    "description": "Automatically creates profile collision UCX for UE FBX Import",
    "author": "ohmcodes",
    "version": (2, 0, 1),
    "blender": (4, 3, 2),
    "location": "View3D > Right panel",
    "category": "UCX",
}

@persistent
def on_selection_changed(scene):
    current_active = bpy.context.active_object
    last_active = scene.last_active_object

    if current_active != last_active:
        fetch_vg(scene)
        scene.last_active_object = current_active

@persistent
def on_checkbox_changed(scene):
    current_checkbox_value = scene.ucx_chkbox.ucx_chkbox
    last_checkbox_value = scene.last_checkbox_value

    if current_checkbox_value != last_checkbox_value:
        fetch_vg(scene)
        scene.last_checkbox_value = current_checkbox_value
        
# Utility Functions
def get_vertex_count(obj, vg):
    """Count vertices in a vertex group."""
    return sum(1 for v in obj.data.vertices if vg.index in [g.group for g in v.groups])

def check_selected_vertices(obj):
    """Check if more than two vertices are selected."""
    bm = bmesh.from_edit_mesh(obj.data)
    return len([v for v in bm.verts if v.select]) > 2

def create_new_name(collection, obj_name):
    """Generate a unique name for the new collision object."""
    base_name_pattern = fr"UCX_{obj_name}_(\d{{2}})"
    existing_numbers = [int(re.match(base_name_pattern, o.name).group(1)) 
                        for o in collection.objects if re.match(base_name_pattern, o.name)]
    next_number = f"{max(existing_numbers) + 1:02d}" if existing_numbers else "00"

    return f"UCX_{obj_name}_{next_number}"

def clean_naming(collection):
    """Remove .000 suffix from object naming in the collection."""
    error = 0
    for obj in collection.objects:
        orig_name = obj.name
        if re.search(r'\.\d{3}$', obj.name):
            obj.name = re.sub(r'\.\d{3}$', '', obj.name)

            if orig_name == obj.name:
                error+=1

    return error

def add_to_vertex_groups(obj):
    obj = bpy.context.active_object
    mode = obj.mode

    if not obj.vertex_groups:
        group_name = f"UCX_{obj.name}_VG_00"
    else:
        existing_groups = [vg.name for vg in obj.vertex_groups if vg.name.startswith(f"UCX_{obj.name}_VG_")]
        if existing_groups:
            valid_numbers = []
            for name in existing_groups:
                try:
                    num = int(name.split('_')[-1])
                    valid_numbers.append(num)
                except ValueError:
                    continue
            if valid_numbers:
                last_num = max(valid_numbers)
                group_name = f"UCX_{obj.name}_VG_{last_num + 1:02d}"
            else:
                group_name = f"UCX_{obj.name}_VG_00"
        else:
            group_name = f"UCX_{obj.name}_VG_00"
    
    # Create a new vertex group
    group = obj.vertex_groups.new(name=group_name)
    bpy.ops.object.vertex_group_assign()
    # bpy.ops.object.mode_set(mode='OBJECT')
    # selected_verts = [v for v in obj.data.vertices if v.select]
    # for v in selected_verts:
    #     group.add([v.index], 1.0, 'ADD')

    # bpy.ops.object.mode_set(mode=mode)

    return group_name

def fetch_vg(scene):
    obj = bpy.context.active_object

    # Check if an object is selected
    if not obj:
        #print("No object selected.")
        return

    # Check if the object is hidden in the viewport or outliner
    if obj.hide_get() or obj.hide_viewport:
        #print(f"Object '{obj.name}' is hidden.")
        return
    
    # Check if the object is a mesh
    if obj.type != 'MESH':
        #print(f"Object '{obj.name}' is not a mesh.")
        return

    if not obj.vertex_groups:
        #print("Object has no groups")
        return

    if scene.vertex_group_items:
        scene.vertex_group_items.clear()
    
    for vg in obj.vertex_groups:
        vertex_count = get_vertex_count(obj, vg)

        if vertex_count <= 2:
            continue

        if scene.ucx_chkbox.ucx_chkbox and "UCX_" not in vg.name:
            continue
        
        item = scene.vertex_group_items.add()
        item.vertex_group_name = vg.name

def vg_validations(context):
    valid = True

    active_object = context.scene.last_active_object

    if not active_object:
        #print("active_object is not valid")
        return False
    
    if active_object.type != 'MESH':
        #print("object is not a mesh")
        return False

    if active_object.hide_get():
        #print("object is hidden")
        return False

    if len(active_object.vertex_groups) == 0:
        #print("object is has no vg")
        return False

    if context.scene.ucx_chkbox.ucx_chkbox and [vg for vg in active_object.vertex_groups if "UCX_" not in vg.name]:
        #print("object select UCX only and object has no UCX vg")
        return False

    return valid

def clean_up_object_data(obj):
    """Remove unnecessary data from the object."""
    if obj.type != 'MESH':
        return
    
    mesh = obj.data
    
    # Clear materials
    mesh.materials.clear()
    
    # Clear vertex groups
    if obj.vertex_groups:
        obj.vertex_groups.clear()
    
    # Clear shape keys
    if mesh.shape_keys:
        mesh.shape_keys.key_blocks.clear()
    
    # Clear UV maps
    if mesh.uv_layers:
        for uv_layer in mesh.uv_layers:
            mesh.uv_layers.remove(uv_layer)
    
    # Clear custom normals
    #mesh.use_auto_smooth = False
    #mesh.normals_split_custom_set([])
    
    # Clear vertex colors
    if mesh.vertex_colors:
        for vcol in mesh.vertex_colors:
            mesh.vertex_colors.remove(vcol)
    
    # Clear geometry data (optional)
    #mesh.clear_geometry()
    
    print(f"Cleaned up data for object: {obj.name}")

def get_bounding_box_corners(obj, use_local_coords=True):
    """Get the bounding box corners of an object in world coordinates."""
    if not use_local_coords:
        return [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    else:
        return [Vector(corner) for corner in obj.bound_box]

def get_merged_bounding_box(selected_objects, isLocal=True):
    # Collect all bounding box corners from selected objects
    bbox_corners = []
    for obj in selected_objects:
        if obj.type != 'MESH':
            print(f"Skipping non-mesh object: {obj.name}")
            continue
        bbox_corners.extend(get_bounding_box_corners(obj, isLocal))

    if not bbox_corners:
        print("No valid mesh objects selected.")
    
    return bbox_corners
           
# Collision Creation Functions
def create_collision_box(collection, obj, context):
    """Create a collision box from the entire object."""
    if obj.type != 'MESH':
        raise Exception("Selected object is not a mesh!")
    
    # Duplicate the object
    new_obj = obj.copy()
    new_obj.data = obj.data.copy()
    new_obj.name = f"UCX_{obj.name}_00"
    collection.objects.link(new_obj)
    
    # Create a convex hull
    bm = bmesh.new()
    bm.from_mesh(new_obj.data)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    bm.to_mesh(new_obj.data)
    bm.free()
    
    # Apply transform
    new_obj.select_set(True)
    bpy.context.view_layer.objects.active = new_obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    
    new_obj.location = obj.location
    new_obj.rotation_euler = obj.rotation_euler
    new_obj.scale = obj.scale

    if context.scene.ucx_chkbox_autohide.ucx_chkbox_autohide:
        new_obj.hide_set(True)

    # Clean up unnecessary data
    clean_up_object_data(new_obj)

    print(f"Created collision box: {new_obj.name}")

def create_bounding_box_cube(collection, obj, context):
    """Create a convex hull using the bounding box of the selected object."""
    if obj.type != 'MESH':
        raise Exception("Selected object is not a mesh!")

    if context.scene.ucx_chkbox_merge.ucx_chkbox_merge:
        selected_objects = bpy.context.selected_objects
        bbox_corners = get_merged_bounding_box(selected_objects, False)

        # Calculate the middle point (centroid) of the merged bounding box
        middle_point = Vector()
        for corner in bbox_corners:
            middle_point += corner
        middle_point /= len(bbox_corners)
    else:
        bbox_corners = get_bounding_box_corners(obj)

    # Create a new mesh and object for the convex hull
    new_mesh = bpy.data.meshes.new(create_new_name(collection, obj.name))
    new_obj = bpy.data.objects.new(new_mesh.name, new_mesh)
    collection.objects.link(new_obj)
    
    # Create a bmesh and add the bounding box corners as vertices
    bm = bmesh.new()
    for corner in bbox_corners:
        bm.verts.new(corner)
    
    # Create the convex hull from the bounding box vertices
    bmesh.ops.convex_hull(bm, input=bm.verts, use_existing_faces=False)
    
    # Write the bmesh data to the mesh
    bm.to_mesh(new_mesh)
    bm.free()
    
    if context.scene.ucx_chkbox_merge.ucx_chkbox_merge:
        # Set the origin to the center of the volume
        bpy.context.view_layer.objects.active = new_obj
        new_obj.select_set(True)
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

        new_obj.location = middle_point
    else:
        # Match the location, rotation, and scale of the original object
        new_obj.location = obj.location

        # Ensure the convex hull object's origin matches the original object's origin
        new_obj.matrix_world = obj.matrix_world
    
    new_obj.rotation_euler = obj.rotation_euler
    new_obj.scale = obj.scale

    if context.scene.ucx_chkbox_autohide.ucx_chkbox_autohide:
        new_obj.hide_set(True)

    # Clean up unnecessary data
    clean_up_object_data(new_obj)

    print(f"Created convex hull from bounds: {new_obj.name}")

def create_collision_from_vertex_groups(collection, context, isFromList = False):
    """Create collision meshes from vertex groups."""

    obj = context.active_object

    for vg in obj.vertex_groups:
        if get_vertex_count(obj, vg) <= 2:
            continue

        if context.scene.ucx_chkbox.ucx_chkbox and "UCX_" not in vg.name:
            continue

        if isFromList and len([vgl for vgl in context.scene.vertex_group_items if vgl.vertex_group_name == vg.name]) == 0:
            continue
        
        # Create a new mesh from the vertex group
        new_mesh = bpy.data.meshes.new(create_new_name(collection, obj.name))
        new_obj = bpy.data.objects.new(new_mesh.name, new_mesh)
        collection.objects.link(new_obj)
        
        # Select vertices in the vertex group
        bm = bmesh.new()
        #bm.from_mesh(obj.data)

        selected_verts = [v for v in obj.data.vertices if vg.index in [g.group for g in v.groups]]
        
        # Create a convex hull
        for v in selected_verts:
            bm.verts.new(v.co)
            
        # Create faces from the selected vertices
        #bmesh.ops.contextual_create(bm, geom=bm.verts)    
        bmesh.ops.convex_hull(bm, input=bm.verts, use_existing_faces=False)

        bm.to_mesh(new_mesh)
        bm.free()

        new_obj.location = obj.location
        new_obj.rotation_euler = obj.rotation_euler
        new_obj.scale = obj.scale
        
        if context.scene.ucx_chkbox_autohide.ucx_chkbox_autohide:
            new_obj.hide_set(True)

        # Clean up unnecessary data
        clean_up_object_data(new_obj)

        print(f"Created collision box: {new_obj.name}")

def create_collision_from_selected_vertices(collection, obj, context):
    """Create a collision mesh from selected vertices."""
    bm = bmesh.from_edit_mesh(obj.data)
    selected_verts = [v for v in bm.verts if v.select]
    
    if not selected_verts:
        raise Exception("No vertices selected!")
    
    # Create a new mesh
    new_mesh = bpy.data.meshes.new(create_new_name(collection, obj.name))
    new_obj = bpy.data.objects.new(new_mesh.name, new_mesh)
    collection.objects.link(new_obj)
    
    # Create a convex hull
    bm_new = bmesh.new()
    for v in selected_verts:
        bm_new.verts.new(v.co)
    bmesh.ops.convex_hull(bm_new, input=bm_new.verts, use_existing_faces=False)
    bm_new.to_mesh(new_mesh)
    bm_new.free()

    new_obj.location = obj.location
    new_obj.rotation_euler = obj.rotation_euler
    new_obj.scale = obj.scale
    
    if context.scene.ucx_chkbox_autohide.ucx_chkbox_autohide:
        new_obj.hide_set(True)

    # Clean up unnecessary data
    clean_up_object_data(new_obj)
    
    print(f"Created collision box: {new_obj.name}")

# Operators
class UCX_OT_CreateCollection(Operator):
    bl_label = ""
    bl_idname = "object.create_collection"
    bl_description = "Quick shortcut to create collection"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        new_collection = bpy.data.collections.new("UCX_Collision_Profiles")
        bpy.context.scene.collection.children.link(new_collection)
        context.scene.ucx_collection = new_collection.name
        return {'FINISHED'}

class UCX_OT_CreateFromObject(Operator):
    bl_label = "From Selected Objects"
    bl_idname = "object.create_from_object"
    bl_description = "Create collisions from selected objects"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH' and context.selected_objects
    
    def execute(self, context):
        collection = bpy.data.collections.get(context.scene.ucx_collection)
        if not collection:
            self.report({'ERROR'}, "No collection selected!")
            return {'CANCELLED'}
        
        for s_obj in context.selected_objects:
            if context.scene.ucx_chkbox_bounding.ucx_chkbox_bounding:
                create_bounding_box_cube(collection, s_obj, context)
            else:
                create_collision_box(collection, s_obj, context) 
            
            if context.scene.ucx_chkbox_merge.ucx_chkbox_merge:
                break

        return {'FINISHED'}

class UCX_OT_CreateFromSelectedVertices(Operator):
    bl_label = "From Selected Vertices"
    bl_idname = "object.create_from_selectedvert"
    bl_description = "Create collisions from selected vertices. required 3 vertex"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH' and context.mode == 'EDIT_MESH' and check_selected_vertices(context.active_object)
    
    def execute(self, context):
        collection = bpy.data.collections.get(context.scene.ucx_collection)
        if not collection:
            self.report({'ERROR'}, "No collection selected!")
            return {'CANCELLED'}
        
        create_collision_from_selected_vertices(collection, context.active_object, context)
        return {'FINISHED'}

class UCX_OT_CreateFromVGroups(Operator):
    bl_label = "From Existing VGroups"
    bl_idname = "object.create_from_vgroups"
    bl_description = "Create collisions from existing Vertex groups can be filtered by checking the box"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        return vg_validations(context)

    def execute(self, context):
        collection = bpy.data.collections.get(context.scene.ucx_collection)
        if not collection:
            self.report({'ERROR'}, "No collection selected!")
            return {'CANCELLED'}
        
        create_collision_from_vertex_groups(collection, context)
        return {'FINISHED'}

class UCX_OT_CreateFromVGList(bpy.types.Operator):
    bl_label = "From Custom VG List"
    bl_idname = "object.create_from_vglist"
    bl_description = "Still Fetch all existing VG but has ability to remove unwanted group"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH' and len(context.scene.vertex_group_items) > 0 and context.selected_objects

    def execute(self, context):
        collection_name = context.scene.ucx_collection
        collection = bpy.data.collections.get(collection_name)
        
        if not collection:
            self.report({'ERROR'}, "No collection selected!")
            return {'CANCELLED'}
        
        if not context.selected_objects:
            self.report({'ERROR'}, "No object selected!")
            return {'CANCELLED'}

        create_collision_from_vertex_groups(collection, context, True)
        
        context.area.tag_redraw()
        return {'FINISHED'}

class UCX_OT_CleanNaming(bpy.types.Operator):
    bl_idname = "object.clean_naming"
    bl_label = "Clean Object naming"
    bl_description = "Removes .000 suffix"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return len(context.collection.objects) > 0 and [c for c in context.collection.objects if "." in c.name]
    
    def execute(self, context):
        collection_name = context.scene.ucx_collection
        collection = bpy.data.collections.get(collection_name)

        if clean_naming(collection) > 0:
            self.report({'WARNING'}, "Renaming Failed. Some of the objects is existed!")

        return {'FINISHED'}

class UCX_OT_RemoveVGEntry(bpy.types.Operator):
    bl_idname = "object.remove_vg_entry"
    bl_label = "Remove Vertex Group Entry"
    bl_options = {"REGISTER", "UNDO"}

    index: bpy.props.IntProperty()

    def execute(self, context):
        context.scene.vertex_group_items.remove(self.index)
        return {'FINISHED'}

class UCX_OT_AddToVertexGroup(bpy.types.Operator):
    bl_label = "Add selected Vertex to VG"
    bl_idname = "object.add_to_vg"
    bl_description = "Add selected vertices to vertex groups with prefix UCX_"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH' and context.mode == 'EDIT_MESH' and check_selected_vertices(context.active_object)
    
    def execute(self, context):
        collection = bpy.data.collections.get(context.scene.ucx_collection)
        if not collection:
            self.report({'ERROR'}, "No collection selected!")
            return {'CANCELLED'}
        
        obj = context.active_object
        
        bm = bmesh.from_edit_mesh(obj.data)
        selected_vertices = [v for v in bm.verts if v.select]
        if len(selected_vertices) >= 3:
            group_name = add_to_vertex_groups(obj)
            self.report({'INFO'}, f"Created vertex group: {group_name}")
            # save the file to reflect assignment
            #bpy.ops.wm.save_mainfile()

        context.area.tag_redraw()
        
        return {'FINISHED'}

class UCX_OT_FetchVG(bpy.types.Operator):
    bl_idname = "object.fetch_vertex_groups"
    bl_label = ""
    bl_description = "Refresh Custom VG list"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        vg_validations(context)
    
    def execute(self, context):
        obj = context.active_object
        
        context.scene.vertex_group_items.clear()
        
        for vg in obj.vertex_groups:
            if get_vertex_count(obj, vg) <= 2:
                continue

            if context.scene.ucx_chkbox.ucx_chkbox and "UCX_" not in vg.name:
                continue
            
            item = context.scene.vertex_group_items.add()
            item.vertex_group_name = vg.name
            
        return {'FINISHED'}
    
class UCX_UL_VGField(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text=item.name)

class UCX_UL_UCXCheckbox(bpy.types.PropertyGroup):
    ucx_chkbox : bpy.props.BoolProperty(
        name="UCX Only",
        description="Choose only UCX Vertex Group names",
        default = True
    )

class UCX_UL_UCXCheckboxBounding(bpy.types.PropertyGroup):
    ucx_chkbox_bounding : bpy.props.BoolProperty(
        name="Bounding Box",
        description="Create Collision from selected object bounding box",
        default = False
    )

class UCX_UL_UCXCheckboxMerge(bpy.types.PropertyGroup):
    ucx_chkbox_merge : bpy.props.BoolProperty(
        name="Merged Bounding Box",
        description="Create Collision from all selected object bounding box",
        default = False
    )

class UCX_UL_UCXCheckboxAutohide(bpy.types.PropertyGroup):
    ucx_chkbox_autohide : bpy.props.BoolProperty(
        name="Auto hide created box",
        description="Auto hide created collision box",
        default = True
    )

class UCX_PG_VertexGroupItems(bpy.types.PropertyGroup):
    vertex_group_name: bpy.props.StringProperty(name="Vertex Group Name")

# UI Panel
class UCX_PT_Panel(Panel):
    bl_label = "Unreal Engine Custom Collision Tool (UCX)"
    bl_idname = "UCX_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "UCX"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        collection_col = layout.row()
        collection_col.prop_search(scene, "ucx_collection", bpy.data, "collections", text="")

        collection_col.operator("object.create_collection", icon='ADD')
        
        layout.label(text="Generate Collisions:")

        layout.separator()
        
        bounding_row = layout.row()
        bounding_row.prop(scene.ucx_chkbox_bounding, "ucx_chkbox_bounding", text="Bounding Box")
        bounding_row.prop(scene.ucx_chkbox_merge, "ucx_chkbox_merge", text="Merge")

        layout.operator("object.create_from_object")

        layout.separator()

        layout.operator("object.create_from_selectedvert")

        layout.operator("object.create_from_vgroups")
        layout.operator("object.create_from_vglist")

        layout.separator()

        layout.prop(scene.ucx_chkbox, "ucx_chkbox", text="Choose only group with prefix UCX_")

        if vg_validations(context):
            layout.separator()

            custom_list_row = layout.row()
            custom_list_row.column().label(text="Custom VG List:")
            custom_list_row.row().operator("object.fetch_vertex_groups", icon="FILE_REFRESH")

            for i, item in enumerate(scene.vertex_group_items):
                #if context.scene.ucx_chkbox.ucx_chkbox and "UCX_" not in item.#vertex_group_name:
                #   continue

                if len(context.selected_objects) > 0 and len([vg for vg in context.selected_objects[0].vertex_groups if vg.name == item.vertex_group_name]) > 0:
                    box = layout.box()
                    row = box.row()
                    row.prop_search(item, "vertex_group_name", context.active_object, "vertex_groups", text=str(i+1))
                    row.operator("object.remove_vg_entry", text="", icon="X").index = i 

        layout.separator()

        layout.label(text="Utilities:")

        layout.operator("object.add_to_vg")

        layout.operator("object.clean_naming")

        layout.prop(scene.ucx_chkbox_autohide, "ucx_chkbox_autohide", text="Auto-hide created collisions")

# Registration
classes = (
    UCX_OT_CreateCollection,
    UCX_OT_CreateFromObject,
    UCX_OT_CreateFromVGroups,
    UCX_OT_CreateFromSelectedVertices,
    UCX_OT_CleanNaming,
    UCX_OT_AddToVertexGroup,
    UCX_OT_FetchVG,
    UCX_OT_CreateFromVGList,
    UCX_OT_RemoveVGEntry,
    UCX_UL_UCXCheckbox,
    UCX_UL_UCXCheckboxBounding,
    UCX_UL_UCXCheckboxMerge,
    UCX_UL_UCXCheckboxAutohide,
    UCX_UL_VGField,
    UCX_PG_VertexGroupItems,
    UCX_PT_Panel,
)

# # Define the main PropertyGroup
# class UCX_Properties(bpy.types.PropertyGroup):
#     ucx_collection: bpy.props.StringProperty(
#         name="Collection",
#         description="Collection to add the collision box to"
#     )
#     ucx_chkbox: bpy.props.PointerProperty(type=UCX_UL_UCXCheckbox)
#     ucx_chkbox_bounding: bpy.props.PointerProperty(type=UCX_UL_UCXCheckboxBounding)
#     ucx_chkbox_merge: bpy.props.PointerProperty(type=UCX_UL_UCXCheckboxMerge)
#     ucx_chkbox_autohide: bpy.props.PointerProperty(type=UCX_UL_UCXCheckboxAutohide)
#     vertex_group_items: bpy.props.CollectionProperty(type=UCX_PG_VertexGroupItems)
#     last_active_object: bpy.props.PointerProperty(type=bpy.types.Object)
#     last_checkbox_value: bpy.props.BoolProperty(default=True)



def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # # Register the main PropertyGroup
    # bpy.utils.register_class(UCX_Properties)

    # # Assign the main PropertyGroup to bpy.types.Scene
    # bpy.types.Scene.ucx_properties = bpy.props.PointerProperty(type=UCX_Properties)
    
    bpy.types.Scene.ucx_collection = StringProperty(
        name="Collection",
        description="Collection to add the collision box to"
    )

    bpy.types.Scene.ucx_chkbox = bpy.props.PointerProperty(type=UCX_UL_UCXCheckbox)

    bpy.types.Scene.ucx_chkbox_bounding = bpy.props.PointerProperty(type=UCX_UL_UCXCheckboxBounding)

    bpy.types.Scene.ucx_chkbox_merge = bpy.props.PointerProperty(type=UCX_UL_UCXCheckboxMerge)

    bpy.types.Scene.ucx_chkbox_autohide = bpy.props.PointerProperty(type=UCX_UL_UCXCheckboxAutohide)

    bpy.types.Scene.vertex_group_items = bpy.props.CollectionProperty(type=UCX_PG_VertexGroupItems)

    bpy.types.Scene.last_active_object = bpy.props.PointerProperty(type=bpy.types.Object)

    bpy.types.Scene.last_checkbox_value = bpy.props.BoolProperty(default=True)

    bpy.app.handlers.depsgraph_update_post.append(on_selection_changed)

    bpy.app.handlers.depsgraph_update_post.append(on_checkbox_changed)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # Unregister the main PropertyGroup
    # del bpy.types.Scene.ucx_properties
    # bpy.utils.unregister_class(UCX_Properties)
    
    del bpy.types.Scene.ucx_collection
    del bpy.types.Scene.ucx_chkbox
    del bpy.types.Scene.ucx_chkbox_bounding
    del bpy.types.Scene.ucx_chkbox_merge
    del bpy.types.Scene.ucx_chkbox_autohide
    del bpy.types.Scene.vertex_group_items

    if on_selection_changed in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(on_selection_changed)

    del bpy.types.Scene.last_active_object

    if on_checkbox_changed in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(on_checkbox_changed)

    del bpy.types.Scene.last_checkbox_value

if __name__ == "__main__":
    register()