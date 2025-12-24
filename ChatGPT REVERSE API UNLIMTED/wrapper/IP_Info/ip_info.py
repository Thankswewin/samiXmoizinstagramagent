from curl_cffi  import requests
from ..logger   import Log
from ..runtime  import Utils


class IP_Info:
    
    @staticmethod
    def fetch_info(session: requests.session.Session) -> str:
        
        ip_infos: list = []
        
        info_request: requests.models.Response = session.get('https://iplocation.com/')
        
        ip_infos.append(Utils.between(info_request.text, '<td><b class="ip">', '<'))
        ip_infos.append(Utils.between(info_request.text, '<td class="city">', '<'))
        ip_infos.append(Utils.between(info_request.text, '<td><span class="region_name">', '<'))
        ip_infos.append(Utils.between(info_request.text, '<td class="lat">', '<'))
        ip_infos.append(Utils.between(info_request.text, '<td class="lng">', '<'))
        
        info_request_2: requests.models.Response = session.get('https://ipaddresslocation.net/ip-to-timezone')
        
        ip_infos.append(Utils.between(info_request_2.text, 'Time Zone:</strong> ', ' '))

        return ip_infos