# coding:utf-8

import logging
import traceback


class RedisMap(object):
    def __init__(self, rds, name):
        self._r = rds
        self._name = name
        self._redismap_prefix = ':RedisMap-'

    def _get_type(self, key):
        value = self._r.hget(self._name, key)
        logging.debug('get type of %s value : %s' % (key, str(value)))
        if value.startswith(self._redismap_prefix):
            t = self._r.type(value)
            if t == 'list':
                return RedisList
            elif t == 'hash':
                return RedisMap
        return str

    def __getitem__(self, key):
        v = self._r.hget(self._name, key)

        t = self._get_type(key)
        logging.debug('get item of %s type : %s' % (key, str(t)))
        if t != str:
            return t(self._r, v)

        return v

    def __setitem__(self, key, value):

        if isinstance(value, list) or isinstance(value, tuple) or isinstance(value, dict):
            new_value = self._redismap_prefix + str(hash(self._name + str(key)))

            if isinstance(value, list) or isinstance(value, tuple):
                l = RedisList(self._r, new_value)
                l.clear()  # 先清空之前存在的
                l.extend(value)
            elif isinstance(value, dict):
                m = RedisMap(self._r, new_value)
                m.clear()
                m.update(value)

            value = new_value

        logging.debug('redis map set %s to %s\n%s' % (key, value, traceback.extract_stack()))

        self._r.hset(self._name, key, value)

    def __delitem__(self, key):
        obj = self[key]
        if not isinstance(obj, str):
            obj.clear()                 # 清空对象
        self._r.hdel(self._name, key)   # 删除map中的键

    def __len__(self):
        return self._r.hlen(self._name)

    def __contains__(self, key):
        return self._r.hexists(self._name, key)

    def rename_key(self, old, new):
        value = self._r.hget(self._name, old)

        self._r.hset(self._name, new, value)
        self._r.hdel(self._name, old)

        logging.debug('rename redis map key : %s -> %s' % (old, new))

    def update(self, values):
        if values:
            for k, v in values.items():
                self[k] = v

    def keys(self):
        for k, _ in self._r.hscan_iter(self._name):
            yield k

    def values(self):
        return (self[k] for k in self.keys())

    def items(self):
        return ((k, self[k]) for k in self.keys())

    def clear(self):
        for k in self.keys():
            del self[k]
        self._r.delete(self._name)


class RedisList(object):
    def __init__(self, rds, name):
        self._r = rds
        self._name = name

    def __setitem__(self, key, value):
        self._r.lset(self._name, key, value)

    def __getitem__(self, key):

        if isinstance(key, slice):
            start = key.start if key.start else 0
            stop = key.stop
            if key.stop is None:
                stop = len(self)
            elif key.stop < 0:
                stop = len(self) + key.stop + 1
            return self._r.lrange(self._name, start, stop - 1)  # lrange的stop指向的位置的元素也会被返回，为模拟list行为，因此减1
        elif isinstance(key, int):
            rt = self._r.lrange(self._name, key, key)  # 返回范围列表
            if len(rt) > 0:
                return rt[0]
            else:
                raise IndexError('list index out of range')

    def __repr__(self):
        return repr(self[:])

    def __str__(self):
        return str(self[:])

    def __len__(self):
        return self._r.llen(self._name)

    def extend(self, values):
        if values:
            for v in values:
                self.append(v)

    def append(self, *val):
        logging.debug('[RedisList] append : %s' % val)
        self._r.rpush(self._name, *val)
        return self

    def pop(self):
        val = self._r.rpop(self._name)
        logging.debug('[RedisList] pop : %s' % val)
        return val

    def clear(self):
        self._r.delete(self._name)
