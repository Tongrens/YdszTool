import urllib.parse
import urllib.request
from math import floor
from json import loads
from time import sleep
from re import search, S
from random import random
from http import cookiejar
from base64 import b64encode
from datetime import datetime
from Crypto.Cipher import AES
from requests import get, post
from urllib3 import disable_warnings
from tkinter import Tk, StringVar, Label, Entry, Button, ttk, END, Checkbutton, Frame


class Ydsz:
    def __init__(self):
        # Disable SSL warnings
        disable_warnings()

        # 参数
        self.username, self.password, self.shopName, self.token, self.r1_type = '', '', '', '', ''
        self.day = '2022-11-06'  # 日期
        self.starttime = 9  # 开始时间
        self.endtime = 12  # 结束时间
        self.max_site = 3  # 最多预约几小时
        self.shopNum = '1001'  # 西丽湖：1001  留仙洞：1002
        self.post_type = '羽毛球'

        self.win_box()

    def win_box(self):
        def func(event=None):
            if box1.get() == '西丽湖':
                box2['values'] = xm1
                box2.current(0)
            else:
                box2['values'] = xm2
                box2.current(0)

        def sec_run():
            flag = True
            print('开始预约')
            while True:
                try:
                    self.login()
                    break
                except Exception as e:
                    if '由于目标计算机积极拒绝，无法连接。' in str(e):
                        print('网站已关闭，正在重试...')
                        sleep(2)
                    else:
                        print('登录失败')
                        print('错误信息：', e)
                        flag = False
                        break
            if flag:
                for _ in range(2500):
                    if self.main():
                        break

        def main_run():
            if len(text1.get()) == 8:
                self.username = text1.get()
            else:
                print('学号格式错误')
                return
            if len(text2.get()) > 7:
                self.password = text2.get()
            else:
                print('密码格式错误')
                return
            tmp_time = text3.get()
            if len(tmp_time) == 10 and tmp_time[4] == '-' and tmp_time[7] == '-':
                self.day = tmp_time
            else:
                print('日期格式错误')
                return
            if int(box3.get()) > int(box4.get()):
                print('开始时间大于结束时间')
                return
            else:
                self.starttime = int(box3.get())
                self.endtime = int(box4.get())
            self.max_site = int(box5.get())
            if value1.get() == '西丽湖':
                self.shopNum = '1001'
            elif value1.get() == '留仙洞':
                self.shopNum = '1002'
            self.post_type = value2.get()
            tmp_dict = {'羽毛球': 'ymq', '健身中心': 'jszx', '游泳': 'yy', '风雨篮球': 'fylq', '灯光篮球': 'dglq',
                        '网球': 'wq', '体能中心': 'tnzx'}
            if self.shopNum == '1001':
                self.shopName = 'xlh' + tmp_dict[self.post_type]
                self.post_type = '西丽湖' + self.post_type
            elif self.shopNum == '1002':
                self.shopName = 'lxd' + tmp_dict[self.post_type]
                self.post_type = '留仙洞' + self.post_type
            try:
                if self.r1_type.get() == 'F':
                    try:
                        self.login()
                        win.update()
                        win.destroy()
                        self.main()
                    except Exception as e:
                        if '由于目标计算机积极拒绝，无法连接。' in str(e):
                            print('网站已关闭，请稍后再试')
                        else:
                            print('登录失败')
                            print('错误信息：', e)
                else:
                    text4_time = text4.get()
                    if len(text4_time) == 10 and text4_time[4] == '-' and text4_time[7] == '-':
                        start_time = datetime.now()
                        end_time = text4.get() + ' ' + box6.get() + ':' + box7.get() + ':' + '00'
                        end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                        seconds = (end_time - start_time).total_seconds()
                        win.update()
                        win.destroy()
                        if seconds > 120:
                            print('开始倒计时，将在' + str(end_time.strftime('%Y-%m-%d %H:%M:%S')) + '两分钟前开始预约')
                            seconds -= 120
                            while seconds > 0:
                                print('距离开始预约还有' + str(int(seconds // 3600)) + '小时' + str(int(
                                    (seconds - 3600 * (seconds // 3600)) // 60)) + '分钟')
                                sleep(60)
                                seconds -= 60
                            sec_run()
                        else:
                            print('预约开始时间小于两分钟或当前时间，将直接开始预约')
                            sec_run()
                    else:
                        print('开始时间格式错误，将直接开始预约')
                        win.update()
                        win.destroy()
                        sec_run()
            except Exception as e:
                print('登录失败')
                print('错误信息：', e)

        win = Tk()
        win.title("韵动深职")
        width = 300
        height = 200
        win.geometry("{}x{}+{}+{}".format(width, height, int((win.winfo_screenwidth() - width) / 2),
                                          int((win.winfo_screenheight() - height) / 2)))
        value1, value2, value3, value4, value5 = StringVar(), StringVar(), StringVar(), StringVar(), StringVar()
        xq = ['西丽湖', '留仙洞']
        xm1 = ['羽毛球', '游泳', '体能中心']
        xm2 = ['羽毛球', '健身中心', '游泳', '风雨篮球', '灯光篮球', '网球']

        txt1 = Label(win, text="学号：")
        txt1.place(x=10, y=10)
        txt2 = Label(win, text="密码：")
        txt2.place(x=10, y=40)

        text1 = Entry(win, width=14)
        text1.place(x=50, y=10)
        text2 = Entry(win, width=14, show="*")
        text2.place(x=50, y=40)

        txt3 = Label(win, text="校区：")
        txt3.place(x=160, y=10)
        txt4 = Label(win, text="项目：")
        txt4.place(x=160, y=40)

        box1 = ttk.Combobox(master=win, state="readonly", textvariable=value1, values=xq, width=8)
        box1.set(xq[0])
        box1.place(x=200, y=10)
        box2 = ttk.Combobox(master=win, state="readonly", textvariable=value2, values=xm1, width=8)
        box2.set(xm1[0])
        box2.place(x=200, y=40)
        box1.bind("<<ComboboxSelected>>", func)

        txt5 = Label(win, text="日期：")
        txt5.place(x=10, y=70)
        txt6 = Label(win, text="开始时间：")
        txt6.place(x=10, y=100)
        txt7 = Label(win, text="结束时间：")
        txt7.place(x=10, y=130)
        txt8 = Label(win, text="预约时长：")
        txt8.place(x=10, y=160)

        text3 = Entry(win, width=14)
        text3.insert(END, "格式:2019-08-18")
        text3.place(x=50, y=70)
        text3.bind("<Button-1>", lambda a: text3.delete(0, END))

        box3 = ttk.Combobox(master=win, state="readonly", values=[str(i) for i in range(9, 20)], width=7,
                            textvariable=value3)
        box3.set('9')
        box3.place(x=80, y=100)
        box4 = ttk.Combobox(master=win, state="readonly", values=[str(i) for i in range(10, 21)], width=7,
                            textvariable=value4)
        box4.set('10')
        box4.place(x=80, y=130)
        box5 = ttk.Combobox(master=win, state="readonly", values=[str(i) for i in range(1, 4)], width=7,
                            textvariable=value5)
        box5.set('1')
        box5.place(x=80, y=160)

        frame1 = Frame(win, width=130, height=85, highlightbackground="black", highlightthickness=1)

        self.r1_type = StringVar()
        self.r1_type.set('F')
        r1 = Checkbutton(frame1, text="定时提交预约", variable=self.r1_type, onvalue="T", offvalue="F")
        r1.place(x=15, y=0)

        text4 = Entry(frame1, width=16)
        text4.insert(END, "日期:2021-12-06")
        text4.place(x=5, y=28)
        text4.bind("<Button-1>", lambda a: text4.delete(0, END))

        box6 = ttk.Combobox(master=frame1, state="readonly", values=[str(i) for i in range(0, 23)], width=2)
        box6.set('0')
        box6.place(x=5, y=55)
        txt8 = Label(frame1, text="时")
        txt8.place(x=45, y=55)
        box7 = ttk.Combobox(master=frame1, state="readonly", values=[str(i) for i in range(0, 60)], width=2)
        box7.set('0')
        box7.place(x=65, y=55)
        txt9 = Label(frame1, text="分")
        txt9.place(x=105, y=55)

        frame1.place(x=160, y=68)

        btn = Button(win, text="预约", command=main_run, width=14)
        btn.place(x=170, y=158)

        win.mainloop()

    def login(self):
        class NoRedirHandler(urllib.request.HTTPRedirectHandler):
            def http_error_302(self, req, fp, code, msg, headers):
                return fp
            http_error_301 = http_error_302

        def aes_get_key(key, pwd):
            def random_string(length):
                aes_chars = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678'
                aes_chars_len = len(aes_chars)
                restr = ''
                for i in range(0, length):
                    restr += aes_chars[floor(random() * aes_chars_len)]
                return restr
            key = key[0:16].encode('utf-8')
            iv = random_string(16).encode()
            raw = random_string(64) + pwd
            text_length = len(raw)
            amount_to_pad = AES.block_size - (text_length % AES.block_size)
            if amount_to_pad == 0:
                amount_to_pad = AES.block_size
            pad = chr(amount_to_pad)
            tmp = raw + pad * amount_to_pad
            raw = tmp.encode()
            cipher = AES.new(key, AES.MODE_CBC, iv)
            return b64encode(cipher.encrypt(raw))

        # 登录请求
        login_url = 'https://authserver.szpt.edu.cn/authserver/login?service=' \
                    'https%3A%2F%2Fydsz.szpt.edu.cn%3A443%2Fcas%2Flogin'
        request = urllib.request.Request(url=login_url, method='GET')
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar.CookieJar()), NoRedirHandler)
        response = opener.open(request)
        html = response.read().decode('utf-8')
        # 获取登录参数
        lt = search('name="lt" value="(.*?)"/>', html, S).group(1)
        execution = search('name="execution" value="(.*?)"/>', html, S).group(1)
        aes_key = search('pwdDefaultEncryptSalt = "(.*?)";', html, S).group(1)
        password_aes = aes_get_key(aes_key, self.password)
        params = {'username': self.username, 'password': password_aes, 'lt': lt, 'dllt': 'userNamePasswordLogin',
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

    def main(self):
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


if __name__ == '__main__':
    run = Ydsz()
    input('程序结束，按回车键退出')
