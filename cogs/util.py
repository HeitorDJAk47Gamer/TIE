import discord, requests, asyncio, datetime, random, re
from discord.ext import commands, tasks

class Utilidade(commands.Cog):

    def __init__(self, tie):
        self.tie = tie

    @commands.command(aliases=['reportar', 'falha'])
    async def report(self, ctx, *, report_msg):
        channel = self.tie.get_channel(893934257834176512)
        if not channel:
            await ctx.send("Não foi possível encontrar o canal de report. Por favor, entre em contato com o suporte.")
            return

        # Cria a mensagem de report
        report_embed = discord.Embed(
            title="Nova mensagem de report",
            description=f"**Autor:** {ctx.author.mention}\n"
                        f"**Servidor:** {ctx.guild.name}\n"
                        f"**Canal:** {ctx.channel.mention}\n"
                        f"**Mensagem:**\n{report_msg}",
            color=discord.Color.red()
        )
        report_embed.set_footer(text=f"ID do autor: {ctx.author.id}")
        report_embed.timestamp = datetime.datetime.utcnow()

        # Envia a mensagem para o canal de report e aguarda a confirmação
        try:
            report_message = await ctx.send(embed=report_embed)
            await report_message.add_reaction("✅")
            await report_message.add_reaction("❌")
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message == report_message
            reaction, user = await self.tie.wait_for("reaction_add", check=check, timeout=30.0)

            if str(reaction.emoji) == "✅":
                await ctx.send("Obrigado pelo seu report. Nossa equipe irá avaliar sua mensagem.")
                await channel.send(embed=report_embed)
            else:
                await ctx.send("Seu report foi cancelado.")
        except discord.Forbidden:
            await ctx.send("Não tenho permissão para enviar mensagens no canal de report.")
        except discord.HTTPException:
            await ctx.send("Não foi possível enviar o report. Por favor, tente novamente mais tarde.")
        except asyncio.TimeoutError:
            await ctx.send("O tempo para confirmar o report acabou. Seu report foi cancelado.")


async def setup(tie):
    await tie.add_cog(Utilidade(tie))