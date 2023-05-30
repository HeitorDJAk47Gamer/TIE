import os
import json
import random
import datetime
import asyncio
import discord
import requests
from io import BytesIO
from discord.ext import commands, tasks
from decouple import config

token = config('TOKEN')

tie = commands.Bot(command_prefix=commands.when_mentioned_or('.'),case_insensitive=True, intents=discord.Intents.all())

@tie.event
async def on_ready():
	calc = tie.latency * 1000
	pong = round(calc)
	stats.start()
	await tie.tree.sync()

	print(f'Nome: {tie.user}  ID: {tie.user.id}')
	print(f'Membros Globais: {len(tie.users)}')
	print(f'Servidores Globais: {len(tie.guilds)}')
	print(f'Ping {pong} ms')

@tasks.loop(minutes=10)
async def stats():
	await tie.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f'{len(tie.users)} Membros'))
	await asyncio.sleep(5 * 60)
	await tie.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'{len(tie.guilds)} Server'))


@tie.event
async def on_message(message):
	if message.author == tie.user or message.mention_everyone:
		return
	elif message.channel.type is discord.ChannelType.private:
		return

	await tie.process_commands(message)

async def load_cogs():
	for filename in os.listdir('./cogs'):
		if filename.endswith('.py'):
			await tie.load_extension(f'cogs.{filename[:-3]}')
			print(f'{filename[:-3]} carregado!')

async def main():
	async with tie:
		await load_cogs()
		await tie.start(token)

@tie.event
async def on_command_error(ctx, error):
	print(f"Ocorreu um erro no comando {ctx.command}: {error}")


@tie.hybrid_command()
async def ping(ctx):
	calc = tie.latency * 1000
	pong = round(calc)
	x = discord.Embed(title=f'Ping do bot {tie.user.display_name}:', description=f' Atualmento o bot está com `{pong} ms`')
	x.timestamp = datetime.datetime.utcnow()
	await ctx.send(embed=x)


@tie.hybrid_command(description='links do servidor para votar ou entrar!')
async def links(ctx):
	x = discord.Embed(title=f'links do servidor {tie.user.display_name}!', description=f'[Disforge](https://disforge.com/server/74106-the-immortal-eagles) \n[Top.gg](https://top.gg/servers/1044599844343382066) \n[DiscordList](https://discordbotlist.com/servers/theeagles)')
	x.timestamp = datetime.datetime.utcnow()
	await ctx.send(embed=x)


@tie.hybrid_command()
async def clear(ctx, quantidade=1000):
	await ctx.channel.purge(limit=quantidade)
	x = discord.Embed(title=f'Sistema de limpeza TIE', description=f'Foram limpadas as ultimás {quantidade} mensagens do canal!')
	x.timestamp = datetime.datetime.utcnow()
	emoji = await ctx.send(embed=x)
	await emoji.add_reaction('✅')


@tie.hybrid_command()
async def anime(ctx):
	url = "https://www.thiswaifudoesnotexist.net/example-{}.jpg".format(random.randint(1, 100000))
	response = requests.get(url)
	file = discord.File(BytesIO(response.content), "anime.jpg")
	embed = discord.Embed(title="Imagem Aleatória de Anime", color=discord.Color.blue())
	embed.set_image(url="attachment://anime.jpg")
	await ctx.send(file=file, embed=embed)


asyncio.run(main())
