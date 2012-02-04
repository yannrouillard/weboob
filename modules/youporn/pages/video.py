# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Romain Bignon
#
# This file is part of weboob.
#
# weboob is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# weboob is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with weboob. If not, see <http://www.gnu.org/licenses/>.


import re
import datetime
from dateutil.parser import parse as parse_dt

from weboob.tools.browser import BrokenPageError

from .base import PornPage
from ..video import YoupornVideo


class VideoPage(PornPage):
    def get_video(self, video=None):
        if not PornPage.on_loaded(self):
            return
        if video is None:
            video = YoupornVideo(self.group_dict['id'])
        video.title = self.get_title()
        video.url, video.ext = self.get_url()
        self.set_details(video)
        return video

    def get_url(self):
        download_div = self.parser.select(self.document.getroot(), 'div#tab-general-download ul li')
        if len(download_div) < 1:
            raise BrokenPageError('Unable to find file URL')

        a = self.parser.select(download_div[0], 'a', 1)
        m = re.match('^(\w+) - .*', a.text)
        if m:
            ext = m.group(1).lower()
        else:
            ext = 'flv'
        return a.attrib['href'], ext

    def get_title(self):
        element = self.parser.select(self.document.getroot(), '#videoCanvas h1', 1)
        return element.text.strip().decode('utf-8')

    def set_details(self, v):
        for li in self.parser.select(self.document.getroot(), 'div#tab-general-details ul li'):
            span = li.find('b')
            name = span.text.strip()
            value = span.tail.strip()

            if name == 'Duration:':
                m = re.match('((\d+)hrs)?((\d+)min)?(\d+)?', value)
                if not m:
                    raise BrokenPageError('Unable to parse datetime: %r' % value)
                hours = m.group(2) or 0
                minutes = m.group(4) or 0
                seconds = m.group(5) or 0
                v.duration = datetime.timedelta(hours=int(hours),
                                                minutes=int(minutes),
                                                seconds=int(seconds))
            elif name == 'Submitted:':
                author = li.find('i')
                if author is None:
                    author = li.find('a')
                if author is None:
                    v.author = value
                else:
                    v.author = author.text
            elif name == 'Rating:':
                r = value.split()
                v.rating = float(r[0])
                v.rating_max = float(r[2])
            elif name == 'Date:':
                v.date = parse_dt(value)