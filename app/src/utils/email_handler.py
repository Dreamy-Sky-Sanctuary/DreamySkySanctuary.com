# Import the following module 
from email.mime.text import MIMEText 
from email.mime.image import MIMEImage 
from email.mime.application import MIMEApplication 
from email.mime.multipart import MIMEMultipart 
import smtplib 
import os

from fastapi import Request
import yagmail

from src.config import config
from src.schemas.Login import UserDB 

defualt_subject = "Password Reset"


async def send_password_reset_mail(request: Request, user: UserDB, token: str) -> None: 
    print(f"Sending password reset email to {user.email}")

    if request:
        host = request.headers.get("host")
    else:
        host = "localhost"
    
    complete_html = f'<p>Hello {user.username},</p><p></p><p>Greetings from the Dreamy Sky Team,</p><p>We received a request to reset the password for the account associated with this e-mail address. Click the link below to reset your password for your account:</p><p>https://{host}/reset-password/{token}</p><p>If clicking the link doesn\'t work, you can copy and paste the link into your web browser\'s address bar. You will be able to create a new password for your account after clicking the link above.</p><p>If you did not request to have your password reset, you can safely ignore this email. Or contact us via email at: contact@dreamyskysanctuary.com</p><p>Thank you for using the Dreamy Sky Sanctuary website!</p><p></p><p>Sincerely,</p><p>The Dreamy Sky Team</p><table class="table__StyledTable-sc-1avdl6r-0 bztkJx" style="" border="0" cellspacing="0" cellpadding="0"><tbody><tr><td><table class="table__StyledTable-sc-1avdl6r-0 bztkJx" style="" border="0" cellspacing="0" cellpadding="0"><tbody><tr><td style="" width="150"><span class="template3__ImageContainer-sc-vj949k-0 gQAWto" style=""><img class="image__StyledImage-sc-hupvqm-0 ctEjzA" style="" src="https://dreamyskysanctuary.com/public/imgs/icon.webp" width="130"></span></td><td style=""><h2 class="name__NameContainer-sc-1m457h3-0 iegFqm" style="margin-top: 0px;margin-bottom: 10px;"><span>Dreamy</span><span>&nbsp;</span><span>Sky Team</span></h2><table class="table__StyledTable-sc-1avdl6r-0 bztkJx" style="" border="0" cellspacing="0" cellpadding="0"><tbody><tr style=""><td style=""><span class="company-details__CompanyContainer-sc-j5pyy8-0 jyMkYn" style=""><span>Contact</span><span>&nbsp;|&nbsp;</span><span>Dreamy Sky Sanctuary</span></span></td></tr><tr style=""><td style=""><a href="https://discord.gg/XQRRDNZQmq">Join Our Discord</a></td></tr></tbody></table></td><td width="30"><div style="">&nbsp;</div></td><td class="color-divider__Divider-sc-1h38qjv-0 iqkkET" style="" width="1" height="auto">&nbsp;</td><td width="30"><div style="">&nbsp;</div></td><td style=""><table class="table__StyledTable-sc-1avdl6r-0 bztkJx" style="" border="0" cellspacing="0" cellpadding="0"><tbody><tr style=""><td style=""><a class="contact-info__ExternalLink-sc-mmkjr6-2 ixYHUl" style="" href="tel:+31 6 20636924"><span>+31 6 20636924</span></a></td></tr><tr style=""><td style=""><a class="contact-info__ExternalLink-sc-mmkjr6-2 ixYHUl" style="" href="mailto:contact@dreamyskysanctuary.com"><span>contact@dreamyskysanctuary.com</span></a></td></tr><tr style=""><td style=""><a class="contact-info__ExternalLink-sc-mmkjr6-2 ixYHUl" style="" href="//DreamySkySanctuary.com"><span>DreamySkySanctuary.com</span></a></td></tr></tbody></table></td></tr></tbody></table></td></tr><tr><td><table class="table__StyledTable-sc-1avdl6r-0 bztkJx" style="" border="0" cellspacing="0" cellpadding="0"><tbody><tr><td class="color-divider__Divider-sc-1h38qjv-0 iqkkET" style="" width="auto" height="1">&nbsp;</td></tr><tr><td height="10">&nbsp;</td></tr></tbody></table></td></tr></tbody></table>'

    await send_email(user.email, defualt_subject, complete_html)

    print("Email sent")

async def send_email(to_email: str, subject: str, body: str) -> None:
    yag = yagmail.SMTP(user=config.SMTP_USERNAME, password=config.SMTP_PASSWORD, host=config.SMTP_SERVER, port=config.SMTP_PORT)
    yag.send(
        to=to_email, 
        subject=subject, 
        contents=body
    )