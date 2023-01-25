import streamlit as st
import boto3 as boto
from botocore.exceptions import ClientError

# constants
k_REGION = "us-west-2"
k_ACCOUNT_ID = "110561467685"
k_DASHBOARD_ID = '87f65650-a75c-427d-8d89-6d46384030f8'
k_USER_ARN = ""
k_ROLE_ARN = "arn:aws:iam::110561467685:role/Supermarine-Quicklit-GenerateEmbedUrlForAnonymousUser"
k_OPEN_ID_TOKEN = ""
k_DOMAINS = ["https://*.streamlit.app"]

# Function to generate embedded URL
# regionId: AWS Region ID  
# accountId: AWS account ID
# dashboardId: Dashboard ID to embed
# userArn: arn of registered user
# allowedDomains: Runtime allowed domain for embedding
# openIdToken: Token to assume role with roleArn
# roleArn: IAM user role to use for embedding
def generateEmbeddingURLForRegisteredUser(regionId, accountId, dashboardId, userArn, allowedDomains, openIdToken, roleArn):
    # Create STS client
    sts = boto.client('sts')

    # Assume proper role
    assumed_role = sts.assume_role(
        RoleArn = roleArn,
        WebIdentityToken = openIdToken,
        RoleSessionName = "AssumeRole_RegisteredUser"
    )

    # Get new credentials
    creds = assumed_role['Credentials']

    # Create quicksight client
    quicksightClient = boto.client(
        'quicksight',
        region_name = regionId,
        aws_access_key_id = creds['AccessKeyId'],
        aws_secret_access_key = creds['SecretAccessKey'],
        aws_session_token = creds['SessionToken']
    )
    
    try:
        response = quicksightClient.generate_embed_url_for_registered_user(
            AwsAccountId = accountId,
            ExperienceConfiguration = {
                'Dashboard': {
                    'InitialDashboardId': dashboardId
                }
            },
            UserArn = userArn,
            AllowedDomains = allowedDomains,
            SessionLifetimeInMinutes = 600
        )
            
        return response

    except ClientError as e:
        st.write(e)
        return {}

response = generateEmbeddingURLForRegisteredUser(k_REGION, k_ACCOUNT_ID, k_DASHBOARD_ID, k_USER_ARN, k_DOMAINS, k_OPEN_ID_TOKEN, k_ROLE_ARN)

# render dashboard
if "EmbedUrl" in response:
    html = response["EmbedUrl"]
    st.components.v1.iframe(html, width=None, height=1000, scrolling=True)
else: 
    st.write("No Embedded URL found")
