# 🔐 Multiple Staff TOTP Management

## Overview

Your Discord 2FA bot is designed to handle **unlimited staff members**, each with their own **unique TOTP secret**. This ensures secure role transfers while maintaining complete isolation between different staff accounts.

## 🔑 How Multiple Staff Keys Work

### **Unique Secret Generation**
- Each staff member gets a **completely unique** TOTP secret
- System automatically checks for duplicates and regenerates if needed
- Up to 5 attempts to ensure uniqueness (extremely unlikely to fail)
- Each secret works with standard authenticator apps

### **Independent Operation**
- **Alice's TOTP codes** only work for Alice's roles
- **Bob's TOTP codes** only work for Bob's roles  
- **No interference** between different staff members
- Each staff member has their own set of backup codes

### **Secure Lookup System**
- When someone uses `!claim 123456`, the system:
  1. Checks **all active staff TOTP secrets**
  2. Finds which staff member's secret generates that code
  3. Transfers **that specific staff member's roles**
  4. Logs the transfer for audit purposes

## 📋 Workflow Examples

### **Scenario: Multiple Staff Setup**

```
Admin: !addstaff @Alice    # Alice gets Moderator, Helper roles
Admin: !addstaff @Bob      # Bob gets Admin, VIP roles  
Admin: !addstaff @Charlie  # Charlie gets Helper, VIP roles
```

### **Each Staff Member Sets Up 2FA:**

**Alice (on her account):**
```
Alice: !auth
Alice: [Clicks Generate 2FA] → Gets unique secret ABCD1234EFGH5678
Alice: [Scans QR in Google Authenticator]
Alice: [Clicks Verify] → Enters 123456 → ✅ Verified
```

**Bob (on his account):**
```
Bob: !auth  
Bob: [Clicks Generate 2FA] → Gets unique secret WXYZ9876MNOP5432
Bob: [Scans QR in different authenticator entry]
Bob: [Clicks Verify] → Enters 789012 → ✅ Verified
```

**Charlie (on his account):**
```
Charlie: !auth
Charlie: [Clicks Generate 2FA] → Gets unique secret QWER4567TYUI8901
Charlie: [Scans QR in authenticator]  
Charlie: [Clicks Verify] → Enters 345678 → ✅ Verified
```

### **Role Transfers to New Accounts:**

**Someone wants Alice's roles:**
```
NewUser1: !claim 111222    # Uses Alice's current TOTP code
Bot: ✅ Roles Transferred Successfully!
     You have successfully claimed the staff roles from Alice!
     Roles Assigned: Moderator, Helper
```

**Someone wants Bob's roles:**
```
NewUser2: !claim 333444    # Uses Bob's current TOTP code  
Bot: ✅ Roles Transferred Successfully!
     You have successfully claimed the staff roles from Bob!
     Roles Assigned: Admin, VIP
```

**Someone wants Charlie's roles:**
```
NewUser3: !claim 555666    # Uses Charlie's current TOTP code
Bot: ✅ Roles Transferred Successfully!
     You have successfully claimed the staff roles from Charlie!
     Roles Assigned: Helper, VIP
```

## 🔒 Security Features

### **Complete Isolation**
- **Alice's codes** cannot access Bob's or Charlie's roles
- **Bob's codes** cannot access Alice's or Charlie's roles
- **Charlie's codes** cannot access Alice's or Bob's roles
- **Zero cross-contamination** between staff accounts

### **Audit Trail**
- Every TOTP code usage is logged with:
  - Which staff member's code was used
  - Who used it (new account)
  - When it was used
  - What roles were transferred

### **Self-Prevention**
- Staff members **cannot use their own codes** to transfer to themselves
- Prevents accidental duplicate role assignments
- System automatically excludes self from TOTP lookups

### **Time-Based Security**
- TOTP codes change every **30 seconds**
- Old codes become invalid automatically
- Each code can only be used **once**
- Standard RFC 6238 implementation

## 👥 Admin Management

### **Staff Overview Commands**

**View all staff status:**
```
Admin: !stafflist
Bot: 📋 Staff Members (Total: 3)
     1. Alice - Status: 🟢 Verified & Transferable
     2. Bob - Status: 🟢 Verified & Transferable  
     3. Charlie - Status: 🟡 Verified (Not Transferable)
```

**View TOTP secrets overview:**
```
Admin: !secrets
Bot: 🔐 TOTP Secrets Overview
     Alice: 🟢 Active & Transferable
     Bob: 🟢 Active & Transferable
     Charlie: 🔴 Generated (Not Verified)
     📊 Summary: 3 Total Staff, 3 Active Secrets, 2 Transferable
```

**View audit logs:**
```
Admin: !logs 10
Bot: 📊 Authentication Logs
     1. Alice - Totp Code Used - TOTP code used for role transfer
     2. Bob - Verify Success - TOTP token verified - roles available
     3. Charlie - Totp Generated - New unique TOTP secret generated
```

## 🔧 Technical Implementation

### **Database Structure**
- Each staff record stores their **unique TOTP secret**
- Separate **backup codes** for each staff member
- **Individual verification status** tracking
- **Transfer availability** flags per staff member

### **TOTP Code Resolution**
```python
# When someone uses !claim 123456
1. Query all staff with active, transferable TOTP secrets
2. For each staff member:
   - Test if their secret generates code "123456"
   - If match found, return that staff member's data
3. Transfer the matched staff member's roles
4. Log the successful transfer
```

### **Uniqueness Guarantee**
```python
# When generating new TOTP secret
1. Generate random 32-character base32 secret
2. Check if ANY existing staff has this exact secret
3. If duplicate found, generate new secret (up to 5 tries)
4. Save unique secret to database
```

## 🎯 Best Practices

### **For Large Teams**
- **Unlimited staff members** supported
- Each gets their own QR code and backup codes
- No performance impact with more staff
- All operations remain fast and secure

### **Role Organization**
- Different staff can have **completely different role sets**
- Transfers are **exact copies** of original permissions
- No role conflicts or overlaps
- Clean separation of responsibilities

### **Security Recommendations**
- **Regular audits** using `!secrets` and `!logs`
- **Revoke unused** TOTP secrets periodically
- **Monitor transfers** for suspicious activity
- **Backup codes** should be stored securely by each staff member

## 🚨 Troubleshooting

### **"Invalid authentication code"**
- Code may have expired (30-second window)
- Staff member may not have verified their setup yet
- Check `!secrets` to see which staff have transferable codes

### **"No roles available for transfer"**
- Staff member hasn't completed verification
- Use `!stafflist` to check verification status
- Original staff member needs to use `!verify` first

### **Multiple staff with same roles**
- This is normal and supported
- Each staff member's codes work independently
- Transfers create separate staff entries for new accounts

---

## ✅ Summary

Your Discord 2FA bot handles multiple staff members perfectly:

- ✅ **Unlimited staff** with unique TOTP secrets
- ✅ **Complete isolation** between different staff
- ✅ **Secure role transfers** with full audit trails  
- ✅ **Easy management** with admin oversight tools
- ✅ **Industry-standard security** (RFC 6238 TOTP)

**Each staff member operates independently while maintaining the highest security standards!** 🔐