#! python3

"""
Tail implementation from https://github.com/tyz/slacktail
Discord.py library from https://github.com/Rapptz/discord.py
Basis for Discord communication from https://github.com/Rapptz/discord.py/blob/async/examples/background_task.py
"""

import argparse
import os
import discord
from discord.ext import commands
import asyncio
import re
import sys
import datetime


client = discord.Client()

def DontStarvePrependEmoji(line):
    # Join
    if "say" in line:
        return ":speech_balloon:" + line

    elif "tells the guild" in line or "tell the guild" in line:
        return ":speech_balloon:" + line

    elif "tells you" in line or "You told" in line:
        line = re.sub("You told", "You tell", line)
        return ":busts_in_silhouette:" + line

    elif "auctions" in line or "You auction" in line:
        return ":moneybag:" + line

    # No match found
    else:
        return None

def DontStarveReactionFilter(line):
    line = line.lower()

    # Moose Goose
    if "vindi" in line or "vindicator" in line:
        return ":sword:"

    # Mosling
    elif "idksomething" in line:
        return ":dagger:"

    # No match found
    else:
        return None

async def file_tail(channelID, filename, wait):
    await client.wait_until_ready()
    channel = client.get_channel(id=channelID)

    await channel.send("Relaying in-game messages here...")

    try:
        file = open(filename, 'r', encoding='utf-8')
    except IOError:
        sys.exit("FATAL ERROR: There was a problem opening \"{}\".".format(filename))

    file.seek(0, os.SEEK_END)
    print("------")
    print("Tailing {} every {} seconds.".format(filename, wait))

    while not client.is_closed():
        skipped = 0.0

        try:
            lines = file.readlines()
        except UnicodeDecodeError:
            print("Encountered unknown character in server log, skipping lines.")
        else:
            for line in lines:

                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                line = re.sub('^\[.*?\] ', '', line)
                line = re.sub('\, \'', ': ``', line)
                line = re.sub('\'$', '``', line)

                if "Players on EverQuest" in line or "Players in EverQuest" in line:
                    whoList = f":scroll: Taking attendance at `{current_time}` ```"

                    for line in lines:
                        # line = re.sub('^\[.*?\] ', '', line)
                        line = re.sub(' ZONE.*$', '', line)
                        line = re.sub(" AFK ", "", line)
                        line = re.sub(" LFG", "", line)

                        if ("<" in line and ">" in line) or "ANONYMOUS" in line:
                            whoList = whoList + line

                        elif "There is " in line or "There are " in line or "Your who request was cut short" in line:
                            whoList = whoList + "```\n"
                            message = await channel.send(whoList)
                            break

                message_line = DontStarvePrependEmoji(line)

                if message_line is None:
                    continue

                try:
                    message = await channel.send(message_line)

                except discord.Forbidden:
                    print("FORBIDDEN EXCEPTION (403): Bot doesn't have permissions to send message.")
                except discord.NotFound:
                    print("NOT FOUND EXCEPTION (404): Couldn't find channel with ID \"{}\", message not sent.".format(channelID))
                except discord.HTTPException as e:
                    print("HTTP EXCEPTION: HTTP request failed, couldn't send message.")
                    print("Response: \"{}\"".format(e.response))
                    print("Text: \"{}\"".format(e.text))
                except discord.InvalidArgument:
                    print("INVALID ARGUMENT EXCEPTION: Destination parameter invalid, couldn't send message.")
                else:

                    reaction = DontStarveReactionFilter(line)

                    if reaction is None:
                        continue

                    skiptime = 1.0
                    await asyncio.sleep(skiptime)
                    skipped += skiptime

                    try:
                        await message.add_reaction(reaction)
                    except discord.Forbidden:
                        print("FORBIDDEN EXCEPTION (403): Bot doesn't have permissions to add reaction.")
                    except discord.NotFound:
                        print("NOT FOUND EXCEPTION (404): Couldn't find message or emoji, reaction not added.")
                    except discord.HTTPException as e:
                        print("HTTP EXCEPTION: HTTP request failed, couldn't add reaction.")
                        print("Response: \"{}\"".format(e.response))
                        print("Text: \"{}\"".format(e.text))
                    except discord.InvalidArgument:
                        print("INVALID ARGUMENT EXCEPTION: Message or emoji parameter invalid, couldn't add reaction.")

        file.seek(0, os.SEEK_END)    # Reset EOF flag by seeking to current position
        await asyncio.sleep(max(wait - skipped, 5.0))

@client.event
async def on_ready():
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("------")

parser = argparse.ArgumentParser(description="Tail a file and output as a Discord bot to a Discord channel.")

parser.add_argument('--token',
                    '-t',
                    help="The bot token that will connect to Discord.")
parser.add_argument('--channel',
                    '-c',
                    type=int,
                    help="Discord channel to output to.")
parser.add_argument('--file',
                    '-f',
                    help="The file to tail.",
                    required=True)
parser.add_argument('--wait',
                    '-W',
                    metavar='SEC',
                    type=int,
                    help="Try to read new lines every SEC seconds. (default: 30)",
                    default=30)

args = parser.parse_args()

client.loop.create_task(file_tail(args.channel, args.file, args.wait))
try:
    client.run(args.token)
except discord.LoginFailure:
    sys.exit("FATAL ERROR: Couldn't login with token \"{}\".".format(args.token))
