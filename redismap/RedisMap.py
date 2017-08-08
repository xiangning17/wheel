# coding:utf-8

import logging
import traceback


class RedisMap(object):
    def __init__(self, rds, name):
        self._r = rds
        self._name = name
        self._list_key_prefix = '[LIST_FOR-%s]:' % name

    def __is_list(self, key):
        return key and key.startswith(self._list_key_prefix)

    def __getitem__(self, key):
        v = self._r.hget(self._name, key)
        if self.__is_list(v):
            return RedisList(self._r, v)

        return v

    def __setitem__(self, key, value):
        if isinstance(value, list) or isinstance(value, tuple):
            new_value = self._list_key_prefix + str(key)
            l = RedisList(self._r, new_value)
            l.clear()  # 先清空之前存在的
            for v in value:
                l.append(v)
            value = new_value
        logging.debug('redis map set %s\n%s' % (key, traceback.extract_stack()))

        self._r.hset(self._name, key, value)

    def __delitem__(self, key):
        v = self._r.hget(self._name, key)
        if self.__is_list(v):  # 删除list
            self._r.delete(v)

        self._r.hdel(self._name, key)

    def __len__(self):
        return self._r.hlen(self._name)

    def __contains__(self, key):
        return self._r.hexists(self._name, key)

    def rename_key(self, old, new):
        remain_value = self._r.hget(self._name, old)
        old_value = self[old]
        new_value = self[new]
        if isinstance(new_value, RedisList):  # 若new对应的值已经存在且是一个列表
            if isinstance(old_value, RedisList):
                if len(old_value) > len(new_value):
                    for v in new_value:
                        old_value.append(v)
                    new_value.clear()
                else:
                    for v in old_value:
                        new_value.append(v)
                    old_value.clear()
                    remain_value = self._r.hget(self._name, new)
            else:
                new_value.append(old_value)

        self._r.hset(self._name, new, remain_value)

        self._r.hdel(self._name, old)

        logging.debug('rename redis map key : %s -> %s' % (old, new))

    def keys(self):
        return (k for k, _ in self._r.hscan_iter(self._name))
        # return self._r.hkeys(self._name)

    def values(self):
        return (RedisList(self._r, v) if self.__is_list(v) else v for _, v in self._r.hscan_iter(self._name))
        # return [RedisList(self._r, v) if self.__is_list(v) else v for v in self._r.hvals(self._name)]

    def items(self):
        return ((k, RedisList(self._r, v) if self.__is_list(v) else v) for k, v in self._r.hscan_iter(self._name))

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

    def append(self, *val):
        logging.debug('[RedisList] append : %s' % val)
        self._r.rpush(self._name, *val)
        return self

    def clear(self):
        self._r.delete(self._name)
