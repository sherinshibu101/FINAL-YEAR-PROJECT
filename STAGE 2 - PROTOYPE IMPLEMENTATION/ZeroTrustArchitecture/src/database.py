"""
Database configuration and setup for Zero Trust Architecture
"""

import os
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from typing import Generator
from loguru import logger

from .models import Base


class DatabaseManager:
    def __init__(self, database_url: str = None):
        if database_url is None:
            # Load from config
            config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            database_url = config['database']['url']
        
        self.engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"Database initialized with URL: {database_url}")
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def drop_tables(self):
        """Drop all database tables"""
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped")
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_db_session(self) -> Generator:
        """Dependency for FastAPI to get database session"""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()


# Global database manager instance
db_manager = DatabaseManager()

# Dependency for FastAPI
def get_db():
    """FastAPI dependency for database sessions"""
    yield from db_manager.get_db_session()


def init_database():
    """Initialize database with tables and sample data"""
    try:
        db_manager.create_tables()
        create_sample_data()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def create_sample_data():
    """Create sample data for testing"""
    from .identity.iam_service import IAMService
    from .models import User, Device, DeviceType
    
    iam_service = IAMService("sample-secret-key")
    
    with db_manager.get_session() as db:
        # Check if sample data already exists
        existing_user = db.query(User).filter(User.username == "admin").first()
        simulation_users_exist = db.query(User).filter(User.username == "doctor_1").first()
        
        if existing_user and simulation_users_exist:
            logger.info("Sample data already exists, skipping creation")
            return
        elif existing_user and not simulation_users_exist:
            logger.info("Adding missing simulation users to existing sample data")
        
        # Create sample users
        sample_users = [
            {
                "username": "admin",
                "email": "admin@hospital.com",
                "password": "admin123",
                "full_name": "System Administrator",
                "department": "IT",
                "role": "system_admin"
            },
            {
                "username": "nurse.jane",
                "email": "jane.doe@hospital.com",
                "password": "nurse123",
                "full_name": "Jane Doe",
                "department": "nursing",
                "role": "user"
            },
            {
                "username": "dr.smith",
                "email": "dr.smith@hospital.com",
                "password": "doctor123",
                "full_name": "Dr. John Smith",
                "department": "clinical",
                "role": "admin"
            },
            {
                "username": "security.admin",
                "email": "security@hospital.com",
                "password": "security123",
                "full_name": "Security Administrator",
                "department": "security",
                "role": "security_admin"
            },
            # Simulation users for testing
            {
                "username": "doctor_1",
                "email": "doctor1@hospital.com",
                "password": "SecurePass123!",
                "full_name": "Dr. Smith 1",
                "department": "Cardiology",
                "role": "doctor"
            },
            {
                "username": "doctor_2",
                "email": "doctor2@hospital.com",
                "password": "SecurePass123!",
                "full_name": "Dr. Smith 2",
                "department": "Cardiology",
                "role": "doctor"
            },
            {
                "username": "attacker_1",
                "email": "hacker1@evil.com",
                "password": "password123",
                "full_name": "Evil User 1",
                "department": "Unknown",
                "role": "admin"
            },
            {
                "username": "attacker_2",
                "email": "hacker2@evil.com",
                "password": "password123",
                "full_name": "Evil User 2",
                "department": "Unknown",
                "role": "admin"
            }
        ]
        
        for user_data in sample_users:
            # Check if user already exists
            existing = db.query(User).filter(User.username == user_data["username"]).first()
            if existing:
                logger.info(f"User {user_data['username']} already exists, skipping")
                continue
                
            hashed_password = iam_service.get_password_hash(user_data["password"])
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                hashed_password=hashed_password,
                full_name=user_data["full_name"],
                department=user_data["department"],
                role=user_data["role"]
            )
            db.add(user)
            logger.info(f"Added user: {user_data['username']}")
        
        # Create sample devices
        sample_devices = [
            {
                "device_id": "HOSP-PC-001",
                "device_name": "Nursing Station Computer 1",
                "device_type": DeviceType.HOSPITAL_COMPUTER,
                "mac_address": "00:1B:63:84:45:E6",
                "ip_address": "10.0.2.10",
                "os_version": "Windows 10 Pro"
            },
            {
                "device_id": "HOSP-LAP-001",
                "device_name": "Doctor Laptop 1",
                "device_type": DeviceType.HOSPITAL_LAPTOP,
                "mac_address": "00:1B:63:84:45:E7",
                "ip_address": "10.0.2.20",
                "os_version": "Windows 11 Pro"
            },
            {
                "device_id": "IOT-MONITOR-001",
                "device_name": "Patient Monitor 1",
                "device_type": DeviceType.IOT_DEVICE,
                "mac_address": "00:1B:63:84:45:E8",
                "ip_address": "10.0.3.10",
                "os_version": "Linux Embedded"
            },
            {
                "device_id": "IOT-PUMP-001",
                "device_name": "Infusion Pump 1",
                "device_type": DeviceType.IOT_DEVICE,
                "mac_address": "00:1B:63:84:45:E9",
                "ip_address": "10.0.3.11",
                "os_version": "Linux Embedded"
            }
        ]
        
        for device_data in sample_devices:
            device = Device(**device_data)
            db.add(device)
        
        db.commit()
        logger.info("Sample data created successfully")


if __name__ == "__main__":
    init_database()