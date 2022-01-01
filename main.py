import configparser
from enum import Enum
from typing import List

import pyrogram as pg
import requests
from functional_extensions import fe
from functional_extensions.fe import l_, f_
from pydantic import BaseModel
from pyrogram import filters, emoji
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

linebreak = '\n'
indent = '    '
space = ' '

class ClientType(Enum):
    user = 0
    bot = 1


class Client(BaseModel, fe.Object):
    Clid: int
    Cldbid: int
    Cid: int
    Client_nickname: str
    Client_type: ClientType


class Channel(BaseModel, fe.Object):
    Cid: int
    Pid: int
    Channel_name: str
    Subchannel_list: 'List[Channel]'
    Client_list: List[Client]


Channel.update_forward_refs()

config = configparser.ConfigParser()
config.read('config.ini')


def main():
    global config
    app = pg.Client('flts3bot', bot_token=config['bot']['bot_token'])
    users_handler = MessageHandler(handle_users_command, filters=filters.command('users'))
    app.add_handler(users_handler)
    app.run()

async def handle_users_command(client: pg.Client, message: Message) -> None:
    global config
    r = requests.get(config['bot']['ts3_api'])
    channel_tree = l_(r.json()).map_inplace_(Channel.parse_obj)\
                               .pipe_(channels_with_users)\
                               .pipe_(format_channel_tree)
    await message.reply_text(channel_tree)

def channels_with_users(all_channels):
    return all_channels.filter_(f_(channel_has_clients).or_(any_subchannel_has_clients))

def channel_has_clients(channel):
    return len(channel.Client_list) > 0

def any_subchannel_has_clients(channel):
    return len(channels_with_users(channel.Subchannel_list)) > 0

def format_channel_tree(channels: List[Channel]) -> str:
    return ''.join(format_channel(channel) for channel in channels)

def format_channel(channel: Channel):
    return linebreak.join([format_channel_name(channel),
                           format_client_list(channel),
                           format_subchannel_list(channel)])

def format_channel_name(channel: Channel) -> str:
    clean_channel_name = channel.Channel_name.replace(r'\s', ' ').replace('[cspacer]', '')
    return emoji.SPEECH_BALLOON + space + clean_channel_name

def format_subchannel_list(channel: Channel) -> str:
    formatted_sub_channels = format_channel_tree(channel.Subchannel_list)
    return linebreak.join(indent + line
                     for line
                     in formatted_sub_channels.split(sep=linebreak)
                     if formatted_sub_channels != '')

def format_client_list(channel: Channel) -> str:
    return linebreak.join(indent + emoji_by_client_type(client) + space + client.Client_nickname
                     for client
                     in channel.Client_list)

def emoji_by_client_type(client: Client) -> str:
    return emoji.BLUE_CIRCLE if client.Client_type == ClientType.user else emoji.ROBOT

if __name__ == '__main__':
    main()
