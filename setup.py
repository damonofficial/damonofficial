#!/usr/bin/env python3
"""
Discord Auth Bot Setup Script
This script helps you set up and configure the Discord Auth Bot.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies!")
        return False

def create_env_file():
    """Create .env file with user input"""
    print("\n🔧 Setting up environment variables...")
    
    if os.path.exists('.env'):
        overwrite = input("📄 .env file already exists. Overwrite? (y/N): ").lower()
        if overwrite != 'y':
            print("⏭️ Skipping .env creation")
            return True
    
    print("\nPlease provide the following information:")
    print("(You can find these in your Discord Developer Portal)")
    
    # Get bot token
    bot_token = input("🤖 Discord Bot Token: ").strip()
    if not bot_token:
        print("❌ Bot token is required!")
        return False
    
    # Get guild ID
    guild_id = input("🏠 Discord Server ID (Guild ID): ").strip()
    if not guild_id.isdigit():
        print("❌ Invalid Guild ID!")
        return False
    
    # Get admin role ID (optional)
    admin_role_id = input("👑 Admin Role ID (optional, leave blank for server admin): ").strip()
    if admin_role_id and not admin_role_id.isdigit():
        print("❌ Invalid Admin Role ID!")
        return False
    
    # Write to .env file
    try:
        with open('.env', 'w') as f:
            f.write(f"DISCORD_TOKEN={bot_token}\n")
            f.write(f"GUILD_ID={guild_id}\n")
            if admin_role_id:
                f.write(f"ADMIN_ROLE_ID={admin_role_id}\n")
        
        print("✅ .env file created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def display_setup_instructions():
    """Display setup instructions"""
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Make sure your bot has the following permissions in your Discord server:")
    print("   • Send Messages")
    print("   • Use Slash Commands") 
    print("   • Manage Roles")
    print("   • Read Message History")
    print("   • Add Reactions")
    print("\n2. Make sure your bot's role is ABOVE the roles you want it to manage")
    print("\n3. Run the bot with:")
    print("   python bot.py")
    print("\n4. Test the bot with:")
    print("   !help_auth")
    print("\n🔧 Bot Commands:")
    print("   Admin: !addstaff, !removestaff, !stafflist, !status")
    print("   Staff: !gencode, !mycodes")
    print("   General: !usecode, !help_auth")
    print("\n⚠️  SECURITY NOTES:")
    print("   • Keep your bot token secure!")
    print("   • Auth codes are sensitive - treat them like passwords")
    print("   • Only trusted admins should add staff members")
    print("="*60)

def main():
    """Main setup function"""
    print("🤖 Discord Auth Bot Setup")
    print("=" * 30)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Create .env file
    if not create_env_file():
        return False
    
    # Display instructions
    display_setup_instructions()
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n❌ Setup failed! Please check the errors above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")
        sys.exit(1)