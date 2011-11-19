import time

from django.core.cache import cache

NoValue = object()

class CachedDict(object):
    def __init__(self, cache=cache):
        self._cache = None
        self._cache_stale = None
        self._last_updated = None

        self.cache = cache
            
    # def __new__(cls, *args, **kwargs):
    #     self = super(ModelDict, cls).__new__(cls, *args, **kwargs)
    #     request_finished.connect(self._cleanup)
    #     return self
    
    def __getitem__(self, key):
        self._populate()
        try:
            return self._cache[key]
        except KeyError:
            value = self.get_default(key)
            if value is NoValue:
                raise
            return value
        except TypeError:
            # Workaround for race condition w/ _cleanup()
            return self._direct_cache[key]

    def __setitem__(self, key, value):
        raise NotImplementedError
    
    def __delitem__(self, key):
        raise NotImplementedError
        
    def __len__(self):
        if self._cache is None:
            self._populate()
        try:
            return len(self._cache)
        except TypeError:
            # Workaround for race condition w/ _cleanup()
            return len(self._direct_cache)
    
    def __contains__(self, key):
        self._populate()
        try:
            return key in self._cache
        except TypeError:
            # Workaround for race condition w/ _cleanup()
            return key in self._direct_cache

    def __iter__(self):
        self._populate()
        try:
            return iter(self._cache)
        except TypeError:
            # Workaround for race condition w/ _cleanup()
            return iter(self._direct_cache)
    
    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.model.__name__)

    def iteritems(self):
        self._populate()
        try:
            return self._cache.iteritems()
        except AttributeError:
            # Workaround for race condition w/ _cleanup()
            return self._direct_cache.iteritems()
    
    def itervalues(self):
        self._populate()
        try:
            return self._cache.itervalues()
        except AttributeError:
            # Workaround for race condition w/ _cleanup()
            return self._direct_cache.itervalues()
    
    def iterkeys(self):
        self._populate()
        try:
            return self._cache.iterkeys()
        except AttributeError:
            # Workaround for race condition w/ _cleanup()
            return self._direct_cache.iterkeys()
    
    def items(self):
        self._populate()
        try:
            return self._cache.items()
        except AttributeError:
            # Workaround for race condition w/ _cleanup()
            return self._direct_cache.items()
        
    def get(self, key, default=None):
        self._populate()
        try:
            return self._cache.get(key, default)
        except AttributeError:
            # Workaround for race condition w/ _cleanup()
            return self._direct_cache.get(key, default)
    
    def pop(self, key, default=NoValue):
        value = self.get(key, default)
        try:
            del self[key]
        except KeyError:
            pass
        return value

    def setdefault(self, key, value):
        if key not in self:
            self[key] = value

    @property
    def _direct_cache(self):
        return self.cache.get(self.cache_key)

    def _populate(self, reset=False):
        if reset:
            self._cache = None
            # TODO: Race condition in updating last_updated.  Needs
            # a test + fix.
            self.last_updated = int(time.time())
            self.cache.set(self.last_updated_cache_key, self.last_updated)
        elif self._cache is None:
            new_last_updated = self.cache.get(self.last_updated_cache_key) or 0
            if new_last_updated > (self._last_updated or 0) or \
              not getattr(self, '_cache_stale', None):
                self._cache = self.cache.get(self.cache_key)
                self._last_updated = new_last_updated
            else:
                self._cache = self._cache_stale
                self._cache_stale = None

        if self._cache is None:
            self._cache = self._get_cache_data()
            self.cache.set(self.cache_key, self._cache)
        return self._cache    

    def _get_cache_data(self):
        raise NotImplementedError

    def _cleanup(self, *args, **kwargs):
        self._cache_stale = self._cache
        self._cache = None

    def clear_cache(self):
        self._cache = None
        self._cache_stale = None

    def get_default(self, value):
        return NoValue

