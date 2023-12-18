import os, json, random, datetime, asyncio, disnake, requests
from io import BytesIO
from disnake.ext import commands, tasks
from decouple import config

token = config('TOKEN')

tie = commands.Bot(command_prefix=commands.when_mentioned_or('.'),case_insensitive=True, intents=disnake.Intents.all())

@tie.event
async def on_ready():
	calc = tie.latency * 1000
	pong = round(calc)
	stats.start()

	print(f'Nome: {tie.user}  ID: {tie.user.id}')
	print(f'Membros Globais: {len(tie.users)}')
	print(f'Servidores Globais: {len(tie.guilds)}')
	print(f'Ping {pong} ms')
	Print(f'As Águias Imorríveis!')

@tasks.loop(minutes=10)
async def stats():
	await tie.change_presence(activity=disnake.Activity(type=disnake.ActivityType.listening, name=f'{len(tie.users)} Membros'))
	await asyncio.sleep(5 * 60)
	await tie.change_presence(activity=disnake.Activity(type=disnake.ActivityType.watching, name=f'{len(tie.guilds)} Server'))


@tie.event
async def on_message(message):
	if message.author == tie.user or message.mention_everyone:
		return
	elif message.channel.type is disnake.ChannelType.private:
		return

	await tie.process_commands(message)

for filename in os.listdir('./cogs'):
	if filename.endswith('.py'):
		tie.load_extension(f'cogs.{filename[:-3]}')
		print(f'{filename[:-3]} carregado!')

@tie.event
async def on_command_error(ctx, error):
	print(f"Ocorreu um erro no comando {ctx.command}: {error}")


@tie.command()
async def ping(ctx):
	calc = tie.latency * 1000
	pong = round(calc)
	x = disnake.Embed(title=f'Ping do bot {tie.user.display_name}:', description=f' Atualmento o bot está com `{pong} ms`')
	x.timestamp = datetime.datetime.utcnow()
	await ctx.send(embed=x)


@tie.command(description='links do servidor para votar ou entrar!')
async def links(ctx):
	x = disnake.Embed(title=f'links do servidor {tie.user.display_name}!', description=f'[Disforge](https://disforge.com/server/74106-the-immortal-eagles) \n[Top.gg](https://top.gg/servers/1044599844343382066) \n[disnakeList](https://disnakebotlist.com/servers/theeagles)')
	x.timestamp = datetime.datetime.utcnow()
	await ctx.send(embed=x)


@tie.command()
async def clear(ctx, quantidade=1000):
	await ctx.channel.purge(limit=quantidade)
	x = disnake.Embed(title=f'Sistema de limpeza TIE', description=f'Foram limpadas as ultimás {quantidade} mensagens do canal!')
	x.timestamp = datetime.datetime.utcnow()
	emoji = await ctx.send(embed=x)
	await emoji.add_reaction('✅')

@tie.command()
async def addrole(ctx, cargo: disnake.Role):
    for membro in ctx.guild.members:
        await membro.add_roles(cargo)
    await ctx.send(f'O cargo {cargo.name} foi adicionado a todos os membros.')

@tie.command()
async def rmvrole(ctx, cargo: disnake.Role):
    for membro in ctx.guild.members:
        await membro.remove_roles(cargo)
    await ctx.send(f'O cargo {cargo.name} foi removido a todos os membros.')

tie.run(token)