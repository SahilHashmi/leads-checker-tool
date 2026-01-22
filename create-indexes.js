// MongoDB Script to Create _email_hash Indexes on All Collections
// This will significantly speed up email verification queries
// 
// Usage:
// mongo "mongodb://username:password@VPS_IP:27017/email_A_G" create-indexes.js

print("=".repeat(60));
print("Creating _email_hash indexes on all collections");
print("=".repeat(60));

var db = db.getSiblingDB(db.getName());
var collections = db.getCollectionNames();

print("\nFound " + collections.length + " collections");
print("");

var created = 0;
var existing = 0;
var errors = 0;

collections.forEach(function(collectionName) {
    try {
        print("Checking collection: " + collectionName);
        
        // Get existing indexes
        var indexes = db[collectionName].getIndexes();
        var hasEmailHashIndex = false;
        
        indexes.forEach(function(idx) {
            if (idx.key && idx.key._email_hash) {
                hasEmailHashIndex = true;
            }
        });
        
        if (hasEmailHashIndex) {
            print("  ✓ Index already exists");
            existing++;
        } else {
            // Create index
            print("  → Creating index...");
            db[collectionName].createIndex({ "_email_hash": 1 });
            print("  ✓ Index created successfully");
            created++;
        }
        
    } catch (e) {
        print("  ✗ Error: " + e);
        errors++;
    }
    print("");
});

print("=".repeat(60));
print("Summary:");
print("  Created: " + created);
print("  Already existed: " + existing);
print("  Errors: " + errors);
print("=".repeat(60));
