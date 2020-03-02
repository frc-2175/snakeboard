from enum import Enum

class NetworkTableType(Enum):
    kBoolean: int
    kBooleanArray: int
    kDouble: int
    kDoubleArray: int
    kRaw: int
    kRpc: int
    kString: int
    kStringArray: int
    kUnassigned: int
