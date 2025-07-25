import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
from database import DatabaseManager
from datetime import datetime, timedelta

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
    """List all staff members"""
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
            
            role_count = len(staff['roles'])
            embed.add_field(
                name=f"{i+1}. {username}",
                value=f"ID: {staff['user_id']}\nRoles: {role_count}\nAdded: {format_datetime(staff['created_at'])}",
                inline=True
            )
        
        if len(staff_members) > 10:
            embed.set_footer(text=f"Showing first 10 of {len(staff_members)} staff members")
        
        await ctx.send(embed=embed)
    
    except Exception as e:
        await ctx.send(f"❌ Error fetching staff list: {str(e)}")

# Auth Code Commands
@bot.command(name='gencode')
async def generate_code(ctx, hours: int = 24):
    """Generate an auth code for yourself (staff only)"""
    try:
        # Check if user is staff
        staff_info = await db.get_staff_member(str(ctx.author.id))
        if not staff_info:
            await ctx.send("❌ You are not registered as a staff member.")
            return
        
        if hours < 1 or hours > 168:  # Max 1 week
            await ctx.send("❌ Hours must be between 1 and 168 (1 week).")
            return
        
        auth_code = await db.generate_auth_code(str(ctx.author.id), hours)
        
        if auth_code:
            expires_at = datetime.now() + timedelta(hours=hours)
            
            embed = discord.Embed(
                title="🔑 Auth Code Generated",
                description="Your auth code has been generated successfully!",
                color=discord.Color.gold()
            )
            embed.add_field(name="Code", value=f"```{auth_code}```", inline=False)
            embed.add_field(name="Expires", value=expires_at.strftime("%Y-%m-%d %H:%M UTC"), inline=True)
            embed.add_field(name="Valid For", value=f"{hours} hours", inline=True)
            embed.add_field(
                name="Usage",
                value=f"Use `!usecode {auth_code}` on your new account to transfer roles.",
                inline=False
            )
            embed.set_footer(text="⚠️ Keep this code secure! Anyone with this code can claim your roles.")
            
            # Try to send DM first, fallback to channel
            try:
                await ctx.author.send(embed=embed)
                await ctx.send("✅ Auth code sent to your DMs!")
            except discord.Forbidden:
                await ctx.send(embed=embed)
                await ctx.send("⚠️ Couldn't send DM. Please delete this message after saving your code!")
        else:
            await ctx.send("❌ Failed to generate auth code.")
    
    except Exception as e:
        await ctx.send(f"❌ Error generating auth code: {str(e)}")

@bot.command(name='usecode')
async def use_code(ctx, code: str):
    """Use an auth code to claim staff roles"""
    try:
        # Validate the auth code
        auth_info = await db.validate_auth_code(code.upper())
        
        if not auth_info:
            await ctx.send("❌ Invalid, expired, or already used auth code.")
            return
        
        # Check if user is trying to use their own code
        if auth_info['original_user_id'] == str(ctx.author.id):
            await ctx.send("❌ You cannot use your own auth code.")
            return
        
        # Check if user already has staff roles
        existing_staff = await db.get_staff_member(str(ctx.author.id))
        if existing_staff:
            await ctx.send("❌ You are already registered as a staff member.")
            return
        
        # Get the roles to assign
        guild = ctx.guild
        roles_to_assign = []
        failed_roles = []
        
        for role_id in auth_info['roles']:
            role = guild.get_role(int(role_id))
            if role and role.name != "@everyone":
                roles_to_assign.append(role)
            else:
                failed_roles.append(role_id)
        
        if not roles_to_assign:
            await ctx.send("❌ No valid roles found to assign.")
            return
        
        # Assign the roles
        try:
            await ctx.author.add_roles(*roles_to_assign, reason=f"Auth code transfer from {auth_info['username']}")
            
            # Mark the code as used and add user as staff
            success = await db.use_auth_code(code.upper(), str(ctx.author.id))
            if success:
                await db.add_staff_member(str(ctx.author.id), ctx.author.display_name, auth_info['roles'])
            
            # Send success message
            embed = discord.Embed(
                title="✅ Roles Transferred Successfully",
                description=f"You have successfully claimed the staff roles from **{auth_info['username']}**!",
                color=discord.Color.green()
            )
            
            role_names = [role.name for role in roles_to_assign]
            embed.add_field(name="Roles Assigned", value=", ".join(role_names), inline=False)
            
            if failed_roles:
                embed.add_field(
                    name="⚠️ Some roles couldn't be assigned",
                    value=f"Role IDs: {', '.join(failed_roles)}",
                    inline=False
                )
            
            embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else None)
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to assign these roles.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to assign roles: {str(e)}")
    
    except Exception as e:
        await ctx.send(f"❌ Error using auth code: {str(e)}")

@bot.command(name='mycodes')
async def my_codes(ctx):
    """View your active auth codes"""
    try:
        # Check if user is staff
        staff_info = await db.get_staff_member(str(ctx.author.id))
        if not staff_info:
            await ctx.send("❌ You are not registered as a staff member.")
            return
        
        auth_codes = await db.get_active_auth_codes(str(ctx.author.id))
        
        if not auth_codes:
            await ctx.send("📝 You have no active auth codes.")
            return
        
        embed = discord.Embed(
            title="🔑 Your Active Auth Codes",
            description=f"You have {len(auth_codes)} active auth code(s)",
            color=discord.Color.blue()
        )
        
        for i, code_info in enumerate(auth_codes[:5]):  # Limit to 5
            status = "🔴 Used" if code_info['is_used'] else "🟢 Available"
            expires_at = format_datetime(code_info['expires_at'])
            
            embed.add_field(
                name=f"Code #{i+1}",
                value=f"```{code_info['code']}```\nStatus: {status}\nExpires: {expires_at}",
                inline=True
            )
        
        if len(auth_codes) > 5:
            embed.set_footer(text=f"Showing first 5 of {len(auth_codes)} codes")
        
        # Try to send DM first
        try:
            await ctx.author.send(embed=embed)
            await ctx.send("✅ Auth codes sent to your DMs!")
        except discord.Forbidden:
            await ctx.send(embed=embed)
    
    except Exception as e:
        await ctx.send(f"❌ Error fetching auth codes: {str(e)}")

# Utility Commands
@bot.command(name='help_auth')
async def help_auth(ctx):
    """Show help for auth commands"""
    embed = discord.Embed(
        title="🤖 Auth Bot Help",
        description="Discord bot for staff role management and authentication",
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
        `!addstaff @user` - Add a staff member with their current roles
        `!removestaff @user` - Remove a staff member
        `!stafflist` - List all staff members
        """,
        inline=False
    )
    
    # Staff commands
    embed.add_field(
        name="👤 Staff Commands",
        value="""
        `!gencode [hours]` - Generate an auth code (default: 24h, max: 168h)
        `!mycodes` - View your active auth codes
        """,
        inline=False
    )
    
    # General commands
    embed.add_field(
        name="🔑 Auth Commands",
        value="""
        `!usecode <code>` - Use an auth code to claim staff roles
        `!help_auth` - Show this help message
        """,
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ How it works",
        value="""
        1. Admins add staff members with `!addstaff`
        2. Staff generate auth codes with `!gencode`
        3. Staff use codes on new accounts with `!usecode`
        4. Roles are automatically transferred!
        """,
        inline=False
    )
    
    embed.set_footer(text="⚠️ Keep auth codes secure! Anyone with a code can claim the associated roles.")
    await ctx.send(embed=embed)

@bot.command(name='status')
@is_admin()
async def bot_status(ctx):
    """Show bot status and statistics"""
    try:
        staff_count = len(await db.get_staff_list())
        
        embed = discord.Embed(
            title="📊 Bot Status",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="🔧 Bot", value=f"{bot.user.name}#{bot.user.discriminator}", inline=True)
        embed.add_field(name="📈 Uptime", value="Online", inline=True)
        embed.add_field(name="👥 Staff Members", value=str(staff_count), inline=True)
        embed.add_field(name="🌐 Server", value=ctx.guild.name, inline=True)
        embed.add_field(name="📁 Database", value="Connected", inline=True)
        embed.add_field(name="🏓 Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
        
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