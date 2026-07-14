"""
Email Receipt Service (FR3 / UC4)
Sends a styled HTML email with case reference details to the complainant.
Falls back to plain text if HTML rendering fails.
"""

from flask_mail import Message
from flask import current_app
from app import mail

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Case Reference Receipt</title>
  <style>
    body  {{ margin:0; padding:0; background:#f4f6f9; font-family:Arial,sans-serif; }}
    .wrap {{ max-width:600px; margin:30px auto; background:#fff;
             border-radius:10px; overflow:hidden;
             box-shadow:0 4px 20px rgba(0,0,0,.12); }}
    .hdr  {{ background:linear-gradient(180deg,#003d7a 0%,#0052a3 100%);
             padding:30px 35px; text-align:center;
             border-bottom:5px solid #0066cc; }}
    .hdr h1 {{ color:#fff; margin:0 0 6px; font-size:20px;
               text-transform:uppercase; letter-spacing:1px; }}
    .hdr p  {{ color:#cbd5e1; margin:0; font-size:13px; }}
    .body {{ padding:30px 35px; }}
    .intro {{ color:#334155; font-size:15px; margin-bottom:22px; line-height:1.6; }}
    .ref-box {{ background:#eff6ff; border:2px solid #bfdbfe;
                border-radius:8px; padding:18px; text-align:center;
                margin-bottom:24px; }}
    .ref-box .label {{ font-size:12px; color:#64748b; font-weight:600;
                       text-transform:uppercase; letter-spacing:.8px; }}
    .ref-box .code  {{ font-size:28px; font-weight:900; color:#1e3a8a;
                       letter-spacing:2px; font-family:monospace; margin:6px 0 0; }}
    .info-table {{ width:100%; border-collapse:collapse; margin-bottom:24px; }}
    .info-table td {{ padding:10px 12px; border-bottom:1px solid #f1f5f9;
                      font-size:14px; }}
    .info-table td:first-child {{ color:#64748b; font-weight:600; width:40%;
                                  text-transform:uppercase; font-size:12px; }}
    .info-table td:last-child  {{ color:#1e293b; font-weight:500; }}
    .btn  {{ display:block; width:fit-content; margin:0 auto 24px;
             padding:13px 32px; background:#0066cc; color:#fff !important;
             text-decoration:none; border-radius:6px; font-weight:700;
             font-size:14px; text-align:center; }}
    .notice {{ background:#fff8e1; border-left:4px solid #f59e0b;
               padding:14px 16px; border-radius:4px; font-size:13px;
               color:#92400e; margin-bottom:18px; }}
    .footer {{ background:#f8fafc; padding:18px 35px; text-align:center;
               font-size:12px; color:#94a3b8; border-top:1px solid #e2e8f0; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hdr">
      <h1>Anti-Carnapping Unit — MPD</h1>
      <p>Philippine National Police · Manila Police District</p>
    </div>
    <div class="body">
      <p class="intro">
        Dear <strong>{complainant_name}</strong>,<br><br>
        Your carnapping complaint has been officially received and recorded
        in our system. Please keep this email for your reference.
      </p>

      <div class="ref-box">
        <div class="label">Your Reference Number</div>
        <div class="code">{reference_no}</div>
      </div>

      <table class="info-table">
        <tr><td>Complainant</td><td>{complainant_name}</td></tr>
        <tr><td>Incident Date</td><td>{incident_date}</td></tr>
        <tr><td>Incident Location</td><td>{incident_location}</td></tr>
        <tr><td>Vehicle</td><td>{vehicle_details}</td></tr>
        <tr><td>Investigator (IOC)</td><td>{ioc}</td></tr>
        <tr><td>Status</td><td><strong>Unsolved</strong></td></tr>
      </table>

      <div class="notice">
        📱 <strong>Track your case anytime:</strong> Scan the QR code on your
        printed reference slip, or use the link below.
      </div>

      <a href="{track_url}" class="btn">🔍 Track My Case Online</a>

      <p style="font-size:13px;color:#64748b;text-align:center;">
        If you have questions, please visit the Anti-Carnapping Unit in person
        with this reference number.
      </p>
    </div>
    <div class="footer">
      This is an automated message. Do not reply to this email.<br>
      PNP Anti-Carnapping Unit · Manila Police District
    </div>
  </div>
</body>
</html>
"""

_PLAIN_TEMPLATE = """\
PNP Anti-Carnapping Unit — Manila Police District
Case Reference Receipt

Dear {complainant_name},

Your carnapping complaint has been officially recorded.

Reference Number : {reference_no}
Complainant      : {complainant_name}
Incident Date    : {incident_date}
Incident Location: {incident_location}
Vehicle          : {vehicle_details}
Investigator (IOC): {ioc}
Status           : Unsolved

Track your case here: {track_url}

Please keep this email for your records.
-- PNP Anti-Carnapping Unit, Manila Police District
"""


def send_reference_email(
    recipient: str,
    reference_no: str,
    track_url: str,
    complainant_name: str = "Complainant",
    incident_date: str = "N/A",
    incident_location: str = "N/A",
    vehicle_details: str = "N/A",
    ioc: str = "N/A",
) -> tuple[bool, str]:
    """
    Send a styled HTML receipt email to the complainant (FR3 / UC4).

    Args:
        recipient         : Email address of the complainant
        reference_no      : Unique case reference number
        track_url         : URL for the public case tracking page
        complainant_name  : Full name of the complainant
        incident_date     : Date of the incident
        incident_location : Location of the incident
        vehicle_details   : Brief vehicle description

    Returns:
        (success: bool, message: str)
    """
    if not current_app.config.get("MAIL_USERNAME"):
        return False, "Email not configured — MAIL_USERNAME is missing in .env."

    ctx = {
        "reference_no": reference_no,
        "track_url": track_url,
        "complainant_name": complainant_name or "Complainant",
        "incident_date": incident_date or "N/A",
        "incident_location": incident_location or "N/A",
        "vehicle_details": vehicle_details or "N/A",
        "ioc": ioc or "N/A",
    }

    try:
        msg = Message(
            subject=f"[PNP ACU] Case Reference Receipt — {reference_no}",
            recipients=[recipient],
            body=_PLAIN_TEMPLATE.format(**ctx),
            html=_HTML_TEMPLATE.format(**ctx),
            sender=current_app.config.get("MAIL_USERNAME"),
        )
        mail.send(msg)
        return True, "Email sent successfully."

    except Exception as exc:
        current_app.logger.error(f"Email send error to {recipient}: {exc}")
        return False, f"Email delivery failed: {exc}"


_STATUS_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Case Status Update</title>
  <style>
    body  {{ margin:0; padding:0; background:#f4f6f9; font-family:Arial,sans-serif; }}
    .wrap {{ max-width:600px; margin:30px auto; background:#fff;
             border-radius:10px; overflow:hidden;
             box-shadow:0 4px 20px rgba(0,0,0,.12); }}
    .hdr  {{ background:linear-gradient(180deg,#003d7a 0%,#0052a3 100%);
             padding:30px 35px; text-align:center;
             border-bottom:5px solid #0066cc; }}
    .hdr h1 {{ color:#fff; margin:0 0 6px; font-size:20px; text-transform:uppercase; }}
    .body {{ padding:30px 35px; }}
    .intro {{ color:#334155; font-size:15px; margin-bottom:22px; line-height:1.6; }}
    .status-box {{ background:#eff6ff; border:2px solid #bfdbfe;
                   border-radius:8px; padding:18px; text-align:center;
                   margin-bottom:24px; }}
    .status-box .label {{ font-size:12px; color:#64748b; font-weight:600; text-transform:uppercase; }}
    .status-box .code  {{ font-size:24px; font-weight:900; color:#1e3a8a; margin:6px 0 0; }}
    .btn  {{ display:block; width:fit-content; margin:0 auto 24px;
             padding:13px 32px; background:#0066cc; color:#fff !important;
             text-decoration:none; border-radius:6px; font-weight:700; }}
    .footer {{ background:#f8fafc; padding:18px 35px; text-align:center;
               font-size:12px; color:#94a3b8; border-top:1px solid #e2e8f0; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hdr">
      <h1>Anti-Carnapping Unit — MPD</h1>
    </div>
    <div class="body">
      <p class="intro">
        Dear <strong>{complainant_name}</strong>,<br><br>
        There has been an update regarding your case (<strong>{reference_no}</strong>).
      </p>
      <div class="status-box">
        <div class="label">New Case Status</div>
        <div class="code">{new_status}</div>
      </div>
      <a href="{track_url}" class="btn">🔍 Track My Case Online</a>
    </div>
    <div class="footer">This is an automated message.</div>
  </div>
</body>
</html>
"""


def send_status_update_email(
    recipient: str,
    reference_no: str,
    track_url: str,
    complainant_name: str,
    new_status: str,
) -> tuple[bool, str]:
    if not current_app.config.get("MAIL_USERNAME"):
        return False, "Email not configured."

    ctx = {
        "reference_no": reference_no,
        "track_url": track_url,
        "complainant_name": complainant_name,
        "new_status": str(new_status).upper(),
    }

    try:
        msg = Message(
            subject=f"[PNP ACU] Case Status Update — {reference_no}",
            recipients=[recipient],
            html=_STATUS_HTML_TEMPLATE.format(**ctx),
            sender=current_app.config.get("MAIL_USERNAME"),
        )
        mail.send(msg)
        return True, "Email sent successfully."
    except Exception as exc:
        current_app.logger.error(f"Email send error: {exc}")
        return False, f"Email failed: {exc}"
