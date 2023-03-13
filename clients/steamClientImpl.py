import os
import sys
from steam.webapi import WebAPI

class steam_hunter():
    """Class to encapsulate interactions with the Steam WebAPI

    Notes: WebAPI documentation can be found here: https://steamapi.xpaw.me/
    """

    def __init__(self) -> None:
        """Constructor for steam_hunter

        Args:
            None
        Exceptions:
            None
        """
        apiKey = os.environ.get('STEAM_API_KEY')
        self.steamClient = WebAPI(key=apiKey)
        self.nameToAppID: dict[str, str] = {}

    def getServerInfo(self):
        print(self.steamClient.ISteamWebAPIUtil.GetServerInfo())
    
    def getAPIList(self):
        print(self.steamClient.ISteamWebAPIUtil.GetSupportedAPIList())
    
    def getCharts(self):
        print(self.steamClient.ISteam)

    def genAppList(self):
        """Method to init dict of steam title: app ID. AppID is necessary for leveraging
        other Steam WebAPIs

        Args:
            None
        Exceptions:
            None
        """
        response = dict(self.steamClient.IStoreService.GetAppList(max_results=50000))
        apps = response['response']['apps']
        for app in apps: 
            self.nameToAppID[app['name']] = app['appid']
        print(self.nameToAppID)
        # 50k results from the app list available on the steam store will be ~ 2 MB in memory
        print(sys.getsizeof(self.nameToAppID))

    


steam_hunter().getServerInfo()
steam_hunter().genAppList()
# steam_hunter().getAPIList()