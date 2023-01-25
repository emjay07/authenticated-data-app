import streamlit as st
import boto3 as boto
from botocore.exceptions import ClientError

# constants
k_REGION = "us-west-2"
k_ACCOUNT_ID = "110561467685"
k_DASHBOARD_ID = "87f65650-a75c-427d-8d89-6d46384030f8"
k_ROLE_ARN = "arn:aws:iam::110561467685:role/Supermarine-Quicklit-GenerateEmbedUrlForRegisteredUser"
k_OPEN_ID_TOKEN = ""
k_DOMAINS = ["https://*.streamlit.app"]
k_NAMESPACE = "default"

def create_qs_client(region_id, role_arn):
    # Create STS client
    sts = boto.client('sts')

    # Assume proper role
    assumed_role = sts.assume_role(
        RoleArn = role_arn,
        #WebIdentityToken = openIdToken,
        RoleSessionName = "AssumeRole_RegisteredUser"
    )

    # Get new credentials
    creds = assumed_role['Credentials']

    # Create quicksight client
    qs_client = boto.client(
        'quicksight',
        region_name = region_id,
        aws_access_key_id = creds['AccessKeyId'],
        aws_secret_access_key = creds['SecretAccessKey'],
        aws_session_token = creds['SessionToken']
    )

    return qs_client

def register_user(qs_client, account_id, qs_namespace, user_email):

    try:
        response = qs_client.register_user(
            AwsAccountId = account_id,
            Namespace = qs_namespace,
            Email = user_email,
            UserName = user_email,
            IdentityType = "QUICKSIGHT",
            UserRole = "READER"
        )

        return response

    except ClientError as e:
        st.write(e)
        return {}   


def list_users(qs_client, account_id, qs_namespace):

    # Note: This does not properly paginate past 100.
    try:
        users = qs_client.list_users(
            AwsAccountId = account_id,
            MaxResults = 100,
            Namespace = qs_namespace
        )

        user_list = users["UserList"]

        # debug
        st.write(user_list)

        return user_list
    
    except ClientError as e:
        st.write(e)
        return {}

def generate_embedding_url_for_registered_user(qs_client, account_id, dashboard_id, user_arn, allowed_domains):

    try:
        response = qs_client.generate_embed_url_for_registered_user(
            AwsAccountId = account_id,
            ExperienceConfiguration = {
                'Dashboard': {
                    'InitialDashboardId': dashboard_id
                }
            },
            UserArn = user_arn,
            AllowedDomains = allowed_domains,
            SessionLifetimeInMinutes = 600
        )
            
        return response

    except ClientError as e:
        st.write(e)
        return {}

def submit_callback(user_email: str):
    qs_client = create_qs_client(k_REGION, k_ROLE_ARN)

    already_registered_users = list_users(qs_client, k_ACCOUNT_ID, k_NAMESPACE)

    user_arn = ""
    for user in already_registered_users:

        # debug
        st.write(user)

        if user['Email'] == user_email:
            user_arn = user['Arn'] # this is probably bad and not secure. 
            break

    if user_arn == "":
        new_user_response = register_user(qs_client, k_ACCOUNT_ID, k_NAMESPACE, user_email)

        register_url = new_user_response['UserInvitationUrl']
        st.components.v1.iframe(register_url, width=None, height=1000, scrolling=True)

        user_arn = new_user_response['User']['Arn']

    url_response = generate_embedding_url_for_registered_user(qs_client, k_ACCOUNT_ID, k_DASHBOARD_ID, user_arn, k_DOMAINS)

    # render dashboard
    k_EMBED_KEY = "EmbedUrl"
    if k_EMBED_KEY in url_response:
        html = url_response[k_EMBED_KEY]
        st.components.v1.iframe(html, width=None, height=1000, scrolling=True)
    else: 
        st.write("No Embedded URL found")


st.title("Registered Users - QuickSight App")

st.write("Please enter your email address to get started")

user_email = st.text_input("Email Address", value="example@domain.com")
clicked = st.button("Submit", on_click=submit_callback, args=(user_email, ) )
