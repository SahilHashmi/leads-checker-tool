from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional, Dict, List
from ..core.config import settings
import asyncio


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None


db = MongoDB()


async def connect_to_mongo():
    """Connect to the main MongoDB database."""
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db.database = db.client[settings.MONGODB_DATABASE]
    
    # Create indexes
    await create_indexes()
    
    print(f"Connected to MongoDB: {settings.MONGODB_DATABASE}")


async def close_mongo_connection():
    """Close the MongoDB connection."""
    if db.client:
        db.client.close()
        print("Closed MongoDB connection")


async def create_indexes():
    """Create necessary indexes for collections."""
    print("Running database migrations...")
    
    # device_keys collection
    await db.database.device_keys.create_index("key", unique=True)
    await db.database.device_keys.create_index("status")
    await db.database.device_keys.create_index("created_at")
    
    # fresh_leads collection
    await db.database.fresh_leads.create_index("email")
    await db.database.fresh_leads.create_index("created_at")
    await db.database.fresh_leads.create_index("task_id")
    await db.database.fresh_leads.create_index([("email", 1), ("task_id", 1)])
    
    # tasks collection
    await db.database.tasks.create_index("task_id", unique=True)
    await db.database.tasks.create_index("status")
    await db.database.tasks.create_index("created_at")
    await db.database.tasks.create_index("device_key")
    
    print("Database migrations completed successfully!")


def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance."""
    return db.database


class ExternalVPSConnections:
    """Manage connections to external VPS databases (READ ONLY)."""
    
    _connections: Dict[str, AsyncIOMotorClient] = {}
    _databases: Dict[str, AsyncIOMotorDatabase] = {}
    
    @classmethod
    def get_vps_configs(cls) -> List[Dict]:
        """Get list of enabled VPS configurations."""
        vps_list = []
        
        vps_configs = [
            ("VPS2", settings.VPS2_MONGODB_URL, settings.VPS2_MONGODB_DATABASE, settings.VPS2_ENABLED),
            ("VPS3", settings.VPS3_MONGODB_URL, settings.VPS3_MONGODB_DATABASE, settings.VPS3_ENABLED),
            ("VPS4", settings.VPS4_MONGODB_URL, settings.VPS4_MONGODB_DATABASE, settings.VPS4_ENABLED),
            ("VPS5", settings.VPS5_MONGODB_URL, settings.VPS5_MONGODB_DATABASE, settings.VPS5_ENABLED),
            ("VPS6", settings.VPS6_MONGODB_URL, settings.VPS6_MONGODB_DATABASE, settings.VPS6_ENABLED),
            ("VPS7", settings.VPS7_MONGODB_URL, settings.VPS7_MONGODB_DATABASE, settings.VPS7_ENABLED),
            ("VPS8", settings.VPS8_MONGODB_URL, settings.VPS8_MONGODB_DATABASE, settings.VPS8_ENABLED),
        ]
        
        for name, url, database, enabled in vps_configs:
            if enabled and url:
                vps_list.append({
                    "name": name,
                    "url": url,
                    "database": database
                })
        
        return vps_list
    
    @classmethod
    async def connect_all(cls):
        """Connect to all enabled external VPS databases."""
        for vps in cls.get_vps_configs():
            try:
                client = AsyncIOMotorClient(vps["url"], serverSelectionTimeoutMS=5000)
                cls._connections[vps["name"]] = client
                cls._databases[vps["name"]] = client[vps["database"]]
                print(f"Connected to external VPS: {vps['name']}")
            except Exception as e:
                print(f"Failed to connect to {vps['name']}: {e}")
    
    @classmethod
    async def close_all(cls):
        """Close all external VPS connections."""
        for name, client in cls._connections.items():
            client.close()
            print(f"Closed connection to {name}")
        cls._connections.clear()
        cls._databases.clear()
    
    @classmethod
    def get_database(cls, vps_name: str) -> Optional[AsyncIOMotorDatabase]:
        """Get a specific VPS database."""
        return cls._databases.get(vps_name)
    
    @classmethod
    def get_all_databases(cls) -> Dict[str, AsyncIOMotorDatabase]:
        """Get all connected VPS databases."""
        return cls._databases.copy()


external_vps = ExternalVPSConnections()
