from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db import Base
import enum

class RakeStatus(enum.Enum):
    AVAILABLE = "available"
    IN_TRANSIT = "in_transit"
    DELAYED = "delayed"
    BLOCKED = "blocked"

class Rake(Base):
    __tablename__ = "rakes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    status = Column(Enum(RakeStatus), default=RakeStatus.AVAILABLE)
    current_station_id = Column(Integer, ForeignKey("stations.id"), nullable=True)
    capacity = Column(Float, nullable=False)
    current_station = relationship("Station", back_populates="rakes")

class Station(Base):
    __tablename__ = "stations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    code = Column(String, unique=True, nullable=False)
    has_yard = Column(Boolean, default=False)
    rakes = relationship("Rake", back_populates="current_station")
    sections_from = relationship("Section", foreign_keys="Section.from_station_id", back_populates="from_station")
    sections_to = relationship("Section", foreign_keys="Section.to_station_id", back_populates="to_station")

class Section(Base):
    __tablename__ = "sections"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    from_station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    to_station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    distance_km = Column(Float, nullable=False)
    is_blocked = Column(Boolean, default=False)
    from_station = relationship("Station", foreign_keys=[from_station_id], back_populates="sections_from")
    to_station = relationship("Station", foreign_keys=[to_station_id], back_populates="sections_to")

class Yard(Base):
    __tablename__ = "yards"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    capacity = Column(Integer, nullable=False)
    current_load = Column(Integer, default=0)
    is_congested = Column(Boolean, default=False)

class FreightDemand(Base):
    __tablename__ = "freight_demands"
    id = Column(Integer, primary_key=True, index=True)
    origin_station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    destination_station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    weight_tons = Column(Float, nullable=False)
    priority = Column(Integer, default=1)
    is_fulfilled = Column(Boolean, default=False)