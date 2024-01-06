import requests, json

def readSetting():
    with open("settings.json", "r", encoding = "utf8") as f: return json.load(f)

def getToken(id: str):
        try:
            data = readSetting()
            url = data['global']['url']['token']

            user = data['users'][id]

            if id == user['id']:
                headers = {
                    "User-Agent":data['global']['user_agent'],
                    "Cookie":data['users'][id]['cookie']
                }

                html = requests.get(url, headers = headers).text
        
                tokenData = json.loads(html)

                return tokenData["access_token"]
            else: return None
        except Exception as e: return print(e)

class MsgAccess:
    def __init__(self, token:str):
        self.token = token

        self.url = readSetting()['global']['url']['msgbackend']
        self.userAgent = readSetting()['global']['user_agent']

    def unreadCount(self):
        try:
            target = self.url + "/services/personal/unread_count?access_token=" + self.token
            headers = {"User-Agent":self.userAgent}
            html = requests.get(target, headers=headers).text
            return json.loads(html)['unread_count']
        except: return None
    
    def listall(self, page:int, count:int):
        try:
            target = self.url + f"/services/personal/messages?access_token={self.token}&page_no={page}&count_per_page={count}"
            headers = {"User-Agent":self.userAgent}
            html = requests.get(target, headers=headers).text
            return json.loads(html)
        except: return None
    
    def readContent(self, msgid: int):
        try:
            target = self.url + f"/services/personal/messages?access_token={self.token}&message_id={msgid}"
            headers = {"User-Agent":self.userAgent}
            html = requests.get(target, headers=headers).text
            return json.loads(html)
        except: return None
    
    def fakeAlreadyRead(self, msgid:int):
        try:
            target = self.url + f"/services/personal/messages"
            payload = {"access_token": self.token, "message_id": str(msgid)}
            headers = {"User-Agent":self.userAgent}
            html = requests.put(target, headers=headers, json = payload).text
            return json.loads(html)
        except: return None