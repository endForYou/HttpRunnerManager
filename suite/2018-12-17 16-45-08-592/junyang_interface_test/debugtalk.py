# debugtalk.py

import pymysql
import pprint
import redis
import requests
import time
from datetime import datetime

import json

authorizationValue = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJXRUIxNTgwMjU1NjcwOCIsImV4cCI6MTU0MzkxNzQyMiwiaWF0IjoxNTQzMzEyNjIyfQ.fc82cfB06D6xFoRPInexjmYiSnBHzbXSOklUC8fYFbiM6dF4EkEaF64rOuntLRbVpAS6cXK0pe3kv9XMNAtveg"
import logging

logger = logging.getLogger("django")  # 为loggers中定义的名称

db = pymysql.connect("39.104.174.120", "developer", "junYang2018_happy", "xuanke")
cursor = db.cursor(pymysql.cursors.DictCursor)


def closeDB():
    cursor.close()
    db.close()


REDIS_SERVER = redis.Redis(host="39.104.174.120", port=6379, db=0)
BASE_URL = "http://testapp.zhizhazhiyuan.comm:8763"


def get_redis_code(redis_server, phone_num):
    # 设置获取redis验证码时间为30s
    for i in range(0, 5):
        time.sleep(5)
        value = redis_server.get("rightCode" + str(phone_num).strip())
        if value:
            return value.decode()
    return False


def login(phone_num):
    phone_num = str(phone_num)
    # phone_num="15386426238"
    # print(111111111111111)
    # 发送验证码
    # print(get_redis_code(phone_num))
    # 首先从数据库里拿对应手机号码的token
    my_db = pymysql.connect("localhost", "root", "qwerty", "httprunner")
    my_cursor = my_db.cursor()
    my_cursor.execute("select token from user_token where phone=%s and is_valid=1", (phone_num,))
    result = my_cursor.fetchone()
    if result:
        token = result[0]
        return token
    # 数据库不存在合法验证码，则发送验证码去获取token，然后将token写入数据库
    else:
        send_response = requests.get(BASE_URL + "/login/weblogin/sendSms/" + phone_num)
        content = send_response.content
        try:
            tmp_dict = json.loads(content.decode())
            if tmp_dict['code'] != "ok" or send_response.status_code != 200:
                # print("验证码发送失败")
                return False
        except BytesWarning:
            # print("验证码发送失败")
            return False
        # 验证码查询不到则登录失败
        code = get_redis_code(REDIS_SERVER, phone_num)
        if not code:
            return False
        data = {
            "phoneNum": phone_num,
            "verificationCode": code
        }
        # print(json.dumps(data))
        headers = {'Content-Type': 'application/json;charset=UTF-8'}
        s = requests.post(url=BASE_URL + "/login/weblogin/checkCode", headers=headers, json=data)
        check_code_re_dict = json.loads(s.content.decode('utf-8'))
        if s.status_code != 200 or 'token' not in check_code_re_dict.keys():
            # print("check_code失败,错误信息为：" + s.content.decode('utf-8'))
            return False
        else:
            create_time = datetime.now()
            update_time = datetime.now()
            token = check_code_re_dict['token']
            phone = phone_num
            is_valid = 1
            params_tuple = (create_time, update_time, token, phone, is_valid)
            my_cursor.execute(
                "insert into user_token(create_time,update_time,token,phone,is_valid) values(%s,%s,%s,%s,%s)",
                params_tuple)
            my_db.commit()
            my_cursor.close()
            my_db.close()
            return token


def get_type():
    sql = "select id type from topic_type where id=1004"
    cursor.execute(sql)
    data = cursor.fetchall()
    return data


def get_type_byBoy():
    sql = "select id typeByBoy from topic_type where id=1003"
    cursor.execute(sql)
    data = cursor.fetchall()
    return data


def getCategoryId():
    sql = "select id getIds from major_category"
    cursor.execute(sql)
    data = cursor.fetchall()
    return data


def getSubCategoryId():
    sql = "SELECT a.id subCategoryIds, a.major_category_id categoryIds FROM major_sub_category AS a WHERE (SELECT COUNT(*) FROM  major_sub_category AS b WHERE b.major_category_id = a.major_category_id AND b.id >= a.id) <= 5"
    cursor.execute(sql)
    data = cursor.fetchall()
    return data


def validateMajorByTypeList(subCategoryIds):
    sql = "select m.id,m.name,count(cm.major_id) collegeCount  from major m left join college_major cm on m.id=cm.major_id  and cm.is_special=0 where m.major_sub_category_id= " + str(
        subCategoryIds) + " GROUP BY m.id  order by collegeCount desc, id asc"
    cursor.execute(sql)
    data = cursor.fetchall()
    return data


# 最热话题
def queryThemeInfoList():
    sql = "select * from theme_info ti where ti.is_hot=1 order by publish_time desc"
    cursor.execute(sql)
    data = cursor.fetchall()
    return data
