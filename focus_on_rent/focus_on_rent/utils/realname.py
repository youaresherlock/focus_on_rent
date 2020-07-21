# coding=UTF-8
import requests
import json

def IDauth(name, id_card):

    host = 'https://idcardcert.market.alicloudapi.com'
    path = '/idCardCert'
    method = 'GET'
    appcode = '4e63f9dd9e5a4e1aaebc7d5c0662a32f'#开通服务后 买家中心-查看AppCode
    querys = 'idCard=%s&name=%s'%(id_card,name)
    bodys = {}
    url = host + path + '?' + querys
    header = {"Authorization":'APPCODE ' + appcode}
    try:
        res = requests.get(url,headers=header)
    except :
        print("URL错误")
        exit()
    httpStatusCode = res.status_code

    if(httpStatusCode == 200):
        print("正常请求计费(其他均不计费)")
        print(res.text)
        content = json.loads(res.text)
        return content

    else:
        httpReason = res.headers['X-Ca-Error-Message']
        if(httpStatusCode == 400 and httpReason == 'Invalid Param Location'):
            print("参数错误")
        elif(httpStatusCode == 400 and httpReason == 'Invalid AppCode'):
            print("AppCode错误")
        elif(httpStatusCode == 400 and httpReason == 'Invalid Url'):
            print("请求的 Method、Path 或者环境错误")
        elif(httpStatusCode == 403 and httpReason == 'Unauthorized'):
            print("服务未被授权（或URL和Path不正确）")
        elif(httpStatusCode == 403 and httpReason == 'Quota Exhausted'):
            print("套餐包次数用完")
        elif(httpStatusCode == 500 ):
            print("API网关错误")
        else:
            print("参数名错误 或 其他错误")
            print(httpStatusCode)
            print(httpReason)
