import aiosqlite
import json
from datetime import datetime
from typing import Optional, List, Dict
from totp_manager import TOTPManager

class DatabaseManager:
    def __init__(self, db_path: str = "auth_bot.db"):
        self.db_path = db_path
        self.totp_manager = TOTPManager()
    
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
                    totp_secret TEXT NULL,  -- TOTP secret key
                    is_verified BOOLEAN DEFAULT FALSE,  -- Whether TOTP is verified on original account
                    is_available_for_transfer BOOLEAN DEFAULT FALSE,  -- Whether roles can be transferred to new account
                    backup_codes TEXT NULL,  -- JSON array of backup codes
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Auth logs table to track verification attempts
            await db.execute("""
                CREATE TABLE IF NOT EXISTS auth_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,  -- 'generate', 'verify_success', 'verify_fail', 'revoke'
                    details TEXT NULL,  -- Additional details
                    ip_address TEXT NULL,  -- For future use
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Role transfers table to track successful verifications and role assignments
            await db.execute("""
                CREATE TABLE IF NOT EXISTS role_transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    staff_user_id TEXT NOT NULL,
                    new_user_id TEXT NOT NULL,
                    roles_transferred TEXT NOT NULL,  -- JSON string of role IDs
                    verification_method TEXT NOT NULL,  -- 'totp' or 'backup_code'
                    transferred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.commit()
    
    async def add_staff_member(self, user_id: str, username: str, role_ids: List[str]) -> bool:
        """Add or update a staff member"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                roles_json = json.dumps(role_ids)
                
                # Check if user already exists
                cursor = await db.execute("SELECT id FROM staff WHERE user_id = ?", (user_id,))
                existing = await cursor.fetchone()
                
                if existing:
                    # Update existing staff member
                    await db.execute("""
                        UPDATE staff 
                        SET username = ?, roles = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (username, roles_json, user_id))
                else:
                    # Insert new staff member
                    await db.execute("""
                        INSERT INTO staff (user_id, username, roles)
                        VALUES (?, ?, ?)
                    """, (user_id, username, roles_json))
                
                await db.commit()
                await self.log_action(user_id, "staff_added", f"Roles: {len(role_ids)}")
                return True
        except Exception as e:
            print(f"Error adding staff member: {e}")
            return False
    
    async def get_staff_member(self, user_id: str) -> Optional[Dict]:
        """Get staff member by user ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT id, user_id, username, roles, totp_secret, is_verified, 
                           is_available_for_transfer, backup_codes, created_at, updated_at
                    FROM staff WHERE user_id = ?
                """, (user_id,))
                row = await cursor.fetchone()
                
                if row:
                    return {
                        'id': row[0],
                        'user_id': row[1],
                        'username': row[2],
                        'roles': json.loads(row[3]),
                        'totp_secret': row[4],
                        'is_verified': bool(row[5]),
                        'is_available_for_transfer': bool(row[6]),
                        'backup_codes': json.loads(row[7]) if row[7] else [],
                        'created_at': row[8],
                        'updated_at': row[9]
                    }
                return None
        except Exception as e:
            print(f"Error getting staff member: {e}")
            return None
    
    async def generate_totp_secret(self, user_id: str) -> Optional[Dict]:
        """Generate TOTP secret for a staff member"""
        try:
            staff = await self.get_staff_member(user_id)
            if not staff:
                return None
            
            # Generate new secret and backup codes
            secret = self.totp_manager.generate_secret()
            backup_codes = self.totp_manager.get_backup_codes()
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE staff 
                    SET totp_secret = ?, backup_codes = ?, is_verified = FALSE, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (secret, json.dumps(backup_codes), user_id))
                await db.commit()
            
            await self.log_action(user_id, "totp_generated", "New TOTP secret generated")
            
            return {
                'secret': secret,
                'backup_codes': backup_codes,
                'formatted_secret': self.totp_manager.format_secret_for_manual_entry(secret)
            }
        except Exception as e:
            print(f"Error generating TOTP secret: {e}")
            return None
    
    async def verify_totp(self, user_id: str, token: str, is_backup_code: bool = False) -> Dict:
        """Verify TOTP token or backup code"""
        try:
            staff = await self.get_staff_member(user_id)
            if not staff or not staff['totp_secret']:
                return {'success': False, 'error': 'No TOTP secret found'}
            
            if is_backup_code:
                # Verify backup code
                if token.upper() in staff['backup_codes']:
                    # Remove used backup code
                    backup_codes = staff['backup_codes']
                    backup_codes.remove(token.upper())
                    
                    async with aiosqlite.connect(self.db_path) as db:
                        await db.execute("""
                            UPDATE staff 
                            SET backup_codes = ?, is_verified = TRUE, updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = ?
                        """, (json.dumps(backup_codes), user_id))
                        await db.commit()
                    
                    await self.log_action(user_id, "verify_success", f"Backup code used. Remaining: {len(backup_codes)}")
                    return {'success': True, 'method': 'backup_code', 'remaining_codes': len(backup_codes)}
                else:
                    await self.log_action(user_id, "verify_fail", "Invalid backup code")
                    return {'success': False, 'error': 'Invalid backup code'}
            else:
                # Verify TOTP token
                if self.totp_manager.verify_token(staff['totp_secret'], token):
                    # Mark as verified and available for transfer
                    async with aiosqlite.connect(self.db_path) as db:
                        await db.execute("""
                            UPDATE staff 
                            SET is_verified = TRUE, is_available_for_transfer = TRUE, updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = ?
                        """, (user_id,))
                        await db.commit()
                    
                    await self.log_action(user_id, "verify_success", "TOTP token verified - roles available for transfer")
                    return {'success': True, 'method': 'totp'}
                else:
                    await self.log_action(user_id, "verify_fail", "Invalid TOTP token")
                    return {'success': False, 'error': 'Invalid TOTP token'}
        except Exception as e:
            print(f"Error verifying TOTP: {e}")
            return {'success': False, 'error': str(e)}
    
    async def revoke_totp(self, user_id: str) -> bool:
        """Revoke TOTP authentication for a staff member"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE staff 
                    SET totp_secret = NULL, backup_codes = NULL, is_verified = FALSE, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (user_id,))
                await db.commit()
            
            await self.log_action(user_id, "totp_revoked", "TOTP authentication revoked")
            return True
        except Exception as e:
            print(f"Error revoking TOTP: {e}")
            return False
    
    async def get_staff_by_totp_secret(self, totp_code: str) -> Optional[Dict]:
        """Find staff member by validating their TOTP code"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT user_id, username, roles, totp_secret, is_verified, is_available_for_transfer
                    FROM staff WHERE totp_secret IS NOT NULL AND is_available_for_transfer = TRUE
                """)
                rows = await cursor.fetchall()
                
                for row in rows:
                    user_id, username, roles, secret, is_verified, is_available = row
                    if self.totp_manager.verify_token(secret, totp_code):
                        return {
                            'user_id': user_id,
                            'username': username,
                            'roles': json.loads(roles),
                            'totp_secret': secret,
                            'is_verified': bool(is_verified),
                            'is_available_for_transfer': bool(is_available)
                        }
                return None
        except Exception as e:
            print(f"Error finding staff by TOTP: {e}")
            return None
    
    async def transfer_roles_with_verification(self, staff_user_id: str, new_user_id: str, verification_method: str) -> bool:
        """Record a role transfer after successful verification"""
        try:
            staff = await self.get_staff_member(staff_user_id)
            if not staff or not staff['is_verified']:
                return False
            
            async with aiosqlite.connect(self.db_path) as db:
                roles_json = json.dumps(staff['roles'])
                await db.execute("""
                    INSERT INTO role_transfers (staff_user_id, new_user_id, roles_transferred, verification_method)
                    VALUES (?, ?, ?, ?)
                """, (staff_user_id, new_user_id, roles_json, verification_method))
                await db.commit()
            
            await self.log_action(staff_user_id, "roles_transferred", f"To user: {new_user_id}, Method: {verification_method}")
            return True
        except Exception as e:
            print(f"Error recording role transfer: {e}")
            return False
    
    async def get_staff_list(self) -> List[Dict]:
        """Get all staff members with their verification status"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT user_id, username, roles, is_verified, is_available_for_transfer, created_at, updated_at
                    FROM staff ORDER BY username
                """)
                rows = await cursor.fetchall()
                
                return [{
                    'user_id': row[0],
                    'username': row[1],
                    'roles': json.loads(row[2]),
                    'is_verified': bool(row[3]),
                    'is_available_for_transfer': bool(row[4]),
                    'created_at': row[5],
                    'updated_at': row[6]
                } for row in rows]
        except Exception as e:
            print(f"Error getting staff list: {e}")
            return []
    
    async def log_action(self, user_id: str, action: str, details: str = None):
        """Log user actions for audit trail"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO auth_logs (user_id, action, details)
                    VALUES (?, ?, ?)
                """, (user_id, action, details))
                await db.commit()
        except Exception as e:
            print(f"Error logging action: {e}")
    
    async def get_auth_logs(self, user_id: str = None, limit: int = 50) -> List[Dict]:
        """Get authentication logs"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                if user_id:
                    cursor = await db.execute("""
                        SELECT user_id, action, details, timestamp
                        FROM auth_logs WHERE user_id = ?
                        ORDER BY timestamp DESC LIMIT ?
                    """, (user_id, limit))
                else:
                    cursor = await db.execute("""
                        SELECT user_id, action, details, timestamp
                        FROM auth_logs ORDER BY timestamp DESC LIMIT ?
                    """, (limit,))
                
                rows = await cursor.fetchall()
                return [{
                    'user_id': row[0],
                    'action': row[1],
                    'details': row[2],
                    'timestamp': row[3]
                } for row in rows]
        except Exception as e:
            print(f"Error getting auth logs: {e}")
            return []
    
    async def remove_staff_member(self, user_id: str) -> bool:
        """Remove a staff member"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM staff WHERE user_id = ?", (user_id,))
                await db.commit()
                await self.log_action(user_id, "staff_removed", "Staff member removed")
                return True
        except Exception as e:
            print(f"Error removing staff member: {e}")
            return False