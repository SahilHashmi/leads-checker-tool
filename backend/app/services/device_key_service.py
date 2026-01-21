import uuid
from datetime import datetime
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models.schemas import DeviceKeyStatus, DeviceKeyResponse
from ..db.mongodb import get_database


class DeviceKeyService:
    
    @staticmethod
    def generate_key() -> str:
        """Generate a unique device key."""
        return str(uuid.uuid4())
    
    @staticmethod
    async def create_key(db: AsyncIOMotorDatabase) -> DeviceKeyResponse:
        """Create a new device key."""
        key = DeviceKeyService.generate_key()
        
        document = {
            "key": key,
            "status": DeviceKeyStatus.ACTIVE.value,
            "created_at": datetime.utcnow()
        }
        
        result = await db.device_keys.insert_one(document)
        
        return DeviceKeyResponse(
            id=str(result.inserted_id),
            key=key,
            status=DeviceKeyStatus.ACTIVE,
            created_at=document["created_at"]
        )
    
    @staticmethod
    async def verify_key(db: AsyncIOMotorDatabase, device_key: str) -> bool:
        """Verify if a device key is valid and active."""
        result = await db.device_keys.find_one({
            "key": device_key,
            "status": DeviceKeyStatus.ACTIVE.value
        })
        return result is not None
    
    @staticmethod
    async def get_all_keys(db: AsyncIOMotorDatabase) -> List[DeviceKeyResponse]:
        """Get all device keys."""
        cursor = db.device_keys.find().sort("created_at", -1)
        keys = []
        
        async for doc in cursor:
            keys.append(DeviceKeyResponse(
                id=str(doc["_id"]),
                key=doc["key"],
                status=DeviceKeyStatus(doc["status"]),
                created_at=doc["created_at"]
            ))
        
        return keys
    
    @staticmethod
    async def update_key_status(
        db: AsyncIOMotorDatabase, 
        key_id: str, 
        status: DeviceKeyStatus
    ) -> Optional[DeviceKeyResponse]:
        """Update the status of a device key."""
        from bson import ObjectId
        
        result = await db.device_keys.find_one_and_update(
            {"_id": ObjectId(key_id)},
            {"$set": {"status": status.value}},
            return_document=True
        )
        
        if result:
            return DeviceKeyResponse(
                id=str(result["_id"]),
                key=result["key"],
                status=DeviceKeyStatus(result["status"]),
                created_at=result["created_at"]
            )
        return None
    
    @staticmethod
    async def delete_key(db: AsyncIOMotorDatabase, key_id: str) -> bool:
        """Delete a device key."""
        from bson import ObjectId
        
        result = await db.device_keys.delete_one({"_id": ObjectId(key_id)})
        return result.deleted_count > 0
