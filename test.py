import hashlib
import os
import random
import re
from urllib.parse import quote
import requests
import sys
import json
from datetime import datetime, timedelta, timezone
import time

def getTimeStr():
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
    return bj_dt.strftime("%Y-%m-%d %H:%M:%S")

def log(content):
    print(getTimeStr() + ' ' + str(content))
    sys.stdout.flush()

urls = {
    'login': 'https://xcxgk1ri59hxo.xybsyw.com/login/login!wx.action',
    'loadAccount': 'https://xcxgk1ri59hxo.xybsyw.com/account/LoadAccountInfo.action',
    'ip': 'https://api.bilibili.com/x/web-interface/zone?jsonp=jsonp',
    'amap': 'https://restapi.amap.com/v3/geocode/regeo?key=c222383ff12d31b556c3ad6145bb95f4&location={lon}%2C{lat}&extensions=all&s=rsx&platform=WXJS&appname=c222383ff12d31b556c3ad6145bb95f4&sdkversion=1.2.0&logversion=2.0',
    'address': 'https://xcxgk1ri59hxo.xybsyw.com/student/clock/GetPlan!detail.action',
    'trainId': 'https://xcxgk1ri59hxo.xybsyw.com/student/clock/GetPlan!getDefault.action',
    'sign':'https://xcxgk1ri59hxo.xybsyw.com/student/clock/PostNew.action',
    'new_sign':'https://xcxgk1ri59hxo.xybsyw.com/student/clock/Post!updateClock.action',
}

#请求签名
def get_sign_header(data: dict):
    re_punctuation = re.compile("[`~!@#$%^&*()+=|{}':;,\\[\\].<>/?！￥…（）—【】‘；：”“’。，、？]")
    cookbook = ["5", "b", "f", "A", "J", "Q", "g", "a", "l", "p", "s", "q", "H", "4", "L", "Q", "g", "1", "6",
                "Q",
                "Z", "v", "w", "b", "c", "e", "2", "2", "m", "l", "E", "g", "G", "H", "I", "r", "o", "s", "d",
                "5",
                "7", "x", "t", "J", "S", "T", "F", "v", "w", "4", "8", "9", "0", "K", "E", "3", "4", "0", "m",
                "r",
                "i", "n"]
    except_key = ["content", "deviceName", "keyWord", "blogBody", "blogTitle", "getType", "responsibilities",
                  "street", "text", "reason", "searchvalue", "key", "answers", "leaveReason", "personRemark",
                  "selfAppraisal", "imgUrl", "wxname", "deviceId", "avatarTempPath", "file", "file", "model",
                  "brand", "system", "deviceId", "platform", "code", "openId", "unionid"]

    noce = [random.randint(0, len(cookbook) - 1) for _ in range(20)]
    now_time = int(time.time())
    sorted_data = dict(sorted(data.items(), key=lambda x: x[0]))

    sign_str = ""
    for k, v in sorted_data.items():
        v = str(v)
        if k not in except_key and not re.search(re_punctuation, v):
            sign_str += str(v)
    sign_str += str(now_time)
    sign_str += "".join([cookbook[i] for i in noce])
    sign_str = re.sub(r'\s+', "", sign_str)
    sign_str = re.sub(r'\n+', "", sign_str)
    sign_str = re.sub(r'\r+', "", sign_str)
    sign_str = sign_str.replace("<", "")
    sign_str = sign_str.replace(">", "")
    sign_str = sign_str.replace("&", "")
    sign_str = sign_str.replace("-", "")
    sign_str = re.sub(f'\uD83C[\uDF00-\uDFFF]|\uD83D[\uDC00-\uDE4F]', "", sign_str)
    sign_str = quote(sign_str)
    sign = hashlib.md5(sign_str.encode('ascii'))

    return {
        "n": ",".join(except_key),
        "t": str(now_time),
        "s": "_".join([str(i) for i in noce]),
        "m": sign.hexdigest(),
        "v": "1.6.36"
    }

# 获取小程序用户唯一标识openId
def getOpenId(userInfo):
    data = {
        'openId': userInfo['token']['openId'],
        'unionId': userInfo['token']['unionId']
    }
    return data

# 获取Header
def getHeader(host):
    userAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36 MicroMessenger/7.0.9.501 NetType/WIFI MiniProgramEnv/Windows WindowsWechat'
    contentType = 'application/x-www-form-urlencoded'
    headers = {
        'wechat': '1',
        'user-agent': userAgent,
        'content-type': contentType,
        'host': host,
        'Connection': 'keep-alive',
        'Referer': 'https://servicewechat.com/wx9f1c2e0bbc10673c/456/page-frame.html',
    }
    return headers

# 登录获取sessionId和loginerId
def login(userInfo):
    data = getOpenId(userInfo)
    headers = getHeader("xcx.xybsyw.com")
    url = urls['login']
    resp = requests.post(url=url, headers=headers, data=data).json()
    if ('成功' in resp['msg']):
        ret = {
            'sessionId': resp['data']['sessionId'],
            'loginerId': resp['data']['loginerId']
        }
        log(f"sessionId:{resp['data']['sessionId']}获取成功")
        log(f"loginerId:{resp['data']['loginerId']}获取成功")
        return ret
    else:
        log('登录失败')
        exit(-1)

# 获取trainID
def getTrainID(sessionId):
    headers = getHeader("xcx.xybsyw.com")
    headers['cookie'] = f'JSESSIONID={sessionId}'
    url = urls['trainId']
    resp = requests.post(url=url, headers=headers).json()
    if ('成功' in resp['msg']):
        ret = resp['data']['clockVo']['traineeId']
        log(f'traineeId:{ret}获取成功')
        return ret
    else:
        log('trainid获取失败')
        exit(-1)

# 获取经纬度\签到地址
def getPosition(sessionId, trainId):
    headers = getHeader("xcx.xybsyw.com")
    headers['cookie'] = f'JSESSIONID={sessionId}'
    url = urls['address']
    data = {
        'traineeId': trainId
    }
    resp = requests.post(url=url, headers=headers, data=data).json()
    if ('成功' in resp['msg']):
        address = resp['data']['postInfo']['address']
        lat = resp['data']['postInfo']['lat']
        lng = resp['data']['postInfo']['lng']
        addressId = resp['data']['postInfo']['address']
        if addressId is None:
            addressId = 'null'
        ret = {
            'lat': lat,
            'lng': lng,
            'address': address,
            'addressId': addressId
        }
        log(f'经度:{lng}|纬度:{lat}')
        log(f'签到地址:{address}')
        return ret
    else:
        log('经纬度获取失败')
        exit(-1)

#获取签到地的adcode
def get_adcode():
    headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0'}
    data = requests.get(url=urls['ip'],headers=headers).json()['data']
    data.update(requests.get(url=urls['amap'].replace('{lon}',str(data['longitude'])).replace('{lat}',str(data['latitude'])),headers=headers).json()['regeocode'])
    #print("IP："+data["addr"])
    #print("国家："+data["country"])
    #print("ISP：" + data["isp"])
    #print("维度："+str(data['latitude']))
    #print("经度："+str(data['longitude']))
    #print("定位地址："+data["formatted_address"])
    #print("邮政编码："+data['addressComponent']["adcode"])
    #print(f"更多定位信息{data['addressComponent']}")
    return data['addressComponent']["adcode"]

#签到表单
def sign_form(userInfo):
    timeStamp = int(time.time())
    data = {
        "traineeId":userInfo['trainId'],
        "adcode":get_adcode(),
        "lat":userInfo['lat'],
        "lng":userInfo['lng'],
        "address":userInfo['address'],
        "deviceName":timeStamp,#"FNE-AN00",
        "punchInStatus":"0",
        "clockStatus":"2",
        "imgUrl":"",
        "reason":"",
        "addressId":userInfo['addressId']
    }
    return data

# 获取username
def getUsername(sessionId):
    headers = getHeader("xcx.xybsyw.com")
    headers['cookie'] = f'JSESSIONID={sessionId}'
    url = urls['loadAccount']
    resp = requests.post(url=url, headers=headers).json()
    if ('成功' in resp['msg']):
        ret = resp['data']['loginer']
        log(f"username:{ret}获取成功")
        return ret
    else:
        log('获取username失败')
        exit(-1)

#发送签到请求
def Sign(sessionId, data,type):
    headers = getHeader("xcx.xybsyw.com")
    sign = get_sign_header(data)
    headers.update(sign)
    headers['cookie'] = f'JSESSIONID={sessionId}'
    url = urls[type]
    resp = requests.post(url=url, headers=headers, data=data).json()
    #log(resp)
    return resp['msg']

# 获取用户信息
def getUserInfo():
    with open('user.json', 'r', encoding='utf8') as fp:
        user = json.load(fp)
    fp.close()
    return user

if __name__ == '__main__':
    userInfo_list = getUserInfo()
    for userInfo in userInfo_list:
        sessions = login(userInfo)
        sessionId = sessions['sessionId']
        loginerId = sessions['loginerId']
        userInfo['trainId'] = getTrainID(sessionId)
        position = getPosition(sessionId, userInfo['trainId'])
        userInfo.update(position)
        getUsername(sessionId)
        sign = Sign(sessionId, sign_form(userInfo),'sign')
        if sign == 'success':
            print("签到成功")
        else:
            print(sign)
        sign = Sign(sessionId, sign_form(userInfo),'new_sign')
        if sign == 'success':
            print("重新签到成功")
        else:
            print(sign)
