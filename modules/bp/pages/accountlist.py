# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011  Nicolas Duhamel
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


from weboob.capabilities.bank import Account, AccountNotFound

from weboob.tools.browser import BasePage


__all__ = ['AccountList']


class AccountList(BasePage):
    def on_loaded(self):
        self.account_list = []
        self.parse_table('comptes')
        self.parse_table('comptesEpargne')
        self.parse_table('comptesTitres')
        self.parse_table('comptesVie')
        self.parse_table('comptesRetraireEuros')

    def get_accounts_list(self):
        return self.account_list

    def parse_table(self, what):
        tables = self.document.xpath("//table[@id='%s']" % what, smart_strings=False)
        if len(tables) < 1:
            return

        lines = tables[0].xpath(".//tbody/tr")
        for line  in lines:
            account = Account()
            tmp = line.xpath("./td//a")[0]
            account.label = tmp.text
            account.link_id = tmp.get("href")

            tmp = line.xpath("./td/span/strong")
            tmp_id = tmp[0].text
            tmp_balance = tmp[1].text
            account.id = tmp_id 
            account.balance = float(''.join(tmp_balance.replace('.','').replace(',','.').split()))
            self.account_list.append(account)

    def get_account(self, id):
        for account in self.account_list:
            if account.id == id:
                return account
        raise AccountNotFound('Unable to find account: %s' % id)