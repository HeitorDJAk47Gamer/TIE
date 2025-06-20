import disnake
from disnake.ext import commands, tasks
import json, os, random

XP_FILE = "chat_xp.json"

class ChatXP(commands.Cog):
    def __init__(self, tie):
        self.tie = tie
        self.xp_data = self.load_xp()
        self.autosave.start()

    def load_xp(self):
        if os.path.exists(XP_FILE):
            with open(XP_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_xp(self):
        with open(XP_FILE, "w") as f:
            json.dump(self.xp_data, f)

    def xp_necessario(self, level):
        return 500 * (level - 1)

    def add_xp(self, guild_id, user_id, amount):
        g, u = str(guild_id), str(user_id)
        self.xp_data.setdefault(g, {}).setdefault(u, {"xp": 0, "level": 1})
        self.xp_data[g][u]["xp"] += amount

        leveled = False
        while self.xp_data[g][u]["xp"] >= self.xp_necessario(self.xp_data[g][u]["level"] + 1):
            self.xp_data[g][u]["level"] += 1
            leveled = True
        return leveled

    def remove_xp(self, guild_id, user_id, amount):
        g, u = str(guild_id), str(user_id)
        self.xp_data.setdefault(g, {}).setdefault(u, {"xp": 0, "level": 1})
        self.xp_data[g][u]["xp"] = max(0, self.xp_data[g][u]["xp"] - amount)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        xp_gain = random.randint(2, 5)
        leveled_up = self.add_xp(message.guild.id, message.author.id, xp_gain)
        if leveled_up:
            lvl = self.xp_data[str(message.guild.id)][str(message.author.id)]["level"]
            try:
                await message.channel.send(f"🎉 {message.author.mention} subiu para o nível {lvl}!")
            except disnake.HTTPException:
                pass  # ignora caso caia no rate limit

    @commands.command()
    async def rank(self, ctx, member: disnake.Member = None):
        member = member or ctx.author
        g, u = str(ctx.guild.id), str(member.id)
        data = self.xp_data.get(g, {}).get(u, {"xp": 0, "level": 1})
        await ctx.send(f"🏅 {member.display_name} – Nível {data['level']} com {data['xp']} XP")

    @commands.command()
    async def top(self, ctx):
        g = str(ctx.guild.id)
        users = self.xp_data.get(g, {})
        top = sorted(users.items(), key=lambda x: x[1]["xp"], reverse=True)[:5]

        embed = disnake.Embed(title="🏆 Top 5 XP")
        for i, (uid, data) in enumerate(top, 1):
            member = ctx.guild.get_member(int(uid))
            if member:
                embed.add_field(
                    name=f"{i}. {member.display_name}",
                    value=f"Nível {data['level']} – {data['xp']} XP",
                    inline=False
                )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def resetxp(self, ctx):
        g = str(ctx.guild.id)
        self.xp_data[g] = {}
        await ctx.send("🔄 XP de todos os membros foi resetado.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addxp(self, ctx, member: disnake.Member, amount: int):
        self.add_xp(ctx.guild.id, member.id, amount)
        await ctx.send(f"✅ {amount} XP adicionado para {member.display_name}.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removexp(self, ctx, member: disnake.Member, amount: int):
        self.remove_xp(ctx.guild.id, member.id, amount)
        await ctx.send(f"❌ {amount} XP removido de {member.display_name}.")

    @tasks.loop(minutes=5)
    async def autosave(self):
        self.save_xp()

    def cog_unload(self):
        self.autosave.cancel()
        self.save_xp()

def setup(tie):
    tie.add_cog(ChatXP(tie))