# 🚀 Quick Start Guide - Discord 2FA Auth Bot

## What This Bot Does

This bot provides **secure 2FA authentication** for Discord staff role management using **authenticator apps** like Google Authenticator. Staff members can:

1. **Generate TOTP secrets** with QR codes
2. **Verify with authenticator apps** (Google Authenticator, Authy, etc.)
3. **Claim roles securely** using 6-digit codes
4. **Use backup codes** for emergency access

## 🎯 Perfect For

- **Discord servers** needing secure staff verification
- **Role transfers** between accounts with 2FA protection
- **Staff management** with audit trails
- **Emergency access** via backup codes

## ⚡ Setup (5 minutes)

### 1. Install & Configure
```bash
# Clone and setup
git clone <your-repo>
cd discord-auth-bot
python setup.py
```

### 2. Discord Bot Setup
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create Application → Bot
3. Copy bot token
4. Invite bot with **Manage Roles** permission
5. **Important**: Bot role must be ABOVE roles it manages!

### 3. Run
```bash
python bot.py
```

## 📱 User Flow

### For Admins:
```
!addstaff @user     # Add staff member
!stafflist          # View all staff + verification status
!revoke @user        # Revoke someone's 2FA
!logs               # View authentication logs
```

### For Staff:
```
!auth              # 🔥 Interactive button panel (RECOMMENDED!)
                   # Click buttons instead of typing commands
!generate          # Generate TOTP secret (sent via DM)
!verify 123456     # Verify authenticator is working  
!claim 789012      # Claim your roles with 2FA
!mystatus          # Check status (with buttons)
```

## 🔐 Security Features

- ✅ **TOTP Standard**: Same technology as Google, GitHub, etc.
- ✅ **QR Code Setup**: Easy scanning with any authenticator app
- ✅ **Backup Codes**: 10 emergency codes for lost devices
- ✅ **One-Time Use**: Each code works only once
- ✅ **Audit Trail**: Complete logging of all activities
- ✅ **Admin Controls**: Revoke access instantly

## 📱 Supported Apps

- **Google Authenticator** (iOS/Android)
- **Microsoft Authenticator** (iOS/Android)
- **Authy** (iOS/Android/Desktop)
- **1Password** (Built-in TOTP)
- Any RFC 6238 TOTP app

## ❓ Common Questions

**Q: What if I lose my phone?**
A: Use backup codes provided during setup, or ask admin to revoke and regenerate.

**Q: Can I use this on multiple accounts?**
A: Yes! Each account gets its own TOTP secret and verification.

**Q: Is this secure?**
A: Yes! Uses industry-standard TOTP (RFC 6238) - same as Google, banks, etc.

**Q: What permissions does the bot need?**
A: Send Messages, Manage Roles, Read Message History. Bot role must be above managed roles.

## 🆘 Troubleshooting

**Bot doesn't respond:**
- Check bot permissions and token
- Ensure bot role is above target roles

**2FA codes don't work:**
- Check time sync on your device
- Ensure you're using the latest code (changes every 30 seconds)
- Try backup codes if available

**Can't scan QR code:**
- Use manual entry key provided in DM
- Check authenticator app supports TOTP

## 📞 Support

Test commands:
- `!help_auth` - See all available commands
- `!status` - Check bot status
- `!mystatus` - Check your 2FA status

---

**🔒 Built for Security, Designed for Simplicity**