#!/usr/bin/env python3
"""
Test script to verify multiple staff members with different TOTP keys
This script tests the core functionality without requiring Discord
"""

import asyncio
import tempfile
import os
from database import DatabaseManager
from totp_manager import TOTPManager

async def test_multiple_staff():
    """Test multiple staff members with different TOTP secrets"""
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        # Initialize database
        db = DatabaseManager(temp_db.name)
        await db.init_database()
        totp_manager = TOTPManager()
        
        print("🔐 Testing Multiple Staff TOTP System")
        print("=" * 50)
        
        # Test 1: Add multiple staff members
        print("\n1️⃣ Adding multiple staff members...")
        
        staff_data = [
            ("123456789", "Alice", ["role1", "role2"]),
            ("987654321", "Bob", ["role2", "role3"]),
            ("555666777", "Charlie", ["role1", "role3", "role4"])
        ]
        
        for user_id, username, roles in staff_data:
            success = await db.add_staff_member(user_id, username, roles)
            print(f"✅ Added {username}: {success}")
        
        # Test 2: Generate unique TOTP secrets for each
        print("\n2️⃣ Generating unique TOTP secrets...")
        
        secrets = {}
        for user_id, username, roles in staff_data:
            totp_data = await db.generate_totp_secret(user_id)
            if totp_data:
                secrets[username] = totp_data['secret']
                print(f"🔑 {username}: {totp_data['secret'][:8]}...")
            else:
                print(f"❌ Failed to generate secret for {username}")
        
        # Test 3: Verify uniqueness
        print("\n3️⃣ Verifying secret uniqueness...")
        secret_values = list(secrets.values())
        unique_secrets = set(secret_values)
        
        if len(secret_values) == len(unique_secrets):
            print("✅ All secrets are unique!")
        else:
            print("❌ Duplicate secrets found!")
            return False
        
        # Test 4: Verify each staff member's TOTP
        print("\n4️⃣ Verifying TOTP for each staff member...")
        
        for user_id, username, roles in staff_data:
            if username in secrets:
                # Generate current TOTP token
                current_token = totp_manager.get_current_token(secrets[username])
                
                # Verify token
                result = await db.verify_totp(user_id, current_token, False)
                if result['success']:
                    print(f"✅ {username}: TOTP verified and available for transfer")
                else:
                    print(f"❌ {username}: TOTP verification failed")
                    return False
        
        # Test 5: Test TOTP code lookup by different staff
        print("\n5️⃣ Testing TOTP code lookup...")
        
        for user_id, username, roles in staff_data:
            if username in secrets:
                current_token = totp_manager.get_current_token(secrets[username])
                
                # Test finding staff by TOTP code
                found_staff = await db.get_staff_by_totp_secret(current_token)
                if found_staff and found_staff['username'] == username:
                    print(f"✅ {username}: Found correctly by TOTP code")
                else:
                    print(f"❌ {username}: Not found by TOTP code")
                    return False
                
                # Test exclusion (shouldn't find themselves)
                found_staff_excluded = await db.get_staff_by_totp_secret(current_token, user_id)
                if found_staff_excluded is None:
                    print(f"✅ {username}: Correctly excluded from self-lookup")
                else:
                    print(f"❌ {username}: Self-exclusion failed")
                    return False
        
        # Test 6: Test role transfer simulation
        print("\n6️⃣ Testing role transfer simulation...")
        
        alice_token = totp_manager.get_current_token(secrets['Alice'])
        
        # Simulate Bob trying to use Alice's token
        found_alice = await db.get_staff_by_totp_secret(alice_token, "987654321")  # Bob's ID
        if found_alice and found_alice['username'] == 'Alice':
            print("✅ Bob can find Alice's roles using her TOTP")
            
            # Record the transfer
            success = await db.transfer_roles_with_verification("123456789", "987654321", "totp")
            if success:
                print("✅ Role transfer recorded successfully")
            else:
                print("❌ Role transfer recording failed")
        else:
            print("❌ Cross-staff TOTP lookup failed")
            return False
        
        # Test 7: Check logs
        print("\n7️⃣ Checking audit logs...")
        
        logs = await db.get_auth_logs(limit=20)
        print(f"📝 Found {len(logs)} log entries")
        
        for log in logs[-5:]:  # Show last 5 logs
            print(f"   {log['user_id'][:8]}... - {log['action']} - {log['details']}")
        
        # Test 8: Staff list overview
        print("\n8️⃣ Staff overview...")
        
        staff_list = await db.get_staff_list()
        for staff in staff_list:
            status = "🟢 Transferable" if staff['is_available_for_transfer'] else "🔴 Not Ready"
            print(f"   {staff['username']}: {status}")
        
        print("\n✅ All tests passed! Multiple staff TOTP system working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        try:
            os.unlink(temp_db.name)
        except:
            pass

async def main():
    """Run the test"""
    success = await test_multiple_staff()
    if success:
        print("\n🎉 Multiple staff TOTP system is ready for production!")
    else:
        print("\n💥 Issues found - please review the implementation")

if __name__ == "__main__":
    asyncio.run(main())