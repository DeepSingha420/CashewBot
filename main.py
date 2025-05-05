import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

active_channel = {}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Game state flag
gamestate = False

@bot.event
async def on_ready():
    print("Bot is running...")
    print("-----------------")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.tree.command(name="wordchain", description="Play Word Chain")
async def wordchain(interaction: discord.Interaction):
    global gamestate
    channel_id = interaction.channel_id
    if gamestate:
        embed = discord.Embed(
            title="⚠️ Game Already Running",
            description="A Word Chain game is already active in this channel.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)
        return

    gamestate = True
    active_channel[channel_id] = {
        'lastuser': None,
        'listword': [],
        'scores': {}
    }

    embed = discord.Embed(
        title="🟢 Word Chain Game Started!",
        description="Start the game by typing any word with at least 2 letters.\n\n**Rules:**\n- Take turns.\n- Each word must start with the last letter of the previous word.\n- Don't repeat your turn!",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="kill", description="Kill Ongoing Word Chain")
async def kill(interaction: discord.Interaction):
    global gamestate
    channel_id = interaction.channel_id
    if not gamestate or channel_id not in active_channel:
        embed = discord.Embed(
            title="❌ No Game Running",
            description="There is no active Word Chain game in this channel.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    data = active_channel[channel_id]
    word_count = len(data['listword'])
    score_text = "\n".join([f"**{user}**: {score} 🧠" for user, score in data['scores'].items()])
    embed = discord.Embed(
        title="🔚 Game Over!",
        description=f"**Total Words Played:** {word_count}\n\n**Final Scores:**\n{score_text}",
        color=discord.Color.blue()
    )

    gamestate = False
    del active_channel[channel_id]
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    global gamestate
    if message.author == bot.user or not gamestate:
        return

    channel_id = message.channel.id
    word = message.content.strip().lower()

    if not word.isalpha() or len(word) < 2:
        await message.add_reaction("🔴")  # Incorrect format
        return

        # Check if game is active in the channel
    if channel_id not in active_channel:
        return

    channel_game = active_channel[channel_id]

    # REPEATED TURN
    if message.author.name == channel_game['lastuser']:
        chain = " → ".join(channel_game['listword'] + [word])
        word_count = len(channel_game['listword']) + 1
        score_text = "\n".join([f"**{user}**: {score} 🧠" for user, score in channel_game['scores'].items()])

        embed = discord.Embed(
            title=f"❌ {message.author.name} Played Twice!",
            description=f"**Final Chain:** {chain}\n\n**Total Words:** {word_count}\n\n**Scores:**\n{score_text}",
            color=discord.Color.red()
        )
        await message.channel.send(embed=embed)
        await message.add_reaction("🔴")
        gamestate = False
        del active_channel[channel_id]
        return

    # WORD REUSE DETECTION
    if word in channel_game['listword']:
        chain = " → ".join(channel_game['listword'] + [word])
        word_count = len(channel_game['listword']) + 1
        score_text = "\n".join([f"**{user}**: {score} 🧠" for user, score in channel_game['scores'].items()])

        embed = discord.Embed(
            title="🔁 Word Reused!",
            description=f"The word **`{word}`** has already been used.\n\n**Final Chain:** {chain}\n\n**Total Words:** {word_count}\n\n**Scores:**\n{score_text}",
            color=discord.Color.red()
        )
        await message.channel.send(embed=embed)
        await message.add_reaction("🔴")
        gamestate = False
        del active_channel[channel_id]
        return

    # WRONG FIRST LETTER
    if channel_game['listword']:
        last_word = channel_game['listword'][-1]
        if word[0] != last_word[-1]:
            await message.channel.send(
                embed=discord.Embed(
                    title="❌ Wrong Starting Letter",
                    description=f"The word should start with `{last_word[-1]}`!",
                    color=discord.Color.red()
                )
            )
            await message.add_reaction("🔴")
            return

    # VALID WORD
    channel_game['listword'].append(word)
    channel_game['lastuser'] = message.author.name
    channel_game['scores'][message.author.name] = channel_game['scores'].get(message.author.name, 0) + 1

    await message.add_reaction("🟢")  # Correct
bot.run(os.getenv('DISCORD_BOT_TOKEN'))
