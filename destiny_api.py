import requests
import json

class DestinyAPI:
	def __init__(self, apiKey):
		self.apiKey = apiKey
		self.headers = {'X-Api-Key': apiKey}
		self.apiBase = 'https://www.bungie.net/Platform/Destiny/'

	def getMembershipId(self, username):
		url = self.apiBase + 'SearchDestinyPlayer/2/' + username
		r = requests.get(url, headers=self.headers)
		result = json.loads(r.content)
		return result["Response"][0]["membershipId"]

	def getCharacterIds(self, membershipId):
		url = self.apiBase + '2/Account/' + membershipId
		r = requests.get(url, headers=self.headers)
		result = json.loads(r.content)
		characters = result["Response"]["data"]["characters"]
		charIdList = [character["characterBase"]["characterId"] for character in characters]
		return charIdList

	def getCharacterActivity(self, membershipId, characterId):
		url = self.apiBase + 'Stats/ActivityHistory/2/' + membershipId + '/' + characterId + '/?mode=None'
		r = requests.get(url, headers=self.headers)
		result = json.loads(r.content)
		activities = result["Response"]["data"]["activities"]
		activityIds = [activity["activityDetails"]["instanceId"] for activity in activities]
		return activityIds

	def getPlayersInActivity(self, activityId):
		url = self.apiBase + 'Stats/PostGameCarnageReport/' + activityId
		r = requests.get(url, headers=self.headers)
		result = json.loads(r.content)
		players = result["Response"]["data"]["entries"]
		usernames = [entry["player"]["destinyUserInfo"]["displayName"] for entry in players]
		return usernames

api = DestinyAPI('f6736009a38a4707b549422b1bd69ea4')
memId = api.getMembershipId('neoleopard')
charIds = api.getCharacterIds(memId)
activityIds = api.getCharacterActivity(memId, charIds[0])
print api.getPlayersInActivity(activityIds[0])
