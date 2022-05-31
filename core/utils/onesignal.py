from onesignal_sdk.client import Client
from config import (
    ONESIGNAL_APP_ID,
    ONESIGNAL_REST_API_KEY,
    ONESIGNAL_USER_AUTH_KEY
)

client = Client(
    app_id=ONESIGNAL_APP_ID,
    rest_api_key=ONESIGNAL_REST_API_KEY,
    user_auth_key=ONESIGNAL_USER_AUTH_KEY
)

def sendNotificationToTokens(tokens, title, message):
    notification_body = {
        'include_player_ids': tokens,
        'contents': {
            'en': message
        },
        'headings': {
            'en': title
        }
    }
    response = client.send_notification(notification_body)
    return response


def sendNotificationToTopic(topics, title, message):
    notification_body = {
        'included_segments': topics,
        'contents': {
            'en': message
        },
        'headings': {
            'en': title
        }
    }
    response = client.send_notification(notification_body)
    return response
