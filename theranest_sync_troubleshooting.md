# TheraNest Tablet-to-Web Sync Troubleshooting Checklist

## Device: Samsung S10+ Tablet | Admin Platform: Insora/TheraNest Web

---

## Step 1: Confirm Where Notes Exist

- [ ] Open the TheraNest app/site on your **tablet** and verify you can see your notes
- [ ] Log into TheraNest on a **desktop/laptop** using your own credentials
- [ ] Check if the same notes appear on desktop
  - **If yes on both:** The issue is admin visibility/permissions (go to Step 4)
  - **If tablet only:** The notes never synced (go to Step 2)
  - **If neither:** The notes may have been lost — check browser history/cache on the tablet

---

## Step 2: Rule Out Sync Failures

- [ ] Confirm your tablet has a stable internet connection (Wi-Fi or cellular)
- [ ] Open a note on the tablet, make a minor edit (add a space), and re-save
- [ ] Check if the edited note now appears on the desktop site
- [ ] Force-close the TheraNest app or browser on the tablet and reopen it
- [ ] Clear the browser cache on the tablet (Chrome > Settings > Privacy > Clear Browsing Data)
- [ ] Log out of TheraNest on the tablet and log back in
- [ ] Retry saving a note and verify it appears on the desktop

---

## Step 3: Check Note Status (Draft vs. Signed)

- [ ] Open a recent session note on the tablet
- [ ] Look for the note status — it will say **Draft**, **Signed**, or **Locked**
- [ ] If the note is in **Draft** status, tap **"Sign & Lock"** or **"Complete"** to finalize it
- [ ] After signing, check whether the note now appears in admin reports
- [ ] Repeat for all session notes that the admin reports as missing

**Key point:** Draft notes do not appear in most reports and may not be visible to your administrator.

---

## Step 4: Verify Note-to-Appointment Linkage

- [ ] Open the TheraNest **calendar** on your tablet
- [ ] Tap on a specific appointment where you documented a note
- [ ] Confirm the note is attached to that appointment (not free-floating)
- [ ] If the note is not linked, re-create it by:
  1. Opening the appointment from the calendar
  2. Selecting **"Add Session Note"** from within the appointment
  3. Copying your documentation into the new linked note
  4. Signing and locking the note

**Key point:** Notes created outside the calendar/appointment flow may not be associated with appointment time slots and will not appear in appointment-based reports.

---

## Step 5: Check Permissions and Admin Visibility

- [ ] Ask your administrator to look under **your staff profile** for any notes (including drafts)
- [ ] Confirm your account role has the correct permissions to create and submit notes
- [ ] Ask the admin to check report filters — ensure they are not filtering by note type, date range, or status in a way that excludes your notes
- [ ] Verify your admin is searching under the correct client records

---

## Step 6: App/Browser Environment

- [ ] Confirm you are accessing TheraNest through **Chrome** (recommended browser for Android)
- [ ] Check that your browser is up to date (Chrome > Settings > About Chrome)
- [ ] Verify you are on the current TheraNest URL (not a cached/bookmarked older version)
- [ ] Disable any battery optimization or data saver settings that may interrupt background sync
  - Samsung Settings > Apps > Chrome > Battery > Unrestricted
  - Samsung Settings > Connections > Data Saver > off (or add Chrome as an exception)
- [ ] Disable any VPN or firewall apps that may block TheraNest traffic

---

## Step 7: Prevent Future Issues

- [ ] Always start notes **from the appointment on the calendar**, not from a standalone notes section
- [ ] Always tap **"Sign & Lock"** at the end of each session before closing
- [ ] After saving a note, briefly switch to the TheraNest desktop site to confirm it appeared
- [ ] Keep your browser and tablet OS updated
- [ ] Avoid using the tablet in areas with poor or intermittent connectivity during sessions

---

## Still Not Resolved?

- Contact TheraNest support at **support@theranest.com** or through the in-app help chat
- Provide them with:
  - Your account email
  - The specific appointment dates/times where notes are missing
  - The device and browser you are using (Samsung S10+, Chrome version)
  - Screenshots showing the note exists on your tablet but not in reports
