import bpy
import bmesh
import re

bl_info = {
    "name": "Unreal Engine Custom Collision Tool (UCX)",
    "description": "Automatically creates profile collision for UE FBX Import",
    "author": "ohmcodes",
    "version": (1, 0, 0),
    "blender": (4, 3, 2),
    "location": "View3D > Right panel",
    "category": "UCX",
}

def create_collision_box(collection):
    # Ensure an object is selected
    if bpy.context.selected_objects:
        # Get the selected object
        selected_obj = bpy.context.selected_objects[0]
        
        # Enter object mode and deselect all
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        
        # Select the object again
        selected_obj.select_set(True)
        bpy.context.view_layer.objects.active = selected_obj
        
        # Duplicate the object and create a bounding box
        bpy.ops.object.duplicate()
        temp_obj = bpy.context.selected_objects[0]
        
        # Enter edit mode and select all vertices
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        
        # Create a convex hull (bounding box)
        bpy.ops.mesh.convex_hull()
        
        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Rename the object for Unreal Engine collision
        temp_obj.name = f"UCX_{selected_obj.name}_00"
        
        # Optionally, apply the scale and rotation
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        
        # Add the collision box to the specified collection
        if collection:
            collection.objects.link(temp_obj)
            # Unlink from the default collection if necessary
            for col in temp_obj.users_collection:
                if col != collection:
                    col.objects.unlink(temp_obj)
                    
        temp_obj.hide_set(True)
        
        # Deselect all and select the original object
        bpy.ops.object.select_all(action='DESELECT')
        selected_obj.select_set(True)
        bpy.context.view_layer.objects.active = selected_obj
        
        print(f"Created collision box: {temp_obj.name}")
    else:
        print("No object selected. Please select a mesh object.")

def get_vertex_count(obj, vg):
    # Initialize a counter for vertices in the group
    vertex_count = 0

    # Iterate over all vertices in the object
    for v in obj.data.vertices:
        # Check if the vertex belongs to the vertex group
        if vg.index in [g.group for g in v.groups]:
            vertex_count += 1

    return vertex_count

def check_selected_vertices(obj):
    obj = bpy.context.object

    bm = bmesh.from_edit_mesh(obj.data)
    selected_vertices = [v for v in bm.verts if v.select]
    if len(selected_vertices) >= 2:
        print("At least two vertices are selected.")
        return True
    else:
        print("Less than two vertices are selected.")
        return False

def create_new_name(collection, obj_name):
    # Define the base name pattern
    obj_name = obj_name.replace(r'.(\d{3})','')
    base_name_pattern = fr"UCX_{obj_name}_(\d{{2}})"
    current_number = "00"

    # List to store objects that match the base name pattern
    matching_objects = []

    # Iterate through all objects in the scene
    for cobj in collection.objects:
        match = re.match(base_name_pattern, cobj.name)
        print(cobj.name)
        if match:
            current_number = match.group(1)
            print(f"current_number from matching: {current_number}")
            matching_objects.append((cobj, current_number))

    # Function to get the next number
    def get_next_number(current_number):
        return f"{int(current_number) + 1:02d}"

    # Print the matching objects and their next numbers
    if matching_objects:
        for cobj, current_number in matching_objects:
            next_number = get_next_number(current_number)
            print(f"Object: {cobj.name}, Next Name: UCX_{obj_name}_{next_number}")
        
        return f"UCX_{obj_name}_{next_number}"
    else:
        print(f"No objects found with the name pattern UCX_{obj_name}_XX in collection {collection}.")
        return f"UCX_{obj_name}_{current_number}"

def clean_names(collection):
    res = 0
    # Iterate over all objects in the collection
    for i, obj in enumerate(collection.objects, 1):
        # Check if the object name ends with ".000"
        
        if re.search(r'\.\d{3}$', obj.name):
            old_name = obj.name
            print(f"Original Object name {old_name}")
            #print(f"Found suffix {obj.name}")
            new_name = re.sub(r'\.\d{3}$', '', obj.name)
            print(f"Renamed to {new_name}")
            obj.name = new_name
            print(f"Applied named {obj.name}")

            if old_name == obj.name:
                print(f"Error renamed {obj.name} existing")
                res+=1
    
    return res

def create_collision_from_vertex_groups(collection, obj):
    vg_to_create = []
    for i, vg in enumerate(obj.vertex_groups):
        vertex_count = get_vertex_count(obj, vg)
        if vertex_count <= 2:
            continue

        if bpy.context.active_object.mode == 'OBJECT':
            if bpy.context.scene.collision_chkbox.collision_chk_ucx_only and "UCX_" not in vg.name:
                continue
        else:
            vg_list = [item.vertex_group_name for item in bpy.context.scene.vertex_group_items]

            if vg.name not in vg_list:
                continue
        
        print(f"{i} {vg.name}")
        vg_to_create.append(vg.name)

        preserve_selected = bpy.context.view_layer.objects.active

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')

        bpy.ops.object.vertex_group_set_active(group=vg.name)
        bpy.ops.object.vertex_group_deselect()
        selected_verts = bpy.ops.object.vertex_group_select()
        
        bpy.ops.object.mode_set(mode='OBJECT')

        if not selected_verts:
            raise Exception("No vertices selected!")

        # Extract the selected vertices
        selected_verts = [v for v in obj.data.vertices if v.select]
        
        # Create a new mesh and object
        new_mesh_name = f"UCX_{obj.name}_{i:02d}"
        new_mesh = bpy.data.meshes.new(new_mesh_name)

        # Other way to create from obj.data
        # Prepare the vertices for the new mesh
        # verts = [v.co for v in selected_verts]
        # edges = []
        # faces = []

        # # Set the vertices, edges, and faces of the new mesh
        # new_mesh.from_pydata(verts, edges, faces)

        new_obj = bpy.data.objects.new(new_mesh_name, new_mesh)
        
        new_bm = bmesh.new()
        # Add the selected vertices to the new BMesh
        for v in selected_verts:
            #print(type(v))
            new_bm.verts.new(v.co)

        new_bm.to_mesh(new_mesh)
        new_bm.free()
        
        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Copy the transform (location, rotation, scale) from the original object
        new_obj.location = obj.location
        new_obj.rotation_euler = obj.rotation_euler
        new_obj.scale = obj.scale

        if collection:
            collection.objects.link(new_obj)
            # Unlink from the default collection if necessary
            for col in new_obj.users_collection:
                if col != collection:
                    col.objects.unlink(new_obj)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = new_obj

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        
        # Call the convex hull operator on the selected vertices
        bpy.ops.mesh.convex_hull(delete_unused=True, use_existing_faces=True, make_holes=False, join_triangles=True)

        new_obj.name = re.sub(r'\.\d{3}$', '', new_obj.name)

        new_obj.hide_set(True)

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = preserve_selected
        bpy.data.objects[preserve_selected.name].select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')    

        print(f"Created collision box: {new_obj.name}")  
        
def create_collision_from_selected_vertices(collection, obj):
    if obj.type != 'MESH':
        raise Exception("Selected object is not a mesh!")
    
    preserve_selected = bpy.context.view_layer.objects.active
    # Ensure we are in object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    new_mesh_name = create_new_name(collection, obj.name)

    # Create a new mesh and object
    new_mesh = bpy.data.meshes.new(new_mesh_name)
    new_obj = bpy.data.objects.new(new_mesh_name, new_mesh)
    
    # Enter edit mode and get the selected vertices
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    
    # Get the selected vertices
    selected_verts = [v for v in bm.verts if v.select]

    if not selected_verts:
        raise Exception("No vertices selected!")
    
    # Create a new BMesh for the new mesh
    new_bm = bmesh.new()

    # Add the selected vertices to the new BMesh
    for v in selected_verts:
        #print(type(v))
        new_bm.verts.new(v.co)

    # Add the selected vertices to the new BMesh
    #[new_bm.verts.new(v.co) for v in selected_verts]

    # Update the new mesh with the new BMesh
    new_bm.to_mesh(new_mesh)
    new_bm.free()

    # Return to object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Copy the transform (location, rotation, scale) from the original object
    new_obj.location = obj.location
    new_obj.rotation_euler = obj.rotation_euler
    new_obj.scale = obj.scale

    # Add the collision box to the specified collection
    if collection:
        collection.objects.link(new_obj)
        # Unlink from the default collection if necessary
        for col in new_obj.users_collection:
            if col != collection:
                col.objects.unlink(new_obj)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = new_obj
    bpy.data.objects[new_obj.name].select_set(True)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    
    # Call the convex hull operator on the selected vertices
    bpy.ops.mesh.convex_hull(delete_unused=True, use_existing_faces=True, make_holes=False, join_triangles=True)
    
    #old_int = int("00")
    #print(f"old int 00 {old_int+1:02d}")
    
    print(f"Created collision box: {new_obj.name}")
    new_obj.name = re.sub(r'\.\d{3}$', '', new_obj.name)

    new_obj.hide_set(True)

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = preserve_selected
    bpy.data.objects[preserve_selected.name].select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

def create_vertex_group_from_selection(obj):
    if not obj.vertex_groups:
        group_name = f"UCX_{obj.name}_00"
    else:
        # Find the next available increment
        existing_groups = [vg.name for vg in obj.vertex_groups if vg.name.startswith(f"UCX_{obj.name}_")]
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
                group_name = f"UCX_{obj.name}_{last_num + 1:02d}"
            else:
                group_name = f"UCX_{obj.name}_00"
        else:
            group_name = f"UCX_{obj.name}_00"
    
    # Create a new vertex group
    vg = obj.vertex_groups.new(name=group_name)
    bpy.ops.object.vertex_group_assign()
    return group_name


class COLLISION_OT_CreateCollection(bpy.types.Operator):
    bl_label = "Create Collection"
    bl_idname = "collision.create_collection"
    
    def execute(self, context):
        # Create a new collection
        new_collection = bpy.data.collections.new("CollisionCollection")
        bpy.context.scene.collection.children.link(new_collection)
        context.scene.collision_collection = new_collection.name
        
        # Force UI redraw
        context.area.tag_redraw()
        return {'FINISHED'}         

class COLLISION_OT_CreateFromObject(bpy.types.Operator):
    bl_label = "From Selected Object"
    bl_idname = "collision.create_from_object"
    
    def execute(self, context):
        # Get the selected collection
        collection_name = context.scene.collision_collection
        collection = bpy.data.collections.get(collection_name)
        
        if not collection:
            self.report({'ERROR'}, "No collection selected!")
            return {'CANCELLED'}
        
        # Call the function to create the collision box
        create_collision_box(collection)
        
        # Redraw UI
        context.area.tag_redraw()
        return {'FINISHED'}

class COLLISION_OT_CreateFromVGroups(bpy.types.Operator):
    bl_label = "From Existing VGroups"
    bl_idname = "collision.create_from_vgroups"
    
    def execute(self, context):
        # Get the selected collection
        collection_name = context.scene.collision_collection
        collection = bpy.data.collections.get(collection_name)
        
        if not collection:
            self.report({'ERROR'}, "No collection selected!")
            return {'CANCELLED'}
        
        if not context.selected_objects:
            self.report({'ERROR'}, "No object selected!")
            return {'CANCELLED'}
        
        obj = context.active_object
        
        #for vg in obj.vertex_groups:
        #    if "UCX_" in vg.name:
        
        # Call the function to create the collision box
        #create_collision_box(collection)
        create_collision_from_vertex_groups(collection, obj)
        
        # Redraw UI
        context.area.tag_redraw()
        return {'FINISHED'}
    
class COLLISION_OT_CreateFromSelectedVertices(bpy.types.Operator):
    bl_label = "From Selected Vertices"
    bl_idname = "collision.create_from_selectedvert"
    
    def execute(self, context):
        # Get the selected collection
        collection_name = context.scene.collision_collection
        collection = bpy.data.collections.get(collection_name)
        
        if not collection:
            self.report({'ERROR'}, "No collection selected!")
            return {'CANCELLED'}
        
        if not context.selected_objects:
            self.report({'ERROR'}, "No object selected!")
            return {'CANCELLED'}
        
        obj = context.active_object

        if not check_selected_vertices(obj):
            self.report({'ERROR'}, "No vertices selected! Or Select two or more")
            return {'CANCELLED'}
        
        
        
        create_collision_from_selected_vertices(collection, obj)
        
        # Redraw UI
        context.area.tag_redraw()
        return {'FINISHED'}

class COLLISION_OT_SwitchEditMode(bpy.types.Operator):
    bl_label = "Edit Mode"
    bl_idname = "collision.switch_edit_mode"
    mode: bpy.props.StringProperty()

    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Redraw UI
        context.area.tag_redraw()
        return {'FINISHED'}

class COLLISION_OT_FetchVG(bpy.types.Operator):
    bl_idname = "collision.fetch_vertex_group"
    bl_label = "Fetch Vertex Groups"

    def execute(self, context):
        obj = context.active_object
        
        context.scene.vertex_group_items.clear()
        
        # Add a new entry for each vertex group
        for vg in obj.vertex_groups:
            vertex_count = get_vertex_count(obj, vg)

            if vertex_count <= 2:
                continue

            if context.scene.collision_chkbox.collision_chk_ucx_only and "UCX_" not in vg.name:
                continue
            
            item = context.scene.vertex_group_items.add()
            item.vertex_group_name = vg.name
            
        return {'FINISHED'}
    
class COLLISION_OT_CreateFromVGList(bpy.types.Operator):
    bl_label = "From List above"
    bl_idname = "collision.create_from_vglist"
    
    def execute(self, context):
        # Get the selected collection
        collection_name = context.scene.collision_collection
        collection = bpy.data.collections.get(collection_name)
        
        if not collection:
            self.report({'ERROR'}, "No collection selected!")
            return {'CANCELLED'}
        
        if not context.selected_objects:
            self.report({'ERROR'}, "No object selected!")
            return {'CANCELLED'}
        
        obj = context.active_object

        create_collision_from_vertex_groups(collection, obj)
        
        # Redraw UI
        context.area.tag_redraw()
        return {'FINISHED'}

class COLLISION_OT_RemoveVGEntry(bpy.types.Operator):
    bl_idname = "collision.remove_vertex_group_entry"
    bl_label = "Remove Vertex Group Entry"

    index: bpy.props.IntProperty()

    def execute(self, context):
        context.scene.vertex_group_items.remove(self.index)
        return {'FINISHED'}

class COLLISION_OT_CleanNames(bpy.types.Operator):
    bl_idname = "collision.clean_names"
    bl_label = "Clean Object names"
    bl_description = "Removes .000 suffix"

    def execute(self, context):
        collection_name = context.scene.collision_collection
        collection = bpy.data.collections.get(collection_name)

        res = clean_names(collection)
        if res > 0:
            self.report({'WARNING'}, "Some of the objects is Existed rename failed.")

        return {'FINISHED'}

class COLLISION_PG_VertexGroupItem(bpy.types.PropertyGroup):
    vertex_group_name: bpy.props.StringProperty(name="Vertex Group Name")

class COLLISION_UL_VertexGroups(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False)
            print("haroo")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text=item.name)
            print("hooray")

class COLLISION_UL_UCXChecbox(bpy.types.PropertyGroup):
    collision_chk_ucx_only : bpy.props.BoolProperty(
        name="UCX Only",
        description="Choose only UCX Vertex Group names",
        default = True
    )

# Operator to add a vertex group
class COLLISION_OT_CreateVertexGroup(bpy.types.Operator):
    bl_label = "Add Selected to Vertex Group"
    bl_idname = "collision.create_vertex_group"
    
    def execute(self, context):
        if not context.selected_objects:
            self.report({'ERROR'}, "No object selected!")
            return {'CANCELLED'}
        
        obj = context.selected_objects[0]
        if obj.type != 'MESH':
            self.report({'ERROR'}, "Selected object is not a mesh!")
            return {'CANCELLED'}
        
        bm = bmesh.from_edit_mesh(obj.data)
        selected_vertices = [v for v in bm.verts if v.select]
        if len(selected_vertices) >= 3:
            # Create a new vertex group
            group_name = create_vertex_group_from_selection(obj)
            self.report({'INFO'}, f"Created vertex group: {group_name}")
            bpy.ops.wm.save_mainfile()

        # Force UI redraw
        context.area.tag_redraw()
        
        return {'FINISHED'}

# Not using
# Operator to remove a vertex group
class COLLISION_OT_RemoveVertexGroup(bpy.types.Operator):
    bl_label = "Remove Vertex Group"
    bl_idname = "collision.remove_vertex_group"
    
    def execute(self, context):
        if not context.selected_objects:
            self.report({'ERROR'}, "No object selected!")
            return {'CANCELLED'}
        
        obj = context.selected_objects[0]
        if obj.type != 'MESH':
            self.report({'ERROR'}, "Selected object is not a mesh!")
            return {'CANCELLED'}
        
        # Remove the active vertex group
        if obj.vertex_groups:
            obj.vertex_groups.remove(obj.vertex_groups[obj.vertex_groups.active_index])
        
        # Force UI redraw
        context.area.tag_redraw()
        return {'FINISHED'}

class COLLISION_PT_Panel(bpy.types.Panel):
    bl_label = "Unreal Engine Custom Collision Tool (UCX)"
    bl_idname = "COLLISION_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "UCX"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.label(text="Automatically creates profile collision for UE FBX Import")
        layout.operator("wm.url_open", text="Open Docs").url = "https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-static-mesh-pipeline?application_version=4.27"

        collectionCol = layout.column()

        collectionCol.label(text="Select Collection:")
        
        collectionSearchRow = collectionCol.row()
        
        collectionSearchRow.prop_search(scene, "collision_collection", bpy.data, "collections", text="Collection")

        collectionSearchRow.operator("collision.create_collection", text="", icon='ADD')

        layout.separator()

        if bpy.context.scene.collision_collection != "":
            
            #bpy.context.active_object.mode == 'OBJECT'
            if not context.selected_objects and scene.collision_mode == 'OBJECT': 
                layout.label(text="Select Object to start.")
                layout.separator()
                
            if context.selected_objects:

                #obj = context.selected_objects[0]
                obj = context.active_object
                
                if bpy.context.active_object.mode == 'OBJECT':  
                    objectButtonsRow = layout.row()
                    objectButtonsCol = objectButtonsRow.column()
                    objectButtonsCol.label(text="Create From: ")
                    # Button to create the collision box
                    objectButtonsRow.operator("collision.create_from_object", text="Object")

                    if len(obj.vertex_groups) > 0:
                        vgButtonsRow = layout.row()
                        vgButtonsCol = vgButtonsRow.column()
                        
                        vgButtonsCol.label(text="Or From:")
                        vgButtonsRow.operator("collision.create_from_vgroups", text="Vertex groups")

                        collision_chkbox = scene.collision_chkbox
                        layout.prop(collision_chkbox, "collision_chk_ucx_only", text="Choose only group with prefix UCX_")
                    

                    layout.separator()

                    layout.operator("collision.switch_edit_mode", text="Or Switch to Edit mode and Select Vertices")

                if bpy.context.active_object.mode == 'EDIT':  
                    cf_sel_vertLRow = layout.row()

                    cf_sel_vertLRow.label(text="Create From: ")
                    cf_sel_vertLRow.operator("collision.create_from_selectedvert")

                    layout.operator("collision.create_vertex_group")
                    layout.separator()
                    
                    collision_chkbox = scene.collision_chkbox
                    layout.prop(collision_chkbox, "collision_chk_ucx_only", text="Choose only group with prefix UCX_")

                    if len(obj.vertex_groups) > 0:
                        has_groups = False
                        if collision_chkbox.collision_chk_ucx_only:
                            ucx_count = 0
                            for vg in obj.vertex_groups:
                                if "UCX_" in vg.name:
                                    ucx_count+=1
                            if ucx_count <= 0:
                                layout.label(text="Create Vertex Groups Select two or more vertices then add") 
                            else:
                                has_groups = True
                        else:
                            has_groups = True

                        if has_groups:
                            layout.operator("collision.fetch_vertex_group")
                            layout.label(text="Note: Save if you add/assign new group to apply")
                            layout.label(text="It will only select groups that has vertices")

                            for i, item in enumerate(scene.vertex_group_items):
                                box = layout.box()
                                row = box.row()
                                row.prop_search(item, "vertex_group_name", obj, "vertex_groups", text=str(i+1))
                                row.operator("collision.remove_vertex_group_entry", text="", icon="X").index = i

                            if len(scene.vertex_group_items) > 0:
                                cf_listRow = layout.row()

                                cf_listRow.label(text="Create From: ")
                                cf_listRow.operator("collision.create_from_vglist")    

                    else:
                        layout.label(text="Create Vertex Groups Select two or more vertices then add")   

            layout.operator("collision.clean_names")

def register():
    bpy.types.Scene.collision_collection = bpy.props.StringProperty(
        name="Collection",
        description="Collection to add the collision box to"
    )
    bpy.types.Scene.collision_mode = bpy.props.EnumProperty(
        name="Mode",
        items=[
            ('OBJECT', "Object", "Create collision for the entire object"),
            ('EDIT', "Edit", "Create collision for vertex groups")
        ],
        default='OBJECT'
    )
    bpy.utils.register_class(COLLISION_PT_Panel)
    bpy.utils.register_class(COLLISION_OT_CreateCollection)
    bpy.utils.register_class(COLLISION_OT_CreateFromObject)
    bpy.utils.register_class(COLLISION_OT_SwitchEditMode)

    bpy.utils.register_class(COLLISION_UL_UCXChecbox)
    bpy.types.Scene.collision_chkbox = bpy.props.PointerProperty(type=COLLISION_UL_UCXChecbox)
    bpy.utils.register_class(COLLISION_PG_VertexGroupItem)
    bpy.types.Scene.vertex_group_items = bpy.props.CollectionProperty(type=COLLISION_PG_VertexGroupItem)
    bpy.utils.register_class(COLLISION_OT_FetchVG)
    bpy.utils.register_class(COLLISION_OT_RemoveVGEntry)
    bpy.utils.register_class(COLLISION_OT_CreateFromSelectedVertices)
    bpy.utils.register_class(COLLISION_OT_CreateFromVGroups)
    bpy.utils.register_class(COLLISION_OT_CreateFromVGList)
    bpy.utils.register_class(COLLISION_OT_CreateVertexGroup)

    bpy.utils.register_class(COLLISION_OT_CleanNames)

    bpy.utils.register_class(COLLISION_UL_VertexGroups)
    
def unregister():
    del bpy.types.Scene.collision_collection
    del bpy.types.Scene.collision_mode
    bpy.utils.unregister_class(COLLISION_PT_Panel)
    bpy.utils.unregister_class(COLLISION_OT_CreateCollection)
    bpy.utils.unregister_class(COLLISION_OT_CreateFromObject)
    bpy.utils.unregister_class(COLLISION_OT_SwitchEditMode)
    

    bpy.utils.unregister_class(COLLISION_UL_UCXChecbox)
    del bpy.types.Scene.collision_chkbox
    bpy.utils.unregister_class(COLLISION_PG_VertexGroupItem)
    del bpy.types.Scene.vertex_group_items
    bpy.utils.unregister_class(COLLISION_OT_FetchVG)
    bpy.utils.unregister_class(COLLISION_OT_RemoveVGEntry)
    bpy.utils.unregister_class(COLLISION_OT_CreateFromSelectedVertices)
    bpy.utils.unregister_class(COLLISION_OT_CreateFromVGroups)
    bpy.utils.unregister_class(COLLISION_OT_CreateFromVGList)
    bpy.utils.unregister_class(COLLISION_OT_CreateVertexGroup)

    bpy.utils.unregister_class(COLLISION_OT_CleanNames)

    bpy.utils.unregister_class(COLLISION_UL_VertexGroups)
    
if __name__ == "__main__":
    register()