from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional, Dict, List
import asyncio
from ..core.config import settings
from ..core.logger import db_logger, vps_logger


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None


db = MongoDB()


async def connect_to_mongo():
    """Connect to MongoDB with retry logic."""
    global db
    
    db_logger.info(f"Connecting to MongoDB at {settings.MONGODB_URL}")
    db_logger.info(f"Database: {settings.MONGODB_DATABASE}")
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(1, max_retries + 1):
        try:
            db_logger.info(f"MongoDB connection attempt {attempt}/{max_retries}")
            
            db.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000
            )
            
            # Test connection
            await asyncio.wait_for(
                db.client.admin.command('ping'),
                timeout=10.0
            )
            
            db.database = db.client[settings.MONGODB_DATABASE]
            db_logger.info(f"✓ Successfully connected to MongoDB: {settings.MONGODB_DATABASE}")
            await create_indexes()
            print(f"Connected to MongoDB: {settings.MONGODB_DATABASE}")
            return
            
        except asyncio.TimeoutError:
            db_logger.error(f"MongoDB connection timeout on attempt {attempt}/{max_retries}")
            if attempt < max_retries:
                db_logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                
        except Exception as e:
            db_logger.error(f"MongoDB connection failed on attempt {attempt}/{max_retries}: {type(e).__name__}: {str(e)}")
            if attempt < max_retries:
                db_logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
    
    error_msg = f"Failed to connect to MongoDB after {max_retries} attempts"
    db_logger.error(error_msg)
    raise ConnectionError(error_msg)


async def close_mongo_connection():
    """Close the MongoDB connection."""
    if db.client:
        db.client.close()
        db_logger.info("MongoDB connection closed")


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
        configs = cls.get_vps_configs()
        
        if not configs:
            vps_logger.warning("⚠ WARNING: No external VPS databases configured!")
            return
        
        vps_logger.info(f"Connecting to {len(configs)} external VPS databases...")
        
        for vps in configs:
            try:
                vps_logger.info(f"Connecting to {vps['name']} at {vps['url']}")
                
                client = AsyncIOMotorClient(
                    vps["url"],
                    serverSelectionTimeoutMS=10000,
                    connectTimeoutMS=10000
                )
                
                # Test connection
                await asyncio.wait_for(
                    client.admin.command('ping'),
                    timeout=10.0
                )
                
                cls._connections[vps["name"]] = client
                cls._databases[vps["name"]] = client[vps["database"]]
                vps_logger.info(f"✓ Connected to external VPS: {vps['name']}")
                
            except asyncio.TimeoutError:
                vps_logger.error(f"✗ Timeout connecting to {vps['name']}")
            except Exception as e:
                vps_logger.error(f"✗ Failed to connect to {vps['name']}: {type(e).__name__}: {str(e)}")
        
        vps_logger.info(f"External VPS connections: {len(cls._databases)}/{len(configs)} successful")
    
    @classmethod
    async def close_all(cls):
        """Close all external VPS connections."""
        for name, client in cls._connections.items():
            try:
                client.close()
                vps_logger.info(f"Closed connection to {name}")
            except Exception as e:
                vps_logger.error(f"Error closing connection to {name}: {e}")
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
