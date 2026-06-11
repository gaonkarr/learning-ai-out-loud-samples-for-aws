# PineRidge Solutions — Information Security Policy
**Document ID: PR-SEC-2026-002**
**Classification: Internal**
**Effective: January 1, 2026**
**Policy Owner: Chief Information Security Officer (CISO), Alex Whitmore**

---

## Purpose

This policy establishes the security requirements and expectations for all PineRidge employees, contractors, and third parties with access to PineRidge systems. Compliance is mandatory. Violations may result in disciplinary action up to and including termination.

---

## Section 1: Access Management

### 1.1 Identity and Authentication

- All access to PineRidge systems is authenticated through Okta (SSO provider).
- Multi-factor authentication (MFA) is mandatory for all accounts. Acceptable second factors:
  - Hardware security key (YubiKey) — preferred
  - Authenticator app (Okta Verify, Google Authenticator, 1Password TOTP)
  - **SMS-based MFA is not permitted** (vulnerable to SIM-swap attacks)
- Biometric authentication (Touch ID, Face ID) may be used for device unlock but does not replace MFA for application access.

### 1.2 Password Requirements

- Minimum 16 characters.
- No maximum length.
- No forced rotation (passwords are changed only when compromised or suspected compromised).
- Must not appear in known breach databases (checked automatically at creation and quarterly thereafter via Have I Been Pwned API integration).
- Password reuse across PineRidge systems is prohibited.
- Password managers are required. PineRidge provides 1Password Team licenses to all employees.

### 1.3 Principle of Least Privilege and the 90-Day Access Rule

- Access is granted based on the minimum permissions needed to perform job functions.
- Access requests are submitted via #access-requests on Slack and require manager approval.
- Elevated access (admin, root, production database) requires a business justification and expires after 90 days unless renewed. This is the 90-day access rule: no permanent elevated permissions.
- Emergency access ("break glass"): Available for on-call engineers during P1 incidents. Automatically expires after 4 hours. All actions logged and reviewed in postmortem.

### 1.4 Access Reviews

- Quarterly access reviews are conducted for all systems classified as Confidential or Restricted.
- Managers must certify that each direct report's access is still appropriate.
- Access not certified within 14 days of the review notification is automatically revoked.
- Accounts with no login activity for 60 days are automatically disabled. Reactivation requires a new access request.

### 1.5 Offboarding Access Revocation

- Upon an employee's departure (voluntary or involuntary):
  - All access is revoked within 1 hour of the official separation time.
  - Active sessions are terminated.
  - MFA tokens and security keys are deactivated.
  - Email access is removed; mailbox is retained for 90 days (legal hold) then deleted.
  - Shared credentials rotated within 24 hours if the departing employee had access.
- IT maintains an automated offboarding runbook triggered by the Workday departure event.

---

## Section 2: Device Security

### 2.1 Company-Issued Devices

All company-issued devices must:

- Have full-disk encryption enabled (FileVault on macOS, BitLocker on Windows).
- Run the company-managed endpoint detection and response (EDR) agent (CrowdStrike Falcon).
- Have automatic OS updates enabled. Critical security patches must be applied within 7 days of release.
- Have a screen lock that activates after 5 minutes of inactivity.
- Be registered in the mobile device management (MDM) system (Jamf for macOS, Intune for Windows).

### 2.2 Personal Devices (BYOD)

Personal devices may access PineRidge resources only under these conditions:

- The device is enrolled in Okta Device Trust.
- A device compliance check passes (OS version not more than 2 major versions behind, screen lock enabled, not jailbroken/rooted).
- Access is limited to: Slack, email, calendar. No source code, no client data, no production systems.
- PineRidge reserves the right to remotely wipe company data (not personal data) from enrolled personal devices if the device is lost, stolen, or the employee departs.

### 2.3 Lost or Stolen Devices

Report immediately to:
1. #security-incidents on Slack (or call the Security hotline: x4911)
2. Your manager

Response:
- Device remotely wiped within 4 hours of report.
- If the device contained unencrypted sensitive data (it shouldn't): incident escalated to P2.
- A replacement device is issued within 2 business days.
- If the lost device is recovered after wipe, IT will re-provision it.

---

## Section 3: Data Protection

### 3.1 Data Classification

| Classification | Description | Examples | Handling |
|---------------|-------------|----------|----------|
| Public | Non-sensitive, intended for external audiences | Blog posts, marketing materials, public docs | No restrictions |
| Internal | Business information for employees only | Meeting notes, project plans, internal wikis | Don't share externally; OK on approved tools |
| Confidential | Sensitive business or client data | Client contracts, financial reports, PII, source code | Encrypted at rest and in transit; access-logged |
| Restricted | Highest sensitivity | Credentials, encryption keys, security audit reports, incident forensics | Named-access only; secrets manager; never in email/Slack |

### 3.2 Data Handling Rules

- **Confidential and Restricted data must never be:**
  - Stored on local drives (use approved cloud storage with access controls)
  - Sent via unencrypted email (use PineRidge's encrypted email option or share a link from the secure system)
  - Posted in Slack channels (even private channels)
  - Stored in personal cloud storage (Google Drive personal, Dropbox personal, iCloud)
  - Shared with AI/LLM tools unless the tool is on the approved AI tools list (see Section 5)

- **Client data specifically:**
  - Must be stored in the client's designated data region (as per contract)
  - Cannot be used for internal testing or demos without explicit written client consent
  - Must be deleted within 90 days of contract termination (or per contractual data retention terms)
  - Anonymized or synthetic data must be used for all development and testing

### 3.3 Encryption Standards

- Data at rest: AES-256 minimum.
- Data in transit: TLS 1.3 minimum for all external connections. TLS 1.2 minimum for internal service-to-service.
- Database: Transparent Data Encryption (TDE) enabled on all RDS instances.
- Backups: Encrypted with a separate key managed by AWS KMS.
- Key rotation: Encryption keys rotated every 12 months. AWS-managed keys rotated automatically.

### 3.4 Data Retention and Disposal

| Data Type | Retention Period | Disposal Method |
|-----------|-----------------|-----------------|
| Client operational data | Per contract (typically 12–36 months post-termination) | Cryptographic erasure |
| Employee records (HR) | 7 years post-departure | Secure deletion |
| Financial records | 7 years | Secure deletion |
| System logs | 90 days (hot), 12 months (cold/archived) | Automatic expiration |
| Security logs | 24 months | Automatic expiration |
| Email | Active: indefinite; departed: 90 days then deleted | Secure deletion |
| Source code (version control) | Indefinite (Git history) | N/A (not deleted) |

---

## Section 4: Network Security

### 4.1 Corporate Network

- The corporate network is segmented: employee devices on one VLAN, servers on another, guest Wi-Fi isolated.
- Direct access from the corporate network to production environments is not permitted. All access goes through the VPN and bastion hosts.
- Guest Wi-Fi provides internet access only. No access to internal resources.

### 4.2 VPN

- Required for accessing internal resources from outside the office (home, travel, coworking spaces).
- Split-tunnel VPN: Only PineRidge traffic routes through VPN. Personal browsing goes direct.
- VPN sessions automatically disconnect after 12 hours and require re-authentication.
- If VPN software is not running, access to internal tools (except Slack and email) is blocked.

### 4.3 Cloud Infrastructure Security

- All AWS accounts are under a centralized AWS Organization with Service Control Policies (SCPs).
- Production accounts are separate from development/staging accounts.
- All infrastructure changes must go through Terraform (no manual console changes in production). Console changes in staging are permitted for experimentation but must be codified within 48 hours.
- Security groups follow "deny all" default. Only explicitly needed ports are opened.
- Public-facing resources: Reviewed weekly by the security team. Any new public endpoint requires a security review before deployment.
- AWS CloudTrail enabled on all accounts. Alerts on: root account usage, permission escalation, unusual API call patterns.

---

## Section 5: AI and LLM Usage Policy

### 5.1 Approved AI Tools

The following AI tools are approved for use with PineRidge data at the specified classification levels:

| Tool | Approved For | Restrictions |
|------|-------------|--------------|
| GitHub Copilot (Business) | Internal and Public code | No Confidential/Restricted data in prompts. No client code without client consent documented in project charter. |
| Amazon Bedrock (PineRidge account) | Up to Confidential | Must use PineRidge's own AWS account. Data stays in-region. |
| ChatGPT Team (PineRidge workspace) | Internal only | Do not paste Confidential data. Use for brainstorming, writing, and general questions only. |
| Grammarly Business | Internal and Public text | No Confidential content. |

### 5.2 Prohibited AI Uses

- Pasting Confidential or Restricted data into any AI tool not listed above.
- Using personal AI accounts (free ChatGPT, personal Copilot, Claude free tier) for any work-related task involving PineRidge or client data.
- Using AI-generated code in production without code review (standard PR process applies — AI-generated code is treated the same as human-written code).
- Uploading client data to any AI tool without explicit written client consent.
- Using AI tools to make employment decisions (hiring, firing, performance ratings) without human review.

### 5.3 Shadow AI

"Shadow AI" refers to the use of unapproved AI tools for work purposes. If you encounter a use case not covered by approved tools:

1. Submit a request via #security-requests with: tool name, intended use, data types involved.
2. Security team reviews within 5 business days.
3. If approved, the tool is added to the approved list with documented restrictions.
4. Do not use the tool before approval. This is a policy violation.

---

## Section 6: Incident Response

### 6.1 What Constitutes a Security Incident

Any event that:
- Compromises the confidentiality, integrity, or availability of PineRidge data or systems
- Involves unauthorized access (successful or attempted)
- Involves loss or theft of a device containing PineRidge data
- Involves a phishing email that was clicked (not just received)
- Involves suspected malware on a PineRidge device
- Involves unauthorized disclosure of Confidential or Restricted data

### 6.2 Reporting

- Report immediately to #security-incidents on Slack (24/7 monitored by Security team).
- Outside business hours: PagerDuty will notify the on-call security engineer.
- When reporting, include: what happened, when, what systems/data are involved (if known), and what actions you've taken.
- **Do not attempt to investigate or contain on your own** unless directed by the Security team or you are the on-call security engineer.

### 6.3 Response Timeline

| Phase | Timeline | Actions |
|-------|----------|---------|
| Detection | Immediate | Automated alerts or human report |
| Triage | Within 30 minutes | Severity assessment, initial scope |
| Containment | Within 2 hours (P1) / 8 hours (P2) | Stop the bleeding — isolate affected systems |
| Eradication | Within 24 hours (P1) / 72 hours (P2) | Remove the threat, patch the vulnerability |
| Recovery | Within 48 hours (P1) | Restore normal operations |
| Post-incident review | Within 5 business days | Blameless postmortem, action items |

### 6.4 Breach Notification

If a confirmed breach involves client data or personal information:

- Legal is notified within 1 hour of confirmation.
- Affected clients are notified within 72 hours (as required by PIPEDA and most contracts).
- If the breach affects 500+ individuals: Privacy Commissioner notified per regulatory requirements.
- CISO and CEO are briefed within 2 hours of a confirmed breach.

---

## Section 7: Acceptable Use

### 7.1 Acceptable Use of Company Systems

Company systems (laptops, networks, software) are provided for business purposes. Incidental personal use is permitted provided it:

- Does not interfere with job performance
- Does not consume excessive bandwidth or storage
- Does not violate any law or other PineRidge policy
- Does not expose PineRidge to security risk

### 7.2 Explicitly Prohibited Activities

- Accessing or attempting to access systems, data, or networks without authorization
- Installing unauthorized software (submit requests via #it-requests)
- Disabling or circumventing security controls (EDR, firewall, MFA)
- Using company systems for cryptocurrency mining
- Connecting unauthorized hardware to the corporate network (personal routers, NAS devices, Raspberry Pi, etc.)
- Sharing credentials with other employees or anyone external
- Using company resources for commercial activity unrelated to PineRidge
- Accessing inappropriate or illegal content

### 7.3 Monitoring Disclosure

PineRidge monitors:
- Network traffic patterns (not content of personal browsing)
- Endpoint security events (malware detection, policy violations)
- Access logs for Confidential and Restricted systems
- Email attachments (DLP scanning for Confidential data leaving the organization)

PineRidge does not:
- Read employee email content without legal cause
- Monitor keystrokes
- Record screens
- Track personal device location (even if enrolled in MDM)

---

## Section 8: Security Training

### 8.1 Required Training

| Training | Audience | Frequency | Delivery |
|----------|----------|-----------|----------|
| Security Awareness Fundamentals | All employees | Annually + within first week | LearnHub (45 min) |
| Phishing Simulation | All employees | Quarterly | Simulated emails |
| Secure Development Practices | Engineering | Annually | LearnHub (90 min) |
| Data Handling and Classification | All employees with Confidential access | Annually | LearnHub (30 min) |
| Incident Response for On-Call | Engineering on-call rotation | Annually | Live tabletop exercise |

### 8.2 Phishing Simulations

- Quarterly phishing simulations are sent to all employees.
- Clicking a simulated phishing link triggers an immediate educational pop-up (not punitive).
- Repeated clicks (3+ in a rolling 12-month period): mandatory additional training session with Security team.
- Reporting a simulated phish to #security-incidents earns recognition (tracked on the security leaderboard).

### 8.3 Security Champions Program

Each engineering squad has a designated Security Champion:

- Attends a monthly security champions meeting (30 min)
- Acts as first point of contact for security questions within the squad
- Reviews security-sensitive PRs (in addition to standard reviewers)
- Participates in annual threat modeling sessions for their squad's services

---

## Section 9: Third-Party and Vendor Security

### 9.1 Vendor Assessment

Before any new vendor is granted access to PineRidge data or systems:

- Security team conducts a risk assessment (timeline: 2–4 weeks).
- Vendors handling Confidential data must provide: SOC 2 Type II report (or equivalent), evidence of encryption practices, data residency confirmation.
- Vendors are classified into tiers:
  - **Tier 1 (Critical):** Handles Confidential/Restricted data or has admin access to systems. Full assessment, annual re-review.
  - **Tier 2 (Standard):** Handles Internal data or integrates with non-critical systems. Standard assessment, bi-annual re-review.
  - **Tier 3 (Low):** No data access, no system integration (e.g., physical office supplies). No security assessment required.

### 9.2 Vendor Access Controls

- Vendor access is provisioned to a separate identity group with explicit scope limitations.
- Vendor accounts require the same MFA standards as employee accounts.
- Access is time-bounded: expires at contract end date. Automatic revocation.
- Vendor activity in production systems is logged and reviewed monthly.
- Vendors are prohibited from subcontracting access without written PineRidge approval.

### 9.3 Data Sharing with Vendors

- A Data Processing Agreement (DPA) must be signed before any Confidential data is shared.
- Data shared with vendors must be the minimum necessary for the contracted service.
- Vendors must confirm deletion of PineRidge data within 30 days of contract termination.
- Annual audit right: PineRidge reserves the right to audit vendor security practices (exercised for Tier 1 vendors).

---

## Section 10: Physical Security

### 10.1 Office Access

- All offices use badge access (proximity cards). Visitors must sign in and be escorted.
- After-hours access (before 7 AM or after 8 PM): badge access works but is logged and reviewed weekly.
- Server rooms / network closets: Separate badge access required, limited to IT and Security teams.
- Tailgating (following someone through a secure door without badging): Report to #security-incidents. Not a "gotcha" — genuinely a security risk.

### 10.2 Clean Desk Policy

- Confidential documents must not be left visible on desks when the employee is away.
- Whiteboards in shared spaces must be erased after meetings if they contain non-Public information.
- Screens must be locked when stepping away (Ctrl+Cmd+Q on macOS, Win+L on Windows).
- Shred bins are provided in all offices for physical documents containing Internal or higher data.

### 10.3 Visitor Policy

- All visitors must be pre-registered by their PineRidge host (reception system).
- Visitors receive a dated badge that must be returned upon departure.
- Visitors are not permitted in server rooms, network closets, or the security operations area.
- Visitor Wi-Fi only (no corporate network access).
- Unescorted visitors in non-public areas should be politely challenged and directed to reception.

---

## Compliance and Consequences

### Reporting Violations

- Report suspected policy violations to #security-incidents or the anonymous Ethics Line (1-800-555-0172).
- Good-faith reports are protected under PineRidge's non-retaliation policy.

### Consequences of Non-Compliance

| Severity | Example | Typical Consequence |
|----------|---------|-------------------|
| Minor | Forgetting to lock screen once, clicking a phishing sim | Educational reminder |
| Moderate | Sharing Confidential data in Slack, repeated phishing clicks | Formal discussion with manager + Security, retraining |
| Serious | Disabling security tools, using unapproved AI with client data | Written warning, access restrictions |
| Critical | Deliberate data exfiltration, sharing credentials externally | Immediate termination, potential legal action |

---

*This policy applies to all PineRidge employees, contractors, and anyone with access to PineRidge systems.*

*Annual policy review: November 2026*
*Questions: security@pineridge.internal or #security-questions on Slack*
