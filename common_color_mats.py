import bpy

## Create Materials from Common Color Names
## script by Joshua R (GitHub user Botmasher)

class MaterialColorizer:
    color_map = {
        'red': (1.0, 0.0, 0.0),
        'green': (0.0, 1.0, 0.0),
        'blue': (0.0, 0.0, 1.0),
        'yellow': (1.0, 1.0, 0.0),
        'magenta': (1.0, 0.0, 1.0),
        'cyan': (0.0, 1.0, 1.0),
        'white': (1.0, 1.0, 1.0),
        'black': (0.0, 0.0, 0.0)
    }

    def __init__(self, name_base=""):
        """Set name to prefix to color materials"""
        self.material_name_base = name_base
        return

    def add_color(self, color_name, color_vec):
        """Map a color value to a named color"""
        if not color_name or color_name in color_map or not color_vec or len(color_vec) != 3:
            return False
        self.color_map[color_name] = color_vec
        return True     # self.color_map[color_name]

    def update_color(self, color_name, color_vec, update_material=True):
        """Update the value of one color name in the color map"""
        if not color_name or color_name not in self.color_map or not color_vec or len(color_vec) != 3:
            return False
        self.color_map[color_name] = color_vec
        update_material and self.update_material(color_name)
        return True     # self.color_map[color_name]

    def update_material(self, color_name):
        """Set color from color map on any material matching formatted name"""
        material_found = False
        for material in bpy.data.materials:
            if "{0}{1}".format(self.material_name_base, color_name) in material.name:
                material.diffuse_color = self.color_map[color_name]
                material_found = True
        return material_found

    def remove_color(self, color_name):
        """Delete a color name and value from the color map"""
        self.color_map = {color:vec for color,vec in self.color_map.items() if color_name == color}
        return

    def remove_colors(self, color_names=[]):
        """Delete an array of colors from the color map"""
        for color_name in color_names:
            self.remove_color(color_name)
        return

    def update_material_name_base(self, name_base):
        """Change the prefix attached to created color material names"""
        self.material_name_base = name_base
        return

    def assign_color(self, material, color_name):
        """Set the diffuse color of a basic material"""
        if color_name not in self.color_map: return
        material.diffuse_color = self.color_map[color_name]
        # TODO set attr using passed-in settings dict
        material.specular_intensity = 0.0
        material.hardness = 120
        material.use_transparent_shadows = True
        return

    def color_object_material(self, obj=bpy.context.scene.objects.active, color_name=None, existing_material=False):
        """Give selected object a material with a named color"""
        if color_name not in self.color_map: return False
        if existing_material:
            material = obj.active_material
        else:
            material = bpy.data.materials.new(name="{0}{1}".format(self.material_name_base, color_name))
            obj.data.materials.append(material)
        # NOTE select active material here either way?
        self.assign_color(material, color_name)
        return True
