import urllib.parse
import urllib.request
from json import loads
from re import search, S
from random import choice
from http import cookiejar
from base64 import b64encode
from requests import get, post
from Cryptodome.Cipher import AES
from django.shortcuts import render
from urllib3 import disable_warnings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


def views(request):
    return render(request, 'dashboard_page.html')


@csrf_exempt
def submit(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    day = request.POST.get('date')
    starttime = int(request.POST.get('start_time', 1))
    endtime = int(request.POST.get('end_time', 1))
    max_site = int(request.POST.get('max_site', 1))
    shopnum = request.POST.get('campus')
    if not username or not password or not day or not starttime or not endtime or not max_site or not shopnum:
        return render(request, 'submit_page.html', {'sta': '请填写完整信息'})
    post_dict = {'羽毛球': 'ymq', '健身中心': 'jszx', '游泳': 'yy', '风雨篮球': 'fylq', '灯光篮球': 'dglq',
                 '网球': 'wq', '体能中心': 'tnzx'}
    post_type = request.POST.get('project', '羽毛球') if shopnum == '1001' else request.POST.get('project1', '羽毛球')
    if shopnum == '1001':
        shopname = 'xlh' + post_dict[post_type]
        post_type = '西丽湖' + post_type
    else:
        shopname = 'lxd' + post_dict[post_type]
        post_type = '留仙洞' + post_type
    try:
        token = login(username, password)
        if '需要图片验证码' in token:
            return render(request, 'submit_page.html', {'sta': token})
    except Exception as e:
        sta = str(e)
        if '远程主机强迫关闭了一个现有的连接' in sta:
            sta = '请连接校园网后重试！'
        return render(request, 'submit_page.html', {'sta': sta})
    return render(request, 'submit_page.html', {'token': token, 'shopname': shopname, 'sta': '登录成功',
                                                'post_type': post_type, 'day': day, 'starttime': starttime,
                                                'endtime': endtime, 'max_site': max_site, 'shopnum': shopnum})


def get_info(request):
    # 获取?后的所有参数字符串拼接
    all_get = ''
    for i in request.GET:
        all_get += i + '=' + request.GET[i] + '&'
    return render(request, 'info_page.html', {'all_get': all_get[:-1]})


def post_info(request):
    disable_warnings()
    token = request.GET.get('token')
    shopname = request.GET.get('shopname')
    post_type = request.GET.get('post_type')
    day = request.GET.get('day')
    starttime = int(request.GET.get('starttime', 1))
    endtime = int(request.GET.get('endtime', 1))
    max_site = int(request.GET.get('max_site', 1))
    shopnum = request.GET.get('shopnum')
    if not token or not day or not starttime or not endtime or not max_site or not shopnum:
        return JsonResponse({'sta': '请登录！'})
    headers = {'Accept': 'application/json, text/plain, */*'}
    # 生成时间列表
    timelst = []
    if starttime < endtime:
        for i in range(starttime, endtime):
            timelst.append(str(i) + ':00' if len(str(i)) > 1 else '0' + str(i) + ':00')
    else:
        return JsonResponse({'sta': '请检查时间参数'})
    # 获取卡ID和卡余额
    url_get = 'https://ydsz.szpu.edu.cn/easyserpClient/card/getCardByUser?shopNum=' + shopnum + '&token=' + token
    try:
        carddate = loads(get(url_get, headers=headers,
                             verify=False).text)['data'][0]
        cardid, cardcash = carddate['cardindex'], carddate['cardcash']
    except Exception as e:
        return JsonResponse({'sta': '获取校园卡数据失败，错误信息为：' + str(e)})
    # 构造数据
    data_post, money, num = [], 0, 0
    url_get = 'https://ydsz.szpu.edu.cn/easyserpClient/datediscount/getPlaceInfoByShortNameDiscount?shopNum=' + \
              shopnum + '&dateymd=' + day + '&shortName=' + shopname + '&token=' + token
    try:
        data = loads(get(url_get, headers=headers, verify=False).text)['data']['placeArray']
    except Exception as e:
        return JsonResponse({'sta': '获取场地信息失败，错误信息为：' + str(e)})
    for i in data:
        for j in i['projectInfo']:
            if j['state'] == 1 and j['starttime'] in timelst and num < max_site:
                if j['money'] + money > cardcash:
                    break
                timelst.remove(j['starttime'])
                data_post.append({"day": day, "startTime": j["starttime"], "endTime": j["endtime"],
                                  "placeShortName": i["projectName"]["shortname"],
                                  "name": i["projectName"]["name"]})
                money += j['money']
                num += 1
    if not data_post:
        return JsonResponse({'sta': '没有可用场地/余额不足'})
    # 提交数据
    url_post = 'https://ydsz.szpu.edu.cn/easyserpClient/place/reservationPlace'
    post_data = 'token=' + token + '&shopNum=' + shopnum + \
                '&fieldinfo=' + urllib.parse.quote(str(data_post)) + \
                '&oldTotal=' + str(int(money)) + '.00&cardPayType=0&type=' + \
                urllib.parse.quote(post_type) + '&offerId=&offerType=&total=' + \
                str(int(money)) + '.00&premerother=&cardIndex=' + cardid + '&masterCardNum=&zengzhiMoney=0'
    try:
        result = loads(post(url_post, headers=headers, verify=False, params=post_data).text)
        if result.get('msg') == 'success':
            sta = f'预定成功，共计{str(num)}个场地，{str(money)}元\n场地信息：\n'
            for i in data_post:
                sta += f"{i['name']} {i['startTime']}-{i['endTime']}\n"
            return JsonResponse({'sta': sta})
        elif result.get('msg') == 'fail':
            if '下手太晚了' in result.get('data'):
                return JsonResponse({'sta': '场地预约尚未开放'})
            else:
                return JsonResponse({'sta': '预定失败，错误信息为：' + result.get('data')})
        else:
            return JsonResponse({'sta': f'预定失败，错误信息为：{str(result.get("status"))} {str(result.get("error"))}'})
    except Exception as e:
        return JsonResponse({'sta': '预定失败\n错误信息：' + str(e)})


def login(username, password):
    print(username + '正在登录...')
    # 登录请求
    login_url = 'https://authserver.szpt.edu.cn/authserver/login?service=' \
                'https%3A%2F%2Fydsz.szpu.edu.cn%3A443%2Fcas%2Flogin'
    request = urllib.request.Request(url=login_url, method='GET')
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar.CookieJar()), NoRedirHandler)
    html = opener.open(request).read().decode('utf-8')
    # 判断是否需要captcha
    check_url = 'https://authserver.szpt.edu.cn/authserver/checkNeedCaptcha.htl?username=' + username
    if loads(opener.open(check_url).read().decode('utf-8'))['isNeed']:
        return '需要图片验证码，请前往登录页面登录后重试！\nhttps://authserver.szpt.edu.cn/authserver/login?service=' \
               'https%3A%2F%2Fydsz.szpu.edu.cn%3A443%2Fcas%2Flogin'
    # 获取登录参数
    execution = search('name="execution" value="(.*?)"', html, S).group(1)
    aes_key = search('pwdEncryptSalt" value="(.*?)"/>', html, S).group(1)[:16].encode('utf-8')
    aes_chars = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678'
    iv = ''.join([choice(aes_chars) for _ in range(16)]).encode()
    raw = ''.join([choice(aes_chars) for _ in range(64)]) + password
    amount_to_pad = AES.block_size - (len(raw) % AES.block_size)
    if amount_to_pad == 0:
        amount_to_pad = AES.block_size
    raw = (raw + chr(amount_to_pad) * amount_to_pad).encode()
    password_aes = b64encode(AES.new(aes_key, AES.MODE_CBC, iv).encrypt(raw))
    params = {'username': username, 'password': str(password_aes)[2:-1], 'captcha': '',
              '_eventId': 'submit', 'cllt': 'userNameLogin', 'dllt': 'generalLogin', 'lt': '',
              'execution': execution}
    # 获取重定向
    result = urllib.request.Request(url=login_url, method='POST',
                                    data=urllib.parse.urlencode(params).encode(encoding='UTF-8'))
    login_url = opener.open(result).headers['Location']
    login_url = opener.open(urllib.request.Request(url=login_url, method='GET')).headers['Location']
    login_url = opener.open(urllib.request.Request(url=login_url, method='GET')).headers['Location']
    # 获取openid
    end_url = 'https://ydsz.szpu.edu.cn/easyserpClient/memberLogin/logined3?' + \
              login_url[62:] + '&clubMemberCode=szzyjsxy0'
    result = urllib.request.Request(url=end_url, method='GET')
    token = loads(opener.open(result, timeout=5).read().decode('utf-8'))['data']['infa']['openid']
    print(username + '登录成功')
    return token


class NoRedirHandler(urllib.request.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        return fp

    http_error_301 = http_error_302
