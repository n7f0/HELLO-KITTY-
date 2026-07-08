import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Select
import random
import json
import os
import datetime

# =================== CONFIGURAÇÕES ===================
TOKEN = os.getenv("TOKEN")
ARQUIVO_DADOS = os.getenv("DATA_PATH", "dados_cafe.json")
GUILD_ID = os.getenv("GUILD_ID")
# =====================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- Arquivo de dados ----------
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# ---------- Emojis e imagens locais ----------
PERSONAGENS_EMOJI = {
    "Nenê": "💫",
    "Hello Kitty": "👧",
    "Dear Daniel": "💙",
    "My Melody": "🎀",
    "Kuromi": "💀",
    "Pompompurin": "🍮",
    "Cinnamoroll": "☁️",
    "Little Twin Stars": "⭐",
    "Keroppi": "🐸",
    "Badtz-Maru": "🐧",
    "Tuxedo Sam": "🐧",
    "Pochacco": "🐶",
    "Chococat": "🐱",
    "Hangyodon": "🐟",
    "Pekkle": "🦆",
    "Spottie Dottie": "🐶",
    "Landry": "🐱",
    "Moppu": "🐹",
    "Coro Chan": "🐰",
    "Minna no Tabo": "🐻",
    "Charmmy Kitty": "🐱",
    "Sugar": "🐰",
    "Tiny Chum": "🐹",
    "Cathy": "🐱",
    "George": "🐵",
    "Fifi": "🐶",
    "Rory": "🐱",
    "Lulu": "🐰",
    "Pipi": "🐤",
    "Nana": "🐱",
    "Mimi": "🐰",
    "Sasa": "🐱",
    "Kiki": "🐱",
    "Lala": "🐰",
    "Mocha": "🐶"
}

# Imagens locais (coloque os arquivos .png na mesma pasta do bot)
IMAGENS_LOCAIS = {
    "Hello Kitty": "hellokitty.png",
    "My Melody": "mymelody.png",
    "Kuromi": "kuromi.png",
    "Cinnamoroll": "cinnamoroll.png",
    "Pompompurin": "pompompurin.png"
}

# Arquivo de imagem da loja
LOJA_IMAGEM = "loja.png"

# ---------- Efeitos descritos ----------
EFEITOS_DESC = {
    "hello_kitty": "20% reembolso, +2💗/msg, 10% frag extra",
    "dear_daniel": "+1💗 a cada 50 msgs",
    "my_melody": "10% reembolso ao comprar",
    "kuromi": "+15% chance Épico+",
    "pompompurin": "50% de não gastar 💗",
    "cinnamoroll": "Troca 2 dups por 1 novo",
    "twin_stars": "+1💗 a cada 10 msgs",
    "keroppi": "+1 🍬 diário extra",
    "badtz_maru": "+5💗 ao comprar personagem",
    "tuxedo_sam": "30% +1 fragmento",
    "pochacco": "+1💗 a cada 20💗 ganhos",
    "chococat": "20% duplicar",
    "hangyodon": "Reciclar dup = 3💗",
    "pekkle": "+5% chance Incomum+",
    "nene": "50% reembolso, +5💗/msg, +3💗/5 msgs, 50% frag extra",
    "spottie_dottie": "+1💗 a cada 15 msgs",
    "landry": "5% duplicar",
    "moppu": "3% reembolso",
    "coro_chan": "5% frag extra",
    "minna_tabo": "10% não gastar 💗",
    "charmmy_kitty": "+1💗 inicial",
    "sugar": "5% +1💗 ao comprar",
    "tiny_chum": "+2💗 inicial",
    "cathy": "2% Épico+",
    "george": "+1 frag a cada 100 msgs",
    "fifi": "+1💗 a cada 20 msgs",
    "rory": "5% +1 frag",
    "lulu": "1% reembolso",
    "pipi": "+1💗 a cada 80 msgs",
    "nana": "+1💗 a cada 25 msgs",
    "mimi": "5% +1💗 ao comprar",
    "sasa": "+1 frag a cada 50 msgs",
    "kiki": "2% duplicar",
    "lala": "10% +1💗 ao fazer amizade",
    "mocha": "+1💗 a cada 60 msgs"
}

# ---------- Personagens ----------
PERSONAGENS = []
PERSONAGENS.append({"nome": "Nenê", "peso": 0, "raridade": "Ultimate", "efeito": "nene"})
PERSONAGENS.append({"nome": "Hello Kitty", "peso": 1, "raridade": "Mítico", "efeito": "hello_kitty"})
PERSONAGENS.append({"nome": "Dear Daniel", "peso": 2, "raridade": "Lendário", "efeito": "dear_daniel"})
PERSONAGENS.append({"nome": "My Melody", "peso": 5, "raridade": "Lendário", "efeito": "my_melody"})
PERSONAGENS.append({"nome": "Kuromi", "peso": 5, "raridade": "Lendário", "efeito": "kuromi"})
PERSONAGENS.append({"nome": "Pompompurin", "peso": 10, "raridade": "Épico", "efeito": "pompompurin"})
PERSONAGENS.append({"nome": "Cinnamoroll", "peso": 10, "raridade": "Épico", "efeito": "cinnamoroll"})
PERSONAGENS.append({"nome": "Little Twin Stars", "peso": 20, "raridade": "Épico", "efeito": "twin_stars"})
PERSONAGENS.append({"nome": "Keroppi", "peso": 200, "raridade": "Raro", "efeito": "keroppi"})
PERSONAGENS.append({"nome": "Badtz-Maru", "peso": 200, "raridade": "Raro", "efeito": "badtz_maru"})
PERSONAGENS.append({"nome": "Tuxedo Sam", "peso": 200, "raridade": "Raro", "efeito": "tuxedo_sam"})
PERSONAGENS.append({"nome": "Pochacco", "peso": 2000, "raridade": "Incomum", "efeito": "pochacco"})
PERSONAGENS.append({"nome": "Chococat", "peso": 2000, "raridade": "Incomum", "efeito": "chococat"})
PERSONAGENS.append({"nome": "Hangyodon", "peso": 2000, "raridade": "Incomum", "efeito": "hangyodon"})
PERSONAGENS.append({"nome": "Pekkle", "peso": 2000, "raridade": "Incomum", "efeito": "pekkle"})

COMUNS_NOMES = [
    "Spottie Dottie", "Landry", "Moppu", "Coro Chan", "Minna no Tabo",
    "Charmmy Kitty", "Sugar", "Tiny Chum", "Cathy", "George",
    "Fifi", "Rory", "Lulu", "Pipi", "Nana", "Mimi", "Sasa", "Kiki", "Lala", "Mocha"
]
COMUNS_EFEITOS = [
    "spottie_dottie", "landry", "moppu", "coro_chan", "minna_tabo",
    "charmmy_kitty", "sugar", "tiny_chum", "cathy", "george",
    "fifi", "rory", "lulu", "pipi", "nana", "mimi", "sasa", "kiki", "lala", "mocha"
]
peso_comum_base = 499567
for i, nome in enumerate(COMUNS_NOMES):
    peso = peso_comum_base if i < 19 else 9991347 - (19 * peso_comum_base)
    PERSONAGENS.append({"nome": nome, "peso": peso, "raridade": "Comum", "efeito": COMUNS_EFEITOS[i]})

TOTAL_PESOS = sum(p["peso"] for p in PERSONAGENS if p["nome"] != "Nenê")
assert TOTAL_PESOS == 10000000

PRECO_MOEDAS = {
    "Comum": 50, "Incomum": 100, "Raro": 250,
    "Épico": 1000, "Lendário": 5000, "Mítico": 20000, "Ultimate": 100000
}

# ---------- Funções auxiliares ----------
def tem_efeito(uid, dados, efeito_nome):
    if uid not in dados: return False
    for nome in set(dados[uid]["personagens"]):
        if nome == "Nenê" and efeito_nome == "nene": return True
        for p in PERSONAGENS:
            if p["nome"] == nome and p["efeito"] == efeito_nome: return True
    return False

def chance_nao_gastar(uid, dados):
    if tem_efeito(uid, dados, "pompompurin") and random.random() < 0.5: return True
    if tem_efeito(uid, dados, "minna_tabo") and random.random() < 0.10: return True
    return False

def calcular_coracoes_msg(uid, dados, msg_count):
    base = 1
    if tem_efeito(uid, dados, "hello_kitty"): base += 2
    if tem_efeito(uid, dados, "nene"): base += 5
    if tem_efeito(uid, dados, "spottie_dottie") and msg_count % 15 == 0: base += 1
    if tem_efeito(uid, dados, "fifi") and msg_count % 20 == 0: base += 1
    if tem_efeito(uid, dados, "nana") and msg_count % 25 == 0: base += 1
    return base

def sortear_personagem(uid, dados, cupom_raridade=False):
    if cupom_raridade:
        pool = [p for p in PERSONAGENS if p["raridade"] in ("Raro", "Épico", "Lendário", "Mítico")]
        return random.choice(pool)
    multiplicadores = {}
    if tem_efeito(uid, dados, "kuromi"):
        for p in PERSONAGENS:
            if p["raridade"] in ("Épico", "Lendário", "Mítico"):
                multiplicadores[p["nome"]] = 1.15
    if tem_efeito(uid, dados, "pekkle"):
        for p in PERSONAGENS:
            if p["raridade"] in ("Incomum", "Raro", "Épico", "Lendário", "Mítico"):
                multiplicadores[p["nome"]] = multiplicadores.get(p["nome"], 1.0) * 1.05
    if tem_efeito(uid, dados, "cathy"):
        for p in PERSONAGENS:
            if p["raridade"] in ("Épico", "Lendário", "Mítico"):
                multiplicadores[p["nome"]] = multiplicadores.get(p["nome"], 1.0) * 1.02
    pesos = []
    chars_validos = [p for p in PERSONAGENS if p["nome"] != "Nenê"]
    for p in chars_validos:
        w = p["peso"]
        if p["nome"] in multiplicadores:
            w = int(w * multiplicadores[p["nome"]])
        pesos.append(w)
    total = sum(pesos)
    rolagem = random.randint(1, total)
    acumulado = 0
    for i, p in enumerate(chars_validos):
        acumulado += pesos[i]
        if rolagem <= acumulado:
            return p
    return chars_validos[0]

def novo_jogador():
    return {
        "coracoes": 3,
        "doces": 0,
        "personagens": [],
        "fragmentos": 0,
        "moedas": 0,
        "msg_count": 0,
        "coracoes_ganhos": 0,
        "ultimo_doce": 0,
        "historico_trocas": []
    }

# ---------- Helper para envio de embed com imagem local ----------
async def enviar_embed_com_imagem(interaction, embed, nome_personagem, ephemeral=False):
    """Envia embed com thumbnail se a imagem local existir."""
    arquivo = None
    if nome_personagem in IMAGENS_LOCAIS:
        caminho = IMAGENS_LOCAIS[nome_personagem]
        if os.path.exists(caminho):
            arquivo = discord.File(caminho, filename=caminho)
            embed.set_thumbnail(url=f"attachment://{caminho}")
    if arquivo:
        await interaction.response.send_message(embed=embed, file=arquivo, ephemeral=ephemeral)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

# =================== VIEW PRINCIPAL ===================
class MenuPrincipal(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Comprar Personagem (1💗) 🎁", style=discord.ButtonStyle.success, custom_id="comprar_personagem")
    async def comprar_personagem(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if uid not in dados:
            dados[uid] = novo_jogador()
        if dados[uid]["coracoes"] < 1:
            await interaction.response.send_message("💔 Você não tem corações! Ganhe conversando ou converta doces na loja.", ephemeral=True)
            return

        gratis = chance_nao_gastar(uid, dados)
        if not gratis:
            dados[uid]["coracoes"] -= 1

        # Nenê (chance independente)
        if random.random() < 1e-11:
            dados[uid]["personagens"].append("Nenê")
            salvar_dados(dados)
            embed = discord.Embed(
                title="💫 IMPOSSÍVEL! Nenê apareceu!",
                description="A Ultimate mais rara do café!",
                color=discord.Color.gold()
            )
            await enviar_embed_com_imagem(interaction, embed, "Nenê")
            return

        personagem = sortear_personagem(uid, dados)
        duplicar = False
        if tem_efeito(uid, dados, "chococat") and random.random() < 0.20: duplicar = True
        if tem_efeito(uid, dados, "landry") and random.random() < 0.05: duplicar = True
        if tem_efeito(uid, dados, "kiki") and random.random() < 0.02: duplicar = True

        dados[uid]["personagens"].append(personagem["nome"])
        if duplicar:
            dados[uid]["personagens"].append(personagem["nome"])

        if personagem["nome"] == "Hello Kitty":
            frags = random.randint(1, 5)
            dados[uid]["fragmentos"] += frags

        if tem_efeito(uid, dados, "hello_kitty") and random.random() < 0.10: dados[uid]["fragmentos"] += 1
        if tem_efeito(uid, dados, "nene") and random.random() < 0.50: dados[uid]["fragmentos"] += 1
        if tem_efeito(uid, dados, "coro_chan") and random.random() < 0.05: dados[uid]["fragmentos"] += 1
        if tem_efeito(uid, dados, "tuxedo_sam") and random.random() < 0.30: dados[uid]["fragmentos"] += 1

        reembolso = False
        if tem_efeito(uid, dados, "my_melody") and random.random() < 0.10: reembolso = True
        if tem_efeito(uid, dados, "hello_kitty") and random.random() < 0.20: reembolso = True
        if tem_efeito(uid, dados, "nene") and random.random() < 0.50: reembolso = True
        if tem_efeito(uid, dados, "moppu") and random.random() < 0.03: reembolso = True
        if tem_efeito(uid, dados, "lulu") and random.random() < 0.01: reembolso = True
        if reembolso and not gratis:
            dados[uid]["coracoes"] += 1

        if tem_efeito(uid, dados, "badtz_maru"): dados[uid]["coracoes"] += 5
        if tem_efeito(uid, dados, "sugar") and random.random() < 0.05: dados[uid]["coracoes"] += 1
        if tem_efeito(uid, dados, "mimi") and random.random() < 0.05: dados[uid]["coracoes"] += 1

        salvar_dados(dados)

        msg = ""
        if gratis: msg += "\n🍮 Você não gastou o 💗!"
        if duplicar: msg += "\n🐱 Amigo duplicado!"
        if reembolso: msg += "\n💖 Coração devolvido!"

        embed = discord.Embed(
            title=f"🎁 Novo Amigo no Café! {PERSONAGENS_EMOJI.get(personagem['nome'], '❓')}",
            description=f"**{personagem['nome']}** ({personagem['raridade']})\n{EFEITOS_DESC.get(personagem['efeito'], '')}{msg}",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        embed.set_footer(text=f"💗: {dados[uid]['coracoes']} | Frag. HK: {dados[uid]['fragmentos']} | 🪙: {dados[uid].get('moedas', 0)}")
        await enviar_embed_com_imagem(interaction, embed, personagem["nome"])

    @discord.ui.button(label="Loja do Café 🛍️", style=discord.ButtonStyle.primary, custom_id="loja_cafe")
    async def loja(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if uid not in dados:
            dados[uid] = novo_jogador()
            salvar_dados(dados)

        embed = discord.Embed(
            title="🛍️ Loja do Hello Kitty Café",
            description=(
                f"💗 {dados[uid]['coracoes']} | 🍬 {dados[uid].get('doces',0)} | 🪙 {dados[uid].get('moedas',0)}\n"
                f"Fragmentos Hello: {dados[uid]['fragmentos']}\n\n"
                "⚡ Converter 100🍬 → 4💗\n"
                "🍀 Cupom da Sorte (200💗+300🍬) → Personagem Raro+\n"
                "👑 Resgatar Hello Kitty (100 fragmentos)\n"
                "🪙 Loja de Moedas"
            ),
            color=discord.Color.gold()
        )
        # Adiciona a imagem da loja se existir
        if os.path.exists(LOJA_IMAGEM):
            file = discord.File(LOJA_IMAGEM, filename=LOJA_IMAGEM)
            embed.set_thumbnail(url=f"attachment://{LOJA_IMAGEM}")
            await interaction.response.send_message(embed=embed, file=file, view=LojaCafeView(uid), ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, view=LojaCafeView(uid), ephemeral=True)

    @discord.ui.button(label="Drops Possíveis 🎲", style=discord.ButtonStyle.secondary, custom_id="drops_possiveis")
    async def drops_possiveis(self, interaction: discord.Interaction, button: Button):
        ordem = {"Ultimate":0, "Mítico":1, "Lendário":2, "Épico":3, "Raro":4, "Incomum":5, "Comum":6}
        chars = sorted(PERSONAGENS, key=lambda x: ordem.get(x["raridade"], 99))
        pages = []
        for i in range(0, len(chars), 10):
            chunk = chars[i:i+10]
            desc = ""
            for p in chunk:
                emoji = PERSONAGENS_EMOJI.get(p["nome"], "❓")
                efeito = EFEITOS_DESC.get(p["efeito"], "—")
                desc += f"{emoji} **{p['nome']}** ({p['raridade']}) - {efeito}\n"
            embed = discord.Embed(title="🎲 Personagens que podem aparecer", description=desc, color=discord.Color.from_rgb(255, 218, 185))
            embed.set_footer(text=f"Página {len(pages)+1}/{(len(chars)-1)//10+1}")
            pages.append(embed)
        if pages:
            await interaction.response.send_message(embed=pages[0], view=PaginaView(pages, 0), ephemeral=True)

    @discord.ui.button(label="Amigos 🤝", style=discord.ButtonStyle.primary, custom_id="amigos_menu")
    async def amigos_menu(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Escolha uma opção:", view=AmigosView(), ephemeral=True)

    @discord.ui.button(label="Tutorial/Ajuda ❔", style=discord.ButtonStyle.secondary, custom_id="tutorial_ajuda")
    async def tutorial_ajuda(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("O que você gostaria de ver?", view=TutorialAjudaView(), ephemeral=True)

# ---------- Paginação ----------
class PaginaView(View):
    def __init__(self, pages, current):
        super().__init__(timeout=60)
        self.pages = pages
        self.current = current
        self.update_buttons()

    def update_buttons(self):
        self.children[0].disabled = self.current == 0
        self.children[1].disabled = self.current == len(self.pages) - 1

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary)
    async def anterior(self, interaction: discord.Interaction, button: Button):
        self.current -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
    async def proximo(self, interaction: discord.Interaction, button: Button):
        self.current += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

# ---------- Loja ----------
class LojaCafeView(View):
    def __init__(self, uid):
        super().__init__(timeout=60)
        self.uid = uid

    @discord.ui.button(label="Doces Diários 🍬", style=discord.ButtonStyle.success)
    async def doces_diarios(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if uid not in dados: dados[uid] = novo_jogador()
        agora = datetime.datetime.utcnow().timestamp()
        ultimo = dados[uid].get("ultimo_doce", 0)
        if agora - ultimo < 86400:
            falta = 86400 - (agora - ultimo)
            horas = int(falta // 3600)
            minutos = int((falta % 3600) // 60)
            await interaction.response.send_message(f"⏰ Volte em {horas}h {minutos}m.", ephemeral=True)
            return
        qtd = random.randint(3, 8)
        if tem_efeito(uid, dados, "keroppi"): qtd += 1
        dados[uid]["doces"] = dados[uid].get("doces", 0) + qtd
        dados[uid]["ultimo_doce"] = agora
        salvar_dados(dados)
        await interaction.response.send_message(f"🍬 Você ganhou **{qtd} Doces**! Total: {dados[uid]['doces']}", ephemeral=False)

    @discord.ui.button(label="Converter 100🍬 → 4💗", style=discord.ButtonStyle.primary)
    async def converter(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if dados[uid].get("doces", 0) < 100:
            await interaction.response.send_message("Precisa de 100 doces.", ephemeral=True)
            return
        dados[uid]["doces"] -= 100
        dados[uid]["coracoes"] += 4
        salvar_dados(dados)
        await interaction.response.send_message("🍬 100 doces → 4💗!", ephemeral=True)

    @discord.ui.button(label="Cupom da Sorte (200💗+300🍬) 🍀", style=discord.ButtonStyle.primary)
    async def cupom(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if dados[uid]["coracoes"] < 200 or dados[uid].get("doces",0) < 300:
            await interaction.response.send_message("Recursos insuficientes.", ephemeral=True)
            return
        dados[uid]["coracoes"] -= 200
        dados[uid]["doces"] -= 300
        personagem = sortear_personagem(uid, dados, cupom_raridade=True)
        dados[uid]["personagens"].append(personagem["nome"])
        salvar_dados(dados)
        embed = discord.Embed(
            title=f"🍀 Cupom da Sorte! {PERSONAGENS_EMOJI.get(personagem['nome'], '❓')}",
            description=f"**{personagem['nome']}** ({personagem['raridade']})",
            color=discord.Color.green()
        )
        await enviar_embed_com_imagem(interaction, embed, personagem["nome"])

    @discord.ui.button(label="Resgatar Hello Kitty (100 frags) 👑", style=discord.ButtonStyle.danger)
    async def resgatar(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if dados[uid].get("fragmentos", 0) < 100:
            await interaction.response.send_message("Precisa de 100 fragmentos.", ephemeral=True)
            return
        dados[uid]["fragmentos"] -= 100
        dados[uid]["personagens"].append("Hello Kitty")
        bonus = random.randint(1,5)
        dados[uid]["fragmentos"] += bonus
        salvar_dados(dados)
        embed = discord.Embed(
            title="👑 Hello Kitty resgatada!",
            description=f"Você agora tem a Hello Kitty e ganhou +{bonus} fragmentos extras!",
            color=discord.Color.gold()
        )
        await enviar_embed_com_imagem(interaction, embed, "Hello Kitty")

    @discord.ui.button(label="Loja de Moedas 🪙", style=discord.ButtonStyle.secondary)
    async def loja_moedas(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        embed = discord.Embed(
            title="🪙 Loja de Moedas – Compre personagens específicos",
            description=f"Saldo: **{dados[uid].get('moedas', 0)}🪙**\n\nSelecione um personagem:",
            color=discord.Color.teal()
        )
        chars = [p for p in PERSONAGENS]
        options = []
        for p in chars[:25]:
            emoji = PERSONAGENS_EMOJI.get(p["nome"], "❓")
            preco = PRECO_MOEDAS[p["raridade"]]
            options.append(discord.SelectOption(label=f"{p['nome']} ({p['raridade']})", description=f"{preco}🪙", value=p["nome"], emoji=emoji))
        select = Select(placeholder="Escolha um personagem...", options=options)
        async def callback(interaction_select: discord.Interaction):
            nome = select.values[0]
            dados = carregar_dados()
            uid = str(interaction_select.user.id)
            p = next((x for x in PERSONAGENS if x["nome"] == nome), None)
            if not p: return
            preco = PRECO_MOEDAS[p["raridade"]]
            if dados[uid].get("moedas", 0) < preco:
                await interaction_select.response.send_message("Moedas insuficientes.", ephemeral=True)
                return
            dados[uid]["moedas"] -= preco
            dados[uid]["personagens"].append(nome)
            salvar_dados(dados)
            embed = discord.Embed(
                title=f"✅ Compra realizada! {PERSONAGENS_EMOJI.get(nome, '❓')}",
                description=f"**{nome}** ({p['raridade']}) foi adicionado à sua turma!",
                color=discord.Color.teal()
            )
            embed.set_footer(text=f"Gasto: {preco}🪙 | Saldo: {dados[uid]['moedas']}🪙")
            await enviar_embed_com_imagem(interaction_select, embed, nome)
        select.callback = callback
        view = View(timeout=60)
        view.add_item(select)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ---------- Amigos ----------
class AmigosView(View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Minha Turma 👥", style=discord.ButtonStyle.primary)
    async def minha_turma(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if uid not in dados or not dados[uid]["personagens"]:
            await interaction.response.send_message("Sua turma está vazia!", ephemeral=True)
            return
        contagem = {}
        for nome in dados[uid]["personagens"]:
            contagem[nome] = contagem.get(nome, 0) + 1
        desc = ""
        for nome, qtd in contagem.items():
            emoji = PERSONAGENS_EMOJI.get(nome, "❓")
            efeito = next((p["efeito"] for p in PERSONAGENS if p["nome"] == nome), None)
            if nome == "Nenê": efeito = "nene"
            desc += f"{emoji} {nome} ×{qtd}  [{EFEITOS_DESC.get(efeito, '—')}]\n"
        embed = discord.Embed(title="👥 Turma do Hello Kitty Café", description=desc, color=discord.Color.from_rgb(255, 105, 180))
        embed.set_footer(text=f"Total: {len(dados[uid]['personagens'])} | Frag. HK: {dados[uid]['fragmentos']} | 🪙: {dados[uid].get('moedas', 0)}")
        await interaction.response.send_message(embed=embed, view=TurmaAcoesView(uid), ephemeral=True)

    @discord.ui.button(label="Trocar com Amigo 🤝", style=discord.ButtonStyle.success)
    async def trocar(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        personagens = list(set(dados[uid]["personagens"]))
        if not personagens:
            await interaction.response.send_message("Você não tem personagens.", ephemeral=True)
            return
        options = [discord.SelectOption(label=f"{nome} {PERSONAGENS_EMOJI.get(nome, '')}", value=nome) for nome in personagens[:25]]
        select = Select(placeholder="Oferecer qual?", options=options)
        async def select_cb(interaction_select: discord.Interaction):
            personagem_oferecido = select.values[0]
            membros = [m for m in interaction.guild.members if not m.bot and m.id != interaction.user.id]
            if not membros:
                await interaction_select.response.send_message("Nenhum amigo no servidor.", ephemeral=True)
                return
            membro_opts = [discord.SelectOption(label=m.display_name, value=str(m.id)) for m in membros[:25]]
            select_m = Select(placeholder="Escolha o amigo...", options=membro_opts)
            async def membro_cb(interaction_m: discord.Interaction):
                alvo_id = select_m.values[0]
                alvo_user = await bot.fetch_user(int(alvo_id))
                trocas_pendentes[uid] = {"alvo": alvo_id, "personagem": personagem_oferecido}
                embed = discord.Embed(
                    title="🤝 Proposta de Troca",
                    description=f"{interaction.user.mention} quer trocar **{personagem_oferecido}** com você!",
                    color=discord.Color.green()
                )
                view = AceitarRecusarView(uid, alvo_id, personagem_oferecido)
                await interaction.channel.send(content=alvo_user.mention, embed=embed, view=view)
                await interaction_m.response.send_message("Pedido enviado!", ephemeral=True)
            select_m.callback = membro_cb
            view_m = View(timeout=60)
            view_m.add_item(select_m)
            await interaction_select.response.send_message("Selecione o amigo:", view=view_m, ephemeral=True)
        select.callback = select_cb
        view = View(timeout=60)
        view.add_item(select)
        await interaction.response.send_message("Escolha o personagem para oferecer:", view=view, ephemeral=True)

    @discord.ui.button(label="Histórico de Trocas 📜", style=discord.ButtonStyle.secondary)
    async def historico(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        historico = dados[uid].get("historico_trocas", [])
        if not historico:
            await interaction.response.send_message("Nenhuma troca realizada.", ephemeral=True)
            return
        msg = "\n".join(historico[-10:])
        embed = discord.Embed(title="📜 Histórico de Trocas", description=msg, color=discord.Color.light_grey())
        await interaction.response.send_message(embed=embed, ephemeral=True)

class TurmaAcoesView(View):
    def __init__(self, uid):
        super().__init__(timeout=60)
        self.uid = uid

    @discord.ui.button(label="Vender Duplicata 💰", style=discord.ButtonStyle.secondary)
    async def vender(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        contagem = {}
        for nome in dados[uid]["personagens"]:
            contagem[nome] = contagem.get(nome, 0) + 1
        dups = [nome for nome, qtd in contagem.items() if qtd > 1]
        if not dups:
            await interaction.response.send_message("Sem duplicatas.", ephemeral=True)
            return
        options = [discord.SelectOption(label=f"{nome} (x{contagem[nome]})", value=nome, emoji=PERSONAGENS_EMOJI.get(nome, "❓")) for nome in dups[:25]]
        select = Select(placeholder="Qual vender?", options=options)
        async def callback(interaction_select: discord.Interaction):
            nome = select.values[0]
            raridade = next((p["raridade"] for p in PERSONAGENS if p["nome"] == nome), "Comum")
            if nome == "Nenê": raridade = "Ultimate"
            valor = PRECO_MOEDAS.get(raridade, 5)
            dados[uid]["personagens"].remove(nome)
            dados[uid]["moedas"] = dados[uid].get("moedas", 0) + valor
            salvar_dados(dados)
            embed = discord.Embed(
                title=f"💰 Venda! {PERSONAGENS_EMOJI.get(nome, '❓')}",
                description=f"**{nome}** vendido por **{valor} moedas**!",
                color=discord.Color.orange()
            )
            await enviar_embed_com_imagem(interaction_select, embed, nome)
        select.callback = callback
        view = View(timeout=60)
        view.add_item(select)
        await interaction.response.send_message("Selecione a duplicata:", view=view, ephemeral=True)

    @discord.ui.button(label="Cinnamoroll: Trocar 2 duplicatas 🔄", style=discord.ButtonStyle.primary)
    async def cinnamoroll(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if not tem_efeito(uid, dados, "cinnamoroll"):
            await interaction.response.send_message("Precisa do Cinnamoroll.", ephemeral=True)
            return
        contagem = {}
        for nome in dados[uid]["personagens"]: contagem[nome] = contagem.get(nome, 0) + 1
        trocaveis = [nome for nome, qtd in contagem.items() if qtd >= 2]
        if not trocaveis:
            await interaction.response.send_message("Sem 2 cópias.", ephemeral=True)
            return
        nome = trocaveis[0]
        for _ in range(2): dados[uid]["personagens"].remove(nome)
        novo = sortear_personagem(uid, dados)
        dados[uid]["personagens"].append(novo["nome"])
        salvar_dados(dados)
        embed = discord.Embed(
            title="🔄 Troca Cinnamoroll",
            description=f"2× {nome} → **{novo['nome']}**",
            color=discord.Color.blue()
        )
        await enviar_embed_com_imagem(interaction, embed, novo["nome"])

    @discord.ui.button(label="Hangyodon: Reciclar duplicata ♻️", style=discord.ButtonStyle.danger)
    async def hangyodon(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if not tem_efeito(uid, dados, "hangyodon"):
            await interaction.response.send_message("Precisa do Hangyodon.", ephemeral=True)
            return
        contagem = {}
        for nome in dados[uid]["personagens"]: contagem[nome] = contagem.get(nome, 0) + 1
        dups = [nome for nome, qtd in contagem.items() if qtd > 1]
        if not dups:
            await interaction.response.send_message("Sem duplicatas.", ephemeral=True)
            return
        nome = dups[0]
        dados[uid]["personagens"].remove(nome)
        dados[uid]["coracoes"] += 3
        salvar_dados(dados)
        await interaction.response.send_message(f"♻️ {nome} → +3💗", ephemeral=True)

# ---------- Tutorial/Ajuda ----------
class TutorialAjudaView(View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Tutorial 📘", style=discord.ButtonStyle.primary)
    async def tutorial(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="📘 Tutorial do Hello Kitty Café",
            description=(
                "**Bem-vindo(a)!** Aqui você monta sua turma de amigos da Sanrio.\n\n"
                "💗 **Corações:** comece com 3. Use 1💗 no botão 'Comprar Personagem' para receber um amigo aleatório. "
                "Ganhe mais corações conversando no servidor.\n\n"
                "🍬 **Doces:** resgate de 3 a 8 doces uma vez por dia na Loja. Junte 100 doces para converter em 4💗.\n\n"
                "🪙 **Moedas:** venda personagens duplicados na sua Turma (dentro de Amigos) para ganhar moedas. "
                "Use moedas na Loja de Moedas para comprar personagens específicos.\n\n"
                "🍀 **Cupom da Sorte:** na Loja, gaste 200💗 + 300🍬 para garantir um personagem Raro ou superior.\n\n"
                "👑 **Hello Kitty:** extremamente rara! Ao encontrá-la, você recebe de 1 a 5 fragmentos. "
                "Junte 100 fragmentos para resgatar uma Hello Kitty extra.\n\n"
                "💫 **Nenê:** a Ultimate, chance quase impossível (0,000000001%).\n\n"
                "🤝 **Amigos:** veja sua turma, troque personagens com outros membros e consulte o histórico de trocas.\n\n"
                "🎲 **Drops Possíveis:** veja todos os personagens que podem aparecer."
            ),
            color=discord.Color.blue()
        )
        embed.set_image(url="attachment://Hello_kitty.png")
        await interaction.response.send_message(embed=embed, file=discord.File("Hello_kitty.png"), ephemeral=True)

    @discord.ui.button(label="Ajuda ❓", style=discord.ButtonStyle.secondary)
    async def ajuda(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🌸 Ajuda Rápida",
            description=(
                "• Ganhe 💗 conversando no chat.\n"
                "• Doces diários na Loja (1 vez por dia).\n"
                "• 100🍬 = 4💗 (Loja).\n"
                "• Venda duplicatas na Turma por 🪙.\n"
                "• Use 🪙 para comprar personagens específicos.\n"
                "• Cupom da Sorte: 200💗+300🍬.\n"
                "• Hello Kitty: 100 fragmentos para resgate.\n"
                "• Troque com amigos no menu Amigos."
            ),
            color=discord.Color.from_rgb(255, 192, 203)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ---------- Aceitar/Recusar troca ----------
class AceitarRecusarView(View):
    def __init__(self, solicitante_id, alvo_id, personagem_oferecido):
        super().__init__(timeout=120)
        self.solicitante_id = solicitante_id
        self.alvo_id = alvo_id
        self.personagem_oferecido = personagem_oferecido

    @discord.ui.button(label="Aceitar ✅", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != self.alvo_id:
            await interaction.response.send_message("Não é para você.", ephemeral=True)
            return
        dados = carregar_dados()
        if self.personagem_oferecido not in dados[self.solicitante_id]["personagens"]:
            await interaction.response.send_message("O amigo não tem mais esse personagem.", ephemeral=True)
            return
        personagens_alvo = list(set(dados[self.alvo_id]["personagens"]))
        if not personagens_alvo:
            await interaction.response.send_message("Você não tem personagens.", ephemeral=True)
            return
        options = [discord.SelectOption(label=f"{nome} {PERSONAGENS_EMOJI.get(nome, '')}", value=nome) for nome in personagens_alvo[:25]]
        select = Select(placeholder="Oferecer qual?", options=options)
        async def callback(interaction_select: discord.Interaction):
            personagem_alvo = select.values[0]
            dados[self.solicitante_id]["personagens"].remove(self.personagem_oferecido)
            dados[self.alvo_id]["personagens"].remove(personagem_alvo)
            dados[self.solicitante_id]["personagens"].append(personagem_alvo)
            dados[self.alvo_id]["personagens"].append(self.personagem_oferecido)
            registro = f"{interaction.user.name} deu **{personagem_alvo}** e recebeu **{self.personagem_oferecido}** de <@{self.solicitante_id}>"
            dados[self.solicitante_id].setdefault("historico_trocas", []).append(registro)
            dados[self.alvo_id].setdefault("historico_trocas", []).append(registro)
            salvar_dados(dados)
            trocas_pendentes.pop(self.solicitante_id, None)
            await interaction_select.response.send_message(f"✅ Troca realizada! {registro}", ephemeral=False)
            self.disable_all_items()
            await interaction.message.edit(view=self)
        select.callback = callback
        view = View(timeout=60)
        view.add_item(select)
        await interaction.response.send_message("Qual personagem oferecer?", view=view, ephemeral=True)

    @discord.ui.button(label="Recusar ❌", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != self.alvo_id:
            await interaction.response.send_message("Não é para você.", ephemeral=True)
            return
        trocas_pendentes.pop(self.solicitante_id, None)
        self.disable_all_items()
        await interaction.message.edit(view=self)
        await interaction.response.send_message("❌ Troca recusada.", ephemeral=True)

    def disable_all_items(self):
        for item in self.children: item.disabled = True

trocas_pendentes = {}

# =================== COMANDO SLASH ===================
@bot.tree.command(name="hellokitty", description="Abre o painel do Hello Kitty Café ☕")
async def hellokitty(interaction: discord.Interaction):
    embed = discord.Embed(
        title="☕ Hello Kitty Café 🎀",
        description="**Clique nos botões para explorar o café!**",
        color=discord.Color.from_rgb(255, 105, 180)
    )
    embed.set_image(url="attachment://Hello_kitty.png")
    await interaction.response.send_message(
        embed=embed,
        file=discord.File("Hello_kitty.png"),
        view=MenuPrincipal()
    )

# =================== EVENTOS ===================
@bot.event
async def on_ready():
    print(f"🌸 {bot.user} está no Hello Kitty Café!")
    bot.add_view(MenuPrincipal())
    if GUILD_ID:
        guild = discord.Object(id=int(GUILD_ID))
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
    else:
        await bot.tree.sync()

@bot.event
async def on_message(message):
    if message.author.bot: return
    dados = carregar_dados()
    uid = str(message.author.id)
    if uid not in dados:
        dados[uid] = novo_jogador()

    jogador = dados[uid]
    jogador["msg_count"] += 1

    if tem_efeito(uid, dados, "dear_daniel") and jogador["msg_count"] % 50 == 0: jogador["coracoes"] += 1
    if tem_efeito(uid, dados, "twin_stars") and jogador["msg_count"] % 10 == 0: jogador["coracoes"] += 1
    if tem_efeito(uid, dados, "nene") and jogador["msg_count"] % 5 == 0: jogador["coracoes"] += 3
    if tem_efeito(uid, dados, "pipi") and jogador["msg_count"] % 80 == 0: jogador["coracoes"] += 1
    if tem_efeito(uid, dados, "mocha") and jogador["msg_count"] % 60 == 0: jogador["coracoes"] += 1

    ganho = calcular_coracoes_msg(uid, dados, jogador["msg_count"])
    jogador["coracoes"] += ganho
    jogador["coracoes_ganhos"] += ganho

    if tem_efeito(uid, dados, "pochacco") and jogador["coracoes_ganhos"] >= 20:
        jogador["coracoes"] += 1
        jogador["coracoes_ganhos"] -= 20

    if tem_efeito(uid, dados, "george") and jogador["msg_count"] % 100 == 0: jogador["fragmentos"] += 1
    if tem_efeito(uid, dados, "sasa") and jogador["msg_count"] % 50 == 0: jogador["fragmentos"] += 1

    salvar_dados(dados)
    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)