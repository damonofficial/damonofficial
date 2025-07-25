#!/usr/bin/env python3
"""
Discord 2FA Role Transfer Bot - Complete Single File Solution
Features:
- MongoDB database with comprehensive logging
- Role names instead of IDs
- Persistent panel in channel
- Auto DM with setup guide
- Comprehensive admin controls
- Enhanced security features
"""

import discord
from discord.ext import commands, tasks
import os
import asyncio
import pyotp
import qrcode
import io
import secrets
import string
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import motor.motor_asyncio
from pymongo import MongoClient
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'discord_2fa_bot')
GUILD_ID = int(os.getenv('GUILD_ID')) if os.getenv('GUILD_ID') else None
ADMIN_ROLE_NAME = os.getenv('ADMIN_ROLE_NAME', 'Admin')
PANEL_CHANNEL_ID = int(os.getenv('PANEL_CHANNEL_ID')) if os.getenv('PANEL_CHANNEL_ID') else None
BOT_NAME = os.getenv('BOT_NAME', 'Discord 2FA Bot')

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

class TOTPManager:
    """TOTP management with enhanced security"""
    
    def __init__(self, issuer_name: str = "Discord 2FA Bot"):
        self.issuer_name = issuer_name
    
    def generate_secret(self) -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, secret: str, account_name: str) -> io.BytesIO:
        """Generate QR code for authenticator app setup"""
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=account_name,
            issuer_name=self.issuer_name
        )
        
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return img_buffer
    
    def verify_token(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)
        except:
            return False
    
    def get_current_token(self, secret: str) -> str:
        """Get current TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.now()
    
    def get_backup_codes(self, count: int = 10) -> list:
        """Generate backup codes"""
        return [''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8)) for _ in range(count)]
    
    def format_secret_for_manual_entry(self, secret: str) -> str:
        """Format secret key for manual entry"""
        return ' '.join([secret[i:i+4] for i in range(0, len(secret), 4)])

class DatabaseManager:
    """MongoDB database manager with comprehensive logging"""
    
    def __init__(self, mongodb_uri: str, database_name: str):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
        self.db = self.client[database_name]
        self.staff_collection = self.db.staff
        self.logs_collection = self.db.logs
        self.settings_collection = self.db.settings
        self.totp_manager = TOTPManager()
    
    async def log_action(self, user_id: str, action: str, details: str = None, guild_id: str = None, channel_id: str = None):
        """Comprehensive logging for all actions"""
        try:
            log_entry = {
                'user_id': user_id,
                'action': action,
                'details': details,
                'guild_id': guild_id,
                'channel_id': channel_id,
                'timestamp': datetime.utcnow(),
                'ip_address': None,  # Can be enhanced with real IP tracking
                'user_agent': None   # Can be enhanced with user agent tracking
            }
            await self.logs_collection.insert_one(log_entry)
            logger.info(f"Action logged: {action} by {user_id} - {details}")
        except Exception as e:
            logger.error(f"Failed to log action: {e}")
    
    async def add_staff_member(self, user_id: str, username: str, role_names: List[str], guild_id: str) -> bool:
        """Add or update a staff member with role names"""
        try:
            staff_data = {
                'user_id': user_id,
                'username': username,
                'role_names': role_names,
                'guild_id': guild_id,
                'totp_secret': None,
                'is_verified': False,
                'is_available_for_transfer': False,
                'backup_codes': [],
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'last_login': None,
                'transfer_count': 0,
                'security_level': 'standard'
            }
            
            await self.staff_collection.replace_one(
                {'user_id': user_id, 'guild_id': guild_id},
                staff_data,
                upsert=True
            )
            
            await self.log_action(user_id, "staff_added", f"Roles: {', '.join(role_names)}", guild_id)
            return True
        except Exception as e:
            logger.error(f"Error adding staff member: {e}")
            return False
    
    async def get_staff_member(self, user_id: str, guild_id: str) -> Optional[Dict]:
        """Get staff member by user ID and guild"""
        try:
            staff = await self.staff_collection.find_one({'user_id': user_id, 'guild_id': guild_id})
            return staff
        except Exception as e:
            logger.error(f"Error getting staff member: {e}")
            return None
    
    async def generate_totp_secret(self, user_id: str, guild_id: str) -> Optional[Dict]:
        """Generate unique TOTP secret for a staff member"""
        try:
            staff = await self.get_staff_member(user_id, guild_id)
            if not staff:
                return None
            
            # Generate unique secret
            max_attempts = 5
            for attempt in range(max_attempts):
                secret = self.totp_manager.generate_secret()
                existing = await self.staff_collection.find_one({'totp_secret': secret, 'guild_id': guild_id})
                if not existing:
                    break
                if attempt == max_attempts - 1:
                    logger.warning(f"Could not generate unique TOTP secret after {max_attempts} attempts")
                    return None
            
            backup_codes = self.totp_manager.get_backup_codes()
            
            await self.staff_collection.update_one(
                {'user_id': user_id, 'guild_id': guild_id},
                {
                    '$set': {
                        'totp_secret': secret,
                        'backup_codes': backup_codes,
                        'is_verified': False,
                        'is_available_for_transfer': False,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            await self.log_action(user_id, "totp_generated", f"New TOTP secret generated", guild_id)
            
            return {
                'secret': secret,
                'backup_codes': backup_codes,
                'formatted_secret': self.totp_manager.format_secret_for_manual_entry(secret)
            }
        except Exception as e:
            logger.error(f"Error generating TOTP secret: {e}")
            return None
    
    async def verify_totp(self, user_id: str, token: str, is_backup_code: bool, guild_id: str) -> Dict:
        """Verify TOTP token or backup code"""
        try:
            staff = await self.get_staff_member(user_id, guild_id)
            if not staff or not staff.get('totp_secret'):
                return {'success': False, 'error': 'No TOTP secret found'}
            
            if is_backup_code:
                if token.upper() in staff.get('backup_codes', []):
                    backup_codes = staff['backup_codes']
                    backup_codes.remove(token.upper())
                    
                    await self.staff_collection.update_one(
                        {'user_id': user_id, 'guild_id': guild_id},
                        {
                            '$set': {
                                'backup_codes': backup_codes,
                                'is_verified': True,
                                'is_available_for_transfer': True,
                                'updated_at': datetime.utcnow(),
                                'last_login': datetime.utcnow()
                            }
                        }
                    )
                    
                    await self.log_action(user_id, "verify_success_backup", f"Backup code used. Remaining: {len(backup_codes)}", guild_id)
                    return {'success': True, 'method': 'backup_code', 'remaining_codes': len(backup_codes)}
                else:
                    await self.log_action(user_id, "verify_fail_backup", "Invalid backup code", guild_id)
                    return {'success': False, 'error': 'Invalid backup code'}
            else:
                if self.totp_manager.verify_token(staff['totp_secret'], token):
                    await self.staff_collection.update_one(
                        {'user_id': user_id, 'guild_id': guild_id},
                        {
                            '$set': {
                                'is_verified': True,
                                'is_available_for_transfer': True,
                                'updated_at': datetime.utcnow(),
                                'last_login': datetime.utcnow()
                            }
                        }
                    )
                    
                    await self.log_action(user_id, "verify_success", "TOTP verified - roles available for transfer", guild_id)
                    return {'success': True, 'method': 'totp'}
                else:
                    await self.log_action(user_id, "verify_fail", "Invalid TOTP token", guild_id)
                    return {'success': False, 'error': 'Invalid TOTP token'}
        except Exception as e:
            logger.error(f"Error verifying TOTP: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_staff_by_totp_secret(self, totp_code: str, guild_id: str, exclude_user_id: str = None) -> Optional[Dict]:
        """Find staff member by validating their TOTP code"""
        try:
            query = {
                'totp_secret': {'$ne': None},
                'is_available_for_transfer': True,
                'guild_id': guild_id
            }
            
            if exclude_user_id:
                query['user_id'] = {'$ne': exclude_user_id}
            
            staff_members = await self.staff_collection.find(query).to_list(None)
            
            for staff in staff_members:
                if self.totp_manager.verify_token(staff['totp_secret'], totp_code):
                    await self.log_action(staff['user_id'], "totp_code_used", "TOTP code used for role transfer", guild_id)
                    return staff
            
            await self.log_action("unknown", "totp_code_failed", f"Invalid TOTP code attempted", guild_id)
            return None
        except Exception as e:
            logger.error(f"Error finding staff by TOTP: {e}")
            return None
    
    async def transfer_roles(self, staff_user_id: str, new_user_id: str, new_username: str, guild_id: str, verification_method: str) -> bool:
        """Record role transfer and create new staff entry"""
        try:
            original_staff = await self.get_staff_member(staff_user_id, guild_id)
            if not original_staff:
                return False
            
            # Create new staff entry for the new user
            await self.add_staff_member(new_user_id, new_username, original_staff['role_names'], guild_id)
            
            # Update transfer statistics
            await self.staff_collection.update_one(
                {'user_id': staff_user_id, 'guild_id': guild_id},
                {'$inc': {'transfer_count': 1}}
            )
            
            # Log the transfer
            await self.log_action(
                new_user_id, 
                "roles_transferred", 
                f"From {original_staff['username']} using {verification_method}. Roles: {', '.join(original_staff['role_names'])}", 
                guild_id
            )
            
            return True
        except Exception as e:
            logger.error(f"Error recording role transfer: {e}")
            return False
    
    async def revoke_user_access(self, user_id: str, guild_id: str) -> bool:
        """Revoke user's TOTP access and remove all authentication data"""
        try:
            result = await self.staff_collection.update_one(
                {'user_id': user_id, 'guild_id': guild_id},
                {
                    '$set': {
                        'totp_secret': None,
                        'backup_codes': [],
                        'is_verified': False,
                        'is_available_for_transfer': False,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                await self.log_action(user_id, "access_revoked", "TOTP access revoked by admin", guild_id)
                return True
            return False
        except Exception as e:
            logger.error(f"Error revoking user access: {e}")
            return False
    
    async def remove_staff_member(self, user_id: str, guild_id: str) -> bool:
        """Completely remove staff member from database"""
        try:
            result = await self.staff_collection.delete_one({'user_id': user_id, 'guild_id': guild_id})
            
            if result.deleted_count > 0:
                await self.log_action(user_id, "staff_removed", "Staff member completely removed", guild_id)
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing staff member: {e}")
            return False
    
    async def get_staff_list(self, guild_id: str) -> List[Dict]:
        """Get all staff members for a guild"""
        try:
            staff_members = await self.staff_collection.find({'guild_id': guild_id}).to_list(None)
            return staff_members
        except Exception as e:
            logger.error(f"Error getting staff list: {e}")
            return []
    
    async def get_logs(self, guild_id: str = None, user_id: str = None, limit: int = 50) -> List[Dict]:
        """Get audit logs with filters"""
        try:
            query = {}
            if guild_id:
                query['guild_id'] = guild_id
            if user_id:
                query['user_id'] = user_id
            
            logs = await self.logs_collection.find(query).sort('timestamp', -1).limit(limit).to_list(None)
            return logs
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return []
    
    async def get_statistics(self, guild_id: str) -> Dict:
        """Get comprehensive statistics"""
        try:
            total_staff = await self.staff_collection.count_documents({'guild_id': guild_id})
            verified_staff = await self.staff_collection.count_documents({'guild_id': guild_id, 'is_verified': True})
            transferable_staff = await self.staff_collection.count_documents({'guild_id': guild_id, 'is_available_for_transfer': True})
            
            # Recent activity
            recent_logs = await self.logs_collection.count_documents({
                'guild_id': guild_id,
                'timestamp': {'$gte': datetime.utcnow() - timedelta(days=7)}
            })
            
            # Transfer statistics
            transfers_today = await self.logs_collection.count_documents({
                'guild_id': guild_id,
                'action': 'roles_transferred',
                'timestamp': {'$gte': datetime.utcnow() - timedelta(days=1)}
            })
            
            return {
                'total_staff': total_staff,
                'verified_staff': verified_staff,
                'transferable_staff': transferable_staff,
                'recent_activity': recent_logs,
                'transfers_today': transfers_today
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

# Initialize database
db = DatabaseManager(MONGODB_URI, DATABASE_NAME)

# UI Views and Modals
class AuthPanelView(discord.ui.View):
    """Persistent authentication panel"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(
        label='🔐 Setup 2FA',
        style=discord.ButtonStyle.primary,
        custom_id='setup_2fa',
        emoji='🔐'
    )
    async def setup_2fa(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        try:
            guild_id = str(interaction.guild.id)
            user_id = str(interaction.user.id)
            
            # Check if user is staff
            staff_info = await db.get_staff_member(user_id, guild_id)
            if not staff_info:
                await interaction.followup.send("❌ You are not registered as a staff member. Contact an admin.", ephemeral=True)
                return
            
            # Generate TOTP secret
            totp_data = await db.generate_totp_secret(user_id, guild_id)
            if not totp_data:
                await interaction.followup.send("❌ Failed to generate 2FA setup. Please try again.", ephemeral=True)
                return
            
            # Send comprehensive setup guide via DM
            await send_setup_guide(interaction.user, totp_data, interaction.guild.name)
            await interaction.followup.send("✅ 2FA setup guide sent to your DMs! Check your direct messages.", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in setup_2fa: {e}")
            await interaction.followup.send("❌ An error occurred. Please try again later.", ephemeral=True)
    
    @discord.ui.button(
        label='✅ Verify 2FA',
        style=discord.ButtonStyle.success,
        custom_id='verify_2fa',
        emoji='✅'
    )
    async def verify_2fa(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = VerifyModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(
        label='🎯 Transfer Roles',
        style=discord.ButtonStyle.green,
        custom_id='transfer_roles',
        emoji='🎯'
    )
    async def transfer_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = TransferModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(
        label='📊 My Status',
        style=discord.ButtonStyle.secondary,
        custom_id='my_status',
        emoji='📊'
    )
    async def my_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        try:
            guild_id = str(interaction.guild.id)
            user_id = str(interaction.user.id)
            
            staff_info = await db.get_staff_member(user_id, guild_id)
            if not staff_info:
                await interaction.followup.send("❌ You are not registered as a staff member.", ephemeral=True)
                return
            
            embed = create_status_embed(staff_info, interaction.user)
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in my_status: {e}")
            await interaction.followup.send("❌ An error occurred. Please try again later.", ephemeral=True)

class VerifyModal(discord.ui.Modal):
    """Modal for TOTP verification"""
    
    def __init__(self):
        super().__init__(title="Verify 2FA Setup")
    
    code = discord.ui.TextInput(
        label="6-Digit Code from Authenticator App",
        placeholder="123456",
        min_length=6,
        max_length=6,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            guild_id = str(interaction.guild.id)
            user_id = str(interaction.user.id)
            
            result = await db.verify_totp(user_id, self.code.value, False, guild_id)
            
            if result['success']:
                embed = discord.Embed(
                    title="✅ Verification Successful!",
                    description="Your 2FA has been verified! Your roles are now available for transfer.",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="🔑 Next Steps",
                    value="Your TOTP codes can now be used on any account to transfer your roles.",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Verification failed: {result['error']}", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in verify modal: {e}")
            await interaction.followup.send("❌ An error occurred during verification.", ephemeral=True)

class TransferModal(discord.ui.Modal):
    """Modal for role transfer"""
    
    def __init__(self):
        super().__init__(title="Transfer Roles with 2FA")
    
    code = discord.ui.TextInput(
        label="6-Digit Code from Authenticator App",
        placeholder="123456",
        min_length=6,
        max_length=6,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            guild_id = str(interaction.guild.id)
            user_id = str(interaction.user.id)
            
            # Check if user already has staff roles
            existing_staff = await db.get_staff_member(user_id, guild_id)
            if existing_staff:
                await interaction.followup.send("❌ You are already registered as a staff member on this account.", ephemeral=True)
                return
            
            # Find staff member by TOTP code
            target_staff = await db.get_staff_by_totp_secret(self.code.value, guild_id, user_id)
            
            if not target_staff:
                await interaction.followup.send("❌ Invalid authentication code or no roles available for transfer.", ephemeral=True)
                return
            
            # Get roles to assign
            guild = interaction.guild
            roles_to_assign = []
            failed_roles = []
            
            for role_name in target_staff['role_names']:
                role = discord.utils.get(guild.roles, name=role_name)
                if role and role.name != "@everyone":
                    if role not in interaction.user.roles:
                        roles_to_assign.append(role)
                else:
                    failed_roles.append(role_name)
            
            if not roles_to_assign:
                await interaction.followup.send("✅ You already have all available roles assigned!", ephemeral=True)
                return
            
            # Assign roles
            try:
                await interaction.user.add_roles(*roles_to_assign, reason=f"2FA verified role transfer from {target_staff['username']}")
                
                # Record the transfer
                await db.transfer_roles(target_staff['user_id'], user_id, interaction.user.display_name, guild_id, 'totp')
                
                # Create success embed
                embed = discord.Embed(
                    title="✅ Roles Transferred Successfully!",
                    description=f"You have successfully claimed staff roles from **{target_staff['username']}**!",
                    color=discord.Color.green()
                )
                
                role_names = [role.name for role in roles_to_assign]
                embed.add_field(name="Roles Assigned", value=", ".join(role_names), inline=False)
                embed.add_field(name="Original Account", value=target_staff['username'], inline=True)
                embed.add_field(name="Transfer Time", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), inline=True)
                
                if failed_roles:
                    embed.add_field(
                        name="⚠️ Roles Not Found",
                        value=f"These roles no longer exist: {', '.join(failed_roles)}",
                        inline=False
                    )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                # Notify admins
                await notify_admins_of_transfer(interaction.guild, target_staff['username'], interaction.user.display_name, role_names)
                
            except discord.Forbidden:
                await interaction.followup.send("❌ I don't have permission to assign these roles. Contact an admin.", ephemeral=True)
            except discord.HTTPException as e:
                await interaction.followup.send(f"❌ Failed to assign roles: {str(e)}", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in transfer modal: {e}")
            await interaction.followup.send("❌ An error occurred during role transfer.", ephemeral=True)

# Helper Functions
async def send_setup_guide(user: discord.User, totp_data: Dict, guild_name: str):
    """Send comprehensive 2FA setup guide via DM"""
    try:
        # Generate QR code
        account_name = f"{user.display_name}@{guild_name}"
        qr_image = TOTPManager().generate_qr_code(totp_data['secret'], account_name)
        
        # Create setup embed
        embed = discord.Embed(
            title="🔐 2FA Authentication Setup Guide",
            description="Follow these steps to set up secure role transfers:",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="📱 Step 1: Download Authenticator App",
            value="""
            Choose one of these apps:
            • **Google Authenticator** (Recommended)
            • **Microsoft Authenticator**
            • **Authy** (Cross-device sync)
            • **1Password** (Premium users)
            """,
            inline=False
        )
        
        embed.add_field(
            name="📷 Step 2: Scan QR Code",
            value="Scan the QR code below with your authenticator app",
            inline=False
        )
        
        embed.add_field(
            name="🔑 Step 3: Manual Entry (If QR Fails)",
            value=f"**Secret Key:** `{totp_data['formatted_secret']}`\n**Account:** {account_name}\n**Type:** Time-based (30 sec)",
            inline=False
        )
        
        embed.add_field(
            name="✅ Step 4: Verify Setup",
            value="Return to Discord and click **Verify 2FA** button, then enter the 6-digit code from your app",
            inline=False
        )
        
        embed.add_field(
            name="🆘 Emergency Backup Codes",
            value=f"**SAVE THESE SECURELY!** Use if you lose your phone:\n```{chr(10).join(totp_data['backup_codes'])}```",
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Security Reminders",
            value="""
            • **NEVER share** your secret key or backup codes
            • **Screenshot** backup codes and store safely
            • **Test verification** before using for transfers
            • **Each code works only once** (30-second rotation)
            """,
            inline=False
        )
        
        embed.set_footer(text="Keep this information secure! Anyone with these codes can claim your roles.")
        
        # Send with QR code
        qr_file = discord.File(qr_image, filename="qr_code.png")
        embed.set_image(url="attachment://qr_code.png")
        
        await user.send(embed=embed, file=qr_file)
        
    except discord.Forbidden:
        logger.warning(f"Could not send DM to user {user.id}")
        raise
    except Exception as e:
        logger.error(f"Error sending setup guide: {e}")
        raise

def create_status_embed(staff_info: Dict, user: discord.User) -> discord.Embed:
    """Create status embed for user"""
    embed = discord.Embed(
        title="🔐 Your 2FA Status",
        color=discord.Color.blue()
    )
    
    # Basic info
    embed.add_field(name="👤 Username", value=staff_info['username'], inline=True)
    embed.add_field(name="📝 Saved Roles", value=str(len(staff_info['role_names'])), inline=True)
    embed.add_field(name="🔄 Transfers Made", value=str(staff_info.get('transfer_count', 0)), inline=True)
    
    # Authentication status
    if staff_info.get('totp_secret'):
        if staff_info.get('is_verified') and staff_info.get('is_available_for_transfer'):
            status = "🟢 Verified & Ready for Transfer"
            transfer_status = "✅ Available"
        elif staff_info.get('is_verified'):
            status = "🟡 Verified (Transfer Not Ready)"
            transfer_status = "❌ Not Available"
        else:
            status = "🟡 Generated (Not Verified)"
            transfer_status = "❌ Verify Required"
        
        backup_count = len(staff_info.get('backup_codes', []))
        
        embed.add_field(name="🔐 2FA Status", value=status, inline=True)
        embed.add_field(name="🔄 Role Transfer", value=transfer_status, inline=True)
        embed.add_field(name="🆘 Backup Codes", value=f"{backup_count} remaining", inline=True)
        
        # Role details
        if staff_info['role_names']:
            embed.add_field(
                name="📋 Your Roles",
                value=", ".join(staff_info['role_names']),
                inline=False
            )
        
        # Last activity
        if staff_info.get('last_login'):
            last_login = staff_info['last_login'].strftime("%Y-%m-%d %H:%M UTC")
            embed.add_field(name="🕒 Last Activity", value=last_login, inline=True)
    else:
        embed.add_field(name="🔐 2FA Status", value="🔴 Not Set Up", inline=True)
        embed.add_field(name="🔄 Role Transfer", value="❌ Not Available", inline=True)
        embed.add_field(
            name="📋 Next Steps",
            value="Click **Setup 2FA** button to begin authentication setup",
            inline=False
        )
    
    embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
    return embed

async def notify_admins_of_transfer(guild: discord.Guild, from_user: str, to_user: str, roles: List[str]):
    """Notify admins of role transfers"""
    try:
        admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)
        if not admin_role:
            return
        
        embed = discord.Embed(
            title="🔄 Role Transfer Notification",
            description=f"A role transfer has been completed",
            color=discord.Color.orange()
        )
        
        embed.add_field(name="From", value=from_user, inline=True)
        embed.add_field(name="To", value=to_user, inline=True)
        embed.add_field(name="Roles", value=", ".join(roles), inline=False)
        embed.add_field(name="Time", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), inline=True)
        
        # Send to admin channel or DM admins
        if PANEL_CHANNEL_ID:
            channel = guild.get_channel(PANEL_CHANNEL_ID)
            if channel:
                await channel.send(f"{admin_role.mention}", embed=embed)
        
    except Exception as e:
        logger.error(f"Error notifying admins: {e}")

async def create_persistent_panel(channel: discord.TextChannel):
    """Create the persistent authentication panel"""
    embed = discord.Embed(
        title="🔐 2FA Role Transfer System",
        description=f"""
        **Secure role transfers using authenticator apps**
        
        🔐 **Setup 2FA** - Generate your unique authentication key
        ✅ **Verify 2FA** - Confirm your authenticator app is working
        🎯 **Transfer Roles** - Move your roles to this account
        📊 **My Status** - Check your current 2FA status
        
        **How it works:**
        1. Admin adds you as staff member
        2. Click **Setup 2FA** to get your QR code
        3. Scan with Google Authenticator (or similar app)
        4. Click **Verify 2FA** to confirm setup
        5. Use **Transfer Roles** on any account with your 6-digit codes
        
        **Security:** Your codes change every 30 seconds and work only once.
        """,
        color=discord.Color.blue()
    )
    
    embed.set_footer(text=f"Powered by {BOT_NAME} | Keep your codes secure!")
    embed.set_thumbnail(url=channel.guild.icon.url if channel.guild.icon else None)
    
    view = AuthPanelView()
    message = await channel.send(embed=embed, view=view)
    
    logger.info(f"Created persistent panel in {channel.name}")
    return message

# Bot Events
@bot.event
async def on_ready():
    """Bot startup sequence"""
    logger.info(f'{bot.user} has connected to Discord!')
    
    # Add persistent view
    bot.add_view(AuthPanelView())
    
    # Create panel if channel is specified
    if PANEL_CHANNEL_ID:
        channel = bot.get_channel(PANEL_CHANNEL_ID)
        if channel:
            # Clear old messages and create new panel
            try:
                await channel.purge(limit=10)
                await create_persistent_panel(channel)
            except Exception as e:
                logger.error(f"Error creating panel: {e}")
    
    logger.info('Bot is ready and panel is active!')

@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        logger.error(f"Command error: {error}")
        await ctx.send(f"❌ An error occurred: {str(error)}")

# Bot Commands (Admin only)
def is_admin():
    """Check if user has admin role"""
    async def predicate(ctx):
        admin_role = discord.utils.get(ctx.guild.roles, name=ADMIN_ROLE_NAME)
        if admin_role:
            return admin_role in ctx.author.roles
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)

@bot.command(name='addstaff')
@is_admin()
async def add_staff(ctx, member: discord.Member):
    """Add a staff member with their current roles"""
    try:
        # Get role names (excluding @everyone)
        role_names = [role.name for role in member.roles if role.name != "@everyone"]
        
        if not role_names:
            await ctx.send("❌ This member has no roles to save.")
            return
        
        success = await db.add_staff_member(str(member.id), member.display_name, role_names, str(ctx.guild.id))
        
        if success:
            embed = discord.Embed(
                title="✅ Staff Member Added",
                description=f"**{member.display_name}** has been added to the staff database.",
                color=discord.Color.green()
            )
            embed.add_field(name="Saved Roles", value=", ".join(role_names), inline=False)
            embed.add_field(name="Next Steps", value="User can now use the 2FA panel to set up authentication.", inline=False)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Failed to add staff member.")
    
    except Exception as e:
        logger.error(f"Error in add_staff: {e}")
        await ctx.send(f"❌ Error adding staff member: {str(e)}")

@bot.command(name='removestaff')
@is_admin()
async def remove_staff(ctx, member: discord.Member):
    """Completely remove a staff member"""
    try:
        success = await db.remove_staff_member(str(member.id), str(ctx.guild.id))
        
        if success:
            embed = discord.Embed(
                title="✅ Staff Member Removed",
                description=f"**{member.display_name}** has been completely removed from the database.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Staff member not found or removal failed.")
    
    except Exception as e:
        logger.error(f"Error in remove_staff: {e}")
        await ctx.send(f"❌ Error removing staff member: {str(e)}")

@bot.command(name='revokeuser')
@is_admin()
async def revoke_user(ctx, member: discord.Member):
    """Revoke user's 2FA access (keeps staff status but removes authentication)"""
    try:
        success = await db.revoke_user_access(str(member.id), str(ctx.guild.id))
        
        if success:
            embed = discord.Embed(
                title="✅ User Access Revoked",
                description=f"**{member.display_name}**'s 2FA access has been revoked.",
                color=discord.Color.orange()
            )
            embed.add_field(name="What was revoked", value="• TOTP secret\n• Backup codes\n• Transfer availability", inline=False)
            embed.add_field(name="What remains", value="• Staff status\n• Saved roles", inline=False)
            embed.add_field(name="Recovery", value="User can generate new 2FA setup", inline=False)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ User not found or revocation failed.")
    
    except Exception as e:
        logger.error(f"Error in revoke_user: {e}")
        await ctx.send(f"❌ Error revoking user access: {str(e)}")

@bot.command(name='stafflist')
@is_admin()
async def staff_list(ctx):
    """List all staff members with their status"""
    try:
        staff_members = await db.get_staff_list(str(ctx.guild.id))
        
        if not staff_members:
            await ctx.send("📝 No staff members found.")
            return
        
        embed = discord.Embed(
            title="📋 Staff Members",
            description=f"Total: {len(staff_members)} staff members",
            color=discord.Color.blue()
        )
        
        for i, staff in enumerate(staff_members[:10]):  # Limit to 10
            user = bot.get_user(int(staff['user_id']))
            username = user.display_name if user else staff['username']
            
            if staff.get('is_verified') and staff.get('is_available_for_transfer'):
                status = "🟢 Ready for Transfer"
            elif staff.get('is_verified'):
                status = "🟡 Verified"
            elif staff.get('totp_secret'):
                status = "🔴 Not Verified"
            else:
                status = "⚫ No 2FA"
            
            role_count = len(staff['role_names'])
            transfers = staff.get('transfer_count', 0)
            
            embed.add_field(
                name=f"{i+1}. {username}",
                value=f"Status: {status}\nRoles: {role_count}\nTransfers: {transfers}",
                inline=True
            )
        
        if len(staff_members) > 10:
            embed.set_footer(text=f"Showing first 10 of {len(staff_members)} staff members")
        
        await ctx.send(embed=embed)
    
    except Exception as e:
        logger.error(f"Error in staff_list: {e}")
        await ctx.send(f"❌ Error fetching staff list: {str(e)}")

@bot.command(name='logs')
@is_admin()
async def view_logs(ctx, member: discord.Member = None, limit: int = 10):
    """View audit logs"""
    try:
        user_id = str(member.id) if member else None
        logs = await db.get_logs(str(ctx.guild.id), user_id, limit)
        
        if not logs:
            await ctx.send("📝 No logs found.")
            return
        
        embed = discord.Embed(
            title="📊 Audit Logs",
            description=f"Recent {len(logs)} entries" + (f" for {member.display_name}" if member else ""),
            color=discord.Color.blue()
        )
        
        for i, log in enumerate(logs[:10]):
            user = bot.get_user(int(log['user_id'])) if log['user_id'] != 'unknown' else None
            username = user.display_name if user else log['user_id']
            action = log['action'].replace('_', ' ').title()
            timestamp = log['timestamp'].strftime("%m/%d %H:%M")
            details = log.get('details', '')[:50] + "..." if len(log.get('details', '')) > 50 else log.get('details', '')
            
            embed.add_field(
                name=f"{i+1}. {username}",
                value=f"**{action}**\n{details}\n*{timestamp}*",
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    except Exception as e:
        logger.error(f"Error in view_logs: {e}")
        await ctx.send(f"❌ Error fetching logs: {str(e)}")

@bot.command(name='stats')
@is_admin()
async def bot_stats(ctx):
    """Show comprehensive bot statistics"""
    try:
        stats = await db.get_statistics(str(ctx.guild.id))
        
        embed = discord.Embed(
            title="📊 Bot Statistics",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="👥 Total Staff", value=str(stats.get('total_staff', 0)), inline=True)
        embed.add_field(name="✅ Verified Staff", value=str(stats.get('verified_staff', 0)), inline=True)
        embed.add_field(name="🔄 Transferable", value=str(stats.get('transferable_staff', 0)), inline=True)
        
        embed.add_field(name="📈 Recent Activity (7d)", value=str(stats.get('recent_activity', 0)), inline=True)
        embed.add_field(name="🎯 Transfers Today", value=str(stats.get('transfers_today', 0)), inline=True)
        embed.add_field(name="🏓 Bot Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
        
        embed.add_field(name="🌐 Server", value=ctx.guild.name, inline=True)
        embed.add_field(name="📁 Database", value="MongoDB Connected", inline=True)
        embed.add_field(name="🔐 Security", value="2FA Active", inline=True)
        
        await ctx.send(embed=embed)
    
    except Exception as e:
        logger.error(f"Error in bot_stats: {e}")
        await ctx.send(f"❌ Error fetching statistics: {str(e)}")

@bot.command(name='createpanel')
@is_admin()
async def create_panel(ctx, channel: discord.TextChannel = None):
    """Create authentication panel in specified channel"""
    try:
        target_channel = channel or ctx.channel
        
        # Clear old messages
        await target_channel.purge(limit=10)
        
        # Create new panel
        await create_persistent_panel(target_channel)
        
        await ctx.send(f"✅ Authentication panel created in {target_channel.mention}")
    
    except Exception as e:
        logger.error(f"Error in create_panel: {e}")
        await ctx.send(f"❌ Error creating panel: {str(e)}")

@bot.command(name='help')
async def help_command(ctx):
    """Show help information"""
    embed = discord.Embed(
        title="🔐 2FA Role Transfer Bot",
        description="Secure role transfers using authenticator apps",
        color=discord.Color.purple()
    )
    
    embed.add_field(
        name="🔧 Admin Commands",
        value="""
        `!addstaff @user` - Add staff member
        `!removestaff @user` - Remove staff member completely
        `!revokeuser @user` - Revoke 2FA access only
        `!stafflist` - List all staff members
        `!logs [@user] [limit]` - View audit logs
        `!stats` - Show bot statistics
        `!createpanel [#channel]` - Create auth panel
        """,
        inline=False
    )
    
    embed.add_field(
        name="👤 User Actions",
        value="""
        **Use the interactive panel buttons:**
        🔐 **Setup 2FA** - Get your authenticator QR code
        ✅ **Verify 2FA** - Confirm your setup works
        🎯 **Transfer Roles** - Move roles to this account
        📊 **My Status** - Check your 2FA status
        """,
        inline=False
    )
    
    embed.add_field(
        name="🔐 How It Works",
        value="""
        1. Admin adds you as staff member
        2. Click **Setup 2FA** → Get QR code in DMs
        3. Scan with Google Authenticator
        4. Click **Verify 2FA** → Enter 6-digit code
        5. On new account: **Transfer Roles** → Enter current code
        """,
        inline=False
    )
    
    embed.set_footer(text="🔒 Your codes are unique and secure - never share them!")
    await ctx.send(embed=embed)

# Main execution
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not found in environment variables!")
        print("Please set DISCORD_TOKEN in your .env file")
        exit(1)
    
    if not PANEL_CHANNEL_ID:
        logger.warning("PANEL_CHANNEL_ID not set - panel will not be automatically created")
    
    try:
        logger.info("Starting Discord 2FA Bot...")
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        exit(1)