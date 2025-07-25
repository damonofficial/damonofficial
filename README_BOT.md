# Discord Auth Bot 🤖

A secure Discord bot that manages staff roles and generates authentication codes for role transfer between different Discord accounts.

## Features ✨

- **Staff Management**: Add/remove staff members with their roles saved to database
- **Auth Code Generation**: Generate secure, time-limited authentication codes
- **Role Transfer**: Transfer staff roles to new Discord accounts using auth codes
- **Security**: Codes expire automatically and can only be used once
- **Audit Trail**: Track all role transfers and auth code usage
- **Admin Controls**: Comprehensive admin commands for staff management

## How It Works 🔄

1. **Admin adds staff**: `!addstaff @user` saves the user's roles to database
2. **Staff generates code**: `!gencode` creates a secure 8-character auth code
3. **Staff uses code on new account**: `!usecode ABC123XY` transfers all saved roles
4. **Automatic cleanup**: Codes expire and are marked as used after successful transfer

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
| `!stafflist` | List all registered staff members | `!stafflist` |
| `!status` | Show bot status and statistics | `!status` |

### Staff Commands (For registered staff only)

| Command | Description | Example |
|---------|-------------|---------|
| `!gencode [hours]` | Generate auth code (default: 24h, max: 168h) | `!gencode 48` |
| `!mycodes` | View your active auth codes | `!mycodes` |

### General Commands (Anyone can use)

| Command | Description | Example |
|---------|-------------|---------|
| `!usecode <code>` | Use auth code to claim staff roles | `!usecode ABC123XY` |
| `!help_auth` | Show help message | `!help_auth` |

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
```

### Generating Auth Code
```
Staff: !gencode 48
Bot: ✅ Auth code sent to your DMs!

DM: 🔑 Auth Code Generated
    Code: ABC123XY
    Expires: 2024-01-15 14:30 UTC
    Valid For: 48 hours
```

### Using Auth Code
```
NewAccount: !usecode ABC123XY
Bot: ✅ Roles Transferred Successfully
     You have successfully claimed the staff roles from StaffMember!
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