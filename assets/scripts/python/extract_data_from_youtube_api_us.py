import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
API_VERSION = 'v3'

youtube = build('youtube', API_VERSION, developerKey=API_KEY)


def get_channel_stats(youtube, channel_id):
    request = youtube.channels().list(
        part='snippet, statistics',
        id=channel_id
    )
    response = request.execute()

    if response.get('items'):
        data = dict(
            channel_id=channel_id,
            channel_name=response['items'][0]['snippet']['title'],
            total_subscribers=response['items'][0]['statistics']['subscriberCount'],
            total_views=response['items'][0]['statistics']['viewCount'],
            total_videos=response['items'][0]['statistics']['videoCount'],
        )
        return data
    else:
        return None


# Read the US dataset
df = pd.read_csv("youtube_data_united-states.csv")

# Extract channel IDs from the NAME column (format: "Channel Name @ChannelID")
df['channel_id'] = df['NAME'].str.split('@').str[-1]

# Get unique channel IDs to avoid redundant API calls
unique_channel_ids = df['channel_id'].unique()

# Fetch stats for each unique channel ID
channel_stats = []
for channel_id in unique_channel_ids:
    stats = get_channel_stats(youtube, channel_id)
    if stats is not None:
        channel_stats.append(stats)

# Build a stats DataFrame keyed on channel_id so the merge is reliable
stats_df = pd.DataFrame(channel_stats)

# Merge on channel_id instead of relying on index alignment
combined_df = df.merge(stats_df, on='channel_id', how='left')

# Save the result
combined_df.to_csv('updated_youtube_data_us.csv', index=False)

print(f"Done. {len(channel_stats)} channels matched out of {len(unique_channel_ids)} unique IDs.")
print(combined_df.head(10))

from sqlalchemy import create_engine

engine = create_engine('sqlite:///youtube_data.db')
combined_df.to_sql('us_channels', engine, if_exists='replace', index=False)
print("SQLite database created: youtube_data.db")
