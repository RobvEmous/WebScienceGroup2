from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
import matplotlib.pyplot as plt
import random
from threading import Thread
import json

DEVELOPER_KEY = "DL}dV|GIMwtMpF3F0jMpmEO;bunFJU}PqEWYvf\\"
YOUTUBE_READONLY_SCOPE = "https://www.googleapis.com/youtube/v3/activities"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


class YouTubeCrawler:

    youtube_api = None

    def __init__(self, n):
        """
        Initializes the Youtube API connection.

        :param n: the cyclic encryption key
        """
        self.youtube_api = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                             developerKey=self.very_safe(DEVELOPER_KEY, n))


    def get_song_info(self, video_id, parts):
        """
        Gets the requested parts of a song using the API.

        :param video_id: the id of the video on YouTube
        :param parts: the requested parts (snippet, id etc)
        :return: the resulting data (JSON)
        """
        search_response = self.youtube_api.videos().list(
            part=parts,
            id=video_id
        ).execute()
        return search_response['items'][0]

    def search_recommended(self, start_video_id, max_results):
        """
        Gets the recommended songs of the base video using the API.

        :param start_video_id: the id of the base video
        :param max_results: the requested number of recommendations
        :return: the recommended songs as a tuple list of id's and titles
        """
        search_response = self.youtube_api.search().list(
            part="snippet",
            type="video",
            relatedToVideoId=start_video_id,
            maxResults=max_results
        ).execute()
        videos = []
        for search_result in search_response.get("items", []):
            if search_result["id"]["kind"] == "youtube#video":
                videos.append((search_result["id"]["videoId"], search_result["snippet"]["title"]))
        return videos

    def very_safe(self, txt, n):
        """
        Very simple encryption/decryption of the key to avoid
        it being in the code in plaintext.

        :param txt: the encrypted/decrypted tekst
        :param n: the cycle number
        :return: the encrypted/decrypted text
        """
        crypt = ""
        for b in txt:
            crypt += chr(ord(b) + n)
        return crypt


def wait_for_input():
    """
    Blocking function which waits for any input.

    :return: the input
    """
    return input('')


def investigate_view_power_law(video_data):
    """
    Plots the distribution of the number of views among the videos

    :param video_data: the view information of video's
    """
    total_views = 0
    for video in video_data:
        total_views += video[1][0]
    xvals, yvals = [], []
    for index, song in enumerate(video_data):
        total_views -= song[1][0]
        xvals.append(total_views)
        yvals.append(index)
    fig = plt.figure()
    plt.plot(xvals, yvals)
    fig.suptitle('Distribution of number of views among video\'s')
    plt.ylabel('Number of video\'s')
    plt.xlabel('Total number of views')
    plt.show()

def create_own_data(youtube_api, start_video_id, num_hops, num_recommendations, min_views, random_choice):
    """
    Crawls YouTube starting with the specified behavior from the start video and writes
    the results in a JSON file.

    :param youtube_api: the Youtube API connection.
    :param start_video_id: the id of the base video
    :param num_hops: number of video-search iterations to make
    :param num_recommendations: number of recommendations used to choose from
    :param min_views: video's with less views will be skipped
    :param random_choice: whether to choose randomly from the recommendations,
     or with 80% chance choose the most viewed one and 20% chance choose a ramdom one
    :return: the fetched video's sorted to number of views
    """

    stop_thread = Thread(target = wait_for_input, args=())
    stop_thread.setDaemon(True)
    stop_thread.start()
    random.seed()

    json_data = []
    vid_dict = dict()
    song_info = yt.get_song_info(start_video_id, "snippet,statistics")
    curr_video = (start_video_id, song_info['snippet']['title'])
    print("YouTube crawler started - type any key to stop")
    print("Start video (1): " + str(curr_video[1]) + " (" + str(curr_video[0]) + ")")
    vid_dict[curr_video[0]] = (int(song_info['statistics']['viewCount']), curr_video[1])

    for i in range(2, num_hops + 1):
        try:
            # get recommended video's
            results = yt.search_recommended(curr_video[0], num_recommendations)
            print("Recommended videos:")
            for j in range(0, len(results)):
                print(str(j + 1) + ": " + str(results[j][1]) + " (" + str(results[j][0]) + ")")
            views = 0
            data = []

            # analyse recommended video's
            for result in results:
                data_item = yt.get_song_info(result[0], "statistics,snippet")
                views = int(data_item['statistics']['viewCount'])
                if views >= min_views:
                    json_data.append(data_item)
                    data.append(data_item)
                    if result[0] not in vid_dict:
                        vid_dict[result[0]] = (views, result[1])
                    else:
                        results.remove(result)
                else:
                    results.remove(result)

            # choose next video
            if random_choice or random.randint(0, 5) < 1:
                curr_video = results[random.randint(0, len(results) - 1)]
            else:
                best_views = 0
                for result in results:
                    try:
                        if vid_dict[result[0]][0] > best_views:
                            curr_video = result
                            best_views = vid_dict[result[0]][0]
                    except KeyError as e:
                        print(e)
                        print(vid_dict)

            # print chosen or last video
            done = not stop_thread.is_alive()
            if i == num_hops or done:
                print("\nFinal chosen video (" + str(i) + "): " + str(curr_video[1]) + " (" + str(curr_video[0]) + ")")
                if done:
                    break
            else:
                print("\nChosen video (" + str(i) + "): " + str(curr_video[1]) + " (" + str(curr_video[0]) + ")")
        except HttpError as e:
            print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))

    # prints all fetched (chosen or recommended) videos
    print("\nAll fetched video's sorted to view-count:")
    vals = vid_dict.items()
    sorted_results = sorted(vals, key=lambda x: x[1][0], reverse=True)
    for i, item in enumerate(sorted_results):
        print(str(i) + ": " + str(item))

    # writes the json file
    with open('data.json', 'w') as outfile:
        json.dump(json_data, outfile, sort_keys=True, indent=4)

    # Plots the view distribution to observe view power laws
    investigate_view_power_law(sorted_results)

    return sorted_results

# Exercise 5
yt = YouTubeCrawler(-3)
create_own_data(yt, "e-ORhEE9VVg", 250, 10, 20000, True)