#!/usr/bin/python
# This source file is part of Obozrenie
# Copyright 2015 Artem Vorotnikov

# For more information, see https://github.com/skybon/obozrenie

# Obozrenie is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3, as
# published by the Free Software Foundation.

# Obozrenie is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Obozrenie.  If not, see <http://www.gnu.org/licenses/>.

"""Helper functions for processing data."""

import os
import pytoml


def search_table(table, level, value):
        if level == 0:
            for i in range(len(table)):
                if table[i] == value:
                    return i
            return None
        elif level == 1:
            for i in range(len(table)):
                for j in range(len(table[i])):
                    if table[i][j] == value:
                        return i, j
            return None
        elif level == 2:
            for i in range(len(table)):
                for j in range(len(table[i])):
                    for k in range(len(table[i][j])):
                        if table[i][j][k] == value:
                            return i, j, k
            return None
        elif level is (3 or -1):
            for i in range(len(table)):
                for j in range(len(table[i])):
                    for k in range(len(table[i][j])):
                        for l in range(len(table[i][j][k])):
                            if table[i][j][k][l] == value:
                                return i, j, k, l
            return None
        else:
            print("Please specify correct search level: 0, 1, 2, 3, or -1 for deepest possible.")


def search_dict_table(table, key, value):
        for i in range(len(table)):
            if table[i][key] == value:
                return i
        return None


def flatten_dict_table(dict_table, leading_key_spec):
    flattened_dict_table = []
    for leading_key in sorted(dict_table):
        flattened_dict_table.append({})

        flattened_dict_table[-1][leading_key_spec] = leading_key
        for key in dict_table[leading_key]:
            flattened_dict_table[-1][key] = dict_table[leading_key][key]

    return flattened_dict_table

def sort_dict_table(dict_table, sort_key):
    sorted_dict_list = sorted(dict_table, key=lambda k: k[sort_key])

    return sorted_dict_list

def dict_to_list(dict_table, key_list):
    list_table = []

    if dict_table is not None:
        for entry in dict_table:
            list_table.append([])

            for key in key_list:
                try:
                    list_table[-1].append(entry[key])
                except KeyError:
                    list_table[-1].append(None)

    return list_table


def flatten_list(nested_list):
    flattened_list = [item for sublist in nested_list for item in sublist]
    return flattened_list

def remove_all_occurences_from_list(target_list, value):
    return [y for y in target_list if y != value]


def load_table(path):
        """Loads settings table into dict"""
        try:
            table_open_object = open(path, 'r')
        except FileNotFoundError:
            return None
        table = pytoml.load(table_open_object)
        return table


def save_table(path, data):
    """Saves settings to a file"""
    try:
        table_open_object = open(path, 'w')
    except FileNotFoundError:
        try:
            os.makedirs(os.path.dirname(path))
        except OSError:
            pass
        table_open_object = open(path, 'x')
    pytoml.dump(table_open_object, data)


def launch_game(game, launch_pattern, game_settings, server, password):
    """Launches the game based on specified launch pattern"""
    from subprocess import call

    try:
        path = game_settings["path"]
        launch_cmd = []
        if launch_pattern == "rigsofrods":
            host, port = server.split(":")
            config_file = os.path.expanduser("~/.rigsofrods/config/RoR.cfg")
            launch_cmd = [path]

            if os.path.exists(config_file):
                call(["sed", "-i", "s/Network enable.*/Network enable=Yes/", config_file])
                call(["sed", "-i", "s/Server name.*/Server name=" + host + "/", config_file])
                call(["sed", "-i", "s/Server port.*/Server port=" + port + "/", config_file])
                call(["sed", "-i", "s/Server password.*/Server password=" + password + "/", config_file])
            else:
                if os.path.exists(os.path.dirname(config_file)) is not True:
                    os.makedirs(os.path.dirname(config_file))
                with open(config_file, "x") as f:
                    f.write("Network enable=Yes" + "\n")
                    f.write("Server name=" + host + "\n")
                    f.write("Server port=" + port + "\n")
                    f.write("Server password=" + password + "\n")
                    f.close()

        elif launch_pattern == "quake":
            launch_cmd = [path, "+password", password, "+connect", server]

        elif launch_pattern == "openttd":
            launch_cmd = [path, "-n", server]

        print("Launching", path)
        call_exit_code = call(launch_cmd)

        if launch_pattern == "rigsofrods":
            call(["sed", "-i", "s/Network enable.*/Network enable=No/", config_file])
        return call_exit_code
    except OSError:
        return 1
