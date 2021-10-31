import lightbulb
from hikari import Intents
import os
import argparse

import config

intents = Intents.GUILD_MESSAGES

bot = lightbulb.Bot(token=config.BOT_TOKEN, prefix=config.BOT_PREFIX, logs="DEBUG", intents=intents)

parser = argparse.ArgumentParser(description='Bot CLI arguments')
parser.add_argument('--all', help='load all modules', action='store_true')
args = parser.parse_args()

# Load plugins from extensions folder
for file in os.listdir("./extensions/"):
    print(file)
    if file.endswith(".py") and not file.startswith("_") and (args.all or file[:-3] in args):
        print(file[:-3])
        try:
            bot.load_extension(f"extensions.{file[:-3]}")
        except lightbulb.errors.ExtensionAlreadyLoaded:
            print(f"Extension \"{file[:-3]}\" is already loaded.")
        except lightbulb.errors.ExtensionMissingLoad:
            print(f"Extension \"{file[:-3]}\" does not contain `load()` function.")
        except lightbulb.errors.ExtensionNotFound:
            print(f"Cannot find extension named \"{file[:-3]}\".")


@lightbulb.check(lightbulb.owner_only)
@bot.command(hidden=True)
async def load(ctx, *, name=None):
    if name is not None:
        try:
            bot.load_extension(f"extensions.{name}")
            await ctx.respond(f"Extension \"{name}\" loaded successfully.")
        except lightbulb.errors.ExtensionAlreadyLoaded:
            await ctx.respond(f"Extension \"{name}\" is already loaded.")
        except lightbulb.errors.ExtensionMissingLoad:
            await ctx.respond(f"Extension \"{name}\" does not contain `load()` function.")
        except lightbulb.errors.ExtensionNotFound:
            await ctx.respond(f"Cannot find extension named \"{name}\".")


@lightbulb.check(lightbulb.owner_only)
@bot.command(hidden=True)
async def unload(ctx, *, name=None):
    if name is not None:
        try:
            bot.unload_extension(f"extensions.{name}")
            await ctx.respond(f"Extension \"{name}\" unloaded successfully.")
        except lightbulb.errors.ExtensionNotLoaded:
            await ctx.respond(f"Extension \"{name}\" is not loaded.")
        except lightbulb.errors.ExtensionMissingUnload:
            await ctx.respond(f"Extension \"{name}\" does not contain `unload()` function.")
        except lightbulb.errors.ExtensionNotFound:
            await ctx.respond(f"Cannot find extension named \"{name}\".")


@unload.command_error()
@load.command_error()
async def error(event: lightbulb.events.CommandErrorEvent):
    if isinstance(event.exception, lightbulb.errors.NotOwner):
        return True
    return False


bot.run()
