import argparse
import requests
import json
from oauth2client.client import GoogleCredentials

import smtplib, ssl, getpass, time

ROOT = 'https://api.firecloud.org/api'

# Sends a GET request to grab the current status of the submission
def get_submission_status(namespace,name,submission_id):
    request = f'{ROOT}/workspaces/{namespace}/{name}/submissions/{submission_id}'
    security_header = generate_header()
    response = requests.get(request,headers=security_header)
    if response.status_code not in [200]:
        return response.status_code, response.content
    else:
        return response.status_code, response.json()

# Makes a get request to the api every 300 seconds (default) 
# When the status of the jobs is no longer 'Running' or 'Submitted'
# Login to gmail and sends a email to yourself 
def set_up_email_client(email,namespace,name,submission_id,wait_interval=300):
    # Sets up gmail client
    smtp_server = "smtp.gmail.com"
    port = 465  # For SSL
    pwd = getpass.getpass(prompt="Email Password: ")
    context = ssl.create_default_context()
    
    # Sending email to yourself
    sender_email = email  
    receiver_email = email  
     
    status_code,status_json = get_submission_status(namespace,name,submission_id)
    submission_status = status_json['status']
        
    # Ask for submission status info every 300 seconds (5 minutes, default) until 
    # the submission status is no longer "Running" then send the email
    while status_code == 200 and (submission_status == 'Running' or submission_status == 'Submitted'):
        time.sleep(wait_interval)
        status_code,status_json = get_submission_status(namespace,name,submission_id)
        print(status_code)
        print(status_json)
        submission_status = status_json['status']
    
    if status_code == 200:
        
        message = f"""\
        Subject: Terra Submission Finished\n

        The status of the submission {namespace}/{name}/{submission_id} is: {submission_status}."""

        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            print("Logging in ...")
            server.login(sender_email, pwd)
            print("Sending mail ...")
            server.sendmail(sender_email, receiver_email, message)
    else:
        print("Request Error")

def generate_header():
    credentials = GoogleCredentials.get_application_default()
    token = credentials.get_access_token().access_token
    return {"Authorization": f"bearer {token}", "Content-Type": "application/json"}

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(prog='Notify when submission finishes', description="Set up email notification")
    arg_parser.add_argument('--namespace', required=True, help='Workspace namespace')
    arg_parser.add_argument('--name', required=True, help='Workspace name')
    arg_parser.add_argument('--email', required=True, help='Email to Notify')
    arg_parser.add_argument('--submission_id', required=True, help='Job Submission ID')
    arg_parser.add_argument('--wait_interval',type=int,help="Seconds to wait before checking status again")
    args = arg_parser.parse_args()
    set_up_email_client(args.email,args.namespace,args.name,args.submission_id,wait_interval=args.wait_interval)
