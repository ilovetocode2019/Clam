import random

# from nltk.corpus import wordnet
import asyncio
import contextlib
from discord.ext import commands
import discord
from discord import Client, Embed, File, Member, Message, Reaction, TextChannel, Webhook
from discord.abc import Snowflake
from typing import Optional, Sequence, Union
import io
import zlib
import codecs
import pathlib
import os

async def quote(message, content, *, quote=None, **kwargs):
    quote = quote or message.content
    quote = discord.utils.escape_mentions(quote)
    quote = quote.replace("\n", "\n> ")
    formatted = f"> {quote}\n{message.author.mention} {content}"
    await message.channel.send(formatted, **kwargs)

async def reply_to(message, content, **kwargs):
    formatted = f"Replying to {message.author.mention} from {message.jump_url}\n{content}"
    await message.channel.send(formatted, **kwargs)


def get_lines_of_code(comments=False):
    total = 0
    file_amount = 0
    for path, subdirs, files in os.walk("."):
        if "venv" in subdirs:
            subdirs.remove("venv")
        if "env" in subdirs:
            subdirs.remove("env")
        for name in files:
            if name.endswith(".py"):
                file_amount += 1
                with codecs.open(
                    "./" + str(pathlib.PurePath(path, name)), "r", "utf-8"
                ) as f:
                    for i, l in enumerate(f):
                        if (
                            l.strip().startswith("#") or len(l.strip()) == 0
                        ):  # skip commented lines.
                            if comments:
                                total += 1
                            pass
                        else:
                            total += 1
    excomments = " (including comments and newlines)" if comments else ""
    return f"I am made of {total:,} lines of Python{excomments}, spread across {file_amount:,} files!"


# https://github.com/Rapptz/RoboDanny/blob/be74a433739dbe8c26edf913b04457ace770c362/cogs/utils/formats.py#L25
class TabularData:
    def __init__(self):
        self._widths = []
        self._columns = []
        self._rows = []

    def set_columns(self, columns):
        self._columns = columns
        self._widths = [len(c) + 2 for c in columns]

    def add_row(self, row):
        rows = [str(r) for r in row]
        self._rows.append(rows)
        for index, element in enumerate(rows):
            width = len(element) + 2
            if width > self._widths[index]:
                self._widths[index] = width

    def add_rows(self, rows):
        for row in rows:
            self.add_row(row)

    def render(self):
        """Renders a table in rST format.
        Example:
        +-------+-----+
        | Name  | Age |
        +-------+-----+
        | Alice | 24  |
        |  Bob  | 19  |
        +-------+-----+
        """

        sep = "+".join("-" * w for w in self._widths)
        sep = f"+{sep}+"

        to_draw = [sep]

        def get_entry(d):
            elem = "|".join(f"{e:^{self._widths[i]}}" for i, e in enumerate(d))
            return f"|{elem}|"

        to_draw.append(get_entry(self._columns))
        to_draw.append(sep)

        for row in self._rows:
            to_draw.append(get_entry(row))

        to_draw.append(sep)
        return "\n".join(to_draw)


class SphinxObjectFileReader:
    # Inspired by Sphinx's InventoryFileReader
    BUFSIZE = 16 * 1024

    def __init__(self, buffer):
        self.stream = io.BytesIO(buffer)

    def readline(self):
        return self.stream.readline().decode("utf-8")

    def skipline(self):
        self.stream.readline()

    def read_compressed_chunks(self):
        decompressor = zlib.decompressobj()
        while True:
            chunk = self.stream.read(self.BUFSIZE)
            if len(chunk) == 0:
                break
            yield decompressor.decompress(chunk)
        yield decompressor.flush()

    def read_compressed_lines(self):
        buf = b""
        for chunk in self.read_compressed_chunks():
            buf += chunk
            pos = buf.find(b"\n")
            while pos != -1:
                yield buf[:pos].decode("utf-8")
                buf = buf[pos + 1 :]
                pos = buf.find(b"\n")


# async def start():
#     wordnet.synsets("test")


# async def thesaurize(msg):
#     isInput = False
#     IncorrectMsg = ""

#     args = msg.split(" ")

#     if len(args) < 2:
#         minReplace = 0
#     else:
#         minReplace = 1

#     # Replace random # of items in the list with random item from GList

#     newMsg = args
#     toBeReplaced = []
#     for i in range(random.randrange(minReplace, len(args))):

#         isVaild = False
#         while isVaild == False:


#             num = random.randrange(0, len(args))


#             if num in toBeReplaced:
#                 pass
#             elif len(args[num]) < 4:
#                 pass
#             else:
#                 toBeReplaced.append(num)
#                 isVaild = True
#                 newWord = (wordnet.synsets(args[num]))#[0].lemmas()[0].name()
#                 if len(newWord) <= 0:
#                     pass
#                 else:
#                     newWord = newWord[0].lemmas()[0].name()

#                     newMsg[num] = newWord

#                 break


#     return " ".join(args)


async def wait_for_deletion(
    message: Message,
    user_ids: Sequence[Snowflake],
    deletion_emoji: str = "❌",
    timeout: int = 60,
    attach_emojis: bool = True,
    client: Optional[Client] = None,
) -> None:
    """
    Wait for up to `timeout` seconds for a reaction by any of the specified `user_ids` to delete the message.
    An `attach_emojis` bool may be specified to determine whether to attach the given
    `deletion_emojis` to the message in the given `context`
    A `client` instance may be optionally specified, otherwise client will be taken from the
    guild of the message.
    """
    if message.guild is None and client is None:
        raise ValueError("Message must be sent on a guild")

    bot = client or message.guild.me

    if attach_emojis:

        await message.add_reaction(deletion_emoji)

    def check(reaction: Reaction, user: Member) -> bool:
        """Check that the deletion emoji is reacted by the approprite user."""
        return (
            reaction.message.id == message.id
            and reaction.emoji == deletion_emoji
            and user.id in user_ids
        )

    # with contextlib.suppress(asyncio.TimeoutError):
    #     await bot.wait_for('reaction_add', check=check, timeout=timeout)
    # for emoji in deletion_emojis:
    #     await message.add_reaction(emoji)
    # await message.delete()
    try:
        await bot.wait_for("reaction_add", check=check, timeout=timeout)
        await message.delete()
    except asyncio.TimeoutError:

        await message.remove_reaction(deletion_emoji, discord.Object(bot.user.id))


def hover_link(ctx, msg, text="`?`"):
    return (
        f"[{text}](https://www.discordapp.com/"
        f"channels/{ctx.guild.id}/{ctx.channel.id} "
        f""""{msg}")"""
    )


def is_int(string):
    try:
        int(string)
        return True
    except ValueError:
        return False
