import uuid
from datetime import datetime
from typing import Optional, List, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models.schemas import DeviceKeyStatus, DeviceKeyResponse
from ..db.mongodb import get_database


class DeviceKeyService:
    
    @staticmethod
    def generate_key() -> str:
        """Generate a unique device key."""
        return str(uuid.uuid4())
    
    @staticmethod
    def _doc_to_response(doc: dict) -> DeviceKeyResponse:
        """Convert MongoDB document to DeviceKeyResponse."""
        return DeviceKeyResponse(
            id=str(doc["_id"]),
            key=doc["key"],
            status=DeviceKeyStatus(doc["status"]),
            hardware_id=doc.get("hardware_id"),
            created_at=doc["created_at"],
            activated_at=doc.get("activated_at")
        )
    
    @staticmethod
    async def create_key(db: AsyncIOMotorDatabase) -> DeviceKeyResponse:
        """Create a new device key."""
        key = DeviceKeyService.generate_key()
        
        document = {
            "key": key,
            "status": DeviceKeyStatus.ACTIVE.value,
            "hardware_id": None,
            "created_at": datetime.utcnow(),
            "activated_at": None
        }
        
        result = await db.device_keys.insert_one(document)
        
        return DeviceKeyResponse(
            id=str(result.inserted_id),
            key=key,
            status=DeviceKeyStatus.ACTIVE,
            hardware_id=None,
            created_at=document["created_at"],
            activated_at=None
        )
    
    @staticmethod
    async def activate_key(
        db: AsyncIOMotorDatabase, 
        device_key: str, 
        hardware_id: str
    ) -> Tuple[bool, str, Optional[DeviceKeyResponse]]:
        """
        Activate a device key and bind it to a hardware ID.
        Returns (success, message, key_response).
        """
        # Find the key
        doc = await db.device_keys.find_one({"key": device_key})
        
        if not doc:
            return False, "Invalid device key", None
        
        if doc["status"] != DeviceKeyStatus.ACTIVE.value:
            return False, "Device key is inactive", None
        
        existing_hardware_id = doc.get("hardware_id")
        
        # If already activated on a different PC
        if existing_hardware_id and existing_hardware_id != hardware_id:
            return False, "This key is already activated on another PC", None
        
        # If already activated on this PC, just return success
        if existing_hardware_id == hardware_id:
            return True, "Key already activated on this PC", DeviceKeyService._doc_to_response(doc)
        
        # Activate the key (bind to this PC)
        result = await db.device_keys.find_one_and_update(
            {"key": device_key},
            {
                "$set": {
                    "hardware_id": hardware_id,
                    "activated_at": datetime.utcnow()
                }
            },
            return_document=True
        )
        
        if result:
            return True, "Key activated successfully", DeviceKeyService._doc_to_response(result)
        
        return False, "Failed to activate key", None
    
    @staticmethod
    async def verify_key(
        db: AsyncIOMotorDatabase, 
        device_key: str, 
        hardware_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Verify if a device key is valid, active, and optionally check hardware ID.
        Returns (valid, message).
        """
        doc = await db.device_keys.find_one({"key": device_key})
        
        if not doc:
            return False, "Invalid device key"
        
        if doc["status"] != DeviceKeyStatus.ACTIVE.value:
            return False, "Device key is inactive"
        
        # If hardware_id is provided, verify it matches
        if hardware_id:
            existing_hardware_id = doc.get("hardware_id")
            
            # Key not yet activated
            if not existing_hardware_id:
                return False, "Key not activated. Please activate first."
            
            # Hardware ID mismatch
            if existing_hardware_id != hardware_id:
                return False, "This key is activated on another PC"
        
        return True, "Device key is valid"
    
    @staticmethod
    async def get_all_keys(db: AsyncIOMotorDatabase) -> List[DeviceKeyResponse]:
        """Get all device keys."""
        cursor = db.device_keys.find().sort("created_at", -1)
        keys = []
        
        async for doc in cursor:
            keys.append(DeviceKeyService._doc_to_response(doc))
        
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
            return DeviceKeyService._doc_to_response(result)
        return None
    
    @staticmethod
    async def delete_key(db: AsyncIOMotorDatabase, key_id: str) -> bool:
        """Delete a device key."""
        from bson import ObjectId
        
        result = await db.device_keys.delete_one({"_id": ObjectId(key_id)})
        return result.deleted_count > 0

