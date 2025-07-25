# Discord 2FA Auth Bot 🔐

A secure Discord bot with TOTP (Time-based One-Time Password) authentication for staff role management. Uses authenticator apps like Google Authenticator for secure role verification.

## Features ✨

- **TOTP Authentication**: Industry-standard 2FA using authenticator apps
- **QR Code Generation**: Easy setup with any TOTP-compatible authenticator app
- **Staff Role Management**: Save and restore staff roles securely
- **Backup Codes**: Emergency access codes when authenticator is unavailable
- **Verification System**: Multi-step verification process for maximum security
- **Audit Trail**: Complete logging of all authentication activities
- **Admin Controls**: Comprehensive management tools for administrators

## How It Works 🔄

1. **Admin adds staff**: `!addstaff @user` saves the user's current roles
2. **Staff generates TOTP**: `!generate` creates secret key and QR code via DM
3. **Setup authenticator**: Scan QR code in Google Authenticator or similar app
4. **Verify setup**: `!verify <6-digit-code>` confirms authenticator is working
5. **Claim roles**: `!claim <6-digit-code>` assigns saved roles with 2FA verification

## Installation 🚀

### Quick Setup

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd discord-auth-bot
   python setup.py
   ```

2. **Create Discord Bot**:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create new application → Bot
   - Copy bot token for setup script

3. **Run the bot**:
   ```bash
   python bot.py
   ```

### Manual Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file**:
   ```env
   DISCORD_TOKEN=your_bot_token_here
   GUILD_ID=your_server_id_here
   ADMIN_ROLE_ID=your_admin_role_id_here  # Optional
   ```

3. **Run**: `python bot.py`

## Bot Permissions 🔐

Your bot needs these Discord permissions:
- Send Messages
- Use Slash Commands
- Manage Roles
- Read Message History
- Add Reactions

**Important**: Bot's role must be ABOVE roles it needs to manage!

## Commands 📝

### Admin Commands (Requires admin role or server admin)

| Command | Description | Example |
|---------|-------------|---------|
| `!addstaff @user` | Add staff member with current roles | `!addstaff @JohnDoe` |
| `!removestaff @user` | Remove staff member from database | `!removestaff @JohnDoe` |
| `!stafflist` | List all staff with verification status | `!stafflist` |
| `!revoke @user` | Revoke user's 2FA authentication | `!revoke @JohnDoe` |
| `!logs [@user] [limit]` | View authentication logs | `!logs @JohnDoe 20` |
| `!status` | Show bot status and statistics | `!status` |

### Staff Commands (For registered staff only)

| Command | Description | Example |
|---------|-------------|---------|
| `!generate` | Generate TOTP secret & QR code (via DM) | `!generate` |
| `!verify <code>` | Verify authenticator app setup | `!verify 123456` |
| `!claim <code>` | Claim roles with 2FA verification | `!claim 789012` |
| `!mystatus` | Check your authentication status | `!mystatus` |
| `!revoke` | Revoke your own 2FA authentication | `!revoke` |

### General Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!help_auth` | Show help message with all commands | `!help_auth` |

## Database Schema 📊

The bot uses SQLite with three main tables:

### Staff Table
- Stores user IDs, usernames, and role IDs
- Tracks when staff members were added/updated

### Auth Codes Table
- Stores generated codes with expiration times
- Tracks usage status and who used the code

### Role Transfers Table
- Audit trail of all role transfers
- Links original user to new user via auth code

## Security Features 🛡️

- **Secure Code Generation**: 8-character codes using cryptographically secure random generator
- **Time-Limited**: Codes expire after specified hours (default 24, max 168)
- **One-Time Use**: Codes are invalidated after successful use
- **Permission Checks**: Only admins can manage staff, only staff can generate codes
- **Audit Trail**: All transfers are logged with timestamps
- **DM Delivery**: Auth codes sent via DM when possible for privacy

## Usage Examples 💡

### Adding Staff Member
```
Admin: !addstaff @StaffMember
Bot: ✅ Staff Member Added
     Saved Roles: Moderator, Helper, VIP
     Next Steps: @StaffMember can now use !generate to set up 2FA authentication.
```

### Generating TOTP Authentication
```
Staff: !generate
Bot: ✅ TOTP setup sent to your DMs! Please check your direct messages.

DM: 🔐 2FA Authentication Setup
    [QR CODE IMAGE]
    Setup Instructions: Download Google Authenticator, scan QR code...
    Manual Entry Key: JBSW Y3DP EHPK 3PXP
    Backup Codes: AB12CD34, EF56GH78, ... (10 codes)
```

### Verifying Setup
```
Staff: !verify 123456
Bot: ✅ Verification Successful!
     Your 2FA authentication has been verified and activated.
     Next Steps: You can now use !claim <6-digit-code> to transfer roles.
```

### Claiming Roles
```
Staff: !claim 789012
Bot: ✅ Roles Claimed Successfully!
     Your staff roles have been successfully assigned!
     Roles Assigned: Moderator, Helper, VIP
```

## Configuration Options ⚙️

### Environment Variables

- `DISCORD_TOKEN`: Your bot's token (required)
- `GUILD_ID`: Your Discord server ID (required)
- `ADMIN_ROLE_ID`: Specific role that can use admin commands (optional)

### Customization

You can modify these settings in `bot.py`:
- Command prefix (default: `!`)
- Maximum code validity (default: 168 hours/1 week)
- Default code validity (default: 24 hours)
- Database file location (default: `auth_bot.db`)

## Troubleshooting 🔧

### Common Issues

**Bot doesn't respond to commands**:
- Check bot has necessary permissions
- Verify bot token is correct
- Ensure message content intent is enabled

**Can't assign roles**:
- Bot's role must be above target roles
- Check "Manage Roles" permission
- Verify roles still exist in server

**Database errors**:
- Check file permissions in bot directory
- Ensure SQLite is available
- Restart bot to reinitialize database

**Auth codes not working**:
- Check if code has expired
- Verify code hasn't been used already
- Ensure user isn't already staff

### Support

For issues or questions:
1. Check the console output for error messages
2. Verify all setup steps were completed
3. Test with `!help_auth` command
4. Check bot permissions in Discord

## Security Considerations ⚠️

- **Keep bot token secure** - never share or commit to public repositories
- **Auth codes are sensitive** - treat like temporary passwords
- **Regular audits** - periodically review staff list and transfers
- **Role hierarchy** - ensure proper role positioning
- **Limited access** - only trusted users should have admin roles

## Development 👨‍💻

Built with:
- **discord.py 2.3.2** - Discord API wrapper
- **aiosqlite 0.19.0** - Async SQLite database
- **python-dotenv 1.0.0** - Environment variable management
- **cryptography 41.0.8** - Secure random code generation

### File Structure
```
discord-auth-bot/
├── bot.py              # Main bot file
├── database.py         # Database management
├── setup.py           # Setup script
├── requirements.txt   # Dependencies
├── .env.example      # Environment template
├── README_BOT.md     # This documentation
└── auth_bot.db       # SQLite database (created on first run)
```

## License 📄

This project is open source. Feel free to modify and distribute according to your needs.

---

**Made with ❤️ for Discord communities**