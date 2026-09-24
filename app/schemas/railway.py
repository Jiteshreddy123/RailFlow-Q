from pydantic import BaseModel
from typing import Optional
from enum import Enum

class RakeStatus(str, Enum):
    AVAILABLE = "available"
    IN_TRANSIT = "in_transit"
    DELAYED = "delayed"
    BLOCKED = "blocked"

class RakeBase(BaseModel):
    name: str
    capacity: float
    current_station_id: Optional[int] = None

class RakeCreate(RakeBase):
    pass

class RakeResponse(RakeBase):
    id: int
    status: RakeStatus
    class Config:
        from_attributes = True

class StationBase(BaseModel):
    name: str
    code: str
    has_yard: bool = False

class StationCreate(StationBase):
    pass

class StationResponse(StationBase):
    id: int
    class Config:
        from_attributes = True

class SectionBase(BaseModel):
    name: str
    from_station_id: int
    to_station_id: int
    distance_km: float

class SectionCreate(SectionBase):
    pass

class SectionResponse(SectionBase):
    id: int
    is_blocked: bool
    class Config:
        from_attributes = True

class YardBase(BaseModel):
    name: str
    station_id: int
    capacity: int

class YardCreate(YardBase):
    pass

class YardResponse(YardBase):
    id: int
    current_load: int
    is_congested: bool
    class Config:
        from_attributes = True

class FreightDemandBase(BaseModel):
    origin_station_id: int
    destination_station_id: int
    weight_tons: float
    priority: int = 1

class FreightDemandCreate(FreightDemandBase):
    pass

class FreightDemandResponse(FreightDemandBase):
    id: int
    is_fulfilled: bool
    class Config:
        from_attributes = True