import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Button, View, Select, Modal, TextInput
import random
import json
import os
import datetime
from datetime import timezone
import asyncpg
import logging
from collections import defaultdict

# =================== CONFIGURAÇÕES ===================
TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
GUILD_ID = os.getenv("GUILD_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

logging.basicConfig(level=logging.INFO)

# =================== BANCO DE DADOS ===================
db_pool = None

async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    async with db_pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                coracoes INTEGER DEFAULT 3,
                doces INTEGER DEFAULT 0,
                fragmentos INTEGER DEFAULT 0,
                moedas INTEGER DEFAULT 0,
                msg_count INTEGER DEFAULT 0,
                coracoes_ganhos INTEGER DEFAULT 0,
                ultimo_doce BIGINT DEFAULT 0,
                xp INTEGER DEFAULT 0,
                nivel INTEGER DEFAULT 1,
                conquistas JSONB DEFAULT '[]'::jsonb,
                missoes_diarias JSONB DEFAULT '{}'::jsonb,
                missoes_semanais JSONB DEFAULT '{}'::jsonb,
                missoes_concluidas JSONB DEFAULT '[]'::jsonb,
                decoracoes JSONB DEFAULT '[]'::jsonb,
                decoracao_ativa JSONB DEFAULT '{}'::jsonb,
                lista_desejos JSONB DEFAULT '[]'::jsonb,
                resumo_dm BOOLEAN DEFAULT FALSE,
                ultimo_drop BIGINT DEFAULT 0,
                personagens JSONB DEFAULT '[]'::jsonb,
                historico_trocas JSONB DEFAULT '[]'::jsonb
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS trocas (
                id SERIAL PRIMARY KEY,
                solicitante_id TEXT REFERENCES users(id),
                alvo_id TEXT REFERENCES users(id),
                personagem_oferecido TEXT,
                personagem_desejado TEXT,
                status TEXT DEFAULT 'pendente',
                timestamp BIGINT
            )
        ''')
        # Tabela para controle da IA por canal
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS canais_ia (
                guild_id BIGINT NOT NULL,
                channel_id BIGINT PRIMARY KEY,
                ativo BOOLEAN DEFAULT TRUE
            )
        ''')
        logging.info("Banco de dados inicializado.")

# ===== FUNÇÕES PARA CONTROLE DE IA POR CANAL =====
async def is_ia_active(channel_id: int) -> bool:
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow('SELECT ativo FROM canais_ia WHERE channel_id = $1', channel_id)
        if row is None:
            return True  # padrão: ativo
        return row['ativo']

async def toggle_ia_channel(guild_id: int, channel_id: int) -> bool:
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow('SELECT ativo FROM canais_ia WHERE channel_id = $1', channel_id)
        if row is None:
            await conn.execute('INSERT INTO canais_ia (guild_id, channel_id, ativo) VALUES ($1, $2, $3)',
                               guild_id, channel_id, True)
            novo_estado = False
            await conn.execute('UPDATE canais_ia SET ativo = $1 WHERE channel_id = $2', novo_estado, channel_id)
        else:
            novo_estado = not row['ativo']
            await conn.execute('UPDATE canais_ia SET ativo = $1 WHERE channel_id = $2', novo_estado, channel_id)
        return novo_estado

async def get_canais_config(guild_id: int):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch('SELECT channel_id, ativo FROM canais_ia WHERE guild_id = $1', guild_id)
        config = {row['channel_id']: row['ativo'] for row in rows}
        return config

# =================== IA (Gemini) ===================
import google.generativeai as genai

cliente_ia = None
MODELO_IA = "gemini-1.0-pro"

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        cliente_ia = genai.GenerativeModel(MODELO_IA)
        logging.info(f"IA Gemini inicializada com modelo {MODELO_IA}.")
    except Exception as e:
        logging.error(f"Erro ao inicializar Gemini com {MODELO_IA}: {e}")
        try:
            cliente_ia = genai.GenerativeModel("gemini-pro")
            logging.info("IA Gemini inicializada com modelo gemini-pro (fallback).")
        except Exception as e2:
            logging.error(f"Erro ao inicializar Gemini com gemini-pro: {e2}")
            cliente_ia = None

# =================== BOT ===================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

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

# ---------- Sistema de níveis ----------
NIVEIS = [
    (1, 0), (2, 100), (3, 250), (4, 500), (5, 800),
    (10, 2000), (15, 4000), (20, 7000), (25, 11000), (30, 16000),
    (40, 25000), (50, 35000), (60, 50000), (70, 70000), (80, 95000),
    (90, 125000), (100, 160000)
]
TITULOS = {10: "☕ Barista do Café", 50: "🤝 Mestre das Amizades", 100: "👑 Lenda da Sanrio"}

# ---------- Conquistas ----------
CONQUISTAS = {
    "colecionador10": {"nome": "🌟 Colecionador Iniciante", "desc": "Tenha 10 personagens únicos", "tipo": "unicos", "meta": 10},
    "colecionador30": {"nome": "🎀 Colecionador Dedicado", "desc": "Tenha 30 personagens únicos", "tipo": "unicos", "meta": 30},
    "sortudo": {"nome": "🍀 Sortudo", "desc": "Encontre um personagem Lendário ou superior", "tipo": "raridade", "meta": 1},
    "social": {"nome": "💌 Social", "desc": "Realize 5 trocas", "tipo": "trocas", "meta": 5},
    "milionario": {"nome": "🪙 Milionário", "desc": "Acumule 1000 moedas", "tipo": "moedas", "meta": 1000}
}

# ---------- Missões ----------
MISSOES_DIARIAS = [
    {"id": "msg30", "desc": "Envie 30 mensagens", "tipo": "mensagens", "meta": 30, "recompensa": {"doces": 5}},
    {"id": "comprar3", "desc": "Compre 3 personagens", "tipo": "compras", "meta": 3, "recompensa": {"coracoes": 3}},
    {"id": "trocar1", "desc": "Troque 1 personagem", "tipo": "trocas", "meta": 1, "recompensa": {"fragmentos": 2}}
]
MISSOES_SEMANAIS = [
    {"id": "msg200", "desc": "Envie 200 mensagens", "tipo": "mensagens", "meta": 200, "recompensa": {"coracoes": 20, "doces": 20}},
    {"id": "comprar10", "desc": "Compre 10 personagens", "tipo": "compras", "meta": 10, "recompensa": {"moedas": 50}},
    {"id": "trocar5", "desc": "Troque 5 personagens", "tipo": "trocas", "meta": 5, "recompensa": {"fragmentos": 10}}
]

# ---------- Decorações ----------
DECORACOES_LOJA = {
    "moldura_ouro": {"nome": "🖼️ Moldura Dourada", "custo": 500, "tipo": "moldura"},
    "moldura_prata": {"nome": "🖼️ Moldura Prateada", "custo": 300, "tipo": "moldura"},
    "fundo_cafe": {"nome": "🌸 Fundo Café", "custo": 200, "tipo": "fundo"},
    "fundo_ceu": {"nome": "☁️ Fundo do Céu", "custo": 200, "tipo": "fundo"}
}
ALBUNS = {
    "turma_pompompurin": {"nome": "🍮 Turma do Pompompurin", "personagens": ["Pompompurin", "Hello Kitty", "My Melody"], "recompensa": {"coracoes": 10, "doces": 10}},
    "amigos_ceu": {"nome": "☁️ Amigos do Céu", "personagens": ["Cinnamoroll", "Little Twin Stars", "Tuxedo Sam"], "recompensa": {"moedas": 100}}
}

# ---------- Funções auxiliares ----------
def tem_efeito(uid, dados, efeito_nome):
    for nome in set(dados["personagens"]):
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

# ---------- Notificações DM ----------
notificacoes_enviadas = defaultdict(set)

async def notificar_meta(uid, milestone, mensagem):
    try:
        if milestone in notificacoes_enviadas[uid]:
            return
        notificacoes_enviadas[uid].add(milestone)
        user = await bot.fetch_user(int(uid))
        await user.send(mensagem)
    except:
        pass

# ---------- Sistema de XP ----------
def calcular_nivel(xp):
    for nivel, xp_necessario in reversed(NIVEIS):
        if xp >= xp_necessario:
            return nivel
    return 1

def recompensa_nivel(nivel):
    if nivel in TITULOS:
        return {"coracoes": nivel, "doces": nivel//2}
    return {}

# ---------- Verificação de conquistas ----------
def verificar_conquistas(uid, dados):
    novas = []
    unicos = len(set(dados["personagens"]))
    trocas = len(dados.get("historico_trocas", []))
    moedas = dados.get("moedas", 0)
    for chave, conq in CONQUISTAS.items():
        if chave in dados.get("conquistas", []):
            continue
        if conq["tipo"] == "unicos" and unicos >= conq["meta"]:
            novas.append(chave)
        elif conq["tipo"] == "raridade" and any(p in dados["personagens"] for p in [c["nome"] for c in PERSONAGENS if c["raridade"] in ("Lendário", "Mítico", "Ultimate")]):
            novas.append(chave)
        elif conq["tipo"] == "trocas" and trocas >= conq["meta"]:
            novas.append(chave)
        elif conq["tipo"] == "moedas" and moedas >= conq["meta"]:
            novas.append(chave)
    return novas

# ---------- Missões ----------
def resetar_missoes_diarias(dados):
    dados["missoes_diarias"] = {m["id"]: 0 for m in MISSOES_DIARIAS}
    dados["ultima_reset_diaria"] = datetime.datetime.now(timezone.utc).timestamp()

def resetar_missoes_semanais(dados):
    dados["missoes_semanais"] = {m["id"]: 0 for m in MISSOES_SEMANAIS}
    dados["ultima_reset_semanal"] = datetime.datetime.now(timezone.utc).timestamp()

# =================== VIEWS ===================

# ---------- MenuPrincipal ----------
class MenuPrincipal(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Comprar Personagem (1💗) 🎁", style=discord.ButtonStyle.success, custom_id="comprar_personagem")
    async def comprar_personagem(self, interaction: discord.Interaction, button: Button):
        dados = await get_user_data(str(interaction.user.id))
        uid = str(interaction.user.id)
        if dados["coracoes"] < 1:
            await interaction.response.send_message("💔 Você não tem corações!", ephemeral=True)
            return

        gratis = chance_nao_gastar(uid, dados)
        if not gratis:
            dados["coracoes"] -= 1

        if random.random() < 1e-11:
            shiny = random.random() < 0.005
            nome_final = "Nenê" if not shiny else "✨ Nenê Cristal"
            dados["personagens"].append(nome_final)
            await update_user_data(uid, dados)
            embed = discord.Embed(title=f"{PERSONAGENS_EMOJI.get('Nenê', '💫')} {nome_final}",
                                  description=f"**Raridade:** Ultimate\n**Habilidade:** {EFEITOS_DESC['nene']}",
                                  color=CORES_RARIDADE["Ultimate"])
            await enviar_card(interaction, embed, "Nenê")
            if "compras" in dados.get("missoes_diarias", {}):
                dados["missoes_diarias"]["compras"] += 1
            if "compras" in dados.get("missoes_semanais", {}):
                dados["missoes_semanais"]["compras"] += 1
            await update_user_data(uid, dados)
            return

        personagem = sortear_personagem(uid, dados)
        shiny = random.random() < 0.005
        nome_final = personagem["nome"] if not shiny else f"✨ {personagem['nome']} Cristal"
        duplicar = False
        if tem_efeito(uid, dados, "chococat") and random.random() < 0.20: duplicar = True
        if tem_efeito(uid, dados, "landry") and random.random() < 0.05: duplicar = True
        if tem_efeito(uid, dados, "kiki") and random.random() < 0.02: duplicar = True

        dados["personagens"].append(nome_final)
        if duplicar:
            dados["personagens"].append(nome_final)

        if personagem["nome"] == "Hello Kitty":
            frags = random.randint(1, 5)
            dados["fragmentos"] += frags

        if tem_efeito(uid, dados, "hello_kitty") and random.random() < 0.10: dados["fragmentos"] += 1
        if tem_efeito(uid, dados, "nene") and random.random() < 0.50: dados["fragmentos"] += 1
        if tem_efeito(uid, dados, "coro_chan") and random.random() < 0.05: dados["fragmentos"] += 1
        if tem_efeito(uid, dados, "tuxedo_sam") and random.random() < 0.30: dados["fragmentos"] += 1
        if tem_efeito(uid, dados, "rory") and random.random() < 0.05: dados["fragmentos"] += 1

        reembolso = False
        if tem_efeito(uid, dados, "my_melody") and random.random() < 0.10: reembolso = True
        if tem_efeito(uid, dados, "hello_kitty") and random.random() < 0.20: reembolso = True
        if tem_efeito(uid, dados, "nene") and random.random() < 0.50: reembolso = True
        if tem_efeito(uid, dados, "moppu") and random.random() < 0.03: reembolso = True
        if tem_efeito(uid, dados, "lulu") and random.random() < 0.01: reembolso = True
        if reembolso and not gratis:
            dados["coracoes"] += 1

        if tem_efeito(uid, dados, "badtz_maru"): dados["coracoes"] += 5
        if tem_efeito(uid, dados, "sugar") and random.random() < 0.05: dados["coracoes"] += 1
        if tem_efeito(uid, dados, "mimi") and random.random() < 0.05: dados["coracoes"] += 1
        if tem_efeito(uid, dados, "lala") and random.random() < 0.10: dados["coracoes"] += 1

        if personagem["nome"] == "Charmmy Kitty":
            dados["coracoes"] += 1
        if personagem["nome"] == "Tiny Chum":
            dados["coracoes"] += 2

        if "compras" in dados.get("missoes_diarias", {}):
            dados["missoes_diarias"]["compras"] += 1
        if "compras" in dados.get("missoes_semanais", {}):
            dados["missoes_semanais"]["compras"] += 1

        await update_user_data(uid, dados)

        extras = ""
        if gratis: extras += "\n🍮 Você não gastou o 💗!"
        if duplicar: extras += "\n🐱 Amigo duplicado!"
        if reembolso: extras += "\n💖 Coração devolvido!"

        embed = discord.Embed(
            title=f"{PERSONAGENS_EMOJI.get(personagem['nome'], '❓')} {nome_final}",
            description=f"**Raridade:** {personagem['raridade']}\n**Habilidade:** {EFEITOS_DESC.get(personagem['efeito'], 'Nenhuma')}{extras}",
            color=CORES_RARIDADE.get(personagem['raridade'], 0xFFB6C1)
        )
        embed.set_footer(text=f"💗: {dados['coracoes']} | Frag. HK: {dados['fragmentos']} | 🪙: {dados['moedas']}")
        await enviar_card(interaction, embed, personagem["nome"])

        novas = verificar_conquistas(uid, dados)
        for c in novas:
            dados["conquistas"].append(c)
            await update_user_data(uid, dados)
            await interaction.followup.send(f"🏆 Conquista desbloqueada: **{CONQUISTAS[c]['nome']}**!", ephemeral=True)

    @discord.ui.button(label="Loja do Café 🛍️", style=discord.ButtonStyle.primary, custom_id="loja_cafe")
    async def loja(self, interaction: discord.Interaction, button: Button):
        dados = await get_user_data(str(interaction.user.id))
        uid = str(interaction.user.id)

        embed = discord.Embed(title="🛍️ Loja do Hello Kitty Café", color=0xFFD700)
        embed.add_field(name="Recursos", value=f"💗 {dados['coracoes']} | 🍬 {dados['doces']} | 🪙 {dados['moedas']}", inline=False)
        embed.add_field(name="Conversões", value="⚡ 100🍬 → 4💗\n🍀 Cupom da Sorte (200💗+300🍬) → Personagem Raro+\n👑 Resgatar Hello Kitty (100 fragmentos)", inline=False)
        embed.add_field(name="Loja de Moedas", value="🪙 Compre personagens específicos", inline=False)
        embed.add_field(name="Decorações", value="🖼️ Compre molduras e fundos para seu perfil", inline=False)
        embed.set_footer(text=f"Fragmentos Hello: {dados['fragmentos']}")

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
        embeds = []
        for p in chars:
            embed = discord.Embed(
                title=f"{PERSONAGENS_EMOJI.get(p['nome'], '❓')} {p['nome']}",
                description=f"**Raridade:** {p['raridade']}\n**Habilidade:** {EFEITOS_DESC.get(p['efeito'], 'Nenhuma')}",
                color=CORES_RARIDADE.get(p['raridade'], 0xFFB6C1)
            )
            if p["nome"] in IMAGENS_LOCAIS:
                caminho = IMAGENS_LOCAIS[p["nome"]]
                if os.path.exists(caminho):
                    embed.set_image(url=f"attachment://{caminho}")
            embeds.append(embed)
        if embeds:
            view = CardsPaginaView(embeds, 0)
            await view.enviar(interaction, ephemeral=True)
        else:
            await interaction.response.send_message("Nenhum personagem disponível.", ephemeral=True)

    @discord.ui.button(label="Amigos 🤝", style=discord.ButtonStyle.primary, custom_id="amigos_menu")
    async def amigos_menu(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Escolha uma opção:", view=AmigosView(), ephemeral=True)

    @discord.ui.button(label="Tutorial/Ajuda ❔", style=discord.ButtonStyle.secondary, custom_id="tutorial_ajuda")
    async def tutorial_ajuda(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("O que você gostaria de ver?", view=TutorialAjudaView(), ephemeral=True)

    # ===== BOTÃO CONFIGURAR IA (agora chama a criação assíncrona) =====
    @discord.ui.button(label="Configurar IA 💬", style=discord.ButtonStyle.blurple, custom_id="config_ia")
    async def configurar_ia(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores podem configurar a IA.", ephemeral=True)
            return
        # Cria a view de forma assíncrona
        view = await ConfigIAView.create(interaction.guild.id)
        await interaction.response.send_message("🔧 Selecione um canal para ativar/desativar a Hello Kitty:", view=view, ephemeral=True)

# ===== VIEW DE CONFIGURAÇÃO DA IA (corrigida) =====
class ConfigIAView(View):
    def __init__(self, options):
        super().__init__(timeout=120)
        self.add_item(SelectIAChannels(options))

    @classmethod
    async def create(cls, guild_id: int):
        """Cria a view de forma assíncrona, carregando os dados do banco."""
        guild = bot.get_guild(guild_id)
        if not guild:
            options = [discord.SelectOption(label="Erro: servidor não encontrado", value="error")]
        else:
            channels = [c for c in guild.channels if isinstance(c, discord.TextChannel)]
            config = await get_canais_config(guild_id)
            options = []
            for ch in channels[:25]:  # limite de 25 opções
                # Se não estiver no config, assume ativo (True)
                estado = config.get(ch.id, True)
                status_texto = "✅ Ativo" if estado else "❌ Desativado"
                options.append(discord.SelectOption(
                    label=f"#{ch.name}",
                    description=f"Status: {status_texto}",
                    value=str(ch.id)
                ))
            if not options:
                options = [discord.SelectOption(label="Nenhum canal de texto encontrado", value="error")]
        return cls(options)

class SelectIAChannels(Select):
    def __init__(self, options):
        super().__init__(placeholder="Selecione um canal para alternar...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "error":
            await interaction.response.send_message("❌ Erro ao carregar canais.", ephemeral=True)
            return
        channel_id = int(self.values[0])
        guild_id = interaction.guild.id
        novo_estado = await toggle_ia_channel(guild_id, channel_id)
        status_texto = "✅ **ativada**" if novo_estado else "❌ **desativada**"
        await interaction.response.send_message(
            f"💬 A Hello Kitty agora está {status_texto} no canal <#{channel_id}>.",
            ephemeral=True
        )
        # Desabilita o select para evitar múltiplas interações
        self.disabled = True
        await interaction.message.edit(view=self.view)

# ---------- CardsPaginaView ----------
class CardsPaginaView(View):
    def __init__(self, embeds, current):
        super().__init__(timeout=120)
        self.embeds = embeds
        self.current = current
        self.update_buttons()

    def update_buttons(self):
        self.children[0].disabled = self.current == 0
        self.children[1].disabled = self.current == len(self.embeds) - 1

    async def enviar(self, interaction, ephemeral=True):
        embed = self.embeds[self.current]
        file = self._get_image_file(embed)
        if file:
            await interaction.response.send_message(embed=embed, file=file, view=self, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(embed=embed, view=self, ephemeral=ephemeral)

    def _get_image_file(self, embed):
        if embed.image.url and embed.image.url.startswith("attachment://"):
            filename = embed.image.url.split("attachment://")[1]
            if os.path.exists(filename):
                return discord.File(filename, filename=filename)
        return None

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary)
    async def anterior(self, interaction: discord.Interaction, button: Button):
        self.current -= 1
        self.update_buttons()
        embed = self.embeds[self.current]
        file = self._get_image_file(embed)
        if file:
            await interaction.response.edit_message(embed=embed, attachments=[file], view=self)
        else:
            await interaction.response.edit_message(embed=embed, attachments=[], view=self)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
    async def proximo(self, interaction: discord.Interaction, button: Button):
        self.current += 1
        self.update_buttons()
        embed = self.embeds[self.current]
        file = self._get_image_file(embed)
        if file:
            await interaction.response.edit_message(embed=embed, attachments=[file], view=self)
        else:
            await interaction.response.edit_message(embed=embed, attachments=[], view=self)

# ---------- LojaCafeView ----------
class LojaCafeView(View):
    def __init__(self, uid):
        super().__init__(timeout=60)
        self.uid = uid

    @discord.ui.button(label="Doces Diários 🍬", style=discord.ButtonStyle.success)
    async def doces_diarios(self, interaction: discord.Interaction, button: Button):
        dados = await get_user_data(self.uid)
        agora = datetime.datetime.now(timezone.utc).timestamp()
        ultimo = dados.get("ultimo_doce", 0)
        if agora - ultimo < 86400:
            falta = 86400 - (agora - ultimo)
            horas = int(falta // 3600)
            minutos = int((falta % 3600) // 60)
            await interaction.response.send_message(f"⏰ Volte em {horas}h {minutos}m.", ephemeral=True)
            return
        qtd = random.randint(3, 8)
        if tem_efeito(self.uid, dados, "keroppi"): qtd += 1
        dados["doces"] = dados.get("doces", 0) + qtd
        dados["ultimo_doce"] = agora
        await update_user_data(self.uid, dados)
        await interaction.response.send_message(f"🍬 Você ganhou **{qtd} Doces**! Total: {dados['doces']}", ephemeral=False)

    @discord.ui.button(label="Converter 100🍬 → 4💗", style=discord.ButtonStyle.primary)
    async def converter(self, interaction: discord.Interaction, button: Button):
        dados = await get_user_data(self.uid)
        if dados.get("doces", 0) < 100:
            await interaction.response.send_message("Precisa de 100 doces.", ephemeral=True)
            return
        dados["doces"] -= 100
        dados["coracoes"] += 4
        await update_user_data(self.uid, dados)
        await interaction.response.send_message("🍬 100 doces → 4💗!", ephemeral=True)

    @discord.ui.button(label="Cupom da Sorte (200💗+300🍬) 🍀", style=discord.ButtonStyle.primary)
    async def cupom(self, interaction: discord.Interaction, button: Button):
        dados = await get_user_data(self.uid)
        if dados["coracoes"] < 200 or dados.get("doces", 0) < 300:
            await interaction.response.send_message("Recursos insuficientes.", ephemeral=True)
            return
        dados["coracoes"] -= 200
        dados["doces"] -= 300
        personagem = sortear_personagem(self.uid, dados, cupom_raridade=True)
        dados["personagens"].append(personagem["nome"])
        await update_user_data(self.uid, dados)
        embed = discord.Embed(
            title=f"{PERSONAGENS_EMOJI.get(personagem['nome'], '❓')} {personagem['nome']}",
            description=f"**Raridade:** {personagem['raridade']}\n**Habilidade:** {EFEITOS_DESC.get(personagem['efeito'], 'Nenhuma')}\n🍀 Cupom da Sorte!",
            color=CORES_RARIDADE.get(personagem['raridade'], 0xFFB6C1)
        )
        await enviar_card(interaction, embed, personagem["nome"])

    @discord.ui.button(label="Resgatar Hello Kitty (100 frags) 👑", style=discord.ButtonStyle.danger)
    async def resgatar(self, interaction: discord.Interaction, button: Button):
        dados = await get_user_data(self.uid)
        if dados.get("fragmentos", 0) < 100:
            await interaction.response.send_message("Precisa de 100 fragmentos.", ephemeral=True)
            return
        dados["fragmentos"] -= 100
        dados["personagens"].append("Hello Kitty")
        bonus = random.randint(1, 5)
        dados["fragmentos"] += bonus
        await update_user_data(self.uid, dados)
        embed = discord.Embed(
            title="👑 Hello Kitty",
            description=f"**Raridade:** Mítico\n**Habilidade:** {EFEITOS_DESC['hello_kitty']}\n👑 Resgatada! +{bonus} fragmentos extras.",
            color=CORES_RARIDADE["Mítico"]
        )
        await enviar_card(interaction, embed, "Hello Kitty")

    @discord.ui.button(label="Loja de Moedas 🪙", style=discord.ButtonStyle.secondary)
    async def loja_moedas(self, interaction: discord.Interaction, button: Button):
        dados = await get_user_data(self.uid)
        embed = discord.Embed(
            title="🪙 Loja de Moedas – Compre personagens específicos",
            description=f"Saldo: **{dados.get('moedas', 0)}🪙**\n\nSelecione um personagem:",
            color=0x1ABC9C
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
            dados = await get_user_data(self.uid)
            p = next((x for x in PERSONAGENS if x["nome"] == nome), None)
            if not p: return
            preco = PRECO_MOEDAS[p["raridade"]]
            if dados.get("moedas", 0) < preco:
                await interaction_select.response.send_message("Moedas insuficientes.", ephemeral=True)
                return
            dados["moedas"] -= preco
            dados["personagens"].append(nome)
            await update_user_data(self.uid, dados)
            embed = discord.Embed(
                title=f"{PERSONAGENS_EMOJI.get(nome, '❓')} {nome}",
                description=f"**Raridade:** {p['raridade']}\n**Habilidade:** {EFEITOS_DESC.get(p['efeito'], 'Nenhuma')}\n💰 Comprado por {preco}🪙",
                color=CORES_RARIDADE.get(p['raridade'], 0xFFB6C1)
            )
            embed.set_footer(text=f"Saldo restante: {dados['moedas']}🪙")
            await enviar_card(interaction_select, embed, nome)
        select.callback = callback
        view = View(timeout=60)
        view.add_item(select)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Decorações 🖼️", style=discord.ButtonStyle.secondary)
    async def decoracoes(self, interaction: discord.Interaction, button: Button):
        dados = await get_user_data(self.uid)
        embed = discord.Embed(title="🖼️ Loja de Decorações", description=f"Moedas: {dados.get('moedas', 0)}🪙", color=0xFF69B4)
        options = [discord.SelectOption(label=f"{d['nome']} ({d['custo']}🪙)", value=chave) for chave, d in DECORACOES_LOJA.items()]
        select = Select(placeholder="Escolha uma decoração...", options=options)
        async def callback(interaction_select: discord.Interaction):
            chave = select.values[0]
            item = DECORACOES_LOJA[chave]
            dados = await get_user_data(self.uid)
            if dados.get("moedas", 0) < item["custo"]:
                await interaction_select.response.send_message("Moedas insuficientes.", ephemeral=True)
                return
            dados["moedas"] -= item["custo"]
            dados["decoracoes"].append(chave)
            dados["decoracao_ativa"][item["tipo"]] = chave
            await update_user_data(self.uid, dados)
            await interaction_select.response.send_message(f"✅ Decoração {item['nome']} comprada e ativada!", ephemeral=True)
        select.callback = callback
        view = View(timeout=60)
        view.add_item(select)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ---------- AceitarRecusarTrocaView ----------
class AceitarRecusarTrocaView(View):
    def __init__(self, trade_id, solicitante_id, alvo_id, personagem_oferecido):
        super().__init__(timeout=300)
        self.trade_id = trade_id
        self.solicitante_id = solicitante_id
        self.alvo_id = alvo_id
        self.personagem_oferecido = personagem_oferecido

    @discord.ui.button(label="Aceitar ✅", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != self.alvo_id:
            await interaction.response.send_message("Essa troca não é direcionada a você.", ephemeral=True)
            return

        async with db_pool.acquire() as conn:
            status = await conn.fetchval('SELECT status FROM trocas WHERE id = $1', self.trade_id)
            if status != 'pendente':
                await interaction.response.send_message("Esta solicitação já foi respondida ou expirou.", ephemeral=True)
                return

        dados_alvo = await get_user_data(self.alvo_id)
        personagens_alvo = list(set(dados_alvo["personagens"]))
        
        if not personagens_alvo:
            await interaction.response.send_message("Você não tem personagens para trocar.", ephemeral=True)
            return

        options = [discord.SelectOption(label=f"{nome} {PERSONAGENS_EMOJI.get(nome, '')}", value=nome) for nome in personagens_alvo[:25]]
        select = Select(placeholder="Escolha o personagem que você dará", options=options)

        async def select_cb(interaction_select: discord.Interaction):
            personagem_dado = select.values[0]
            
            dados_solicitante = await get_user_data(self.solicitante_id)
            dados_alvo_final = await get_user_data(self.alvo_id)

            if self.personagem_oferecido not in dados_solicitante["personagens"]:
                await interaction_select.response.send_message("O solicitante não possui mais esse personagem.", ephemeral=True)
                async with db_pool.acquire() as conn2:
                    await conn2.execute('UPDATE trocas SET status = $1 WHERE id = $2', 'cancelada', self.trade_id)
                self.disable_all_items()
                await interaction.message.edit(view=self)
                return

            if personagem_dado not in dados_alvo_final["personagens"]:
                await interaction_select.response.send_message("Você não possui mais esse personagem.", ephemeral=True)
                return

            dados_solicitante["personagens"].remove(self.personagem_oferecido)
            dados_solicitante["personagens"].append(personagem_dado)
            dados_alvo_final["personagens"].remove(personagem_dado)
            dados_alvo_final["personagens"].append(self.personagem_oferecido)

            registro = f"{interaction.user.name} deu **{personagem_dado}** e recebeu **{self.personagem_oferecido}** de <@{self.solicitante_id}>"

            dados_solicitante.setdefault("historico_trocas", []).append(registro)
            dados_alvo_final.setdefault("historico_trocas", []).append(registro)
            
            if "trocas" in dados_solicitante.get("missoes_diarias", {}):
                dados_solicitante["missoes_diarias"]["trocas"] += 1
            if "trocas" in dados_solicitante.get("missoes_semanais", {}):
                dados_solicitante["missoes_semanais"]["trocas"] += 1
            if "trocas" in dados_alvo_final.get("missoes_diarias", {}):
                dados_alvo_final["missoes_diarias"]["trocas"] += 1
            if "trocas" in dados_alvo_final.get("missoes_semanais", {}):
                dados_alvo_final["missoes_semanais"]["trocas"] += 1

            await update_user_data(self.solicitante_id, dados_solicitante)
            await update_user_data(self.alvo_id, dados_alvo_final)

            async with db_pool.acquire() as conn2:
                await conn2.execute('UPDATE trocas SET status = $1 WHERE id = $2', 'concluida', self.trade_id)

            self.disable_all_items()
            embed = interaction.message.embeds[0]
            embed.color = 0x3498DB
            embed.description = f"✅ **Troca Concluída!**\n{registro}"
            await interaction.message.edit(embed=embed, view=self)
            await interaction_select.response.send_message("✅ Troca concluída com sucesso!", ephemeral=True)

            try:
                solicitante_user = await bot.fetch_user(int(self.solicitante_id))
                await solicitante_user.send(f"✅ A sua troca com {interaction.user.display_name} foi concluída! Você recebeu **{personagem_dado}** e deu **{self.personagem_oferecido}**.")
            except:
                pass

        select.callback = select_cb
        view = View(timeout=60)
        view.add_item(select)
        await interaction.response.send_message("Escolha o personagem para finalizar a troca:", view=view, ephemeral=True)

    @discord.ui.button(label="Recusar ❌", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != self.alvo_id:
            await interaction.response.send_message("Essa troca não é direcionada a você.", ephemeral=True)
            return

        async with db_pool.acquire() as conn:
            await conn.execute('UPDATE trocas SET status = $1 WHERE id = $2', 'recusada', self.trade_id)

        self.disable_all_items()
        embed = interaction.message.embeds[0]
        embed.color = 0xE74C3C
        embed.description = f"❌ Troca recusada por {interaction.user.mention}."
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message("A troca foi recusada com sucesso.", ephemeral=True)

    def disable_all_items(self):
        for item in self.children:
            item.disabled = True

# ---------- AmigosView ----------
class AmigosView(View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Minha Turma 👥", style=discord.ButtonStyle.primary)
    async def minha_turma(self, interaction: discord.Interaction, button: Button):
        dados = await get_user_data(str(interaction.user.id))
        uid = str(interaction.user.id)
        if not dados["personagens"]:
            await interaction.response.send_message("Sua turma está vazia!", ephemeral=True)
            return
        contagem = {}
        for nome in dados["personagens"]:
            contagem[nome] = contagem.get(nome, 0) + 1
        desc = ""
        for nome, qtd in contagem.items():
            emoji = PERSONAGENS_EMOJI.get(nome, "❓")
            efeito = next((p["efeito"] for p in PERSONAGENS if p["nome"] == nome), None)
            if nome == "Nenê": efeito = "nene"
            desc += f"{emoji} {nome} ×{qtd}  [{EFEITOS_DESC.get(efeito, '—')}]\n"
        embed = discord.Embed(title="👥 Turma do Hello Kitty Café", description=desc, color=0xFF69B4)
        embed.set_footer(text=f"Total: {len(dados['personagens'])} | Frag. HK: {dados['fragmentos']} | 🪙: {dados['moedas']}")
        await interaction.response.send_message(embed=embed, view=TurmaAcoesView(uid), ephemeral=True)

    @discord.ui.button(label="Trocar com Amigo 🤝", style=discord.ButtonStyle.success)
    async def trocar(self, interaction: discord.Interaction, button: Button):
        dados = await get_user_data(str(interaction.user.id))
        uid = str(interaction.user.id)
        personagens = list(set(dados["personagens"]))
        if not personagens:
            await interaction.response.send_message("Você não tem personagens para trocar.", ephemeral=True)
            return
            
        options = [discord.SelectOption(label=f"{nome} {PERSONAGENS_EMOJI.get(nome, '')}", value=nome) for nome in personagens[:25]]
        select = Select(placeholder="Qual personagem você quer oferecer?", options=options)
        
        async def select_cb(interaction_select: discord.Interaction):
            personagem_oferecido = select.values[0]
            membros = [m for m in interaction.guild.members if not m.bot and m.id != interaction.user.id]
            if not membros:
                await interaction_select.response.send_message("Nenhum amigo encontrado no servidor.", ephemeral=True)
                return
                
            membro_opts = [discord.SelectOption(label=m.display_name, value=str(m.id)) for m in membros[:25]]
            select_m = Select(placeholder="Escolha o amigo para a troca...", options=membro_opts)
            
            async def membro_cb(interaction_m: discord.Interaction):
                alvo_id = select_m.values[0]
                check_dados = await get_user_data(uid)
                if personagem_oferecido not in check_dados["personagens"]:
                    await interaction_m.response.send_message("Você não possui mais esse personagem.", ephemeral=True)
                    return

                async with db_pool.acquire() as conn:
                    trade_id = await conn.fetchval('''
                        INSERT INTO trocas (solicitante_id, alvo_id, personagem_oferecido, timestamp)
                        VALUES ($1, $2, $3, $4)
                        RETURNING id
                    ''', uid, alvo_id, personagem_oferecido, int(datetime.datetime.now(timezone.utc).timestamp()))
                
                alvo_user = await bot.fetch_user(int(alvo_id))
                embed = discord.Embed(
                    title="🤝 Proposta de Troca",
                    description=f"{interaction.user.mention} quer trocar **{personagem_oferecido}** com você, {alvo_user.mention}!\n\nClique abaixo para responder.",
                    color=0x2ECC71
                )
                view_troca = AceitarRecusarTrocaView(trade_id, uid, alvo_id, personagem_oferecido)
                await interaction_m.response.send_message("✅ Pedido de troca enviado no canal!", ephemeral=True)
                await interaction.channel.send(content=alvo_user.mention, embed=embed, view=view_troca)
                
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
        dados = await get_user_data(str(interaction.user.id))
        historico = dados.get("historico_trocas", [])
        if not historico:
            await interaction.response.send_message("Nenhuma troca realizada.", ephemeral=True)
            return
        msg = "\n".join(historico[-10:])
        embed = discord.Embed(title="📜 Histórico de Trocas", description=msg, color=0xBDC3C7)
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ---------- TurmaAcoesView ----------
class TurmaAcoesView(View):
    def __init__(self, uid):
        super().__init__(timeout=60)
        self.uid = uid

    @discord.ui.button(label="Vender Duplicata 💰", style=discord.ButtonStyle.secondary)
    async def vender(self, interaction: discord.Interaction, button: Button):
        dados = await get_user_data(self.uid)
        contagem = {}
        for nome in dados["personagens"]:
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
            dados = await get_user_data(self.uid)
            dados["personagens"].remove(nome)
            dados["moedas"] = dados.get("moedas", 0) + valor
            await update_user_data(self.uid, dados)
            embed = discord.Embed(
                title=f"💰 Venda: {PERSONAGENS_EMOJI.get(nome, '❓')} {nome}",
                description=f"**Raridade:** {raridade}\nValor: **{valor}🪙**",
                color=CORES_RARIDADE.get(raridade, 0xFFB6C1)
            )
            embed.set_footer(text=f"Total de moedas: {dados['moedas']}")
            await enviar_card(interaction_select, embed, nome)
        select.callback = callback
        view = View(timeout=60)
        view.add_item(select)
        await interaction.response.send_message("Selecione a duplicata:", view=view, ephemeral=True)

    @discord.ui.button(label="Cinnamoroll: Trocar 2 duplicatas 🔄", style=discord.ButtonStyle.primary)
    async def cinnamoroll(self, interaction: discord.Interaction, button: Button):
        dados = await get_user_data(self.uid)
        if not tem_efeito(self.uid, dados, "cinnamoroll"):
            await interaction.response.send_message("Precisa do Cinnamoroll.", ephemeral=True)
            return
        contagem = {}
        for nome in dados["personagens"]: contagem[nome] = contagem.get(nome, 0) + 1
        trocaveis = [nome for nome, qtd in contagem.items() if qtd >= 2]
        if not trocaveis:
            await interaction.response.send_message("Sem 2 cópias.", ephemeral=True)
            return
        nome = trocaveis[0]
        for _ in range(2): dados["personagens"].remove(nome)
        novo = sortear_personagem(self.uid, dados)
        dados["personagens"].append(novo["nome"])
        await update_user_data(self.uid, dados)
        embed = discord.Embed(
            title=f"🔄 Troca Cinnamoroll: {PERSONAGENS_EMOJI.get(novo['nome'], '❓')} {novo['nome']}",
            description=f"**Raridade:** {novo['raridade']}\n**Habilidade:** {EFEITOS_DESC.get(novo['efeito'], 'Nenhuma')}\n(2× {nome})",
            color=CORES_RARIDADE.get(novo['raridade'], 0xFFB6C1)
        )
        await enviar_card(interaction, embed, novo["nome"])

    @discord.ui.button(label="Hangyodon: Reciclar duplicata ♻️", style=discord.ButtonStyle.danger)
    async def hangyodon(self, interaction: discord.Interaction, button: Button):
        dados = await get_user_data(self.uid)
        if not tem_efeito(self.uid, dados, "hangyodon"):
            await interaction.response.send_message("Precisa do Hangyodon.", ephemeral=True)
            return
        contagem = {}
        for nome in dados["personagens"]: contagem[nome] = contagem.get(nome, 0) + 1
        dups = [nome for nome, qtd in contagem.items() if qtd > 1]
        if not dups:
            await interaction.response.send_message("Sem duplicatas.", ephemeral=True)
            return
        nome = dups[0]
        dados["personagens"].remove(nome)
        dados["coracoes"] += 3
        await update_user_data(self.uid, dados)
        await interaction.response.send_message(f"♻️ {nome} → +3💗", ephemeral=True)

# ---------- TutorialAjudaView ----------
class TutorialAjudaView(View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Tutorial 📘", style=discord.ButtonStyle.primary)
    async def tutorial(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title="📘 Tutorial do Hello Kitty Café",
                              description="Bem-vindo(a)! Aqui você monta sua turma de amigos da Sanrio.\n\n"
                                          "💗 Corações: comece com 3. Use 1💗 no botão 'Comprar Personagem'.\n"
                                          "🍬 Doces: resgate 1x/dia na Loja.\n"
                                          "🪙 Moedas: venda duplicatas na Turma.\n"
                                          "👑 Hello Kitty: chance raríssima, ganhe fragmentos e resgate.\n"
                                          "💫 Nenê: Ultimate, quase impossível!\n"
                                          "🤝 Amigos: troque com outros membros.\n"
                                          "🎯 Missões diárias/semanais: completem para ganhar recompensas.\n"
                                          "🏆 Conquistas: desbloqueie medalhas.\n"
                                          "Use /perfil, /ranking, /minijogo e muito mais!",
                              color=0x3498DB)
        embed.set_image(url="attachment://Hello_kitty.png")
        await interaction.response.send_message(embed=embed, file=discord.File("Hello_kitty.png"), ephemeral=True)

    @discord.ui.button(label="Ajuda ❓", style=discord.ButtonStyle.secondary)
    async def ajuda(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title="🌸 Ajuda Rápida",
                              description="• Ganhe 💗 conversando.\n"
                                          "• Doces diários na Loja.\n"
                                          "• 100🍬 = 4💗.\n"
                                          "• Venda duplicatas por 🪙.\n"
                                          "• Cupom da Sorte: 200💗+300🍬.\n"
                                          "• Hello Kitty: 100 fragmentos.\n"
                                          "• Troque com amigos.\n"
                                          "• /conversar para falar comigo 💬",
                              color=0xFFC0CB)
        await interaction.response.send_message(embed=embed, ephemeral=True)

# =================== COMANDOS SLASH ===================

@bot.tree.command(name="hellokitty", description="Abre o painel do Hello Kitty Café ☕")
async def hellokitty(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title="☕ Hello Kitty Café 🎀",
                          description="**Clique nos botões para explorar o café!**",
                          color=0xFF69B4)
    if os.path.exists("Hello_kitty.png"):
        file = discord.File("Hello_kitty.png", filename="Hello_kitty.png")
        embed.set_image(url="attachment://Hello_kitty.png")
        await interaction.followup.send(embed=embed, file=file, view=MenuPrincipal())
    else:
        await interaction.followup.send(embed=embed, view=MenuPrincipal())

@bot.tree.command(name="perfil", description="Veja seu perfil no Hello Kitty Café")
async def perfil(interaction: discord.Interaction):
    dados = await get_user_data(str(interaction.user.id))
    unicos = len(set(dados["personagens"]))
    nivel = calcular_nivel(dados.get("xp", 0))
    titulo = TITULOS.get(nivel, "")
    embed = discord.Embed(title=f"🌸 Perfil de {interaction.user.display_name}", color=0xFF69B4)
    embed.add_field(name="Nível", value=f"{nivel} {titulo}")
    embed.add_field(name="💗 Corações", value=dados["coracoes"])
    embed.add_field(name="🍬 Doces", value=dados.get("doces", 0))
    embed.add_field(name="🪙 Moedas", value=dados.get("moedas", 0))
    embed.add_field(name="✨ Fragmentos Hello", value=dados["fragmentos"])
    embed.add_field(name="👥 Personagens únicos", value=unicos)
    embed.add_field(name="🤝 Trocas", value=len(dados.get("historico_trocas", [])))
    if dados.get("conquistas"):
        embed.add_field(name="🏆 Conquistas", value=", ".join(CONQUISTAS[c]["nome"] for c in dados["conquistas"] if c in CONQUISTAS), inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="ranking", description="Veja o ranking do servidor")
async def ranking(interaction: discord.Interaction):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch('SELECT id, personagens, coracoes FROM users')
    ranking = []
    for row in rows:
        try:
            member = interaction.guild.get_member(int(row['id']))
            if member:
                personagens = json.loads(row['personagens'])
                ranking.append((member.display_name, len(set(personagens)), row['coracoes']))
        except:
            pass
    ranking.sort(key=lambda x: x[1], reverse=True)
    desc = "\n".join(f"**{i+1}.** {nome} - {uni} únicos, {cor}💗" for i, (nome, uni, cor) in enumerate(ranking[:10]))
    embed = discord.Embed(title="🏆 Ranking do Café", description=desc or "Nenhum jogador ainda.", color=0xFFD700)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="drop", description="Resgate seu drop a cada 4 horas!")
async def drop(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    dados = await get_user_data(uid)
    agora = datetime.datetime.now(timezone.utc).timestamp()
    ultimo = dados.get("ultimo_drop", 0)
    intervalo = 4 * 3600
    restante = intervalo - (agora - ultimo)

    embed = discord.Embed(title="🎁 Drop do Café", color=0xFF69B4)
    if restante <= 0:
        embed.description = "**Você pode resgatar seu drop agora!** Clique no botão abaixo."
        embed.set_footer(text="Disponível!")
        view = DropView(uid, disponivel=True)
    else:
        horas = int(restante // 3600)
        minutos = int((restante % 3600) // 60)
        segundos = int(restante % 60)
        embed.description = f"⏳ Próximo drop disponível em **{horas}h {minutos}m {segundos}s**"
        embed.set_footer(text="Volte mais tarde!")
        view = DropView(uid, disponivel=False)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class DropView(View):
    def __init__(self, uid, disponivel):
        super().__init__(timeout=300)
        self.uid = uid
        self.disponivel = disponivel

    @discord.ui.button(label="Resgatar 🎁", style=discord.ButtonStyle.success, custom_id="resgatar_drop")
    async def resgatar_drop(self, interaction: discord.Interaction, button: Button):
        button.disabled = True
        await interaction.response.edit_message(view=self)

        dados = await get_user_data(self.uid)
        agora = datetime.datetime.now(timezone.utc).timestamp()
        ultimo = dados.get("ultimo_drop", 0)

        if agora - ultimo < 4 * 3600:
            await interaction.followup.send("⏳ Ainda não passou 4 horas desde seu último drop!", ephemeral=True)
            return

        premios = [
            ("💗", "coracoes", random.randint(3, 8)),
            ("🍬", "doces", random.randint(2, 5)),
            ("✨", "fragmentos", random.randint(1, 3)),
            ("🪙", "moedas", random.randint(5, 15))
        ]
        escolha = random.choice(premios)
        dados[escolha[1]] = dados.get(escolha[1], 0) + escolha[2]
        dados["ultimo_drop"] = agora
        await update_user_data(self.uid, dados)

        embed = discord.Embed(
            title="🎁 Drop Resgatado!",
            description=f"Você ganhou **{escolha[2]} {escolha[0]}**!",
            color=0x2ECC71
        )
        embed.set_footer(text="Próximo drop em 4 horas.")
        await interaction.edit_original_response(embed=embed, view=None)

@bot.tree.command(name="minijogo", description="Jogue um minijogo: roleta, memória ou adivinhe")
@app_commands.choices(jogo=[
    app_commands.Choice(name="Roleta da Sorte", value="roleta"),
    app_commands.Choice(name="Adivinhe o Personagem", value="adivinhe")
])
async def minijogo(interaction: discord.Interaction, jogo: app_commands.Choice[str]):
    if jogo.value == "roleta":
        premios = [("💗 5 corações", "coracoes", 5), ("🍬 3 doces", "doces", 3),
                   ("✨ 1 fragmento", "fragmentos", 1), ("🪙 10 moedas", "moedas", 10)]
        premio = random.choice(premios)
        dados = await get_user_data(str(interaction.user.id))
        uid = str(interaction.user.id)
        dados[premio[1]] = dados.get(premio[1], 0) + premio[2]
        await update_user_data(uid, dados)
        await interaction.response.send_message(f"🎰 **Roleta da Sorte:** Você ganhou {premio[0]}!", ephemeral=False)
    elif jogo.value == "adivinhe":
        personagem = random.choice([p for p in PERSONAGENS if p["nome"] != "Nenê"])
        await interaction.response.send_modal(AdivinheModal(personagem["nome"]))

class AdivinheModal(Modal, title="Adivinhe o Personagem"):
    def __init__(self, nome_correto):
        super().__init__()
        self.nome_correto = nome_correto
        self.resposta = TextInput(label="Digite o nome do personagem:", placeholder="Ex: Hello Kitty")
        self.add_item(self.resposta)

    async def on_submit(self, interaction: discord.Interaction):
        if self.resposta.value.strip().lower() == self.nome_correto.lower():
            dados = await get_user_data(str(interaction.user.id))
            uid = str(interaction.user.id)
            bonus = random.randint(1, 3)
            dados["coracoes"] = dados.get("coracoes", 0) + bonus
            await update_user_data(uid, dados)
            await interaction.response.send_message(f"🎉 Correto! Você ganhou **{bonus}💗**!", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Errado! O personagem era **{self.nome_correto}**.", ephemeral=True)

# ---------- COMANDO PARA CONFIGURAR IA (ALTERNATIVO) ----------
@bot.tree.command(name="configurar_ia", description="Ativar/desativar a Hello Kitty em um canal (Admin)")
@app_commands.default_permissions(administrator=True)
async def configurar_ia_cmd(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores podem usar este comando.", ephemeral=True)
        return
    view = await ConfigIAView.create(interaction.guild.id)
    await interaction.response.send_message("🔧 Selecione um canal para ativar/desativar a Hello Kitty:", view=view, ephemeral=True)

# ---------- Comandos de IA ----------
@bot.tree.command(name="historinha", description="A Hello Kitty conta uma historinha com seus personagens!")
async def historinha(interaction: discord.Interaction):
    if not cliente_ia:
        await interaction.response.send_message("💔 IA não disponível (chave API não configurada).", ephemeral=True)
        return
    dados = await get_user_data(str(interaction.user.id))
    personagens = dados.get("personagens", [])
    if not personagens:
        await interaction.response.send_message("Você ainda não tem personagens!", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        prompt = f"Crie uma historinha curta e fofa (máximo 100 palavras) com os seguintes personagens: {', '.join(set(personagens[:5]))}. A Hello Kitty é a anfitriã do café."
        response = cliente_ia.generate_content(prompt)
        texto = response.text[:1500]
        await interaction.followup.send(f"📖 {texto}")
    except Exception as e:
        logging.error(f"Erro na historinha: {e}")
        try:
            fallback_model = genai.GenerativeModel("gemini-pro")
            response = fallback_model.generate_content(prompt)
            texto = response.text[:1500]
            await interaction.followup.send(f"📖 {texto}")
        except:
            await interaction.followup.send("🌸 Ops! A Hello Kitty está com preguiça de escrever hoje... tente de novo mais tarde. 😿")

@bot.tree.command(name="conversar", description="Fale com a Hello Kitty!")
async def conversar(interaction: discord.Interaction, mensagem: str):
    if not cliente_ia:
        await interaction.response.send_message("💔 IA não disponível.", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        prompt = f"""Você é a Hello Kitty, uma gatinha meiga e amigável do universo Sanrio.
        Você está no servidor do Discord "Hello Kitty Café", um joguinho de colecionar personagens.
        Responda de forma fofa, animada e ajude o jogador com dicas sobre o jogo.
        Mensagem do jogador: {mensagem}"""
        response = cliente_ia.generate_content(prompt)
        texto = response.text[:1800]
        await interaction.followup.send(f"🌸 **Hello Kitty:** {texto}")
    except Exception as e:
        logging.error(f"Erro na IA: {e}")
        try:
            fallback_model = genai.GenerativeModel("gemini-pro")
            response = fallback_model.generate_content(prompt)
            texto = response.text[:1800]
            await interaction.followup.send(f"🌸 **Hello Kitty:** {texto}")
        except:
            await interaction.followup.send("🌸 Ops! A Hello Kitty está descansando... tente de novo mais tarde. 😿")

# =================== EVENTOS ===================

@bot.event
async def on_ready():
    print(f"🌸 {bot.user} está no Hello Kitty Café!")
    await init_db()
    bot.add_view(MenuPrincipal())
    if GUILD_ID:
        guild = discord.Object(id=int(GUILD_ID))
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
    else:
        await bot.tree.sync()
    logging.info("Bot pronto!")

# ---------- Processamento de mensagens ----------
ia_cooldowns = {}
ia_falhas_consecutivas = defaultdict(int)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = str(message.author.id)
    dados = await get_user_data(uid)

    dados["msg_count"] += 1
    mensagens = dados["msg_count"]

    dados["xp"] = dados.get("xp", 0) + 1
    nivel_antigo = calcular_nivel(dados["xp"] - 1)
    nivel_novo = calcular_nivel(dados["xp"])
    if nivel_novo > nivel_antigo:
        recomp = recompensa_nivel(nivel_novo)
        for k, v in recomp.items():
            dados[k] = dados.get(k, 0) + v
        await notificar_meta(uid, f"nivel_{nivel_novo}", f"🎉 Você subiu para o nível {nivel_novo}! {TITULOS.get(nivel_novo, '')}\nRecompensas: {recomp}")

    agora = datetime.datetime.now(timezone.utc).timestamp()
    if "ultima_reset_diaria" not in dados or agora - dados.get("ultima_reset_diaria", 0) > 86400:
        resetar_missoes_diarias(dados)
    if "ultima_reset_semanal" not in dados or agora - dados.get("ultima_reset_semanal", 0) > 604800:
        resetar_missoes_semanais(dados)

    if "mensagens" in dados.get("missoes_diarias", {}):
        dados["missoes_diarias"]["mensagens"] += 1
    if "mensagens" in dados.get("missoes_semanais", {}):
        dados["missoes_semanais"]["mensagens"] += 1

    # Efeitos de mensagem
    if tem_efeito(uid, dados, "dear_daniel") and mensagens % 50 == 0:
        dados["coracoes"] += 1
        await notificar_meta(uid, f"daniel_{mensagens}", f"📬 Dear Daniel te enviou +1💗! ({mensagens} msgs)")
    if tem_efeito(uid, dados, "twin_stars") and mensagens % 10 == 0:
        dados["coracoes"] += 1
        await notificar_meta(uid, f"twin_{mensagens}", f"⭐ Little Twin Stars: +1💗! ({mensagens} msgs)")
    if tem_efeito(uid, dados, "nene") and mensagens % 5 == 0:
        dados["coracoes"] += 3
        await notificar_meta(uid, f"nene_{mensagens}", f"💫 Nenê radiante: +3💗! ({mensagens} msgs)")
    if tem_efeito(uid, dados, "pipi") and mensagens % 80 == 0:
        dados["coracoes"] += 1
        await notificar_meta(uid, f"pipi_{mensagens}", f"🐤 Pipi: +1💗! ({mensagens} msgs)")
    if tem_efeito(uid, dados, "mocha") and mensagens % 60 == 0:
        dados["coracoes"] += 1
        await notificar_meta(uid, f"mocha_{mensagens}", f"🐶 Mocha: +1💗! ({mensagens} msgs)")

    ganho = calcular_coracoes_msg(uid, dados, mensagens)
    dados["coracoes"] += ganho
    dados["coracoes_ganhos"] += ganho

    if tem_efeito(uid, dados, "pochacco") and dados["coracoes_ganhos"] >= 20:
        dados["coracoes"] += 1
        dados["coracoes_ganhos"] -= 20

    if tem_efeito(uid, dados, "george") and mensagens % 100 == 0:
        dados["fragmentos"] += 1
        await notificar_meta(uid, f"george_{mensagens}", f"🐵 George: +1 fragmento Hello! ({mensagens} msgs)")
    if tem_efeito(uid, dados, "sasa") and mensagens % 50 == 0:
        dados["fragmentos"] += 1
        await notificar_meta(uid, f"sasa_{mensagens}", f"🐱 Sasa: +1 fragmento Hello! ({mensagens} msgs)")

    # Verificar missões
    for missao in MISSOES_DIARIAS:
        if dados["missoes_diarias"].get(missao["id"], 0) >= missao["meta"] and f"diaria_{missao['id']}" not in dados.get("missoes_concluidas", []):
            dados.setdefault("missoes_concluidas", []).append(f"diaria_{missao['id']}")
            for k, v in missao["recompensa"].items():
                dados[k] = dados.get(k, 0) + v
            await notificar_meta(uid, f"missao_{missao['id']}", f"✅ Missão diária concluída: {missao['desc']}! Recompensa: {missao['recompensa']}")

    for missao in MISSOES_SEMANAIS:
        if dados["missoes_semanais"].get(missao["id"], 0) >= missao["meta"] and f"semanal_{missao['id']}" not in dados.get("missoes_concluidas", []):
            dados.setdefault("missoes_concluidas", []).append(f"semanal_{missao['id']}")
            for k, v in missao["recompensa"].items():
                dados[k] = dados.get(k, 0) + v
            await notificar_meta(uid, f"missaos_{missao['id']}", f"✅ Missão semanal concluída: {missao['desc']}! Recompensa: {missao['recompensa']}")

    await update_user_data(uid, dados)

    # ---------- Resposta natural da IA (somente se o canal estiver ativo) ----------
    if not cliente_ia:
        await bot.process_commands(message)
        return

    if not await is_ia_active(message.channel.id):
        await bot.process_commands(message)
        return

    if ia_falhas_consecutivas[message.channel.id] >= 3:
        await bot.process_commands(message)
        return

    canal_id = message.channel.id
    agora_ts = datetime.datetime.now(timezone.utc).timestamp()
    if canal_id in ia_cooldowns and agora_ts - ia_cooldowns[canal_id] < 30:
        await bot.process_commands(message)
        return

    ia_cooldowns[canal_id] = agora_ts

    try:
        prompt = f"""Você é a Hello Kitty, uma gatinha meiga e amigável do universo Sanrio.
Você está em um chat do Discord no servidor "Hello Kitty Café", um joguinho de colecionar personagens.
Converse naturalmente com os membros, dê dicas fofas sobre o jogo, e mantenha um tom animado.
Responda em português, de forma curta e amigável (máximo 2 frases).
Mensagem recebida: {message.content}"""
        response = cliente_ia.generate_content(prompt)
        texto = response.text
        if len(texto) > 2000:
            texto = texto[:1997] + "..."
        await message.channel.send(f"🌸 {texto}")
        ia_falhas_consecutivas[canal_id] = 0
    except Exception as e:
        ia_falhas_consecutivas[canal_id] += 1
        erro_str = str(e)
        if "RESOURCE_EXHAUSTED" not in erro_str and "quota" not in erro_str.lower():
            logging.error(f"Erro na IA: {erro_str[:150]}")

    await bot.process_commands(message)

# =================== TAREFAS ===================
@tasks.loop(hours=24)
async def enviar_resumos_diarios():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch('SELECT id, resumo_dm, coracoes, doces, moedas FROM users')
    for row in rows:
        if row['resumo_dm']:
            try:
                user = await bot.fetch_user(int(row['id']))
                msg = f"🌸 **Resumo Diário do Café**\n💗 Corações: {row['coracoes']}\n🍬 Doces: {row['doces']}\n🪙 Moedas: {row['moedas']}\nTenha um dia fofo!"
                await user.send(msg)
            except:
                pass

# =================== INICIALIZAÇÃO ===================
if __name__ == "__main__":
    if not DATABASE_URL:
        logging.error("DATABASE_URL não definida.")
        exit(1)
    bot.run(TOKEN)