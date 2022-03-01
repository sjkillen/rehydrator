from lib import *


def example_get_all_type_hints():
    class Foo(Rehydratable):
        a: Collection
        b: MeshObject

    class Bar(Foo):
        b: SurfaceObject
        c: EmptyObject

    class Baz(Rehydratable):
        c: MeshObject

    class Chair(Bar, Baz):
        pass

    assert Chair.get_all_type_hints() == {
        "a": Collection,
        "b": SurfaceObject,
        "c": EmptyObject,
    }


def example_imports():
    class Foo(Rehydratable):
        a: MeshObject
        a_append_from = "/home/capybara/Downloads/untitled.blend@Cube"


def example():
    class B(Rehydratable):
        obj: EmptyObject

    class A(Rehydratable):
        mesh: MeshObject
        curve: CurveObject
        counter: int
        b: B

        def __init__(self, container: Collection = None, rehydrating=False):
            super().__init__(container, rehydrating)
            if not rehydrating:
                self.counter = 0


def example_class_names():
    class Foo(Rehydratable):
        pass

    class Bar(Foo):
        pass

    class Baz(Bar, Foo):
        pass

    name = Rehydratable.dehydrate_classname(Baz)
    assert name == "Foo.Bar.Baz"
    assert Rehydratable.rehydrate_classname(name) == Baz

def rehydrate_scene():
    class Foo(Rehydratable):
        a: Collection
    foo = Foo()
    # Cache may create a new instance so just compare names
    # assert bpy.context.scene.rehydrate()[0] == foo

rehydrate_scene()