// Campaign Respond — Registration Webhook
// Deploy as Google Apps Script Web App attached to your "Campaign Respond Users" sheet
//
// Setup:
// 1. Create a Google Sheet called "Campaign Respond Users"
// 2. Add headers in Row 1: Timestamp | Name | Email | Candidate | Office | State | Platform | Version
// 3. Go to Extensions → Apps Script, paste this code
// 4. Deploy → New Deployment → Web App → Anyone can access → Deploy
// 5. Copy the web app URL and paste it into install.sh (REGISTRATION_URL variable)

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();

    sheet.appendRow([
      new Date().toISOString(),
      data.name || "",
      data.email || "",
      data.candidate || "",
      data.office || "",
      data.state || "",
      data.platform || "",
      data.version || "1.0.0"
    ]);

    // Send Teddy a notification email for each new install
    var subject = "New Campaign Respond Install: " + (data.candidate || "Unknown");
    var body = "New install registered:\n\n"
      + "Name: " + (data.name || "—") + "\n"
      + "Email: " + (data.email || "—") + "\n"
      + "Candidate: " + (data.candidate || "—") + "\n"
      + "Office: " + (data.office || "—") + "\n"
      + "State: " + (data.state || "—") + "\n"
      + "Platform: " + (data.platform || "—") + "\n"
      + "Time: " + new Date().toLocaleString();

    GmailApp.sendEmail("ctgiii@pm.me", subject, body);

    return ContentService.createTextOutput(
      JSON.stringify({ status: "ok" })
    ).setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService.createTextOutput(
      JSON.stringify({ status: "error", message: err.toString() })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService.createTextOutput(
    JSON.stringify({ status: "ok", service: "Campaign Respond Registration" })
  ).setMimeType(ContentService.MimeType.JSON);
}
