from typing import Callable, List

from .ConnectionInfo import ConnectionInfo
from .constants import kDefaultPort
from .NetworkTable import NetworkTable
from .NetworkTableEntry import NetworkTableEntry

class NetworkTables:
    @staticmethod
    def addConnectionListener(callback: Callable[[bool, ConnectionInfo], None], immediate_notify: bool): ...
    @staticmethod
    def deleteAllEntries(): ...
    @staticmethod
    def getEntries(prefix: str, types: int) -> List[NetworkTableEntry]: ...
    @staticmethod
    def getTable(key: str) -> NetworkTable: ...
    @staticmethod
    def startClient(server_name: str, port: int = kDefaultPort): ...
    @staticmethod
    def startClientTeam(team: int, port: int = kDefaultPort): ...