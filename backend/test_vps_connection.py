import asyncio
from app.services.email_checker_service import EmailCheckerService

async def test_vps_connections():
    """Test VPS database connections."""
    checker = EmailCheckerService()
    
    print("Testing VPS database connections...")
    print(f"VPS configs found: {len(checker.get_vps_configs())}")
    
    for config in checker.get_vps_configs():
        print(f"\nConfig: {config['name']}")
        print(f"  URL: {config['url']}")
        print(f"  Database: {config['database']}")
    
    print("\n" + "="*50)
    print("Attempting to connect to all VPS databases...")
    print("="*50 + "\n")
    
    await checker.connect_all()
    
    print("\n" + "="*50)
    print("Connection Summary:")
    print("="*50)
    print(f"Total connections established: {len(checker._databases)}")
    print(f"Connected VPS: {list(checker._databases.keys())}")
    
    # Test a sample email check
    if checker._databases:
        test_email = "test@gmail.com"
        print(f"\nTesting email check for: {test_email}")
        result = await checker.check_email_exists(test_email)
        print(f"Result: {'Found (leaked)' if result else 'Not found (fresh)'}")
    
    checker.close_all()

if __name__ == "__main__":
    asyncio.run(test_vps_connections())
