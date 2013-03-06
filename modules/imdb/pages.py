# -*- coding: utf-8 -*-

# Copyright(C) 2013 Julien Veyssier
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


from weboob.capabilities.cinema import Person
from weboob.capabilities.base import NotAvailable
from weboob.tools.browser import BasePage

from datetime import datetime


__all__ = ['MoviePage','PersonPage','MovieCrewPage','BiographyPage','FilmographyPage']


class MoviePage(BasePage):
    ''' Page describing a movie, only used to go on the MovieCrewPage
    '''
    def iter_persons(self, id, role=None):
        self.browser.location('http://www.imdb.com/title/%s/fullcredits'%id)
        assert self.browser.is_on_page(MovieCrewPage)
        for p in self.browser.page.iter_persons(role):
            yield p

    def iter_persons_ids(self,id):
        self.browser.location('http://www.imdb.com/title/%s/fullcredits'%id)
        assert self.browser.is_on_page(MovieCrewPage)
        for p in self.browser.page.iter_persons_ids():
            yield p


class BiographyPage(BasePage):
    ''' Page containing biography of a person
    '''
    def get_biography(self):
        bio = ''
        tn = self.parser.select(self.document.getroot(),'div#tn15content',1)
        #for p in self.parser.select(tn,'p'):
        #    bio += '\n\n%s'%p.text_content().strip()
        # get children, append if label or tag = a,p,h...
        bio = tn.text_content().strip()
        if bio == "":
            bio = NotAvailable
        return bio


class MovieCrewPage(BasePage):
    ''' Page listing all the persons related to a movie
    '''
    def iter_persons(self, role_filter=None):
        if (role_filter == None or (role_filter != None and role_filter == 'actor')):
            tables = self.parser.select(self.document.getroot(),'table.cast')
            if len(tables) > 0:
                table = tables[0]
                tds = self.parser.select(table,'td.nm')
                for td in tds:
                    id = td.find('a').attrib.get('href','').strip('/').split('/')[-1]
                    yield self.browser.get_person(id)

        for gloss_link in self.parser.select(self.document.getroot(),'table[cellspacing=1] h5 a'):
            role = gloss_link.attrib.get('name','').rstrip('s')
            if (role_filter == None or (role_filter != None and role == role_filter)):
                tbody = gloss_link.getparent().getparent().getparent().getparent()
                for line in self.parser.select(tbody,'tr')[1:]:
                    for a in self.parser.select(line,'a'):
                        href = a.attrib.get('href','')
                        if '/name/nm' in href:
                            id = href.strip('/').split('/')[-1]
                            yield self.browser.get_person(id)

    def iter_persons_ids(self):
        tables = self.parser.select(self.document.getroot(),'table.cast')
        if len(tables) > 0:
            table = tables[0]
            tds = self.parser.select(table,'td.nm')
            for td in tds:
                id = td.find('a').attrib.get('href','').strip('/').split('/')[-1]
                yield id


class PersonPage(BasePage):
    ''' Page giving informations about a person
    It is used to build a Person instance and to get the movie list related to a person
    '''
    def get_person(self,id):
        name = NotAvailable
        short_biography = NotAvailable
        birth_place = NotAvailable
        birth_date = NotAvailable
        death_date = NotAvailable
        real_name = NotAvailable
        gender = NotAvailable
        roles = {}
        nationality = NotAvailable
        td_overview = self.parser.select(self.document.getroot(),'td#overview-top',1)
        descs = self.parser.select(td_overview,'span[itemprop=description]')
        if len(descs) > 0:
            short_biography = descs[0].text
        rname_block = self.parser.select(td_overview,'div.txt-block h4.inline')
        if len(rname_block) > 0 and "born" in rname_block[0].text.lower():
            links = self.parser.select(rname_block[0].getparent(),'a')
            for a in links:
                href = a.attrib.get('href','').strip()
                if href == 'bio':
                    real_name = a.text.strip()
                elif 'birth_place' in href:
                    birth_place = a.text.lower().strip()
        names = self.parser.select(td_overview,'h1[itemprop=name]')
        if len(names) > 0:
            name = names[0].text.strip()
        times = self.parser.select(td_overview,'time[itemprop=birthDate]')
        if len(times) > 0:
            time = times[0].attrib.get('datetime','').split('-')
            if len(time) == 2:
                time.append('1')
            elif len(time) == 1:
                time.append('1')
                time.append('1')
            birth_date = datetime(int(time[0]),int(time[1]),int(time[2]))
        dtimes = self.parser.select(td_overview,'time[itemprop=deathDate]')
        if len(dtimes) > 0:
            dtime = dtimes[0].attrib.get('datetime','').split('-')
            if len(dtime) == 2:
                dtime.append('1')
            elif len(dtime) == 1:
                dtime.append('1')
                dtime.append('1')
            death_date = datetime(int(dtime[0]),int(dtime[1]),int(dtime[2]))
        # go to the filmography page
        self.browser.location('http://www.imdb.com/name/%s/filmotype'%id)
        assert self.browser.is_on_page(FilmographyPage)
        roles = self.browser.page.get_roles()

        person = Person(id,name)
        person.real_name       = real_name
        person.birth_date      = birth_date
        person.death_date      = death_date
        person.birth_place     = birth_place
        person.gender          = gender
        person.nationality     = nationality
        person.short_biography = short_biography
        person.roles           = roles
        return person

    def iter_movies_ids(self,person_id):
        for movie_div in self.parser.select(self.document.getroot(),'div[class~=filmo-row]'):
            a = self.parser.select(movie_div,'b a',1)
            id = a.attrib.get('href','').strip('/').split('/')[-1]
            yield id

class FilmographyPage(BasePage):
    ''' Page of detailed filmography of a person, sorted by type of role
    This page is easier to parse than the main person page filmography
    '''
    def get_roles(self):
        roles = {}
        for role_div in self.parser.select(self.document.getroot(),'div.filmo'):
            role = self.parser.select(role_div,'h5 a',1).text.replace(':','')
            roles[role] = []
            for a in self.parser.select(role_div,'ol > li > a'):
                id = a.attrib.get('href','').strip('/').split('/')[-1]
                if id.startswith('tt'):
                    if '(' in a.tail and ')' in a.tail:
                        between_p = a.tail.split(')')[0].split('(')[1]
                    else:
                        between_p = '????'
                    roles[role].append('(%s) %s'%(between_p,a.text))
        return roles

    def iter_movies(self, role_filter=None):
        for role_div in self.parser.select(self.document.getroot(),'div.filmo'):
            role = self.parser.select(role_div,'h5 a',1).text.replace(':','')
            if (role_filter == None or (role_filter != None and role.lower().strip() == role_filter))\
            and role != 'In Development':
                for a in self.parser.select(role_div,'ol > li > a'):
                    id = a.attrib.get('href','').strip('/').split('/')[-1]
                    if id.startswith('tt'):
                        movie = self.browser.get_movie(id)
                        if movie != None:
                            yield movie