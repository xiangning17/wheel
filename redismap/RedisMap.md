# RedisMap类实现

**<font size=4 color=blue>S:</font>**

在python map中存储大量对象时导致程序内存占用过大，但在某时刻使用的数据量并不大。
根据Redis数据库特性，其能存储大量数据，我们可以根据需要按需提取数据，不必将全部数据载入内存占用大量空间。
其中的map存储结构与python map一致，因此考虑使用redis代替map进行数据存取。

但是，redis中的map类型不能存储list（强行存储list到redis map只会将list的str形式存入其中，相应对其操作久只能一次性读取整个list的str表达式并手工再处理）。
但很多时候存储如python map般存储list的能力是需要的。

因此，需要为redis map增加存储list的能力。

**<font size=4 color=red>已为RedisMap增加存储子map的功能,详情查看文档最后的<更新></font>**

**<font size=4 color=blue>T:</font>**

结合redis提供的list类型存储，我们可以实现对redis的map存储进行扩展，使其支持list存储。

**<font size=4 color=blue>A:</font>**

Redis本身提供存储list的能力，因此设计方案为：对于想往map中存储list的操作，我们将真正的数据存储到redis的list类型中，
然后在map中该key对应的实际值为存储为该list在redis中存储的键值，因此后续的从redis map操作该list元素时可以通过键值映射到对应的redis list。

**<font size=4 color=blue>R:</font>**

1. 完成了RedisMap类，其可以存储list类型的数据。
2. 对RedisMap类进行定制，使其满足python map的一些操作，而不必关心redis的API
3. 对于RedisMap中存储的list对象，在获取时返回一个经过包装的RedisList对象，也不用使用Redis API


# RedisMap 简单使用示例

**其中执行完存储，删除某些元素的操作时，可以直接进redis数据库看看发生了什么。**

    r = redis.Redis(host='127.0.0.1', port=6379)    # 获取redis实例对象
    m = RedisMap(r, 'map_name')     # 通过数据库对象与相应的map name构造RedisMap对象

    m['key_str'] = '普通字串'   # 此处的key或者value都可以是任意python对象，只不过存储时会自动调用str()强转成字符串 

    s = m['key_str']    # s = '普通字串'
    
    print len(m)    # 输出map中元素个数
    
    key = 'key_str'
    if key in m:     # 使用'in'操作符判断是否存在
        print '%s is in map, and value = %s' % (key, m[key])
    
    for key in m.keys():    # 返回keys上的迭代器
        print key, m[key]
    
    for v in m.values():    # 返回values上的迭代器
        print v
        
    for k, v in m.items():  # 返回items上的迭代器
        print k, v
       
    m['key_list'] = [1, 2]    # 存储list到RedisMap，也可以先存一个空的list‘[]’
    
    list = m['key_list']    # 此处返回的是经过包装的RedisList对象,这是一个对Redis list的包装，因此对其进行操作不会导致加载很多数据到内存。
    
    i = list[0]     # i = '1'，字符串的‘1’，需要自己转换成其他类型
    print i         # 输出‘1’
    
    list[0] = 5     # list[0]赋值为5
    print list[0]
    
    list.append(3)  # 在末尾添加一个元素
    print list[2]
    
    print len(list) # 输出list的长度，此时为3
    
    python_list = list[:]   # 返回一个python list,也支持'[:-1]',不支持步长
    
    list.clear()    # 清空list，
    
    
    del m['key_list']   # 删除某个元素，若元素是列表，还会执行相当于前一句‘list.clear()’
    m.clear()           # 清空map


# 更新

**1. 为RedisMap增加存储子map的功能，并增加update方法。**

    m = RedisMap(r, 'map_name')
    m['mm'] = {'first':100, 'second':90, 'third':89}
    mm = rm['mm']       # 返回的也为RedisMap对象
    print mm['first']   # 输出“100”
    
**2. 为RedisList增加extend和pop方法。**