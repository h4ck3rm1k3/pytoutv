# Copyright (c) 2012, Benjamin Vanheuverzwijn <bvanheu@gmail.com>
# Copyright (c) 2014, Philippe Proulx <eepp.ca>
# All rights reserved.
#
# Thanks to Marc-Etienne M. Leveille
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of pytoutv nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL Benjamin Vanheuverzwijn OR Philippe Proulx
# BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re
import os
import errno
import struct
import logging
import requests
from Crypto.Cipher import AES
import toutv.config
import toutv.exceptions
import toutv.m3u8
import pprint

import logging

# These two lines enable debugging at httplib level (requests->urllib3->http.client)
# You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.

import http.client as http_client

http_client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

import http.cookiejar
http.cookiejar.debug=True
requests_log = logging.getLogger("http.cookiejar")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


class Bo:

    def set_proxies(self, proxies):
        self._proxies = proxies

    def get_proxies(self):
        if hasattr(self, '_proxies'):
            return self._proxies

        self._proxies = None

        return self._proxies

    def _do_request(self, session, url, timeout=None, params=None):
        proxies = self.get_proxies()

        try:
            r = session.get(url,
                            params=params,
                            headers=toutv.config.HEADERS,
                            proxies=proxies,
                            timeout=timeout,
                            allow_redirects=False
            )
            if r.status_code == 302:
                pprint.pprint(r)
            if r.status_code != 200:
                raise toutv.exceptions.UnexpectedHttpStatusCodeError(url,
                                                                     r.status_code)
        except requests.exceptions.Timeout:
            raise toutv.exceptions.RequestTimeoutError(url, timeout)

        return r

class Episode(Bo):

    class Quality:

        def __init__(self, bitrate, xres, yres):
            self._bitrate = bitrate
            self._xres = xres
            self._yres = yres

        @property
        def bitrate(self):
            return self._bitrate

        @property
        def xres(self):
            return self._xres

        @property
        def yres(self):
            return self._yres

        def __hash__(self):
            return hash(self._bitrate) + hash(self._xres) + hash(self._yres)

        def __eq__(self, other):
            return self.bitrate == other.bitrate and self.xres == other.xres \
                and self.yres == other.yres

        def __repr__(self):
            s = 'Quality(res={xres}x{yres}, bitrate={bitrate})'
            return s.format(xres=self.xres,
                            yres=self.yres,
                            bitrate=self.bitrate)

    def __init__(self, session):
        self._session = session
        self.AdPattern = None
        self.AirDateFormated = None
        self.AirDateLongString = None
        self.Captions = None
        self.CategoryId = None
        self.ChapterStartTimes = None
        self.ClipType = None
        self.Copyright = None
        self.Country = None
        self.DateSeasonEpisode = None
        self.Description = None
        self.DescriptionShort = None
        self.EpisodeNumber = None
        self.EstContenuJeunesse = None
        self.Event = None
        self.EventDate = None
        self.FullTitle = None
        self.GenreTitle = None
        self.Id = None
        self.ImageBackground = None
        self.ImagePlayerLargeA = None
        self.ImagePlayerNormalC = None
        self.ImagePromoLargeI = None
        self.ImagePromoLargeJ = None
        self.ImagePromoNormalK = None
        self.ImageThumbMicroG = None
        self.ImageThumbMoyenL = None
        self.ImageThumbNormalF = None
        self.IsMostRecent = None
        self.IsUniqueEpisode = None
        self.Keywords = None
        self.LanguageCloseCaption = None
        self.Length = None
        self.LengthSpan = None
        self.LengthStats = None
        self.LengthString = None
        self.LiveOnDemand = None
        self.MigrationDate = None
        self.Musique = None
        self.Network = None
        self.Network2 = None
        self.Network3 = None
        self.NextEpisodeDate = None
        self.OriginalAirDate = None
        self.PID = None
        self.Partner = None
        self.PeopleAuthor = None
        self.PeopleCharacters = None
        self.PeopleCollaborator = None
        self.PeopleColumnist = None
        self.PeopleComedian = None
        self.PeopleDesigner = None
        self.PeopleDirector = None
        self.PeopleGuest = None
        self.PeopleHost = None
        self.PeopleJournalist = None
        self.PeoplePerformer = None
        self.PeoplePersonCited = None
        self.PeopleSpeaker = None
        self.PeopleWriter = None
        self.PromoDescription = None
        self.PromoTitle = None
        self.Rating = None
        self.RelatedURL1 = None
        self.RelatedURL2 = None
        self.RelatedURL3 = None
        self.RelatedURL4 = None
        self.RelatedURL5 = None
        self.RelatedURLText1 = None
        self.RelatedURLText2 = None
        self.RelatedURLText3 = None
        self.RelatedURLText4 = None
        self.RelatedURLText5 = None
        self.RelatedURLimage1 = None
        self.RelatedURLimage2 = None
        self.RelatedURLimage3 = None
        self.RelatedURLimage4 = None
        self.RelatedURLimage5 = None
        self.SeasonAndEpisode = None
        self.SeasonAndEpisodeLong = None
        self.SeasonNumber = None
        self.Show = None
        self.ShowSearch = None
        self.ShowSeasonSearch = None
        self.StatusMedia = None
        self.Subtitle = None
        self.Team1CountryCode = None
        self.Team2CountryCode = None
        self.Title = None
        self.TitleID = None
        self.TitleSearch = None
        self.Url = None
        self.UrlEmission = None
        self.Year = None
        self.iTunesLinkUrl = None

    def get_title(self):
        return self.Title

    def get_id(self):
        return self.Id

    def get_author(self):
        return self.PeopleAuthor

    def get_director(self):
        return self.PeopleDirector

    def get_year(self):
        return self.Year

    def get_genre_title(self):
        return self.GenreTitle

    def get_url(self):
        if self.Url is None:
            return None

        return '{}/{}'.format(toutv.config.TOUTV_BASE_URL, self.Url)

    def get_season_number(self):
        return self.SeasonNumber

    def get_episode_number(self):
        return self.EpisodeNumber

    def get_sae(self):
        return self.SeasonAndEpisode

    def get_description(self):
        return _clean_description(self.Description)

    def get_emission_id(self):
        return self.CategoryId

    def get_length(self):
        tot_seconds = int(self.Length) // 1000
        minutes = tot_seconds // 60
        seconds = tot_seconds - (60 * minutes)

        return minutes, seconds

    def get_air_date(self):
        if self.AirDateFormated is None:
            return None

        dt = datetime.datetime.strptime(self.AirDateFormated, '%Y%m%d')

        return dt.date()

    def set_emission(self, emission):
        self._emission = emission

    def get_emission(self):
        return self._emission

    @staticmethod
    def _get_video_qualities(playlist):
        qualities = []

        for stream in playlist.streams:
            # TOU.TV team doesnt use the "AUDIO" or "VIDEO" M3U8 tags so
            # we must parse the URL to find out about video stream:
            #   index_X_av.m3u8 -> audio-video (av)
            #   index_X_a.m3u8 -> audio (a)
            if not re.search(r'_av\.m3u8', stream.uri):
                continue

            xres = None
            yres = None

            if stream.resolution is not None:
                m = re.match(r'(\d+)x(\d+)', stream.resolution)

                if m:
                    xres = int(m.group(1))
                    yres = int(m.group(2))

            bw = int(stream.bandwidth)
            quality = Episode.Quality(bw, xres, yres)

            qualities.append(quality)

        return qualities

    def _get_playlist_url(self):
        url = toutv.config.TOUTV_PLAYLIST_URL
        params = dict(toutv.config.TOUTV_PLAYLIST_PARAMS)
        params['idMedia'] = self.PID
        r = self._do_request(self._session,url, params=params)
        response_obj = r.json()

        if response_obj['errorCode']:
            raise RuntimeError(response_obj['message'])

        return response_obj['url']

    def get_playlist_cookies(self, url):


        
        r = self._do_request(self._session, url)
        header = r.text
        cookies = r.cookies
        newurl = r.url

        pprint.pprint({
            "HISTORY": r.history
        })

        #pprint.pprint(r.__dict__)
        #pprint.pprint(cookies.__dict__)
        pprint.pprint(self._session.__dict__)
        pprint.pprint(self._session.cookies.__dict__)
        pprint.pprint(self._session.cookies)
        #pprint.pprint(self._session.__dict__)

        regex = r'\{\"sharing_url\":\s+\"([\w\d]+)\"'
        m = re.search(regex, header)
        sharing_token=""
        if (m) :
            sharing_token=m.group(1)
            print("Sharing token:" + sharing_token)
        else:
            raise Exception("no sharing url")
        
        #{"sharing_url": "KG5pkHT6YptFYTZ4MUFsEPf0UdeA7ZlL9uI2CWMg5jksQNyRCLGX8upylDeVMveL"

        # sharingUrl
        r = self._session.post("https://bluejeans.com/api/auth/sharing_token/",
                               headers= {
                                   'User-Agent':
                                   'Mozilla/5.0 (X11; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0',
                                   'Host': 'bluejeans.com',
                                   'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                   'X-CSRFToken': None,
                                'X-Requested-With': 'XMLHttpRequest',
                                   'Referer': newurl,
                                   'DNT': 1,
                                   'Connection': 'keep-alive'                                   
                               },
                               data={
                                   'sharing_url': sharing_token,
                                
                               },
                               cookies=cookies,
                               allow_redirects=False
        )
        
        pprint.pprint(r.__dict__)        
        print(r.status_code, r.reason)
        print(r.text)
        
        ###
        
        # parse M3U8 file
        m3u8_file = r.text
        playlist = toutv.m3u8.parse(m3u8_file, os.path.dirname(url))

        return playlist, r.cookies

    def get_available_qualities(self):
        # Get playlist
        proxies = self.get_proxies()
        playlist, cookies = self.get_playlist_cookies()

        # Get video qualities
        qualities = Episode._get_video_qualities(playlist)

        qualities.sort(key=lambda q: q.bitrate)

        return qualities

    def get_medium_thumb_urls(self):
        return [self.ImageThumbMoyenL]

    def __str__(self):
        return '{} ({})'.format(self.get_title(), self.get_id())


class D:

    _seg_aes_iv = struct.Struct('>IIII')

    def _init_download(self, uri):
        # prevent overwriting
        if not self._overwrite and os.path.exists(self._output_path):
            raise FileExistsError()

        pl, cookies = self._episode.get_playlist_cookies(uri)
        self._playlist = pl
        self._cookies = cookies
        self._done_bytes = 0
        self._done_segments = 0
        self._done_segments_bytes = 0
        self._do_cancel = False

    def __init__(self,  output_dir=os.getcwd(),
                 filename=None, on_progress_update=None,
                 on_dl_start=None, overwrite=False, proxies=None,
                 timeout=15):
        self._logger = logging.getLogger(__name__)

        self._bitrate = 1324000
        self._output_dir = output_dir
        self._filename = filename
        self._on_progress_update = on_progress_update
        self._on_dl_start = on_dl_start
        self._overwrite = overwrite
        self._proxies = proxies
        self._timeout = timeout
        self._session = requests.Session()
        self._episode = Episode(self._session)        
        self._set_output_path()
    def _gen_filename(self):
        # remove illegal characters from filename
        emission_title = "test"
        episode_title = "test"


        br = self._bitrate // 1000
        episode_title = '{} {}kbps'.format(episode_title, br)
        filename = '{}.{}.ts'.format(emission_title, episode_title)
        regex = r'[^ \'a-zA-Z0-9áàâäéèêëíìîïóòôöúùûüÁÀÂÄÉÈÊËÍÌÎÏÓÒÔÖÚÙÛÜçÇ()._-]'
        filename = re.sub(regex, '', filename)
        filename = re.sub(r'\s', '.', filename)

        return filename

    def _set_output_path(self):
        # create output directory if it doesn't exist
        try:
            os.makedirs(self._output_dir)
        except:
            pass

        # generate a filename if not specified by user
        if self._filename is None:
            self._filename = self._gen_filename()

        # set output path
        self._output_path = os.path.join(self._output_dir, self._filename)

    def _do_request(self, url, params=None, stream=False):
        self._logger.debug('HTTP GET request @ {}'.format(url))

        try:
            r = self._session.get(url,
                                params=params, headers=toutv.config.HEADERS,
                                proxies=self._proxies, cookies=self._cookies,
                                timeout=self._timeout, stream=stream,
        allow_redirects=False)

            if r.status_code != 200:
                raise toutv.exceptions.UnexpectedHttpStatusCodeError(url,
                                                                     r.status_code)
        except requests.exceptions.Timeout:
            raise toutv.exceptions.RequestTimeoutError(url, timeout)
        except requests.exceptions.ConnectionError as e:
            raise toutv.exceptions.NetworkError() from e

        return r

    def download(self,uri):

        #page = self._do_request(uri)
        #print (page.text)

        ######
        self._init_download(uri)
        # get video playlist
        r = self._do_request(uri)
        m3u8_file = r.text
        self._video_playlist = toutv.m3u8.parse(m3u8_file,
                                                os.path.dirname(stream.uri))
        self._segments = self._video_playlist.segments
        self._total_segments = len(self._segments)
        self._logger.debug('parsed M3U8 file: {} total segments'.format(self._total_segments))

        # get decryption key
        uri = self._segments[0].key.uri
        r = self._do_request(uri)
        self._key = r.content
        self._logger.debug('decryption key: {}'.format(self._key))

        # download segments
        self._notify_dl_start()
        self._notify_progress_update()

        for segindex in range(len(self._segments)):
            try:
                self._download_segment_with_retry(segindex)
            except Exception as e:
                if type(e) is OSError and e.errno == errno.ENOSPC:
                    raise NoSpaceLeftError()

                raise DownloadError('Cannot download segment {}: {}'.format(segindex + 1, e))

            self._done_segments += 1
            self._done_segments_bytes = self._done_bytes
            self._notify_progress_update()

        # stitch individual segment files as a complete file
        try:
            self._stitch_segment_files()
        except Exception as e:
            if type(e) is OSError and e.errno == errno.ENOSPC:
                raise NoSpaceLeftError()

            raise DownloadError('Cannot stitch segment files: {}'.format(e))

        # remove segment files
        self._remove_segment_files()

d= D()
uri='https://bluejeans.com/s/UG8O7/'
d.download(uri)

#https://bluejeans.com/seamapi/v1/user/333361/cms/2503237?access_token=c8b21cf27d7b4679b1c1701d26fc5d47&_=1477647860820
#https://bjn-videoshare-prod.s3.amazonaws.com/333361/trans/0-424088970Mediac20323b7-4298-4ead-9c90-60eb164a43de.jpg?AWSAccessKeyId=AKIAI4PMZ7OI5M7DGL2Q&Expires=
#https://bluejeans.com/seamapi/v1/user/333361/cms/2503260?access_token=c8b21cf27d7b4679b1c1701d26fc5d47&_=1477647860995
