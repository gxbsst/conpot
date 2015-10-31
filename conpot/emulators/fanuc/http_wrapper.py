#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name: 对http访问的封装
#
# Author: Zhen Wang
#
# Created: 2014-09-09
#
# Modification History:
#     2014-09-09 - [Zhen Wang] - Modified from the version by qianlifeng.
#                                Use random User Agient in case network shield.
#-------------------------------------------------------------------------------

import base64
import urllib
import urllib2
import sys
import random

class HttpRequestWrapper:
    """
    网页请求增强类
    HttpRequestWrapper('http://xxx.com',data=dict, type='POST', auth='base',user='xxx', password='xxx')
    """

    def __init__(self, url, data=None, method='GET', auth=None, user=None, password=None, cookie = None, **header):
        """
        url: 请求的url，不能为空
        date: 需要post的内容，必须是字典
        method: Get 或者 Post，默认为Get
        auth: 'base' 或者 'cookie'
        user: 用于base认证的用户名
        password: 用于base认证的密码
        cookie: 请求附带的cookie，一般用于登录后的认证
        其他头信息:
        e.g. referer='www.sina.com.cn'
        """

        self.url = url
        self.data = data
        self.method = method
        self.auth = auth
        self.user = user
        self.password = password
        self.cookie = cookie

        if 'referer' in header:
                self.referer = header[referer]
        else:
                self.referer = None

        if 'user-agent' in header:
                self.user_agent = header[user-agent]
        else:
                self.user_agent = self.__getRandomUserAgent()

        self.__SetupRequest()
        self.__SendRequest()

    def __getRandomUserAgent(self):
        #the default user_agent_list composes chrome,I E,firefox,Mozilla,opera,netscape
        #for more user agent strings,you can find it in http://www.useragentstring.com/pages/useragentstring.php
        user_agent_list = [\
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"\
            "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",\
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",\
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",\
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",\
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",\
            "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",\
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",\
            "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",\
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",\
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",\
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",\
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",\
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",\
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",\
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",\
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",\
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
        ]

        user_agent = random.choice(user_agent_list)

        return user_agent
    
    def __SetupRequest(self):

        if self.url is None or self.url == '':
            raise 'url 不能为空!'

        #访问方式设置
        if self.method.lower() == 'post':
            self.Req = urllib2.Request(self.url, urllib.urlencode(self.data))

        elif self.method.lower() == 'get':
            if self.data == None:
                self.Req = urllib2.Request(self.url)
        else:
            self.Req = urllib2.Request(self.url + '?' + urllib.urlencode(self.data))

        #设置认证信息
        if self.auth == 'base':
            if self.user == None or self.password == None:
                raise 'The user or password was not given!'
            else:
                auth_info = base64.encodestring(self.user + ':' + self.password).replace('\n','')
                auth_info = 'Basic ' + auth_info
                self.Req.add_header("Authorization", auth_info)

        elif self.auth == 'cookie':
            if self.cookie == None:
                raise 'The cookie was not given!'
            else:
                self.Req.add_header("Cookie", self.cookie)

        if self.referer:
            self.Req.add_header('referer', self.referer)
        if self.user_agent:
            self.Req.add_header('user-agent', self.user_agent)


    def __SendRequest(self):

        try:
            self.Response = urllib2.urlopen(self.Req)
            self.source = self.Response.read()
            self.code = self.Response.getcode()
            # print (dir(self.Response.info()))
            # print ('*'*50)
            # print (self.Response.info())
            # print ('*'*50)
            # print (type(self.Response.info()))
            self.head_dict = self.Response.info().dict
            self.Response.close()
        except:
            print "Error: HttpWrapper=>_SendRequest ", sys.exc_info()[1]

    def Refresh(self):
        self.__SetupRequest()
        self.__SendRequest()

    def GetResponseCode(self):
        """
        得到服务器返回的状态码(200表示成功,404网页不存在)
        """
        return self.code

    def GetSource(self):
        """
        得到网页源代码，需要解码后在使用
        """
        if "source" in dir(self):
            return self.source
        return u''

    def GetHeaderInfo(self):
        """
        u'得到响应头信息'
        """
        return self.head_dict

    def GetCookie(self):
        """
        得到服务器返回的Cookie，一般用于登录后续操作
        """
        if 'set-cookie' in self.head_dict:
            return self.head_dict['set-cookie']
        else:
            return None

    def GetContentType(self):
        """
        得到返回类型
        """
        if 'content-type' in self.head_dict:
            return self.head_dict['content-type']
        else:
            return None

    def GetCharset(self):
        """
        尝试得到网页的编码
        如果得不到返回None
        """
        contentType = self.GetContentType()
        if contentType is not None:
            index = contentType.find("charset")
            if index > 0:
                return contentType[index+8:]
            return None

    def GetExpiresTime(self):
        """
        得到网页过期时间
        """
        if 'expires' in self.head_dict:
            return self.head_dict['expires']
        else:
            return None

    def GetServerName(self):
        """
        得到服务器名字
        """
        if 'server' in self.head_dict:
            return self.head_dict['server']
        else:
            return None

__all__ = [HttpRequestWrapper,]

if __name__ == '__main__':
    b = HttpRequestWrapper("http://news.163.com/latest/")
    print b.GetSource()
    b.Refresh()
    print(b.GetSource())
