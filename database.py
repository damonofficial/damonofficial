import aiosqlite
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import json

class DatabaseManager:
    def __init__(self, db_path: str = "auth_bot.db"):
        self.db_path = db_path
    
    async def init_database(self):
        """Initialize the database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Staff table to store staff member information
            await db.execute("""
                CREATE TABLE IF NOT EXISTS staff (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    roles TEXT NOT NULL,  -- JSON string of role IDs
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Auth codes table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS auth_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    staff_id INTEGER NOT NULL,
                    is_used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    used_at TIMESTAMP NULL,
                    used_by_user_id TEXT NULL,
                    FOREIGN KEY (staff_id) REFERENCES staff (id)
                )
            """)
            
            # Role transfers table to track role assignments
            await db.execute("""
                CREATE TABLE IF NOT EXISTS role_transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    auth_code_id INTEGER NOT NULL,
                    original_user_id TEXT NOT NULL,
                    new_user_id TEXT NOT NULL,
                    roles_transferred TEXT NOT NULL,  -- JSON string of role IDs
                    transferred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (auth_code_id) REFERENCES auth_codes (id)
                )
            """)
            
            await db.commit()
    
    async def add_staff_member(self, user_id: str, username: str, role_ids: List[str]) -> bool:
        """Add or update a staff member"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                roles_json = json.dumps(role_ids)
                await db.execute("""
                    INSERT OR REPLACE INTO staff (user_id, username, roles, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, username, roles_json))
                await db.commit()
                return True
        except Exception as e:
            print(f"Error adding staff member: {e}")
            return False
    
    async def get_staff_member(self, user_id: str) -> Optional[Dict]:
        """Get staff member by user ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT id, user_id, username, roles, created_at, updated_at
                    FROM staff WHERE user_id = ?
                """, (user_id,))
                row = await cursor.fetchone()
                
                if row:
                    return {
                        'id': row[0],
                        'user_id': row[1],
                        'username': row[2],
                        'roles': json.loads(row[3]),
                        'created_at': row[4],
                        'updated_at': row[5]
                    }
                return None
        except Exception as e:
            print(f"Error getting staff member: {e}")
            return None
    
    async def generate_auth_code(self, user_id: str, expires_hours: int = 24) -> Optional[str]:
        """Generate an auth code for a staff member"""
        try:
            staff = await self.get_staff_member(user_id)
            if not staff:
                return None
            
            # Generate a secure random code
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO auth_codes (code, staff_id, expires_at)
                    VALUES (?, ?, ?)
                """, (code, staff['id'], expires_at))
                await db.commit()
                
                return code
        except Exception as e:
            print(f"Error generating auth code: {e}")
            return None
    
    async def validate_auth_code(self, code: str) -> Optional[Dict]:
        """Validate an auth code and return staff info if valid"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT ac.id, ac.code, ac.is_used, ac.expires_at,
                           s.user_id, s.username, s.roles
                    FROM auth_codes ac
                    JOIN staff s ON ac.staff_id = s.id
                    WHERE ac.code = ?
                """, (code,))
                row = await cursor.fetchone()
                
                if not row:
                    return None
                
                # Check if code is expired
                expires_at = datetime.fromisoformat(row[3])
                if datetime.now() > expires_at:
                    return None
                
                # Check if code is already used
                if row[2]:  # is_used
                    return None
                
                return {
                    'auth_code_id': row[0],
                    'code': row[1],
                    'original_user_id': row[4],
                    'username': row[5],
                    'roles': json.loads(row[6])
                }
        except Exception as e:
            print(f"Error validating auth code: {e}")
            return None
    
    async def use_auth_code(self, code: str, new_user_id: str) -> bool:
        """Mark an auth code as used and record the transfer"""
        try:
            auth_info = await self.validate_auth_code(code)
            if not auth_info:
                return False
            
            async with aiosqlite.connect(self.db_path) as db:
                # Mark auth code as used
                await db.execute("""
                    UPDATE auth_codes 
                    SET is_used = TRUE, used_at = CURRENT_TIMESTAMP, used_by_user_id = ?
                    WHERE code = ?
                """, (new_user_id, code))
                
                # Record the role transfer
                roles_json = json.dumps(auth_info['roles'])
                await db.execute("""
                    INSERT INTO role_transfers (auth_code_id, original_user_id, new_user_id, roles_transferred)
                    VALUES (?, ?, ?, ?)
                """, (auth_info['auth_code_id'], auth_info['original_user_id'], new_user_id, roles_json))
                
                await db.commit()
                return True
        except Exception as e:
            print(f"Error using auth code: {e}")
            return False
    
    async def get_staff_list(self) -> List[Dict]:
        """Get all staff members"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT user_id, username, roles, created_at, updated_at
                    FROM staff ORDER BY username
                """)
                rows = await cursor.fetchall()
                
                return [{
                    'user_id': row[0],
                    'username': row[1],
                    'roles': json.loads(row[2]),
                    'created_at': row[3],
                    'updated_at': row[4]
                } for row in rows]
        except Exception as e:
            print(f"Error getting staff list: {e}")
            return []
    
    async def get_active_auth_codes(self, user_id: str) -> List[Dict]:
        """Get active auth codes for a staff member"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT ac.code, ac.created_at, ac.expires_at, ac.is_used
                    FROM auth_codes ac
                    JOIN staff s ON ac.staff_id = s.id
                    WHERE s.user_id = ? AND ac.expires_at > CURRENT_TIMESTAMP
                    ORDER BY ac.created_at DESC
                """, (user_id,))
                rows = await cursor.fetchall()
                
                return [{
                    'code': row[0],
                    'created_at': row[1],
                    'expires_at': row[2],
                    'is_used': bool(row[3])
                } for row in rows]
        except Exception as e:
            print(f"Error getting auth codes: {e}")
            return []
    
    async def remove_staff_member(self, user_id: str) -> bool:
        """Remove a staff member"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM staff WHERE user_id = ?", (user_id,))
                await db.commit()
                return True
        except Exception as e:
            print(f"Error removing staff member: {e}")
            return False