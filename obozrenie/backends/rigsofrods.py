#!/usr/bin/python
# This source file is part of Obozrenie
# Copyright 2015 Artem Vorotnikov

# Obozrenie is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3, as
# published by the Free Software Foundation.

# Obozrenie is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Obozrenie.  If not, see <http://www.gnu.org/licenses/>.

import os

import ast
import html.parser
import requests

from obozrenie import N_

import obozrenie.helpers as helpers
import obozrenie.ping as ping
from obozrenie.global_settings import *

BACKEND_CONFIG = os.path.join(SETTINGS_INTERNAL_BACKENDS_DIR, "rigsofrods.toml")
RIGSOFRODS_GAME_NAME = "rigsofrods"


class ServerListParser(html.parser.HTMLParser):
    """The HTML Parser for Master server list retrieved from master_uri"""
    def __init__(self):
        super().__init__()

        self.list1 = []
        self.list2 = []
        self.parser_mode = 0

        self.replacements = (["<tr><td><b>Players</b></td><td><b>Type</b></td><td><b>Name</b></td><td><b>Terrain</b></td></tr>", ""],
                             ["rorserver://", ""],
                             ["user:pass@", ""],
                             ["<td valign='middle'>password</td>", "<td valign='middle'>True</td>"],
                             ["<td valign='middle'></td>", "<td valign='middle'>False</td>"])
        self.format = (("players", int),
                       ("password", bool),
                       ("name", str),
                       ("terrain", str))

        self.col_num = 0

    def handle_data(self, data):
        """Normal data handler"""
        if data == 'False':
            data = False
        if self.parser_mode == 0:
            if data == "Full server":
                self.parser_mode = 1
            else:
                if self.col_num >= len(self.format):
                    self.col_num = 0

                if self.col_num == 0:
                    self.list1.append([])

                    self.list1[-1] = dict()

                if self.format[self.col_num][0] == "players":
                    self.list1[-1]["player_count"] = int(data.split('/')[0])
                    self.list1[-1]["player_limit"] = int(data.split('/')[1])
                else:
                    self.list1[-1][self.format[self.col_num][0]] = self.format[self.col_num][1](data)

                self.col_num += 1

        elif self.parser_mode == 1:
            self.list2.append(data)

    def handle_starttag(self, tag, value):
        """Extracts host link from cell"""
        if tag == "a":
            self.list1[-1]["host"] = value[0][1].replace("/", "")


def add_game_name(array, game_name):
    for entry in array:
        entry["game_id"] = game_name
        entry["game_type"] = game_name


def add_master_info(array, master):
    for entry in array:
        entry["master"] = master


def add_rtt_info(array):
    """Appends server response time to the table."""
    hosts_array = []
    rtt_temp_array = []
    rtt_temp_array.append([])
    rtt_array = []
    rtt_array.append([])

    for i in range(len(array)):
        try:
            hosts_array.append(array[i]["host"].split(':')[0])
        except:
            pass

    pinger = ping.Pinger()
    pinger.hosts = list(set(hosts_array))
    pinger.action = "ping"

    pinger.status.clear()
    rtt_array = pinger.start()

    # Match ping in host list.
    for i in range(len(array)):
        try:
            ip = array[i]["host"].split(':')[0]
            array[i]["ping"] = rtt_array[ip]
        except:
            pass


def stat_master(game, game_table_slice, proxy=None):
    """Stats the master server"""

    backend_config_object = helpers.load_table(BACKEND_CONFIG)

    protocol = backend_config_object["protocol"]["version"]
    master_uri_list = game_table_slice["settings"]["master_uri"].split(',')

    parser = ServerListParser()

    server_table = []

    for master_uri in master_uri_list:
        master_page_uri = master_uri.strip('/') + '/?version=' + protocol
        try:
            master_page_object = requests.get(master_page_uri)
            master_page = master_page_object.text
        except:
            print(N_("Accessing URI {0} failed with error code {1}".format(master_page_uri, "unknown")))
            continue

        for i in range(len(parser.replacements)):
            master_page = master_page.replace(parser.replacements[i][0], parser.replacements[i][1])

        try:
            parser.feed(master_page)
        except:
            print(N_("Error parsing URI {0}".format(master_page_uri)))
            continue

        temp_table = parser.list1.copy()
        parser.list1.clear()

        temp_table = helpers.remove_all_occurences_from_list(temp_table, {})
        add_game_name(temp_table, RIGSOFRODS_GAME_NAME)
        add_master_info(temp_table, master_uri)
        server_table.append(temp_table)

    server_table = helpers.flatten_list(server_table)

    add_rtt_info(server_table)

    if proxy is not None:
        for entry in server_table:
            proxy.append(entry)

    return server_table
