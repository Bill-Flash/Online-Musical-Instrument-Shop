import redis

# 连接Redis,相当于redis.Redis()    暂时是本地连接，decode_responses=True是将redis读取出来的验证码转换成字符串类型，原本是二进制字节
r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)


# 存储验证码
def redis_set(key, value, timeout=300):         # timeout=60过期时间60s
    return r.set(key, value, timeout)


# 提取验证码
def redis_get(key):
    return r.get(key)          # 这里输出的原本是二进制字节类型数据，decode_responses=True自动转换成字符串


# 删除验证码
def redis_delete(key):
    return r.delete(key)