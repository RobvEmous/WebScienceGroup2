import matplotlib.pyplot as plt
import json
from os import listdir
from os.path import isfile, join
import math
import operator


class MusicAnalyser:

    def read_files(self, path):
        """
        Reads the YouTube JSON files.

        :return: the JSON files
        """
        json_data = []
        yt_files = [f for f in listdir(path) if isfile(join(path, f))]
        for i, file in enumerate(yt_files):
            json_data.append([])
            with open(path + "/" + file) as json_raw:
                json_data[-1] = json.loads(json_raw.read())
        return json_data


    def read_like_count(self, json_data, from_num, to_num):
        """
        Gets the like count a certain interval of video.

        :param json_data: the input data
        :param from_num: begin video index
        :param to_num: end video index
        :return: the like count
        """
        song_stats = {}
        for day_i, day in enumerate(json_data):
            for song_i, song in enumerate(day):
                if from_num > 0 and song_i + 1 < from_num:
                    continue
                if song['id'] not in song_stats:
                    song_stats[song['id']] = [song['snippet']['title']]
                num_likes = int(song['statistics']['likeCount'])
                num_dislikes = int(song['statistics']['dislikeCount'])
                song_stats[song['id']].append((num_likes + num_dislikes, num_likes - num_dislikes))
                if to_num > 0 and song_i + 1 >= to_num:
                    break
        return song_stats

    def read_view_count(self, json_data, from_num, to_num):
        """
        Gets the view count a certain interval of video.

        :param json_data: the input data
        :param from_num: begin video index
        :param to_num: end video index
        :return: the view count
        """
        song_stats = {}
        for day_i, day in enumerate(json_data):
            #print(day_i)
            sum_views = 0.0
            for song_i, song in enumerate(day):
                sum_views += int(song['statistics']['viewCount'])
            for song_i, song in enumerate(day):
                #print("\t" + str(song_i))
                if from_num > 0 and song_i + 1 < from_num:
                    continue
                if song['id'] not in song_stats:
                    song_stats[song['id']] = [song['snippet']['title']]
                num_views = int(song['statistics']['viewCount'])
                song_stats[song['id']].append((day_i, num_views))
                if to_num > 0 and song_i + 1 >= to_num:
                    break
        return song_stats

    def plot_likes(self, video_stats):
        """
        Plots the ratio of positive likes to the total number of likes.

        :param video_stats: the input data
        """
        sorted_songs = sorted(video_stats.values(), key=lambda x: (math.fabs(x[-1][1] - x[1][1]) / x[1][1]), reverse=True)
        for i, title in enumerate([song[0] for song in sorted_songs]):
            print(str(i) + ": " + title)
        for i, song in enumerate(video_stats):
            print(song + ": " + str(video_stats[song]))
            l_x, l_y = unzip(video_stats[song][1:])
            ref_x, ref_y = linear_extrapolation(video_stats[song][1], video_stats[song][2], video_stats[song][-1])
            if i == 0:
                plt.plot(ref_x, ref_y, '-r', label='Linear reference')
            else:
                plt.plot(ref_x, ref_y, '-r')
            plt.plot(l_x, l_y, label=video_stats[song][0])
        plt.xlabel('Total number of likes', fontsize=14)
        plt.ylabel('Difference positive and negative likes', fontsize=14)
        plt.legend()
        plt.show()
        return

    def plot_views(self, video_stats):
        """
        Plots the distribution of views over time.

        :param song_stats: the input data
        """
        sorted_songs = sorted(video_stats.values(), key=lambda x: (math.fabs(x[-1][1] - x[1][1]) / x[1][1]), reverse=True)
        for i, title in enumerate([song[0] for song in sorted_songs]):
            print(str(i) + ": " + title)
        for i, song in enumerate(video_stats):
            print(song + ": " + str(video_stats[song]))
            l_x, l_y = unzip(video_stats[song][1:])
            ref_x, ref_y = linear_extrapolation(video_stats[song][1], video_stats[song][2], video_stats[song][-1])
            if i == 0:
                plt.plot(ref_x, ref_y, '-r', label='Linear reference')
            else:
                plt.plot(ref_x, ref_y, '-r')
            plt.plot(l_x, l_y, label=video_stats[song][0])
        plt.xlabel('Time (days)', fontsize=14)
        plt.ylabel('Fraction of views', fontsize=14)
        plt.legend()
        plt.show()

    def investigate_rich_get_richer(self, json_data, day=1):
        """
        Investigate the rich-get-richer effects by plotting the distribution of the number
        of views among the songs on several different days.
        :param json_data: the input data
        :param day: The day to be analysed (range 1-14)
        :return:
        """
        if day > 0 and day < 15:
            total_views, index_day = 0, day - 1
            song_to_views = {}
            subtitle, xlabel, ylabel = 'Distribution of number of views among songs: Day ',\
                                       'Total number of views', 'Percentage of songs'
            subtitle += str(day)
            dayta = json_data[day - 1]
            for song_i, song in enumerate(dayta):
                views = int(song['statistics']['viewCount'])
                total_views += views
                song_to_views[song['id']] = views
            xvals, yvals = [], []
            sorted_songs = sorted(song_to_views.items(), key=operator.itemgetter(1), reverse=True)
            for index, song in enumerate(sorted_songs):
                xvals.append(total_views)
                yvals.append(index)
                total_views -= song[1]
            plot_data(xvals, yvals, subtitle, xlabel, ylabel)
        else:
            print('Day ', day, ' is not in range.')

    def compare_rankings(self, json_data_sp, json_data_yt, save_location, save_amount_songs=25, day=1):
        """
        Compares the rankings of songs on spotify with their ranking on youtube and generate a csv-file
        with the result.
        :param json_data_sp: the Spotify input data
        :param json_data_yt: the YouTube input data
        :param save_location: The location where the csv-file containing the result will be saved
        :param save_amount_songs: The amount of songs to be saved
        :param day: The day of which the rankings have to be compared (range 1-14)
        :return:
        """
        if day > 0 and day < 15:
            song_to_views = []
            dayta_sp = json_data_sp[day - 1]
            for song in dayta_sp['tracks']['items']:
                track = song['track']
                name, popularity = track['name'], track['popularity']
                song_to_views.append([name, popularity])
            dayta_yt = json_data_yt[day - 1]
            for song_i, song in enumerate(dayta_yt):
                views = int(song['statistics']['viewCount'])
                song_to_views[song_i].append(views)
            song_to_views = self.generate_rankings(song_to_views)
            song_to_views.sort(key=lambda x: x[1], reverse=True)
            if save_amount_songs >= 0 and save_amount_songs < len(song_to_views):
                song_to_views = song_to_views[0:save_amount_songs]
            else:
                print('Save Amount ',save_amount_songs ,' is not in range.')
            self.generate_rankings_csv(save_location, song_to_views)
        else:
            print('Day ',day ,' is not in range.')

    def generate_rankings(self, song_to_views):
        """
        Calculates the Spotify And Youtube rankings based on the songs popularity and view count
        :param song_to_views: A list of lists containing the song name, popularity and view count of each song
        :return: song_to_views
        """
        spotify_ranking, youtube_ranking = [], []
        for index, elem in enumerate(song_to_views):
            spotify_ranking.append([index, elem[1]])
            youtube_ranking.append([index, elem[2]])
        spotify_ranking.sort(key=lambda x: x[1])
        youtube_ranking.sort(key=lambda x: x[1])
        for index, elem in enumerate(spotify_ranking):
            song_to_views[elem[0]][1] = index + 1
        for index, elem in enumerate(youtube_ranking):
            song_to_views[elem[0]][2] = index + 1
        return song_to_views

    def generate_rankings_csv(self, location, ranking):
        """
        Generate a csv file containing the Spotify and YouTube rankings for each song
        :param location: The location where the csv file will be saved
        :param ranking: The ranking values
        :return:
        """
        with open(location, 'w') as file:
            newline, separator, space, song_header, spotify_header, youtube_header = '\n', ',', ' ', 'Song', 'Spotify Rating', 'Youtube Viewcount'
            file.write(song_header + separator + spotify_header + separator + youtube_header + newline)
            for value in ranking:
                song_name, spotify_ranking, youtube_ranking = str(value[0]).replace(separator, space), str(value[1]), str(value[2])
                file.write(song_name + separator + spotify_ranking + separator + youtube_ranking + newline)


def plot_data(xvals, yvals, subtitle, xlabel, ylabel):
    """
    Generates a plot.
    :param xvals: Number of views
    :param yvals: Percentage of songs
    :param subtitle: Subtitle of songs
    :param xlabel: Label of the x axis
    :param ylabel: Label of the y axis
    :return:
    """
    fig = plt.figure()
    fig.suptitle(subtitle)
    plt.plot(xvals, yvals)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.show()

def linear_extrapolation(first, second, end):
    """
    Generates a straight line with its direction based on the
    first two coordinates up to the end coordinate.

    :param first: the first coordinate
    :param second: the second coordinate
    :param end: the final coordinate
    :return: the table of the line
    """
    items_x = [first[0]]
    items_y = [first[1]]
    curr = second
    inc = first[1] < second[1]
    if first[1] < second[1]:
        while curr[0] <= end[0] and ((inc and curr[1] <= end[1]) or (not inc and curr[1] >= end[1])):
            items_x.append(curr[0])
            items_y.append(curr[1])
            curr = (curr[0] + second[0] - first[0], curr[1] + second[1] - first[1])
    items_x.append(curr[0])
    items_y.append(curr[1])
    return items_x, items_y

def unzip(items):
    """
    Converts a list of tuples into two lists
    :param items: the list of tuples [(a,b)]
    :return: two lists [a], [b]
    """
    l1, l2 = [], []
    for item in items:
        l1.append(item[0])
        l2.append(item[1])
    return l1, l2

# initialize and read the files
ma = MusicAnalyser()
json_yt = ma.read_files("Files/youtube_top100")
json_sp = ma.read_files("Files/spotify_top100")

# exercise 1
likes = ma.read_like_count(json_yt, 1, 1)
ma.plot_likes(likes)

# exercise 2
views = ma.read_view_count(json_yt, 1, 1)
ma.plot_views(views)

# exercise 3
ma.investigate_rich_get_richer(json_yt, day=1)
ma.compare_rankings(json_sp, json_yt, 'Results/results.csv', day=1)