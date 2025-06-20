import disnake, os, json, datetime, requests, io
from disnake.ext import commands, tasks
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

DB_PATH = "voice_times.json"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # ou outro caminho válido para fonte

class VoiceTimeTracker(commands.Cog):
    def __init__(self, tie):
        self.tie = tie
        self.join_times = {}  # {guild_id: {user_id: join_time}}
        self.total_times = {}  # {guild_id: {user_id: total_seconds}}
        self._load_db()
        self.autosave_task.start()

    def _load_db(self):
        if os.path.isfile(DB_PATH):
            with open(DB_PATH, "r") as f:
                data = json.load(f)
                self.total_times = {int(g): {int(u): s for u, s in us.items()} for g, us in data.items()}
        else:
            self.total_times = {}

    def _save_db(self):
        with open(DB_PATH, "w") as f:
            json.dump({str(g): us for g, us in self.total_times.items()}, f)

    def _update_time(self, member):
        gid, uid = member.guild.id, member.id
        now = datetime.datetime.utcnow()
        if gid in self.join_times and uid in self.join_times[gid]:
            joined = datetime.datetime.fromisoformat(self.join_times[gid][uid])
            delta = (now - joined).total_seconds()
            self.total_times[gid][uid] = self.total_times[gid].get(uid, 0) + delta
            self.join_times[gid][uid] = now.isoformat()  # reinicia o contador

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        gid, uid = member.guild.id, member.id
        now = datetime.datetime.utcnow()
        if member.bot:
            return

        self.join_times.setdefault(gid, {})
        self.total_times.setdefault(gid, {})

        if before.channel is None and after.channel:
            if not after.self_mute and not after.mute:
                self.join_times[gid][uid] = now.isoformat()

        elif before.channel and after.channel is None:
            self._update_time(member)
            self.join_times[gid].pop(uid, None)

        elif before.channel and after.channel:
            if before.self_mute != after.self_mute:
                if after.self_mute:
                    self._update_time(member)
                    self.join_times[gid].pop(uid, None)
                else:
                    self.join_times[gid][uid] = now.isoformat()

    @commands.command(aliases=['vt', 'vct'])
    async def voicetime(self, ctx, membro: disnake.Member = None):
        membro = membro or ctx.author
        gid = ctx.guild.id
        uid = membro.id

        self.total_times.setdefault(gid, {})
        tempo_total = self.total_times[gid].get(uid, 0)

        if gid in self.join_times and uid in self.join_times[gid]:
            agora = datetime.datetime.utcnow()
            entrada = datetime.datetime.fromisoformat(self.join_times[gid][uid])
            tempo_total += (agora - entrada).total_seconds()

        h, r = divmod(int(tempo_total), 3600)
        m, s = divmod(r, 60)

        ranked = sorted(self.total_times[gid].items(), key=lambda x: x[1], reverse=True)
        user_ids = [uid for uid, _ in ranked]
        try:
            pos = user_ids.index(uid) + 1
        except ValueError:
            pos = len(user_ids) + 1

        emb = disnake.Embed(
            title=f"⏱️ Voice Time de {membro.display_name}",
            color=disnake.Color.blurple()
        )
        emb.add_field(name="Tempo total", value=f"{h}h {m}m {s}s", inline=False)
        emb.add_field(name="Posição no servidor", value=f"{pos}/{len(user_ids)}", inline=False)

        await ctx.reply(embed=emb)

    def gerar_imagem_top10(self, ctx, ranking):

        largura, altura = 1000, 1300

        # Baixar ícone do servidor
        try:
            resposta = requests.get(str(ctx.guild.icon.url), timeout=10)
            bg_img = Image.open(io.BytesIO(resposta.content)).convert("RGBA").resize((largura, altura))
            bg_img = bg_img.filter(ImageFilter.GaussianBlur(15))
        except:
            bg_img = Image.new("RGBA", (largura, altura), (30, 20, 60, 255))

        draw = ImageDraw.Draw(bg_img)

        try:
            fonte_bold = ImageFont.truetype("arialbd.ttf", 40)
            fonte_normal = ImageFont.truetype("arial.ttf", 26)
            fonte_pequena = ImageFont.truetype("arial.ttf", 22)
        except:
            fonte_bold = fonte_normal = fonte_pequena = ImageFont.load_default()

        cores_tiers = [
            {"bg": (66, 50, 24, 200), "borda": (255, 215, 0, 255)},      # Ouro
            {"bg": (47, 47, 47, 200), "borda": (192, 192, 192, 255)},    # Prata
            {"bg": (51, 34, 17, 200), "borda": (205, 127, 50, 255)},     # Bronze
            {"bg": (26, 26, 47, 150), "borda": (74, 74, 106, 255)}       # Restante
        ]
        medalhas = [
                    Image.open("imgs/ouro.png").convert("RGBA"),
                    Image.open("imgs/prata.png").convert("RGBA"),
                    Image.open("imgs/bronze.png").convert("RGBA")
                ]

        # Título centralizado (compatível com Pillow >= 10.0)
        titulo = f"Ranking de voz: {ctx.guild.name}"
        bbox = fonte_bold.getbbox(titulo)
        text_width = bbox[2] - bbox[0]
        draw.text(((largura - text_width) // 2, 20), titulo, font=fonte_bold, fill=(255, 255, 255, 230))

        y_position = 100

        for idx, (membro, tempo) in enumerate(ranking[:10]):
            tier = idx if idx < 3 else 3
            is_top3 = idx < 3

            # Avatar
            try:
                resposta = requests.get(str(membro.display_avatar.url), timeout=10)
                avatar = Image.open(io.BytesIO(resposta.content)).convert("RGBA").resize((80, 80))
                mask = Image.new("L", avatar.size, 0)
                ImageDraw.Draw(mask).ellipse((0, 0, 80, 80), fill=255)
                avatar.putalpha(mask)
            except:
                avatar = Image.new("RGBA", (80, 80), (100, 100, 100, 255))

            item_width = largura - 100
            item_height = 100 if is_top3 else 90
            item_fundo = Image.new("RGBA", (item_width, item_height), cores_tiers[tier]["bg"])
            item_draw = ImageDraw.Draw(item_fundo)

            # Avatar
            item_fundo.alpha_composite(avatar, (10, 10))

            # Nome
            item_draw.text((100, 15), membro.display_name[:20], font=fonte_normal, fill=cores_tiers[tier]["borda"])

            # Tempo
            h = int(tempo) // 3600
            m = (int(tempo) % 3600) // 60
            item_draw.text((100, 45), f"{h}h {m}m", font=fonte_pequena, fill=(255, 255, 255, 220))

            # Posição
            pos_text = f"#{idx+1}"
            item_draw.text((item_width - 90, 30), pos_text, font=fonte_bold, fill=cores_tiers[tier]["borda"])

            # Medalha
            if is_top3:
                medalha_img = medalhas[idx].resize((40, 40))
                item_fundo.alpha_composite(medalha_img, (item_width - 150, 25))

            item_fundo = item_fundo.filter(ImageFilter.SMOOTH)
            bg_img.alpha_composite(item_fundo, (50, y_position))
            y_position += item_height + 15

        caminho = "top10_voicetime.png"
        bg_img.convert("RGB").save(caminho, "PNG", optimize=True, quality=100)
        return caminho


    @commands.command(aliases=['ldb', 'ld'])
    async def leaderboard(self, ctx):
        async with ctx.typing():
            gid = ctx.guild.id
            usermap = self.total_times.get(gid, {})

            # Atualiza todos os usuários atualmente em call antes de gerar o ranking
            for uid in list(self.join_times.get(gid, {})):
                member = ctx.guild.get_member(uid)
                if member:
                    self._update_time(member)

            sorted_users = sorted(usermap.items(), key=lambda x: x[1], reverse=True)[:10]
            ranking = [(ctx.guild.get_member(uid), secs) for uid, secs in sorted_users if ctx.guild.get_member(uid)]
            caminho = self.gerar_imagem_top10(ctx, ranking)

            file = disnake.File(caminho, filename="top10_voicetime.png")
            await ctx.reply(file=file)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addtime(self, ctx, membro: disnake.Member, horas: float):
        gid = ctx.guild.id
        self.total_times.setdefault(gid, {})
        segs = int(horas * 3600)
        self.total_times[gid][membro.id] = self.total_times[gid].get(membro.id, 0) + segs
        await ctx.reply(f"✅ Adicionados {horas:.2f}h a {membro.display_name}.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removetime(self, ctx, membro: disnake.Member, horas: float):
        gid = ctx.guild.id
        segs = int(horas * 3600)
        self.total_times.setdefault(gid, {})
        atual = self.total_times[gid].get(membro.id, 0)
        self.total_times[gid][membro.id] = max(0, atual - segs)
        await ctx.reply(f"❌ Removidos {horas:.2f}h de {membro.display_name}.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def resetvoicetime(self, ctx, membro: disnake.Member = None):
        gid = ctx.guild.id
        self.total_times.setdefault(gid, {})

        if membro:
            # Resetar apenas um membro
            if membro.id in self.total_times[gid]:
                self.total_times[gid][membro.id] = 0
                self.join_times.get(gid, {}).pop(membro.id, None)
                await ctx.send(f"🔄 Tempo de voz resetado para {membro.display_name}.")
            else:
                await ctx.send(f"⚠️ {membro.display_name} não possui tempo registrado.")
        else:
            # Resetar todos os membros
            self.total_times[gid] = {}
            self.join_times[gid] = {}
            await ctx.reply("🔄 Todos os tempos de voz foram resetados para este servidor.")

    @tasks.loop(minutes=5)
    async def autosave_task(self):
        self._save_db()

    def cog_unload(self):
        self.autosave_task.cancel()
        self._save_db()

def setup(tie):
    tie.add_cog(VoiceTimeTracker(tie))
