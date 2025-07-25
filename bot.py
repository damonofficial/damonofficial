import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
from database import DatabaseManager
from totp_manager import TOTPManager
from datetime import datetime
import io
from views import GenerateAuthView, VerifyAuthView, ClaimRolesView, StaffStatusView

# Load environment variables
load_dotenv()

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID')) if os.getenv('GUILD_ID') else None
ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID')) if os.getenv('ADMIN_ROLE_ID') else None

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
db = DatabaseManager()
totp_manager = TOTPManager()

# Utility functions
def is_admin():
    """Check if user has admin role"""
    async def predicate(ctx):
        if ADMIN_ROLE_ID:
            return any(role.id == ADMIN_ROLE_ID for role in ctx.author.roles)
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)

def format_datetime(dt_string):
    """Format datetime string for display"""
    try:
        dt = datetime.fromisoformat(dt_string)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except:
        return dt_string

# Events
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await db.init_database()
    print('Database initialized!')
    
    # Sync commands
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

# Error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}")
        print(f"Error in command {ctx.command}: {error}")

# Staff Management Commands
@bot.command(name='addstaff')
@is_admin()
async def add_staff(ctx, member: discord.Member):
    """Add a staff member with their current roles"""
    try:
        # Get non-everyone roles
        role_ids = [str(role.id) for role in member.roles if role.name != "@everyone"]
        
        if not role_ids:
            await ctx.send("❌ This member has no roles to save.")
            return
        
        success = await db.add_staff_member(str(member.id), member.display_name, role_ids)
        
        if success:
            role_names = [role.name for role in member.roles if role.name != "@everyone"]
            embed = discord.Embed(
                title="✅ Staff Member Added",
                description=f"**{member.display_name}** has been added to the staff database.",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Saved Roles",
                value=", ".join(role_names) if role_names else "None",
                inline=False
            )
            embed.add_field(
                name="Next Steps",
                value=f"{member.mention} can now use `!generate` to set up 2FA authentication.",
                inline=False
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Failed to add staff member to database.")
    
    except Exception as e:
        await ctx.send(f"❌ Error adding staff member: {str(e)}")

@bot.command(name='removestaff')
@is_admin()
async def remove_staff(ctx, member: discord.Member):
    """Remove a staff member from the database"""
    try:
        success = await db.remove_staff_member(str(member.id))
        
        if success:
            embed = discord.Embed(
                title="✅ Staff Member Removed",
                description=f"**{member.display_name}** has been removed from the staff database.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Failed to remove staff member or member not found.")
    
    except Exception as e:
        await ctx.send(f"❌ Error removing staff member: {str(e)}")

@bot.command(name='stafflist')
@is_admin()
async def staff_list(ctx):
    """List all staff members with their verification status"""
    try:
        staff_members = await db.get_staff_list()
        
        if not staff_members:
            await ctx.send("📝 No staff members found in the database.")
            return
        
        embed = discord.Embed(
            title="📋 Staff Members",
            description=f"Total: {len(staff_members)} staff members",
            color=discord.Color.blue()
        )
        
        for i, staff in enumerate(staff_members[:10]):  # Limit to 10 to avoid embed limits
            user = bot.get_user(int(staff['user_id']))
            username = user.display_name if user else staff['username']
            
            if staff['is_verified'] and staff['is_available_for_transfer']:
                status = "🟢 Verified & Transferable"
            elif staff['is_verified']:
                status = "🟡 Verified (Not Transferable)"
            else:
                status = "🔴 Not Verified"
            
            role_count = len(staff['roles'])
            
            embed.add_field(
                name=f"{i+1}. {username}",
                value=f"ID: {staff['user_id']}\nRoles: {role_count}\nStatus: {status}\nAdded: {format_datetime(staff['created_at'])}",
                inline=True
            )
        
        if len(staff_members) > 10:
            embed.set_footer(text=f"Showing first 10 of {len(staff_members)} staff members")
        
        await ctx.send(embed=embed)
    
    except Exception as e:
        await ctx.send(f"❌ Error fetching staff list: {str(e)}")

# TOTP Authentication Commands
@bot.command(name='auth')
async def auth_panel(ctx):
    """Show authentication panel with interactive buttons"""
    try:
        # Check if user is staff
        staff_info = await db.get_staff_member(str(ctx.author.id))
        if not staff_info:
            embed = discord.Embed(
                title="❌ Not Registered",
                description="You are not registered as a staff member. Contact an admin to be added.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🔐 2FA Authentication Panel",
            description="Choose an action below to manage your 2FA authentication:",
            color=discord.Color.blue()
        )
        
        # Show current status
        if staff_info['totp_secret']:
            status = "🟢 Verified & Active" if staff_info['is_verified'] else "🟡 Generated (Not Verified)"
            backup_count = len(staff_info['backup_codes'])
            
            embed.add_field(name="Current Status", value=status, inline=True)
            embed.add_field(name="Backup Codes", value=f"{backup_count} remaining", inline=True)
        else:
            embed.add_field(name="Current Status", value="🔴 Not Set Up", inline=True)
        
        embed.add_field(name="Available Actions", value="Use the buttons below:", inline=False)
        
        view = StaffStatusView(bot)
        await ctx.send(embed=embed, view=view)
    
    except Exception as e:
        await ctx.send(f"❌ Error displaying auth panel: {str(e)}")

@bot.command(name='generate')
async def generate_totp(ctx):
    """Generate TOTP secret and QR code for authenticator app setup"""
    try:
        # Check if user is staff
        staff_info = await db.get_staff_member(str(ctx.author.id))
        if not staff_info:
            await ctx.send("❌ You are not registered as a staff member. Contact an admin to be added.")
            return
        
        # Generate TOTP secret
        totp_data = await db.generate_totp_secret(str(ctx.author.id))
        
        if not totp_data:
            await ctx.send("❌ Failed to generate TOTP secret.")
            return
        
        # Generate QR code
        account_name = f"{ctx.author.display_name}@{ctx.guild.name}"
        qr_image = totp_manager.generate_qr_code(totp_data['secret'], account_name)
        
        # Create DM embed
        embed = discord.Embed(
            title="🔐 2FA Authentication Setup",
            description="Your TOTP authentication has been generated!",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="📱 Setup Instructions",
            value="""
            1. **Download an authenticator app:**
               • Google Authenticator
               • Microsoft Authenticator
               • Authy
               • Any TOTP-compatible app
            
            2. **Add this account to your app:**
               • Scan the QR code below, OR
               • Manually enter the secret key
            
            3. **Verify your setup:**
               • Use `!verify <6-digit-code>` in the server
            """,
            inline=False
        )
        
        embed.add_field(
            name="🔑 Manual Entry Key",
            value=f"```{totp_data['formatted_secret']}```",
            inline=False
        )
        
        embed.add_field(
            name="🆘 Backup Codes",
            value=f"Save these codes securely! You can use them if you lose access to your authenticator app.\n```{chr(10).join(totp_data['backup_codes'])}```",
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Important",
            value="• Keep your secret key and backup codes secure!\n• You must verify within the server to activate authentication\n• This replaces any previous TOTP setup",
            inline=False
        )
        
        # Try to send DM with QR code
        try:
            qr_file = discord.File(qr_image, filename="qr_code.png")
            embed.set_image(url="attachment://qr_code.png")
            await ctx.author.send(embed=embed, file=qr_file)
            await ctx.send("✅ TOTP setup sent to your DMs! Please check your direct messages.")
        except discord.Forbidden:
            await ctx.send("❌ I couldn't send you a DM. Please enable DMs from server members and try again.")
    
    except Exception as e:
        await ctx.send(f"❌ Error generating TOTP: {str(e)}")

@bot.command(name='verify')
async def verify_totp(ctx, token: str):
    """Verify TOTP token or backup code (for original account only)"""
    try:
        # Check if user is staff
        staff_info = await db.get_staff_member(str(ctx.author.id))
        if not staff_info:
            await ctx.send("❌ You are not registered as a staff member.")
            return
        
        if not staff_info['totp_secret']:
            await ctx.send("❌ You haven't generated a TOTP secret yet. Use `!generate` first.")
            return
        
        # Determine if it's a backup code or TOTP token
        is_backup_code = len(token) == 8 and token.isalnum()
        
        # Verify the token
        result = await db.verify_totp(str(ctx.author.id), token, is_backup_code)
        
        if result['success']:
            embed = discord.Embed(
                title="✅ Verification Successful!",
                description="Your 2FA authentication has been verified and your roles are now available for transfer!",
                color=discord.Color.green()
            )
            
            if result['method'] == 'backup_code':
                embed.add_field(
                    name="🆘 Backup Code Used",
                    value=f"You have {result.get('remaining_codes', 0)} backup codes remaining.",
                    inline=False
                )
            
            embed.add_field(
                name="🔑 TOTP Code Ready",
                value="Your current TOTP codes can now be used on **any account** to transfer your roles.",
                inline=False
            )
            
            embed.add_field(
                name="🎯 How to Transfer",
                value="On your **new account**, use: `!claim <6-digit-code>` with a current TOTP code.",
                inline=False
            )
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ Verification failed: {result['error']}")
    
    except Exception as e:
        await ctx.send(f"❌ Error verifying token: {str(e)}")

@bot.command(name='claim')
async def claim_roles(ctx, token: str):
    """Claim staff roles using TOTP code (works on any account)"""
    try:
        # First, check if this is the original account trying to claim their own roles
        staff_info = await db.get_staff_member(str(ctx.author.id))
        
        if staff_info and staff_info['is_verified']:
            # This is the original account - verify with their own TOTP
            is_backup_code = len(token) == 8 and token.isalnum()
            verification = await db.verify_totp(str(ctx.author.id), token, is_backup_code)
            
            if verification['success']:
                target_staff = staff_info
                await ctx.send("✅ You already have access to these roles on this account!")
                return
        
        # This is a different account - find the staff member by TOTP code
        target_staff = await db.get_staff_by_totp_secret(token, str(ctx.author.id))
        
        if not target_staff:
            await ctx.send("❌ Invalid authentication code or no roles available for transfer.")
            return
        
        if not target_staff['is_available_for_transfer']:
            await ctx.send("❌ This TOTP code has not been verified yet. The original account must verify first.")
            return
        
        # Check if user already has staff roles
        existing_staff = await db.get_staff_member(str(ctx.author.id))
        if existing_staff:
            await ctx.send("❌ You are already registered as a staff member on this account.")
            return
        
        # Get the roles to assign
        guild = ctx.guild
        roles_to_assign = []
        failed_roles = []
        
        for role_id in target_staff['roles']:
            role = guild.get_role(int(role_id))
            if role and role.name != "@everyone":
                # Check if user already has this role
                if role not in ctx.author.roles:
                    roles_to_assign.append(role)
            else:
                failed_roles.append(role_id)
        
        if not roles_to_assign:
            await ctx.send("✅ You already have all available roles assigned!")
            return
        
        # Assign the roles
        try:
            await ctx.author.add_roles(*roles_to_assign, reason=f"2FA verified role transfer from {target_staff['username']}")
            
            # Add the new user as staff with the same roles
            await db.add_staff_member(str(ctx.author.id), ctx.author.display_name, [str(role.id) for role in roles_to_assign])
            
            # Record the transfer
            await db.transfer_roles_with_verification(
                target_staff['user_id'], 
                str(ctx.author.id), 
                'totp'
            )
            
            # Send success message
            embed = discord.Embed(
                title="✅ Roles Transferred Successfully!",
                description=f"You have successfully claimed the staff roles from **{target_staff['username']}**!",
                color=discord.Color.green()
            )
            
            role_names = [role.name for role in roles_to_assign]
            embed.add_field(name="Roles Assigned", value=", ".join(role_names), inline=False)
            embed.add_field(name="Original Account", value=target_staff['username'], inline=True)
            embed.add_field(name="Transfer Method", value="TOTP Verification", inline=True)
            
            if failed_roles:
                embed.add_field(
                    name="⚠️ Some roles couldn't be assigned",
                    value=f"Role IDs no longer exist: {', '.join(failed_roles)}",
                    inline=False
                )
            
            embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else None)
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to assign these roles. Contact an admin.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to assign roles: {str(e)}")
    
    except Exception as e:
        await ctx.send(f"❌ Error claiming roles: {str(e)}")

@bot.command(name='revoke')
async def revoke_totp(ctx, member: discord.Member = None):
    """Revoke TOTP authentication (admins can revoke for others)"""
    try:
        # Determine target user
        if member and ctx.author.guild_permissions.administrator:
            target_user_id = str(member.id)
            target_name = member.display_name
        else:
            target_user_id = str(ctx.author.id)
            target_name = ctx.author.display_name
        
        # Check if user is staff
        staff_info = await db.get_staff_member(target_user_id)
        if not staff_info:
            await ctx.send("❌ Target user is not registered as a staff member.")
            return
        
        if not staff_info['totp_secret']:
            await ctx.send("❌ No TOTP authentication found for this user.")
            return
        
        # Revoke TOTP
        success = await db.revoke_totp(target_user_id)
        
        if success:
            embed = discord.Embed(
                title="✅ TOTP Authentication Revoked",
                description=f"2FA authentication has been revoked for **{target_name}**.",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="Next Steps",
                value="User must use `!generate` to set up new 2FA authentication.",
                inline=False
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Failed to revoke TOTP authentication.")
    
    except Exception as e:
        await ctx.send(f"❌ Error revoking TOTP: {str(e)}")

@bot.command(name='mystatus')
async def my_status(ctx):
    """Check your authentication status with interactive buttons"""
    try:
        staff_info = await db.get_staff_member(str(ctx.author.id))
        
        if not staff_info:
            await ctx.send("❌ You are not registered as a staff member.")
            return
        
        embed = discord.Embed(
            title="🔐 Your Authentication Status",
            color=discord.Color.blue()
        )
        
        # Basic info
        embed.add_field(name="👤 Username", value=staff_info['username'], inline=True)
        embed.add_field(name="🆔 User ID", value=staff_info['user_id'], inline=True)
        embed.add_field(name="📝 Roles Saved", value=str(len(staff_info['roles'])), inline=True)
        
        # Authentication status
        if staff_info['totp_secret']:
            if staff_info['is_verified'] and staff_info['is_available_for_transfer']:
                status = "🟢 Verified & Ready for Transfer"
                transfer_status = "✅ Available"
            elif staff_info['is_verified']:
                status = "🟡 Verified (Transfer Not Available)"
                transfer_status = "❌ Not Available"
            else:
                status = "🟡 Generated (Not Verified)"
                transfer_status = "❌ Verify Required"
            
            backup_count = len(staff_info['backup_codes'])
            
            embed.add_field(name="🔐 2FA Status", value=status, inline=True)
            embed.add_field(name="🔄 Role Transfer", value=transfer_status, inline=True)
            embed.add_field(name="🆘 Backup Codes", value=f"{backup_count} remaining", inline=True)
            
            if not staff_info['is_verified']:
                embed.add_field(
                    name="⚠️ Action Required",
                    value="Use the **Verify Setup** button below to enable role transfers",
                    inline=False
                )
            elif staff_info['is_available_for_transfer']:
                embed.add_field(
                    name="✅ Ready for Transfer",
                    value="Your TOTP codes can now be used on **any account** to transfer roles",
                    inline=False
                )
        else:
            embed.add_field(name="🔐 2FA Status", value="🔴 Not Set Up", inline=True)
            embed.add_field(name="🔄 Role Transfer", value="❌ Not Available", inline=True)
            embed.add_field(
                name="📋 Next Steps",
                value="Use the **Generate 2FA** button below to set up authentication",
                inline=False
            )
        
        # Recent activity
        recent_logs = await db.get_auth_logs(str(ctx.author.id), 5)
        if recent_logs:
            log_text = []
            for log in recent_logs[:3]:
                action = log['action'].replace('_', ' ').title()
                timestamp = format_datetime(log['timestamp'])
                log_text.append(f"• {action} - {timestamp}")
            
            embed.add_field(
                name="📊 Recent Activity",
                value="\n".join(log_text),
                inline=False
            )
        
        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        # Add interactive buttons
        view = StaffStatusView(bot)
        await ctx.send(embed=embed, view=view)
    
    except Exception as e:
        await ctx.send(f"❌ Error fetching status: {str(e)}")

# Admin utility commands
@bot.command(name='logs')
@is_admin()
async def view_logs(ctx, member: discord.Member = None, limit: int = 10):
    """View authentication logs"""
    try:
        user_id = str(member.id) if member else None
        logs = await db.get_auth_logs(user_id, limit)
        
        if not logs:
            await ctx.send("📝 No authentication logs found.")
            return
        
        embed = discord.Embed(
            title="📊 Authentication Logs",
            description=f"Recent {len(logs)} entries" + (f" for {member.display_name}" if member else ""),
            color=discord.Color.blue()
        )
        
        for i, log in enumerate(logs[:10]):
            user = bot.get_user(int(log['user_id']))
            username = user.display_name if user else log['user_id']
            action = log['action'].replace('_', ' ').title()
            timestamp = format_datetime(log['timestamp'])
            details = log['details'] or ""
            
            embed.add_field(
                name=f"{i+1}. {username}",
                value=f"**{action}**\n{details}\n*{timestamp}*",
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    except Exception as e:
        await ctx.send(f"❌ Error fetching logs: {str(e)}")

@bot.command(name='secrets')
@is_admin()
async def view_secrets(ctx):
    """View TOTP secret status for all staff (admin only)"""
    try:
        staff_list = await db.get_staff_list()
        
        if not staff_list:
            await ctx.send("📝 No staff members found.")
            return
        
        embed = discord.Embed(
            title="🔐 TOTP Secrets Overview",
            description=f"Security status for {len(staff_list)} staff members",
            color=discord.Color.blue()
        )
        
        active_secrets = 0
        transferable = 0
        
        for staff in staff_list:
            user = bot.get_user(int(staff['user_id']))
            username = user.display_name if user else staff['username']
            
            if staff['is_verified'] and staff['is_available_for_transfer']:
                status = "🟢 Active & Transferable"
                transferable += 1
            elif staff['is_verified']:
                status = "🟡 Active (Not Transferable)"
            elif 'totp_secret' in staff and staff.get('totp_secret'):
                status = "🔴 Generated (Not Verified)"
            else:
                status = "⚫ No Secret"
            
            if 'totp_secret' in staff and staff.get('totp_secret'):
                active_secrets += 1
            
            # Only show first 15 to avoid embed limits
            if len(embed.fields) < 15:
                embed.add_field(
                    name=username,
                    value=f"ID: {staff['user_id'][:8]}...\nStatus: {status}",
                    inline=True
                )
        
        embed.add_field(
            name="📊 Summary",
            value=f"**Total Staff:** {len(staff_list)}\n**Active Secrets:** {active_secrets}\n**Transferable:** {transferable}",
            inline=False
        )
        
        if len(staff_list) > 15:
            embed.set_footer(text=f"Showing first 15 of {len(staff_list)} staff members")
        
        await ctx.send(embed=embed)
    
    except Exception as e:
        await ctx.send(f"❌ Error fetching secrets overview: {str(e)}")

# Help and utility commands
@bot.command(name='help_auth')
async def help_auth(ctx):
    """Show help for authentication commands"""
    embed = discord.Embed(
        title="🔐 2FA Auth Bot Help",
        description="Discord bot with TOTP 2FA authentication for staff role management",
        color=discord.Color.purple()
    )
    
    # Admin commands
    if ADMIN_ROLE_ID:
        admin_role = ctx.guild.get_role(ADMIN_ROLE_ID)
        admin_name = admin_role.name if admin_role else "Admin"
    else:
        admin_name = "Administrator"
    
    embed.add_field(
        name=f"🔧 Admin Commands ({admin_name} only)",
        value="""
        `!addstaff @user` - Add staff member with current roles
        `!removestaff @user` - Remove staff member
        `!stafflist` - List all staff with verification status
        `!secrets` - View TOTP secrets overview for all staff
        `!revoke @user` - Revoke user's 2FA authentication
        `!logs [@user] [limit]` - View authentication logs
        """,
        inline=False
    )
    
    # Staff commands
    embed.add_field(
        name="👤 Staff Commands",
        value="""
        `!auth` - 🔥 **Interactive 2FA panel with buttons**
        `!generate` - Generate TOTP secret & QR code
        `!verify <code>` - Verify your authenticator setup
        `!claim <code>` - Claim roles with 2FA verification
        `!mystatus` - Check authentication status (with buttons)
        `!revoke` - Revoke your own 2FA authentication
        """,
        inline=False
    )
    
    embed.add_field(
        name="🔐 How 2FA Role Transfer Works",
        value="""
        **On Original Account:**
        1. Admin adds you as staff with `!addstaff`
        2. Use `!auth` → **Generate 2FA** → Scan QR code
        3. **Verify Setup** → Roles become transferable
        
        **On New Account:**
        4. Use `!claim <6-digit-code>` with current TOTP
        5. Roles transferred instantly! 🎉
        """,
        inline=False
    )
    
    embed.add_field(
        name="📱 Supported Authenticator Apps",
        value="• Google Authenticator\n• Microsoft Authenticator\n• Authy\n• Any TOTP-compatible app",
        inline=True
    )
    
    embed.add_field(
        name="🆘 Emergency Access",
        value="Use backup codes if you lose\naccess to your authenticator app",
        inline=True
    )
    
    embed.set_footer(text="⚠️ Keep your authenticator secure! It's your key to staff roles.")
    await ctx.send(embed=embed)

@bot.command(name='status')
@is_admin()
async def bot_status(ctx):
    """Show bot status and statistics"""
    try:
        staff_list = await db.get_staff_list()
        verified_count = sum(1 for staff in staff_list if staff['is_verified'])
        
        embed = discord.Embed(
            title="📊 Bot Status",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="🔧 Bot", value=f"{bot.user.name}", inline=True)
        embed.add_field(name="📈 Status", value="Online", inline=True)
        embed.add_field(name="🏓 Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
        
        embed.add_field(name="👥 Total Staff", value=str(len(staff_list)), inline=True)
        embed.add_field(name="✅ Verified Staff", value=str(verified_count), inline=True)
        embed.add_field(name="⏳ Pending Verification", value=str(len(staff_list) - verified_count), inline=True)
        
        embed.add_field(name="🌐 Server", value=ctx.guild.name, inline=True)
        embed.add_field(name="📁 Database", value="Connected", inline=True)
        embed.add_field(name="🔐 2FA System", value="Active", inline=True)
        
        await ctx.send(embed=embed)
    
    except Exception as e:
        await ctx.send(f"❌ Error fetching status: {str(e)}")

# Run the bot
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN not found in environment variables!")
        print("Please create a .env file with your bot token.")
        exit(1)
    
    try:
        bot.run(DISCORD_TOKEN)
    except discord.LoginFailure:
        print("❌ Invalid Discord token!")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")