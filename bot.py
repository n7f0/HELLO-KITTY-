import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Select
import random
import json
import os
import datetime
import asyncio
import google.generativeai as genai

# =================== CONFIGURAÇÕES ===================
TOKEN = os.getenv("TOKEN")
ARQUIVO_DADOS = os.getenv("DATA_PATH", "dados_cafe.json")
GUILD_ID = os.getenv("GUILD_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ARQUIVO_IA = "ia_config.json"
# =====================================================

# Configurar Gemini
modelo_ia = None
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    modelo_ia = genai.GenerativeModel('gemini-1.5-flash')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- Arquivos de dados ----------
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def carregar_config_ia():
    if os.path.exists(ARQUIVO_IA):
        with open(ARQUIVO_IA, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_config_ia(config):
    with open(ARQUIVO_IA, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# ---------- Emojis e imagens ----------
PERSONAGENS_EMOJI = {
    "Nenê": "💫", "Hello Kitty": "👧", "Dear Daniel": "💙", "My Melody": "🎀",
    "Kuromi": "💀", "Pompompurin": "🍮", "Cinnamoroll": "☁️",
    "Little Twin Stars": "⭐", "Keroppi": "🐸", "Badtz-Maru": "🐧",
    "Tuxedo Sam": "🐧", "Pochacco": "🐶", "Chococat": "🐱",
    "Hangyodon": "🐟", "Pekkle": "🦆",
    "Spottie Dottie": "🐶", "Landry": "🐱", "Moppu": "🐹", "Coro Chan": "🐰",
    "Minna no Tabo": "🐻", "Charmmy Kitty": "🐱", "Sugar": "🐰",
    "Tiny Chum": "🐹", "Cathy": "🐱", "George": "🐵", "Fifi": "🐶",
    "Rory": "🐱", "Lulu": "🐰", "Pipi": "🐤", "Nana": "🐱", "Mimi": "🐰",
    "Sasa": "🐱", "Kiki": "🐱", "Lala": "🐰", "Mocha": "🐶"
}

IMAGENS_LOCAIS = {
    "Nenê": "nene.png", "Hello Kitty": "hellokitty.png",
    "My Melody": "mymelody.png", "Kuromi": "kuromi.png",
    "Cinnamoroll": "cinnamoroll.png", "Pompompurin": "pompompurin.png",
    "Keroppi": "keroppi.png", "Badtz-Maru": "badtz_manu.png",
    "Pochacco": "pochacco.png", "Little Twin Stars": "littletwinstars.png"
}
LOJA_IMAGEM = "loja.png"

CORES_RARIDADE = {
    "Ultimate": 0xFFD700, "Mítico": 0xFF1493, "Lendário": 0x9932CC,
    "Épico": 0xFF8C00, "Raro": 0x1E90FF, "Incomum": 0x32CD32, "Comum": 0xA9A9A9
}

# ---------- Efeitos ----------
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
    "charmmy_kitty": "+1💗 inicial (ganho ao adquiri-la)",
    "sugar": "5% +1💗 ao comprar",
    "tiny_chum": "+2💗 inicial (ganho ao adquiri-la)",
    "cathy": "2% chance Épico+",
    "george": "+1 frag a cada 100 msgs",
    "fifi": "+1💗 a cada 20 msgs",
    "rory": "5% +1 frag ao comprar",
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
        "coracoes": 3, "doces": 0, "personagens": [], "fragmentos": 0,
        "moedas": 0, "msg_count": 0, "coracoes_ganhos": 0,
        "ultimo_doce": 0, "historico_trocas": []
    }

def preparar_embed_com_imagem(embed, nome_personagem):
    if nome_personagem in IMAGENS_LOCAIS:
        caminho = IMAGENS_LOCAIS[nome_personagem]
        if os.path.exists(caminho):
            arquivo = discord.File(caminho, filename=caminho)
            embed.set_image(url=f"attachment://{caminho}")
            return arquivo
    return None

async def enviar_card(interaction, embed, nome_personagem, ephemeral=False):
    arquivo = preparar_embed_com_imagem(embed, nome_personagem)
    if arquivo:
        await interaction.response.send_message(embed=embed, file=arquivo, ephemeral=ephemeral)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

# =================== NOTIFICAÇÕES DM ===================
notificacoes_enviadas = {}  # {uid: set(milestone)}

async def notificar_meta(uid, milestone, mensagem):
    try:
        # Evitar notificações repetidas
        if uid not in notificacoes_enviadas:
            notificacoes_enviadas[uid] = set()
        if milestone in notificacoes_enviadas[uid]:
            return
        notificacoes_enviadas[uid].add(milestone)

        user = await bot.fetch_user(int(uid))
        await user.send(mensagem)
    except:
        pass  # DM fechada ou erro

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

        if random.random() < 1e-11:
            dados[uid]["personagens"].append("Nenê")
            salvar_dados(dados)
            embed = discord.Embed(
                title="💫 Nenê",
                description="**Raridade:** Ultimate\n**Habilidade:** " + EFEITOS_DESC["nene"],
                color=CORES_RARIDADE["Ultimate"]
            )
            await enviar_card(interaction, embed, "Nenê")
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
        if tem_efeito(uid, dados, "rory") and random.random() < 0.05: dados[uid]["fragmentos"] += 1

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
        if tem_efeito(uid, dados, "lala") and random.random() < 0.10: dados[uid]["coracoes"] += 1

        if personagem["nome"] == "Charmmy Kitty":
            dados[uid]["coracoes"] += 1
        if personagem["nome"] == "Tiny Chum":
            dados[uid]["coracoes"] += 2

        salvar_dados(dados)

        extras = ""
        if gratis: extras += "\n🍮 Você não gastou o 💗!"
        if duplicar: extras += "\n🐱 Amigo duplicado!"
        if reembolso: extras += "\n💖 Coração devolvido!"

        embed = discord.Embed(
            title=f"{PERSONAGENS_EMOJI.get(personagem['nome'], '❓')} {personagem['nome']}",
            description=f"**Raridade:** {personagem['raridade']}\n**Habilidade:** {EFEITOS_DESC.get(personagem['efeito'], 'Nenhuma')}{extras}",
            color=CORES_RARIDADE.get(personagem['raridade'], 0xFFB6C1)
        )
        embed.set_footer(text=f"💗: {dados[uid]['coracoes']} | Frag. HK: {dados[uid]['fragmentos']} | 🪙: {dados[uid].get('moedas', 0)}")
        await enviar_card(interaction, embed, personagem["nome"])

    @discord.ui.button(label="Loja do Café 🛍️", style=discord.ButtonStyle.primary, custom_id="loja_cafe")
    async def loja(self, interaction: discord.Interaction, button: Button):
        # ... (código da loja igual ao anterior, sem alterações) ...
        pass  # substitua pelo conteúdo real da view da loja

    # Os demais botões (Drops Possíveis, Amigos, Tutorial/Ajuda) também são mantidos.

# (Inclua aqui todas as outras views: CardsPaginaView, LojaCafeView, AmigosView, etc.)

# =================== COMANDOS SLASH ===================
@bot.tree.command(name="hellokitty", description="Abre o painel do Hello Kitty Café ☕")
async def hellokitty(interaction: discord.Interaction):
    embed = discord.Embed(
        title="☕ Hello Kitty Café 🎀",
        description="**Clique nos botões para explorar o café!**",
        color=0xFF69B4
    )
    embed.set_image(url="attachment://Hello_kitty.png")
    await interaction.response.send_message(
        embed=embed,
        file=discord.File("Hello_kitty.png"),
        view=MenuPrincipal()
    )

@bot.tree.command(name="ativaria", description="Ativar a IA da Hello Kitty no servidor (admin)")
@app_commands.default_permissions(administrator=True)
async def ativar_ia(interaction: discord.Interaction):
    config = carregar_config_ia()
    config[str(interaction.guild.id)] = True
    salvar_config_ia(config)
    await interaction.response.send_message("🌸 A IA da Hello Kitty foi **ativada**! Use /conversar para falar comigo.", ephemeral=True)

@bot.tree.command(name="desativaria", description="Desativar a IA da Hello Kitty no servidor (admin)")
@app_commands.default_permissions(administrator=True)
async def desativar_ia(interaction: discord.Interaction):
    config = carregar_config_ia()
    config[str(interaction.guild.id)] = False
    salvar_config_ia(config)
    await interaction.response.send_message("🌸 A IA da Hello Kitty foi **desativada**.", ephemeral=True)

@bot.tree.command(name="conversar", description="Fale com a Hello Kitty!")
async def conversar(interaction: discord.Interaction, mensagem: str):
    config = carregar_config_ia()
    if not config.get(str(interaction.guild.id), False):
        await interaction.response.send_message("🌸 A IA está desativada neste servidor. Peça a um admin para usar /ativaria.", ephemeral=True)
        return

    if not modelo_ia:
        await interaction.response.send_message("💔 A IA não está configurada (chave da API ausente).", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=False)
    try:
        prompt = f"""Você é a Hello Kitty, uma gatinha meiga e amigável do universo Sanrio.
Você está no servidor do Discord "Hello Kitty Café", um joguinho de colecionar personagens.
Responda de forma fofa, animada e ajude o jogador com dicas sobre o jogo (como conseguir corações, doces, fragmentos, trocar com amigos).
Mensagem do jogador: {mensagem}"""

        response = modelo_ia.generate_content(prompt)
        texto = response.text
        await interaction.followup.send(f"🌸 **Hello Kitty:** {texto}")
    except Exception as e:
        await interaction.followup.send("🌸 Ops! A Hello Kitty está descansando... tente de novo mais tarde. 😿")

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
    mensagens = jogador["msg_count"]

    # Efeitos e notificações
    if tem_efeito(uid, dados, "dear_daniel") and mensagens % 50 == 0:
        jogador["coracoes"] += 1
        await notificar_meta(uid, f"daniel_{mensagens}", f"📬 **Dear Daniel** te enviou +1💗! (Você já mandou {mensagens} mensagens!)")
    if tem_efeito(uid, dados, "twin_stars") and mensagens % 10 == 0:
        jogador["coracoes"] += 1
        await notificar_meta(uid, f"twin_{mensagens}", f"⭐ **Little Twin Stars** brilharam! Você ganhou +1💗! (Mensagem #{mensagens})")
    if tem_efeito(uid, dados, "nene") and mensagens % 5 == 0:
        jogador["coracoes"] += 3
        await notificar_meta(uid, f"nene_{mensagens}", f"💫 **Nenê** está radiante! +3💗 para você! ({mensagens} mensagens)")
    if tem_efeito(uid, dados, "pipi") and mensagens % 80 == 0:
        jogador["coracoes"] += 1
        await notificar_meta(uid, f"pipi_{mensagens}", f"🐤 **Pipi** piou! +1💗 extra! ({mensagens} mensagens)")
    if tem_efeito(uid, dados, "mocha") and mensagens % 60 == 0:
        jogador["coracoes"] += 1
        await notificar_meta(uid, f"mocha_{mensagens}", f"🐶 **Mocha** te deu +1💗! ({mensagens} mensagens)")

    ganho = calcular_coracoes_msg(uid, dados, mensagens)
    jogador["coracoes"] += ganho
    jogador["coracoes_ganhos"] += ganho

    if tem_efeito(uid, dados, "pochacco") and jogador["coracoes_ganhos"] >= 20:
        jogador["coracoes"] += 1
        jogador["coracoes_ganhos"] -= 20

    if tem_efeito(uid, dados, "george") and mensagens % 100 == 0:
        jogador["fragmentos"] += 1
        await notificar_meta(uid, f"george_{mensagens}", f"🐵 **George** encontrou +1 fragmento Hello! ({mensagens} msgs)")
    if tem_efeito(uid, dados, "sasa") and mensagens % 50 == 0:
        jogador["fragmentos"] += 1
        await notificar_meta(uid, f"sasa_{mensagens}", f"🐱 **Sasa** trouxe +1 fragmento Hello! ({mensagens} msgs)")

    salvar_dados(dados)
    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)