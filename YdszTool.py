import urllib.parse
import urllib.request
from json import loads
from time import sleep
from re import search, S
from random import choice
from http import cookiejar
from base64 import b64encode
from datetime import datetime
from requests import get, post
from Cryptodome.Cipher import AES
from urllib3 import disable_warnings
from tkinter import Tk, StringVar, Label, Entry, Button, ttk


class Ydsz:
    def __init__(self, iusername, ipassword, iday, istarttime, iendtime, imax_site, ishopnum, ipost_type):
        # Disable SSL warnings
        disable_warnings()

        # 参数
        self.token, self.shopName = '', ''
        self.username, self.password = iusername, ipassword
        self.day, self.starttime, self.endtime, self.max_site = iday, istarttime, iendtime, imax_site
        self.shopNum, self.post_type = ishopnum, ipost_type
        self.post_dict = {'羽毛球': 'ymq', '健身中心': 'jszx', '游泳': 'yy', '风雨篮球': 'fylq', '灯光篮球': 'dglq',
                          '网球': 'wq', '体能中心': 'tnzx'}

    def login(self):
        class NoRedirHandler(urllib.request.HTTPRedirectHandler):
            def http_error_302(self, req, fp, code, msg, headers):
                return fp
            http_error_301 = http_error_302

        print('正在登录...')
        # 登录请求
        login_url = 'https://authserver.szpt.edu.cn/authserver/login?service=' \
                    'https%3A%2F%2Fydsz.szpt.edu.cn%3A443%2Fcas%2Flogin'
        request = urllib.request.Request(url=login_url, method='GET')
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar.CookieJar()), NoRedirHandler)
        html = opener.open(request).read().decode('utf-8')
        # 获取登录参数
        lt = search('name="lt" value="(.*?)"/>', html, S).group(1)
        execution = search('name="execution" value="(.*?)"/>', html, S).group(1)
        aes_key = search('pwdDefaultEncryptSalt = "(.*?)";', html, S).group(1)[:16].encode('utf-8')
        aes_chars = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678'
        iv = ''.join([choice(aes_chars) for _ in range(16)]).encode()
        raw = ''.join([choice(aes_chars) for _ in range(64)]) + self.password
        amount_to_pad = AES.block_size - (len(raw) % AES.block_size)
        if amount_to_pad == 0:
            amount_to_pad = AES.block_size
        raw = (raw + chr(amount_to_pad) * amount_to_pad).encode()
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        password_aes = b64encode(cipher.encrypt(raw))
        params = {'username': self.username, 'password': password_aes, 'lt': lt,
                  'dllt': 'userNamePasswordLogin',
                  'execution': execution, '_eventId': 'submit', 'rmShown': '1'}
        # 获取重定向
        result = urllib.request.Request(url=login_url, method='POST',
                                        data=urllib.parse.urlencode(params).encode(encoding='UTF-8'))
        login_url = search('href="(.*?)"', opener.open(result).read().decode('utf-8'), S).group(1)
        result = urllib.request.Request(url=login_url, method='GET')
        login_url = opener.open(result).headers['Location']
        result = urllib.request.Request(url=login_url, method='GET')
        login_url = opener.open(result).headers['Location']
        # 获取openid
        end_url = 'https://ydsz.szpt.edu.cn/easyserpClient/memberLogin/logined3?' + login_url[62:] + '&clubMemberCode' \
                                                                                                     '=szzyjsxy0'
        result = urllib.request.Request(url=end_url, method='GET')
        self.token = loads(opener.open(result).read().decode('utf-8'))['data']['infa']['openid']
        print('登录成功')

    def send_info(self):
        # 生成时间列表
        timelst = []
        if self.starttime < self.endtime:
            for i in range(self.starttime, self.endtime):
                if len(str(i)) < 2:
                    i = '0' + str(i)
                else:
                    i = str(i)
                timelst.append(i + ':00')
        else:
            print('请检查时间参数')
            return 2
        # 获取卡ID和卡余额
        url_get = 'https://ydsz.szpt.edu.cn/easyserpClient/card/getCardByUser?shopNum=' + \
                  self.shopNum + '&token=' + self.token
        try:
            carddate = loads(get(url_get, headers={'Accept': 'application/json, text/plain, */*'}, verify=False)
                             .text)['data'][0]
            cardid = carddate['cardindex']
            cardcash = carddate['cardcash']
        except Exception as e:
            print('获取校园卡数据失败，错误信息为：' + str(e))
            return 2
        # 构造数据
        data_post = []
        money = 0
        num = 0
        url_get = 'https://ydsz.szpt.edu.cn/easyserpClient/datediscount/getPlaceInfoByShortNameDiscount?shopNum=' + \
                  self.shopNum + '&dateymd=' + self.day + '&shortName=' + self.shopName + '&token=' + self.token
        try:
            data = loads(get(url_get, headers={'Accept': 'application/json, text/plain, */*'},
                             verify=False).text)['data']['placeArray']
        except Exception as e:
            print('获取场地信息失败，错误信息为：' + str(e))
            return 2
        for i in data:
            for j in i['projectInfo']:
                if j['state'] == 1 and j['starttime'] in timelst and num < self.max_site:
                    if j['money'] + money > cardcash:
                        break
                    timelst.remove(j['starttime'])
                    data_post.append({"day": self.day, "startTime": j["starttime"], "endTime": j["endtime"],
                                      "placeShortName": i["projectName"]["shortname"],
                                      "name": i["projectName"]["name"]})
                    money += j['money']
                    num += 1
        if not data_post:
            print('没有可用场地')
            return
        # 提交数据
        url_post = 'https://ydsz.szpt.edu.cn/easyserpClient/place/reservationPlace'
        post_data = 'token=' + self.token + '&shopNum=' + self.shopNum + '&fieldinfo=' + urllib.parse.quote(str(
            data_post)) + '&oldTotal=' + str(int(money)) + '.00&cardPayType=0&type=' + urllib.parse.quote(
            self.post_type) + '&offerId=&offerType=&total=' + str(int(money)) + '.00&premerother=&cardIndex=' + \
            cardid + '&masterCardNum=&zengzhiMoney=0'
        try:
            result = loads(post(url_post, headers={'Accept': 'application/json, text/plain, */*'}, verify=False,
                                params=post_data).text)
            if result.get('msg') == 'success':
                print(datetime.now().strftime('%H:%M:%S') + '预定成功，共计' + str(num) + '个场地，' + str(money) + '元')
                print('场地信息：')
                for i in data_post:
                    print(i['name'] + ' ' + i['startTime'] + '-' + i['endTime'])
                return 1
            elif result.get('msg') == 'fail':
                print('预定失败，错误信息为：' + result.get('data'))
                return 2
            else:
                print('预定失败，错误信息为：' + str(result.get('status'), str(result.get('error'))))
                return 2
        except Exception as e:
            print('预定失败')
            print('错误信息：' + str(e))
            return 2

    def run(self):
        flag = True
        print('开始预约' + self.day[:4] + '年' + self.day[5:7] + '月' + self.day[8:] + '日' + str(self.starttime) +
              '-' + str(self.endtime) + '点' + self.post_type + str(self.max_site) + '小时场地')
        while True:
            try:
                self.login()
                break
            except Exception as e:
                if '由于目标计算机积极拒绝，无法连接。' in str(e):
                    print('一网通已关闭，正在重试...')
                    sleep(2)
                elif '502' in str(e):
                    print('韵动深职寄了，正在重试...')
                    sleep(2)
                else:
                    print('登录失败')
                    print('错误信息：', e)
                    flag = False
                    break
        while flag:
            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            for _ in range(100):
                if self.send_info():
                    flag = False
                    break

    def win_box(self):
        def func(_):
            if xq_inp.get() == '西丽湖':
                xm_inp['values'] = xm1
                xm_inp.current(0)
            else:
                xm_inp['values'] = xm2
                xm_inp.current(0)

        def win_run():
            if len(xh_inp.get()) == 8:
                self.username = xh_inp.get()
            else:
                print('学号格式错误')
                return
            if len(mm_inp.get()) > 7:
                self.password = mm_inp.get()
            else:
                print('密码格式错误')
                return
            tmp_time = rq_inp.get()
            if len(tmp_time) == 10 and tmp_time[4] == '-' and tmp_time[7] == '-':
                self.day = tmp_time
            else:
                print('日期格式错误')
                return
            if int(kssj_inp.get()) > int(jssj_inp.get()):
                print('开始时间大于结束时间')
                return
            else:
                self.starttime = int(kssj_inp.get())
                self.endtime = int(jssj_inp.get())
            if datetime.strptime(self.day + ' ' + str(self.starttime) + ':00:00', '%Y-%m-%d %H:%M:%S') < \
                    datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'):
                print('开始时间小于当前时间')
                return
            self.max_site = int(yysc_inp.get())
            if value1.get() == '西丽湖':
                self.shopNum = '1001'
            elif value1.get() == '留仙洞':
                self.shopNum = '1002'
            self.post_type = value2.get()
            if self.shopNum == '1001':
                self.shopName = 'xlh' + self.post_dict[self.post_type]
                self.post_type = '西丽湖' + self.post_type
            elif self.shopNum == '1002':
                self.shopName = 'lxd' + self.post_dict[self.post_type]
                self.post_type = '留仙洞' + self.post_type
            try:
                win.update()
                win.destroy()
                self.run()
            except Exception as e:
                print('订场失败')
                print('错误信息：', e)

        win = Tk()
        win.title("韵动深职")
        width, height = 420, 130
        win.geometry("{}x{}+{}+{}".format(width, height, int((win.winfo_screenwidth() - width) / 2),
                                          int((win.winfo_screenheight() - height) / 2)))
        value1, value2, value3, value4, value5 = StringVar(), StringVar(), StringVar(), StringVar(), StringVar()
        xq = ['西丽湖', '留仙洞']
        xm1 = ['羽毛球', '游泳', '体能中心']
        xm2 = ['羽毛球', '健身中心', '游泳', '风雨篮球', '灯光篮球', '网球']

        xh_text = Label(win, text="学号：")
        xh_text.place(x=10, y=10)
        mm_text = Label(win, text="密码：")
        mm_text.place(x=10, y=50)
        rq_text = Label(win, text="日期：")
        rq_text.place(x=10, y=90)

        xh_inp = Entry(win, width=11)
        xh_inp.place(x=50, y=10)
        mm_inp = Entry(win, width=11, show="*")
        mm_inp.place(x=50, y=50)
        rq_inp = Entry(win, width=11)
        rq_inp.place(x=50, y=90)

        kssj_text = Label(win, text="开始时间：")
        kssj_text.place(x=140, y=10)
        jssj_text = Label(win, text="结束时间：")
        jssj_text.place(x=140, y=50)
        yysc_text = Label(win, text="预约时长：")
        yysc_text.place(x=140, y=90)

        kssj_inp = ttk.Combobox(master=win, state="readonly", values=[str(i) for i in range(9, 20)], width=7,
                                textvariable=value3)
        kssj_inp.set('9')
        kssj_inp.place(x=205, y=10)
        jssj_inp = ttk.Combobox(master=win, state="readonly", values=[str(i) for i in range(10, 21)], width=7,
                                textvariable=value4)
        jssj_inp.set('10')
        jssj_inp.place(x=205, y=50)
        yysc_inp = ttk.Combobox(master=win, state="readonly", values=[str(i) for i in range(1, 4)], width=7,
                                textvariable=value5)
        yysc_inp.set('1')
        yysc_inp.place(x=205, y=90)

        xq_test = Label(win, text="校区：")
        xq_test.place(x=285, y=10)
        xm_test = Label(win, text="项目：")
        xm_test.place(x=285, y=50)

        xq_inp = ttk.Combobox(master=win, state="readonly", textvariable=value1, values=xq, width=8)
        xq_inp.set(xq[0])
        xq_inp.place(x=325, y=10)
        xm_inp = ttk.Combobox(master=win, state="readonly", textvariable=value2, values=xm1, width=8)
        xm_inp.set(xm1[0])
        xm_inp.place(x=325, y=50)
        xq_inp.bind("<<ComboboxSelected>>", func)

        yy_btn = Button(win, text="预约", command=win_run, width=14)
        yy_btn.place(x=292, y=85)

        print('请输入信息以预约')
        print('!!!请注意日期格式为\"2022-11-29\"!!!')

        win.mainloop()

    def linux_run(self):
        if self.shopNum == '1001':
            self.shopName = 'xlh' + self.post_dict[self.post_type]
            self.post_type = '西丽湖' + self.post_type
        else:
            self.shopName = 'lxd' + self.post_dict[self.post_type]
            self.post_type = '留仙洞' + self.post_type
        if len(self.day) != 10 or self.day[4] != '-' or self.day[7] != '-':
            print('日期格式错误')
            return
        if self.starttime > self.endtime:
            print('开始时间大于结束时间')
            return
        if datetime.strptime(self.day + ' ' + str(self.starttime) + ':00:00', '%Y-%m-%d %H:%M:%S') < \
                datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'):
            print('开始时间小于当前时间')
            return
        if self.max_site > 3:
            print('最多预约3小时')
            return
        try:
            self.run()
        except Exception as e:
            print('订场失败')
            print('错误信息：', e)


if __name__ == '__main__':
    username = ''   # 一网通账号
    password = ''   # 一网通密码
    day = '2023-02-28'  # 预约日期
    starttime = 9  # 开始时间
    endtime = 12  # 结束时间
    max_site = 3  # 最多预约几小时(最多3小时)
    shopNum = '1001'  # 西丽湖：1001  留仙洞：1002
    post_type = '羽毛球'  # 羽毛球, 健身中心, 游泳, 风雨篮球, 灯光篮球, 网球, 体能中心
    run_type = 1  # 1：Windows端  2：Linux端
    main = Ydsz(username, password, day, starttime, endtime, max_site, shopNum, post_type)
    main.win_box() if run_type == 1 else main.linux_run()
    input('程序结束，按回车键退出')
