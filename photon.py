# coding: UTF-8
from collections import OrderedDict
import urllib
import urllib2
import cookielib
from bs4 import BeautifulSoup
import hmac
import hashlib
import base64
import uuid
import json

class NoRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        infourl = urllib.addinfourl(fp, headers, req.get_full_url())
        infourl.status = code
        infourl.code = code
        return infourl
    http_error_300 = http_error_302
    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302

class LobiAPI:
	UserAgent 	= "photon-python"
	platform 	= "android"
	DeviceUUID 	= ""
	Token 		= ""
	def __init__(self):
		opener = urllib2.build_opener(NoRedirectHandler(), urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
		urllib2.install_opener(opener)

	def GetSpell(self, mail, password):
		header = {
			"User-Agent": "Mozilla/5.0 (Linux; Android 5.1; Google Nexus 10 - 5.1.0 - API 22 - 2560x1600 Build/LMY47D) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/39.0.0.0 Safari/537.36 Lobi/8.10.3",
			"Host": "lobi.co",
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
			"Accept-Language": "ja-JP,en-US;q=0.8",
			"X-Requested-With": "com.kayac.nakamap"
		}
		source1 = urllib2.urlopen(urllib2.Request("https://lobi.co/inapp/signin/password?webview=1", None, header)).read()
		soup = BeautifulSoup(source1, "html.parser")
		csrf_token = soup.find('input', {'name':'csrf_token'})['value']
		header["Referer"] = "https://lobi.co/inapp/signin/password?webview=1"
		header["Origin"]  = "https://lobi.co"
		post_data = {
			"csrf_token": csrf_token,
			"email": mail,
			"password": password
		}
		res = urllib2.urlopen(urllib2.Request("https://lobi.co/inapp/signin/password", urllib.urlencode(post_data), header))
		res_headers = res.info()
		location = res_headers.getheader("Location")
		key = "nakamapbridge://signin?spell="
		if location != None and key in location and len(location) > len(key):
			return location[len(key):]
		return ""

	def GetToken(self, device_uuid, spell):
		sig = base64.b64encode(hmac.new("db6db1788023ce4703eecf6aa33f5fcde35a458c", spell, hashlib.sha1).digest())
		header = {
			"User-Agent": self.UserAgent,
			"Host": "api.lobi.co"
		}
		post_data = {
			"device_uuid": device_uuid,
			"sig": sig,
			"spell": spell,
			"lang": "ja"
		}
		source = urllib2.urlopen(urllib2.Request("https://api.lobi.co/1/signin_confirmation", urllib.urlencode(post_data), header)).read()
		result = json.loads(source)
		return result["token"]
		
	def Login(self, mail, password):
		spell = self.GetSpell(mail, password)
		if spell == None or spell == "":
			return false
		self.DeviceUUID = uuid.uuid4()
		self.Token = self.GetToken(self.DeviceUUID, spell)
		return self.Token != None and len(self.Token) > 0

	def GetMe(self):
		return self.GET(1, "me")

	def GetContacts(self, user_id = None):
		if user_id == None:
			return self.GET(3, "me/contacts")
		result = []
		data = {}
		while True:
			res = self.GET(1, "user/{user_id}/contacts".format(user_id=user_id), data)
			if res == None or res.get("users") == None or len(res["users"]) == 0:
				break
			result.extend(res["users"])
			if res.get("next_cursor") == None or res["next_cursor"] == -1 or res["next_cursor"] == 0:
				break
			data["cursor"] = res["next_cursor"]
		return result

	def GetFollowers(self, user_id = None):
		if user_id == None:
			return self.GET(2, "me/followers")
		result = []
		data = {}
		while True:
			res = self.GET(1, "user/{user_id}/followers".format(user_id=user_id), data)
			if res == None or res.get("users") == None or len(res["users"]) == 0:
				break
			result.extend(res["users"])
			if res.get("next_cursor") == None or res["next_cursor"] == -1 or res["next_cursor"] == 0:
				break
			data["cursor"] = res["next_cursor"]
		return result

	def GetUser(self, user_id):
		return self.GET(1, "user/{user_id}".format(user_id=user_id), { "fields": "is_blocked" })

	def GetBlockingUsersAll(self):
		result = []
		data = {}
		while True:
			res = self.GET(2, "me/blocking_users", data)
			if res == None or res.get("users") == None or len(res["users"]) == 0:
				break
			result.extend(res["users"])
			if res.get("next_cursor") == None or res["next_cursor"] == -1 or res["next_cursor"] == 0:
				break
			data["cursor"] = res["next_cursor"]
		return result

	def GetInvited(self):
		return self.GET(1, "groups/invited")

	def GetPublicGroupAll(self, uesr_id = None):
		result = []
		if user_id == None:
			page = 1
			while True:
				res = self.GET(1, "public_groups", {
					"with_archived": "true",
					"count": 1000,
					"page": page
				})
				page += 1
				if res == None or len(res) == 0 or res[0] == None or res[0].get("items") == None or len(res[0]["items"]) == 0:
					break
				result.extend(res[0]["items"])
				if len(res[0]["items"]) < 1000:
					break
		else:
			result = []
			data = { "with_archived": "true" }
			while True:
				res = self.GET(1, "user/{user_id}/visible_groups".format(user_id=user_id), data)
				if res == None or res.get("public_groups") == None or len(res["public_groups"]) == 0:
					break
				result.extend(res["public_groups"])
				if res.get("next_cursor") == None or res["next_cursor"] == -1 or res["next_cursor"] == 0:
					break
				data["cursor"] = res["next_cursor"]
		return result

	def GetPublicGroup(self, page, count = 1000):
		res = self.GET(1, "public_groups", {
			"with_archived": "true",
			"count": count,
			"page": page
		})
		if res == None or len(res) == 0 or res[0] == None or res[0].get("items") == None or len(res[0]["items"]) == 0:
			return []
		return res[0]["items"]

	def GetPrivateGroupAll(self):
		result = []
		page = 1
		while True:
			res = self.GET(3, "groups", {
				"with_archived": "true",
				"count": 1000,
				"page": page
			})
			page += 1
			if res == None or len(res) == 0 or res[0] == None or res[0].get("items") == None or len(res[0]["items"]) == 0:
				break
			result.extend(res[0]["items"])
			if len(res[0]["items"]) < 1000:
				break
		return result

	def GetPrivateGroup(self, page, count = 1000):
		res = self.GET(3, "groups", {
			"with_archived": "true",
			"count": count,
			"page": page
		})
		if res == None or len(res) == 0 or res[0] == None or res[0].get("items") == None or len(res[0]["items"]) == 0:
			return []
		return res[0]["items"]

	def GetGroup(self, group_id):
		return self.GET(2, "group/{group_id}".format(group_id=group_id), {
			"members_count": 1,
			"fields": "subleaders"
		})

	def GetGroupLeader(self, group_id):
		return self.GET(2, "group/{group_id}/members".format(group_id=group_id), {
			"members_count": 1,
			"fields": "owner"
		}).get("owner")

	def GetGroupSubleaders(self, group_id):
		res = self.GET(2, "group/{group_id}/members".format(group_id=group_id), {
			"members_count": 1,
			"fields": "owner"
		}).get("subleaders")
		if res == None:
			return []
		return res

	def GetGroupMembersAll(self, group_id):
		result = []
		data = { "members_count": "1000" }
		while True:
			res = self.GET(1, "group/{group_id}/members".format(group_id=group_id), data)
			if res == None or res.get("members") == None or len(res["members"]) == 0:
				break
			result.extend(res["members"])
			if res.get("next_cursor") == None or res["next_cursor"] == -1 or res["next_cursor"] == 0:
				break
			data["cursor"] = res["next_cursor"]
		return result

	def GetThreads(self, group_id, count = 20, older_than = None, newer_than = None):
		data = { "count": count }
		if older_than != None and older_than != "":
			data["older_than"] = older_than
		if newer_than != None and newer_than != "":
			data["newer_than"] = newer_than
		return self.GET(2, "group/{group_id}/chats".format(group_id=group_id), data)

	def GetRepliesAll(self, group_id, chat_id):
		return self.GET(1, "group/{group_id}/chats/replies".format(group_id=group_id), { "to": chat_id })

	def GetPokesAll(self, group_id, chat_id):
		result = []
		data = { "id": chat_id }
		while True:
			res = self.GET(2, "group/{group_id}/chats/pokes".forma(group_id=group_id), data)
			if res == None or res.get("users") == None or len(res["users"]) == 0:
				break
			result.extend(res["users"])
			if res.get("next_cursor") == None or res["next_cursor"] == -1 or res["next_cursor"] == 0:
				break
			data["cursor"] = res["next_cursor"]
		return result

	def GetNotifications(self, count = 20, cursor = None):
		data = { "count": count }
		if cursor != None and cursor != "":
			data["last_cursor"] = cursor
		return self.GET(2, "info/nontifications", data)

	def GET(self, version, request_url, query = {}):
		url = "https://api.lobi.co/{version}/{request_url}?platform={platform}&lang=ja&token={token}&{query}".format(version=version, request_url=request_url, platform=self.platform, token=self.Token, query=urllib.urlencode(query))
		header = {
			"User-Agent": self.UserAgent,
			"Host": "api.lobi.co"
		}
		return json.loads(urllib2.urlopen(urllib2.Request(url, None, header)).read())

	def POST(self, version, request_url, query = {}):
		url = "https://api.lobi.co/{version}/{request_url}".format(version=version, request_url=request_url)
		header = {
			"User-Agent": self.UserAgent,
			"Host": "api.lobi.co"
		}
		data = {
			"lang": "ja",
			"token": self.Token,
			"platform": self.platform
		}.extend(query)
		return json.loads(urllib2.urlopen(urllib2.Request(url, data, header)).read())

api = LobiAPI()
if api.Login("メールアドレス", "パスワード"):
	me = api.GetMe()
	print "####################   " + me["name"] + "   ####################"
	print me["description"]
	me_contacts = api.GetContacts()

