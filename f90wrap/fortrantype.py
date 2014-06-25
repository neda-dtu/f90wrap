import weakref

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
    
class FortranModule(object):
    """
    Baseclass for Fortran modules

    Metaclass is set to Singleton, so only one instane of each subclass of
    FortranModule can be created.
    """
    __metaclass__ = Singleton
    def __init__(self):
        self._arrays = {}
        self._objs = {}        

class FortranDerivedType(object):
    """
    Base class for Fortran derived types
    """
        
    def __init__(self):
        self._handle = None
        self._arrays = {}
        self._objs = {}
        self._alloc = True

    @classmethod
    def from_handle(cls, handle):
        self = cls.__new__(cls)
        FortranDerivedType.__init__(self) # always call the base constructor only
        self._handle = handle
        self._alloc = False
        return self
        
class FortranDerivedTypeArray(object):

    def __init__(self, parent, getfunc, setfunc, lenfunc, doc, arraytype):
        self.parent = weakref.ref(parent)
        self.getfunc = getfunc
        self.setfunc = setfunc
        self.lenfunc = lenfunc
        self.doc = doc
        self.arraytype = arraytype

    def iterindices(self):
        return iter(range(len(self)))

    indices = property(iterindices)

    def iteritems(self):
        for idx in self.indices:
            yield self[idx]

    def __iter__(self):
        return self.iteritems()

    def __len__(self):
        parent = self.parent()
        if parent is None:
            raise RuntimeError("Array's parent has gone out of scope")        
        return self.lenfunc(parent._handle)

    def __getitem__(self, i):
        parent = self.parent()
        if parent is None:
            raise RuntimeError("Array's parent has gone out of scope")
            
        i += 1  # convert from 0-based (Python) to 1-based indices (Fortran)
        element_handle = self.getfunc(parent._handle, i)
        try:
            obj = parent._objs[tuple(element_handle)]
        except KeyError:
            obj = parent._objs[tuple(element_handle)] = self.arraytype.from_handle(element_handle)
        return obj

    def __setitem__(self, i, value):
        parent = self.parent()
        if parent is None:
            raise RuntimeError("Array's parent has gone out of scope")
        
        i += 1 # convert from 0-based (Python) to 1-based indices (Fortran)
        self.setfunc(parent._handle, i, value._handle)

