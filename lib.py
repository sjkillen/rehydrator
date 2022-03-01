import base64
from functools import reduce
import bpy
from bpy.types import (
    Collection,
    Object,
    Mesh,
    Curve,
    SurfaceCurve,
    MetaBall,
    Text,
    Volume,
    GreasePencil,
    Armature,
    Image,
    Light,
    LightProbe,
    Camera,
    Speaker,
    Scene,
)
from typing import TypeVar, Generic, NewType, get_type_hints
from functools import lru_cache
from contextlib import contextmanager
import pickle
import base64

T = TypeVar("T")


class ObjectData(Generic[T], Object):
    data: T


def Append(o: T, path: str) -> T:
    return path


EmptyObject = ObjectData[None]
MeshObject = ObjectData[Mesh]
CurveObject = ObjectData[Curve]
SurfaceObject = ObjectData[SurfaceCurve]
MetaBallObject = ObjectData[MetaBall]
TextObject = ObjectData[Text]
VolumeObject = ObjectData[Volume]
GreasePencilObject = ObjectData[GreasePencil]
ArmatureObject = ObjectData[Armature]
ImageObject = ObjectData[Image]
LightObject = ObjectData[Light]
LightProbeObject = ObjectData[LightProbe]
CameraObject = ObjectData[Camera]
SpeakerObject = ObjectData[Speaker]
# data is None, but not sure how to construct new forces.
ForceObject = NewType("ForceObject", ObjectData[None])


all_blend_types = {
    Collection,
    EmptyObject,
    MeshObject,
    CurveObject,
    SurfaceObject,
    MetaBallObject,
    TextObject,
    VolumeObject,
    GreasePencilObject,
    ArmatureObject,
    ImageObject,
    LightObject,
    LightProbeObject,
    CameraObject,
    SpeakerObject,
}


class Rehydratable:
    def __init__(self, container: Collection = None, rehydrating=False):
        self.__prefix = Rehydratable.dehydrate_classname(type(self))
        if rehydrating:
            self.__c = container
            return
        if container is None:
            container = bpy.data.collections.new(self.__prefix)
            bpy.context.scene.collection.children.link(container)
        self.__c = container
        self.initialize_bpy_structure()

    def __setattr__(self, field: str, v):
        super().__setattr__(field, v)
        if field.startswith(f"_{Rehydratable.__name__}"):
            return
        hints = get_type_hints(type(self))
        if hints.get(field, None) not in all_blend_types and not isinstance(
            v, Rehydratable
        ):
            with storage_ctx(self.__data) as storage:
                storage[field] = v

    def initialize_bpy_structure(self):
        self.__data = bpy.data.objects.new(f"{self.__prefix}.__data", None)
        self.__c.objects.link(self.__data)
        self.__data["__prefix"] = self.__prefix
        init_storage(self.__data)

        fields = {
            field: cls
            for field, cls in type(self).get_all_type_hints().items()
            if not field.endswith("_append_from")
        }

        for field, cls in fields.items():
            self.initialize_bpy_field(field, cls, self.__data)

    def initialize_bpy_field(self, field: str, Cls, data: EmptyObject):
        name = f"{self.__prefix}.{field}"
        append_path = f"{field}_append_from"
        if Cls == Collection or (
            Cls not in all_blend_types and issubclass(Cls, Rehydratable)
        ):
            if hasattr(self, append_path):
                blend_file, obj_name = getattr(self, append_path).split("@")
                with bpy.data.libraries.load(blend_file) as (src, dest):
                    dest.collections = [obj_name]
                obj = dest.collections[0]
            else:
                obj = bpy.data.collections.new(name)
            self.__c.children.link(obj)
            obj["__field"] = field
            if issubclass(Cls, Rehydratable):
                obj = Cls(obj)
        elif Cls in all_blend_types:
            if hasattr(self, append_path):
                blend_file, obj_name = getattr(self, append_path).split("@")
                with bpy.data.libraries.load(blend_file) as (src, dest):
                    dest.objects = [obj_name]
                obj = dest.objects[0]
            else:
                if Cls == EmptyObject:
                    data = None
                elif Cls == MeshObject:
                    data = bpy.data.meshes.new(f"{name}.mesh")
                elif Cls == CameraObject:
                    data = bpy.data.cameras.new(f"{name}.camera")
                elif Cls == CurveObject:
                    data = bpy.data.curves.new(f"{name}.curve", type="CURVE")
                else:
                    raise Exception("Type", Cls, "not supported")
                obj = bpy.data.objects.new(name, data)
            self.__c.objects.link(obj)
            obj["__field"] = field
        else:
            setattr(self, field, None)
            return
        setattr(self, field, obj)

    @staticmethod
    @lru_cache(maxsize=None)
    def rehydrate_classname(name: str) -> "Rehydratable":
        "Takes a string returned by dehydrate_classname and gives the class the was passed"
        work_list = [("", a) for a in Rehydratable.__subclasses__()]
        while len(work_list) > 0:
            prefix, subtype = work_list.pop()
            protoname = f"{prefix}{subtype.__name__}"
            if protoname == name:
                return subtype
            work_list.extend((f"{protoname}.", a) for a in subtype.__subclasses__())
        else:
            raise Exception("Not found")

    @staticmethod
    @lru_cache(maxsize=None)
    def dehydrate_classname(rtype: "Rehydratable") -> str:
        """
        Get a string that uniquely identifies a class that extends Rehydratable
        If the class indirectly extends Rehydratable, then a prefix is placed before the name that contains the parent Rehydratable class
        Parents are searched in the order rtype extends them so when multiple names are 'possible' only one name is valid

        This will break if two classes have the same name and parents
        """
        parent = next(
            (cls for cls in rtype.__bases__ if issubclass(cls, Rehydratable)), None
        )
        if parent is None:
            raise Exception("Class does not extend Rehydratable")
        order = [rtype]
        while parent != Rehydratable:
            order.insert(0, parent)
            parent = next(
                cls for cls in parent.__bases__ if issubclass(cls, Rehydratable)
            )
        return ".".join(cls.__name__ for cls in order)

    @staticmethod
    @lru_cache(maxsize=None)
    def rehydrate(target: Collection) -> "Rehydratable":
        prefix = Rehydratable.try_get_prefix(target)
        Cls = Rehydratable.rehydrate_classname(prefix)
        obj = Cls(target, rehydrating=True)

        for prop_obj in target.objects:
            if "__field" in prop_obj:
                setattr(obj, prop_obj["__field"], prop_obj)
        for prop_col in target.children:
            if "__field" in prop_col:
                d = prop_col
                if Rehydratable.try_get_prefix(prop_col):
                    d = Rehydratable.rehydrate(prop_col)
                setattr(obj, prop_col["__field"], d)

        data = next(obj for obj in target.objects if ".__data" in obj.name)
        setattr(obj, f"_{Rehydratable.__name__}__data", data)
        with storage_ctx(data) as storage:
            obj.__dict__.update(storage)

        return obj

    @classmethod
    def get_all_type_hints(cls):
        rehydratable_bases = tuple(
            get_type_hints(base)
            for base in cls.__bases__
            if issubclass(base, Rehydratable)
        )[::-1]
        return reduce(
            lambda a, b: {**a, **b}, (*rehydratable_bases, get_type_hints(cls)), dict()
        )

    @staticmethod
    def get_part(c: Collection, part: str):
        next(obj for obj in c.objects if obj.name.startswith(part))

    @staticmethod
    def try_get_prefix(c: Collection) -> str:
        if data := next((obj for obj in c.objects if ".__data" in obj.name), None):
            return data["__prefix"]






class RehydrateSceneOperator(bpy.types.Operator):
    bl_idname = "object.rehydrate_scene"
    bl_label = "Rehydrate Scene"

    def execute(self, context):
        wl = [bpy.context.collection]
        while len(wl) > 0:
            for col in wl.pop().children:
                if Rehydratable.try_get_prefix(col):
                    obj = Rehydratable.rehydrate(col)
                else:
                    wl.append(col)

        return {"FINISHED"}





ops = (RehydrateSceneOperator,)

menus = tuple(lambda menu, context: menu.layout.operator(Op.bl_idname) for Op in ops)


def register():
    for menu in menus:
        bpy.types.TOPBAR_MT_blender_system.append(menu)


def unregister():
    for menu in menus:
        bpy.types.TOPBAR_MT_blender_system.remove(menu)


@contextmanager
def storage_ctx(data: EmptyObject):
    storage = pickle.loads(base64.decodebytes(data["__data"].encode("ASCII")))
    try:
        yield storage
    finally:
        data["__data"] = base64.encodebytes(pickle.dumps(storage)).decode("ASCII")


def init_storage(data: EmptyObject):
    data["__data"] = base64.encodebytes(pickle.dumps(dict())).decode("ASCII")


def rehydrate_scene(self: Scene):
    wl = [self.collection]
    results = []
    while len(wl) > 0:
        item = wl.pop()
        if isinstance(item, Collection):
            if Rehydratable.try_get_prefix(item):
                results.append(Rehydratable.rehydrate(item))
            else:
                wl.extend(item.children)
    return results


bpy.types.Scene.rehydrate = rehydrate_scene
bpy.types.Rehydratable = Rehydratable
