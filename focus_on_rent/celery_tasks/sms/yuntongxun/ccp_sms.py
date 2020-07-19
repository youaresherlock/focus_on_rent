# -*- coding:utf-8 -*-

import ssl

import sys
# print(sys.path)

# sys.path ====> []

# sys.path.insert(0, '../../../')

# from meiduo_mall.libs.yuntongxun.CCPRestSDK import REST
from celery_tasks.sms.yuntongxun.CCPRestSDK import REST

# 全局取消证书验证，就是解决部分172001：网络错误的问题
ssl._create_default_https_context = ssl._create_unverified_context


# 说明：主账号，登陆云通讯网站后，可在"控制台-应用"中看到开发者主账号ACCOUNT SID
_accountSid = '8aaf0708723b53c901723c6b157400c9'

# 说明：主账号Token，登陆云通讯网站后，可在控制台-应用中看到开发者主账号AUTH TOKEN
_accountToken = 'e7dc771b5d2447eebf9e0727e49a5268'

# 请使用管理控制台首页的APPID或自己创建应用的APPID
_appId = '8aaf070872d9c1450172fa67ce690c7e'

# 说明：请求地址，生产环境配置成app.cloopen.com
# 如果总是报172001：网络错误，可以尝试把服务器改成正式的服务器，测试服务器可能不太稳定
# _serverIP = 'sandboxapp.cloopen.com'
_serverIP = 'app.cloopen.com'

# 说明：请求端口 ，生产环境为8883
_serverPort = "8883"

# 说明：REST API版本号保持不变
_softVersion = '2013-12-26'


class CCP(object):
    """发送短信的辅助类"""

    def __new__(cls, *args, **kwargs):
        # 判断是否存在类属性_instance，_instance是类CCP的唯一对象，即单例
        if not hasattr(CCP, "_instance"):
            cls._instance = super(CCP, cls).__new__(cls, *args, **kwargs)
            cls._instance.rest = REST(_serverIP, _serverPort, _softVersion)
            cls._instance.rest.setAccount(_accountSid, _accountToken)
            cls._instance.rest.setAppId(_appId)
        return cls._instance


    def send_template_sms(self, to, datas, temp_id):
        # 模拟网络延迟：这一步仅仅是为了放大网络延迟的效果，
        # import time
        # time.sleep(15)

        """发送模板短信"""
        # @param to 手机号码
        # @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
        # @param temp_id 模板Id
        result = self.rest.sendTemplateSMS(to, datas, temp_id)
        # 我们可以通过手动的输出结果信息，来查看成功和失败的具体返回的信息
        print(result)

        # 如果云通讯发送短信成功，返回的字典数据result中statuCode字段的值为"000000"
        if result.get("statusCode") == "000000":
            # 返回0 表示发送短信成功
            return 0
        else:
            # 返回-1 表示发送失败
            return -1


# if __name__ == '__main__':
#     # 注意： 测试的短信模板编号为1
#     # CCP().send_template_sms('测试的手机号码', ['短信验证码', '过期时间'], '模板ID')
#     CCP().send_template_sms('15619368905', ['777777', 4], 1)
