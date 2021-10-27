from hikari import GatewayBot,Intents
import config

intents=Intents.DM_MESSAGES | Intents.GUILD_MESSAGES

bot = GatewayBot(token=config.BOT_TOKEN,intents=intents)

bot.run()