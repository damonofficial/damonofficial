import discord
from discord.ext import commands
from database import DatabaseManager
from totp_manager import TOTPManager
import asyncio

class AuthView(discord.ui.View):
    def __init__(self, bot, timeout=300):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.db = DatabaseManager()
        self.totp_manager = TOTPManager()

class GenerateAuthView(discord.ui.View):
    def __init__(self, bot, timeout=300):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.db = DatabaseManager()
        self.totp_manager = TOTPManager()
    
    @discord.ui.button(label='🔐 Generate 2FA', style=discord.ButtonStyle.primary, emoji='🔐')
    async def generate_2fa(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if user is staff
            staff_info = await self.db.get_staff_member(str(interaction.user.id))
            if not staff_info:
                await interaction.followup.send("❌ You are not registered as a staff member. Contact an admin to be added.", ephemeral=True)
                return
            
            # Generate TOTP secret
            totp_data = await self.db.generate_totp_secret(str(interaction.user.id))
            
            if not totp_data:
                await interaction.followup.send("❌ Failed to generate TOTP secret.", ephemeral=True)
                return
            
            # Generate QR code
            account_name = f"{interaction.user.display_name}@{interaction.guild.name}"
            qr_image = self.totp_manager.generate_qr_code(totp_data['secret'], account_name)
            
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
                   • Use the verify button or `!verify <6-digit-code>`
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
                value="• Keep your secret key and backup codes secure!\n• You must verify to activate authentication\n• This replaces any previous TOTP setup",
                inline=False
            )
            
            # Create verify view
            verify_view = VerifyAuthView(self.bot)
            
            # Try to send DM with QR code
            try:
                qr_file = discord.File(qr_image, filename="qr_code.png")
                embed.set_image(url="attachment://qr_code.png")
                await interaction.user.send(embed=embed, file=qr_file, view=verify_view)
                await interaction.followup.send("✅ TOTP setup sent to your DMs! Please check your direct messages.", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send("❌ I couldn't send you a DM. Please enable DMs from server members and try again.", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error generating TOTP: {str(e)}", ephemeral=True)

class VerifyAuthView(discord.ui.View):
    def __init__(self, bot, timeout=300):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.db = DatabaseManager()
    
    @discord.ui.button(label='✅ Verify Code', style=discord.ButtonStyle.success, emoji='✅')
    async def verify_code(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Create modal for code input
        modal = VerifyCodeModal(self.db)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='🆘 Use Backup Code', style=discord.ButtonStyle.secondary, emoji='🆘')
    async def use_backup(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Create modal for backup code input
        modal = BackupCodeModal(self.db)
        await interaction.response.send_modal(modal)

class ClaimRolesView(discord.ui.View):
    def __init__(self, bot, timeout=300):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.db = DatabaseManager()
    
    @discord.ui.button(label='🎯 Claim Roles', style=discord.ButtonStyle.primary, emoji='🎯')
    async def claim_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Create modal for code input
        modal = ClaimRolesModal(self.bot, self.db)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='🆘 Use Backup Code', style=discord.ButtonStyle.secondary, emoji='🆘')
    async def claim_with_backup(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Create modal for backup code input
        modal = ClaimBackupModal(self.bot, self.db)
        await interaction.response.send_modal(modal)

class StaffStatusView(discord.ui.View):
    def __init__(self, bot, timeout=300):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.db = DatabaseManager()
    
    @discord.ui.button(label='🔐 Generate 2FA', style=discord.ButtonStyle.primary, emoji='🔐')
    async def generate_2fa(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = GenerateAuthView(self.bot)
        await view.generate_2fa(interaction, button)
    
    @discord.ui.button(label='✅ Verify Setup', style=discord.ButtonStyle.success, emoji='✅')
    async def verify_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = VerifyCodeModal(self.db)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='🎯 Claim Roles', style=discord.ButtonStyle.green, emoji='🎯')
    async def claim_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ClaimRolesModal(self.bot, self.db)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='🔄 Revoke 2FA', style=discord.ButtonStyle.danger, emoji='🔄')
    async def revoke_2fa(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = RevokeConfirmView(self.db, str(interaction.user.id))
        embed = discord.Embed(
            title="⚠️ Confirm Revoke 2FA",
            description="Are you sure you want to revoke your 2FA authentication?\n\n**This will:**\n• Remove your current TOTP secret\n• Delete all backup codes\n• Require new setup to claim roles again",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class RevokeConfirmView(discord.ui.View):
    def __init__(self, db, user_id, timeout=60):
        super().__init__(timeout=timeout)
        self.db = db
        self.user_id = user_id
    
    @discord.ui.button(label='✅ Yes, Revoke', style=discord.ButtonStyle.danger)
    async def confirm_revoke(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        success = await self.db.revoke_totp(self.user_id)
        
        if success:
            embed = discord.Embed(
                title="✅ 2FA Authentication Revoked",
                description="Your 2FA authentication has been successfully revoked.",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="Next Steps",
                value="Use the **Generate 2FA** button to set up new authentication.",
                inline=False
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send("❌ Failed to revoke 2FA authentication.", ephemeral=True)
        
        # Disable the view
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)
    
    @discord.ui.button(label='❌ Cancel', style=discord.ButtonStyle.secondary)
    async def cancel_revoke(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="❌ Revoke Cancelled",
            description="Your 2FA authentication remains active.",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)

# Modal classes for text input
class VerifyCodeModal(discord.ui.Modal, title="Verify 2FA Code"):
    def __init__(self, db):
        super().__init__()
        self.db = db
    
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
            # Verify the token
            result = await self.db.verify_totp(str(interaction.user.id), self.code.value, False)
            
            if result['success']:
                embed = discord.Embed(
                    title="✅ Verification Successful!",
                    description="Your 2FA authentication has been verified and activated.",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="🎯 Next Steps",
                    value="You can now use the **Claim Roles** button to get your staff roles.",
                    inline=False
                )
                
                # Add claim roles button
                view = ClaimRolesView(interaction.client)
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Verification failed: {result['error']}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error verifying code: {str(e)}", ephemeral=True)

class BackupCodeModal(discord.ui.Modal, title="Use Backup Code"):
    def __init__(self, db):
        super().__init__()
        self.db = db
    
    code = discord.ui.TextInput(
        label="8-Character Backup Code",
        placeholder="AB12CD34",
        min_length=8,
        max_length=8,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verify the backup code
            result = await self.db.verify_totp(str(interaction.user.id), self.code.value, True)
            
            if result['success']:
                embed = discord.Embed(
                    title="✅ Backup Code Verified!",
                    description="Your backup code has been accepted and used.",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="🆘 Backup Codes Remaining",
                    value=f"You have {result.get('remaining_codes', 0)} backup codes left.",
                    inline=False
                )
                embed.add_field(
                    name="🎯 Next Steps",
                    value="You can now use the **Claim Roles** button to get your staff roles.",
                    inline=False
                )
                
                # Add claim roles button
                view = ClaimRolesView(interaction.client)
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Backup code verification failed: {result['error']}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error verifying backup code: {str(e)}", ephemeral=True)

class ClaimRolesModal(discord.ui.Modal, title="Claim Roles with 2FA"):
    def __init__(self, bot, db):
        super().__init__()
        self.bot = bot
        self.db = db
    
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
            # Check if user is staff
            staff_info = await self.db.get_staff_member(str(interaction.user.id))
            if not staff_info:
                await interaction.followup.send("❌ You are not registered as a staff member.", ephemeral=True)
                return
            
            if not staff_info['is_verified']:
                await interaction.followup.send("❌ You must verify your 2FA first using the **Verify** button.", ephemeral=True)
                return
            
            # Verify TOTP for role claiming
            verification = await self.db.verify_totp(str(interaction.user.id), self.code.value, False)
            
            if not verification['success']:
                await interaction.followup.send(f"❌ Invalid authentication code: {verification['error']}", ephemeral=True)
                return
            
            # Get the roles to assign
            guild = interaction.guild
            roles_to_assign = []
            failed_roles = []
            
            for role_id in staff_info['roles']:
                role = guild.get_role(int(role_id))
                if role and role.name != "@everyone":
                    # Check if user already has this role
                    if role not in interaction.user.roles:
                        roles_to_assign.append(role)
                else:
                    failed_roles.append(role_id)
            
            if not roles_to_assign:
                await interaction.followup.send("✅ You already have all available roles assigned!", ephemeral=True)
                return
            
            # Assign the roles
            try:
                await interaction.user.add_roles(*roles_to_assign, reason=f"2FA verified role claim via button")
                
                # Record the transfer
                await self.db.transfer_roles_with_verification(
                    str(interaction.user.id), 
                    str(interaction.user.id), 
                    verification['method']
                )
                
                # Send success message
                embed = discord.Embed(
                    title="✅ Roles Claimed Successfully!",
                    description="Your staff roles have been successfully assigned!",
                    color=discord.Color.green()
                )
                
                role_names = [role.name for role in roles_to_assign]
                embed.add_field(name="Roles Assigned", value=", ".join(role_names), inline=False)
                
                if failed_roles:
                    embed.add_field(
                        name="⚠️ Some roles couldn't be assigned",
                        value=f"Role IDs no longer exist: {', '.join(failed_roles)}",
                        inline=False
                    )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
            except discord.Forbidden:
                await interaction.followup.send("❌ I don't have permission to assign these roles. Contact an admin.", ephemeral=True)
            except discord.HTTPException as e:
                await interaction.followup.send(f"❌ Failed to assign roles: {str(e)}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error claiming roles: {str(e)}", ephemeral=True)

class ClaimBackupModal(discord.ui.Modal, title="Claim Roles with Backup Code"):
    def __init__(self, bot, db):
        super().__init__()
        self.bot = bot
        self.db = db
    
    code = discord.ui.TextInput(
        label="8-Character Backup Code",
        placeholder="AB12CD34",
        min_length=8,
        max_length=8,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if user is staff
            staff_info = await self.db.get_staff_member(str(interaction.user.id))
            if not staff_info:
                await interaction.followup.send("❌ You are not registered as a staff member.", ephemeral=True)
                return
            
            if not staff_info['is_verified']:
                await interaction.followup.send("❌ You must verify your 2FA first.", ephemeral=True)
                return
            
            # Verify backup code for role claiming
            verification = await self.db.verify_totp(str(interaction.user.id), self.code.value, True)
            
            if not verification['success']:
                await interaction.followup.send(f"❌ Invalid backup code: {verification['error']}", ephemeral=True)
                return
            
            # Get the roles to assign (same logic as regular claim)
            guild = interaction.guild
            roles_to_assign = []
            failed_roles = []
            
            for role_id in staff_info['roles']:
                role = guild.get_role(int(role_id))
                if role and role.name != "@everyone":
                    if role not in interaction.user.roles:
                        roles_to_assign.append(role)
                else:
                    failed_roles.append(role_id)
            
            if not roles_to_assign:
                await interaction.followup.send("✅ You already have all available roles assigned!", ephemeral=True)
                return
            
            # Assign the roles
            try:
                await interaction.user.add_roles(*roles_to_assign, reason=f"Backup code verified role claim via button")
                
                # Record the transfer
                await self.db.transfer_roles_with_verification(
                    str(interaction.user.id), 
                    str(interaction.user.id), 
                    verification['method']
                )
                
                # Send success message
                embed = discord.Embed(
                    title="✅ Roles Claimed with Backup Code!",
                    description="Your staff roles have been successfully assigned using a backup code.",
                    color=discord.Color.green()
                )
                
                role_names = [role.name for role in roles_to_assign]
                embed.add_field(name="Roles Assigned", value=", ".join(role_names), inline=False)
                embed.add_field(
                    name="🆘 Backup Codes Remaining", 
                    value=f"You have {verification.get('remaining_codes', 0)} backup codes left.", 
                    inline=False
                )
                
                if failed_roles:
                    embed.add_field(
                        name="⚠️ Some roles couldn't be assigned",
                        value=f"Role IDs no longer exist: {', '.join(failed_roles)}",
                        inline=False
                    )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
            except discord.Forbidden:
                await interaction.followup.send("❌ I don't have permission to assign these roles. Contact an admin.", ephemeral=True)
            except discord.HTTPException as e:
                await interaction.followup.send(f"❌ Failed to assign roles: {str(e)}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error claiming roles: {str(e)}", ephemeral=True)