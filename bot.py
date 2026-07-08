import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import random
import json
import os

# =================== CONFIGURAÇÕES ===================
TOKEN = os.getenv("TOKEN")
ARQUIVO_DADOS = os.getenv("DATA_PATH", "dados_sanrio.json")
GUILD_ID = os.getenv("GUILD_ID")  # opcional, para sincronização rápida
# =====================================================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- Banco de dados ----------
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# ---------- Lista completa de personagens com pesos ----------
# Total de pesos = 10.000.000 (Hello Kitty 1/10M = 0,00001%)
PERSONAGENS = [
    # Mítico
    {"nome": "Hello Kitty",           "peso": 1,        "raridade": "Mítico",   "efeito": "hello_kitty"},
    # Lendários
    {"nome": "Dear Daniel",           "peso": 2,        "raridade": "Lendário", "efeito": "dear_daniel"},
    {"nome": "My Melody",             "peso": 5,        "raridade": "Lendário", "efeito": "my_melody"},
    {"nome": "Kuromi",                "peso": 5,        "raridade": "Lendário", "efeito": "kuromi"},
    # Épicos
    {"nome": "Pompompurin",           "peso": 10,       "raridade": "Épico",    "efeito": "pompompurin"},
    {"nome": "Cinnamoroll",           "peso": 10,       "raridade": "Épico",    "efeito": "cinnamoroll"},
    {"nome": "Little Twin Stars",     "peso": 20,       "raridade": "Épico",    "efeito": "twin_stars"},
    # Raros
    {"nome": "Keroppi",               "peso": 200,      "raridade": "Raro",     "efeito": "keroppi"},
    {"nome": "Badtz-Maru",            "peso": 200,      "raridade": "Raro",     "efeito": "badtz_maru"},
    {"nome": "Tuxedo Sam",            "peso": 200,      "raridade": "Raro",     "efeito": "tuxedo_sam"},
    # Incomuns
    {"nome": "Pochacco",              "peso": 2000,     "raridade": "Incomum",  "efeito": "pochacco"},
    {"nome": "Chococat",              "peso": 2000,     "raridade": "Incomum",  "efeito": "chococat"},
    {"nome": "Hangyodon",             "peso": 2000,     "raridade": "Incomum",  "efeito": "hangyodon"},
    {"nome": "Pekkle",                "peso": 2000,     "raridade": "Incomum",  "efeito": "pekkle"},
]
# Comuns (20 personagens, totalizando 10.000.000)
# 19 * 500.000 = 9.500.000; último = 491.347 para completar exatamente 10M
PERSONAGENS_COMUNS = [
    "Spottie Dottie", "Landry", "Moppu", "Coro Chan", "Minna no Tabo",
    "Charmmy Kitty", "Sugar", "Tiny Chum", "Cathy", "George",
    "Fifi", "Rory", "Lulu", "Pipi", "Nana", "Mimi", "Sasa", "Kiki", "Lala"
]
for i, nome in enumerate(PERSONAGENS_COMUNS):
    peso = 500000 if i < 19 else 491347
    PERSONAGENS.append({"nome": nome, "peso": peso, "raridade": "Comum", "efeito": None})

# Verificação de total (debug)
TOTAL_PESOS = sum(p["peso"] for p in PERSONAGENS)
assert TOTAL_PESOS == 10000000, f"Pesos não somam 10.000.000! ({TOTAL_PESOS})"

# ---------- Descrições de efeitos (para exibição) ----------
DESCRICAO_EFEITOS = {
    "hello_kitty": "+2 corações/msg, 20% desc. loja, 10% frag. extra",
    "dear_daniel": "+1 convite a cada 50 msgs",
    "my_melody": "10% desc. na loja",
    "kuromi": "+15% chance Épico+",
    "pompompurin": "50% não gastar convite",
    "cinnamoroll": "Troca 2 duplicatas por 1 novo",
    "twin_stars": "+1 convite a cada 10 msgs",
    "keroppi": "Começa com 5 convites",
    "badtz_maru": "+5💗 ao comprar convite",
    "tuxedo_sam": "30% ganhar +1 convite ao conhecer",
    "pochacco": "+1 convite a cada 20💗 ganhos",
    "chococat": "20% duplicar amigo encontrado",
    "hangyodon": "Reciclar duplicata = 3💗",
    "pekkle": "+5% chance Incomum+",
}

# ---------- Funções de efeitos ----------
def tem_efeito(uid, dados, efeito_nome):
    """Verifica se o jogador possui um personagem com determinado efeito."""
    if uid not in dados:
        return False
    for nome in set(dados[uid]["personagens"]):
        for p in PERSONAGENS:
            if p["nome"] == nome and p["efeito"] == efeito_nome:
                return True
    return False

def obter_desconto(uid, dados):
    """Retorna o desconto máximo na loja (0.0 a 1.0)."""
    max_desc = 0.0
    if tem_efeito(uid, dados, "my_melody"):
        max_desc = max(max_desc, 0.10)
    if tem_efeito(uid, dados, "hello_kitty"):
        max_desc = max(max_desc, 0.20)
    return max_desc

def calcular_coracoes_mensagem(uid, dados):
    base = 1
    if tem_efeito(uid, dados, "hello_kitty"):
        base += 2
    return base

def fitas_iniciais(uid, dados):
    return 5 if tem_efeito(uid, dados, "keroppi") else 3

# ---------- Sorteio com modificadores ----------
def sortear_personagem(uid, dados):
    """
    Retorna um personagem aleatório baseado nos pesos,
    aplicando bônus de Kuromi e Pekkle.
    """
    # Modificador de chance
    multiplicadores = {}
    if tem_efeito(uid, dados, "kuromi"):
        for p in PERSONAGENS:
            if p["raridade"] in ("Épico", "Lendário", "Mítico"):
                multiplicadores[p["nome"]] = 1.15
    if tem_efeito(uid, dados, "pekkle"):
        for p in PERSONAGENS:
            if p["raridade"] in ("Incomum", "Raro", "Épico", "Lendário", "Mítico"):
                multiplicadores[p["nome"]] = multiplicadores.get(p["nome"], 1.0) * 1.05

    # Calcula pesos ajustados
    pesos_ajustados = []
    for p in PERSONAGENS:
        peso = p["peso"]
        if p["nome"] in multiplicadores:
            peso = int(peso * multiplicadores[p["nome"]])
        pesos_ajustados.append(peso)

    total = sum(pesos_ajustados)
    rolagem = random.randint(1, total)
    acumulado = 0
    for i, p in enumerate(PERSONAGENS):
        acumulado += pesos_ajustados[i]
        if rolagem <= acumulado:
            return p
    return PERSONAGENS[0]

# =================== VIEW PRINCIPAL (PERSISTENTE) ===================
class MenuPrincipal(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Conhecer Amigo 🎁", style=discord.ButtonStyle.success, custom_id="conhecer")
    async def conhecer(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if uid not in dados:
            dados[uid] = {
                "coracoes": 20,
                "fitas": fitas_iniciais(uid, dados),
                "personagens": [],
                "fragmentos": 0,
                "msg_count": 0,
                "coracoes_ganhos": 0
            }

        # Verifica fitas (convites)
        if dados[uid]["fitas"] <= 0:
            await interaction.response.send_message(
                "🌸 Você não tem convites! Compre na **Loja de Presentes** ou ganhe corações participando.",
                ephemeral=True
            )
            return

        # Efeito Pompompurin: 50% de não gastar
        gastar = True
        if tem_efeito(uid, dados, "pompompurin"):
            if random.random() < 0.5:
                gastar = False

        if gastar:
            dados[uid]["fitas"] -= 1

        # Sorteia personagem
        personagem = sortear_personagem(uid, dados)

        # Efeito Chococat: 20% de duplicar
        duplicar = False
        if tem_efeito(uid, dados, "chococat"):
            if random.random() < 0.20:
                duplicar = True

        # Adiciona à coleção
        dados[uid]["personagens"].append(personagem["nome"])
        if duplicar:
            dados[uid]["personagens"].append(personagem["nome"])

        # Fragmentos se duplicata de raridade Lendário/Mítico
        if dados[uid]["personagens"].count(personagem["nome"]) > 1:
            if personagem["raridade"] == "Mítico":
                dados[uid]["fragmentos"] += 10
            elif personagem["raridade"] == "Lendário":
                dados[uid]["fragmentos"] += 1

        # Efeito Tuxedo Sam: 30% ganhar +1 convite
        if tem_efeito(uid, dados, "tuxedo_sam"):
            if random.random() < 0.30:
                dados[uid]["fitas"] += 1

        # Efeito Hello Kitty: 10% fragmento extra
        if tem_efeito(uid, dados, "hello_kitty"):
            if random.random() < 0.10:
                dados[uid]["fragmentos"] += 1

        salvar_dados(dados)

        # Mensagem de resultado
        msg_extra = ""
        if not gastar:
            msg_extra += "\n🍮 **Pompompurin** evitou que você gastasse o convite!"
        if duplicar:
            msg_extra += "\n🐱 **Chococat** duplicou o amigo!"

        embed = discord.Embed(
            title="🎁 Novo Amigo!",
            description=f"**{personagem['nome']}**\n"
                        f"Raridade: **{personagem['raridade']}** {personagem.get('emoji', '')}\n"
                        f"✨ Efeito: {DESCRICAO_EFEITOS.get(personagem['efeito'], 'Nenhum')}" +
                        msg_extra,
            color=discord.Color.from_rgb(255, 182, 193)
        )
        embed.set_footer(text=f"Convites: {dados[uid]['fitas']} | Corações: {dados[uid]['coracoes']} | Fragmentos Hello: {dados[uid]['fragmentos']}")
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @discord.ui.button(label="Minha Turma 👥", style=discord.ButtonStyle.primary, custom_id="turma")
    async def turma(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if uid not in dados or not dados[uid]["personagens"]:
            await interaction.response.send_message("👥 Sua turma está vazia! Conheça novos amigos primeiro.", ephemeral=True)
            return

        personagens = dados[uid]["personagens"]
        contagem = {}
        for nome in personagens:
            contagem[nome] = contagem.get(nome, 0) + 1

        descricao = ""
        for nome, qtd in contagem.items():
            efeito = next((p["efeito"] for p in PERSONAGENS if p["nome"] == nome), None)
            desc_efeito = DESCRICAO_EFEITOS.get(efeito, "—") if efeito else "—"
            descricao += f"{nome} ×{qtd}  [{desc_efeito}]\n"

        embed = discord.Embed(
            title="👥 Sua Turma da Sanrio",
            description=descricao,
            color=discord.Color.from_rgb(255, 105, 180)
        )
        embed.set_footer(text=f"Total de amigos: {len(personagens)} | Fragmentos Hello: {dados[uid].get('fragmentos', 0)}")

        # View extra com opções de Cinnamoroll e Hangyodon
        view = TurmaAcoesView(uid)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Loja de Presentes 🛍️", style=discord.ButtonStyle.secondary, custom_id="loja")
    async def loja(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if uid not in dados:
            dados[uid] = {
                "coracoes": 20,
                "fitas": fitas_iniciais(uid, dados),
                "personagens": [],
                "fragmentos": 0,
                "msg_count": 0,
                "coracoes_ganhos": 0
            }
            salvar_dados(dados)

        desconto = obter_desconto(uid, dados)
        preco = int(10 * (1 - desconto))
        embed = discord.Embed(
            title="🛍️ Loja de Convites",
            description=f"**1 Convite = {preco} Corações 💗**\n"
                        f"Saldo: **{dados[uid]['coracoes']}** 💗 | Convites: **{dados[uid]['fitas']}**\n"
                        f"Fragmentos Hello: {dados[uid]['fragmentos']}",
            color=discord.Color.gold()
        )
        view = LojaView(uid)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Ajuda ❓", style=discord.ButtonStyle.danger, custom_id="ajuda")
    async def ajuda(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🌸 Hello Kitty: Amigos da Sanrio",
            description=(
                "**Bem-vinda!** Monte sua turma com os personagens da Sanrio!\n\n"
                "🎁 Use **convites** para conhecer novos amigos.\n"
                "💗 Converse no servidor para ganhar corações.\n"
                "🛍️ Compre convites na loja.\n"
                "✨ Cada amigo especial tem um poder único.\n"
                "💎 Duplicatas de lendários dão Fragmentos Hello.\n"
                "👑 Junte 100 fragmentos para resgatar a Hello Kitty!"
            ),
            color=discord.Color.from_rgb(255, 192, 203)
        )
        embed.set_image(url="attachment://Hello_kitty.png")
        await interaction.response.send_message(
            embed=embed,
            file=discord.File("Hello_kitty.png"),
            ephemeral=True
        )

# View de ações na turma (Cinnamoroll troca, Hangyodon recicla)
class TurmaAcoesView(View):
    def __init__(self, uid):
        super().__init__(timeout=60)
        self.uid = uid

    @discord.ui.button(label="Trocar 2 duplicatas (Cinnamoroll) 🔄", style=discord.ButtonStyle.primary, custom_id="trocar_cinnamoroll")
    async def trocar_cinnamoroll(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if not tem_efeito(uid, dados, "cinnamoroll"):
            await interaction.response.send_message("🌸 Você não tem o Cinnamoroll para usar essa habilidade.", ephemeral=True)
            return

        contagem = {}
        for nome in dados[uid]["personagens"]:
            contagem[nome] = contagem.get(nome, 0) + 1
        trocaveis = [nome for nome, qtd in contagem.items() if qtd >= 2]
        if not trocaveis:
            await interaction.response.send_message("Você precisa de pelo menos 2 cópias de um amigo.", ephemeral=True)
            return

        nome = trocaveis[0]
        for _ in range(2):
            dados[uid]["personagens"].remove(nome)
        novo = sortear_personagem(uid, dados)
        dados[uid]["personagens"].append(novo["nome"])
        salvar_dados(dados)
        await interaction.response.send_message(f"🔄 Trocou 2× {nome} por **{novo['nome']}**!", ephemeral=True)

    @discord.ui.button(label="Reciclar duplicata (Hangyodon) ♻️", style=discord.ButtonStyle.secondary, custom_id="reciclar_hangyodon")
    async def reciclar_hangyodon(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if not tem_efeito(uid, dados, "hangyodon"):
            await interaction.response.send_message("Você não tem o Hangyodon.", ephemeral=True)
            return

        contagem = {}
        for nome in dados[uid]["personagens"]:
            contagem[nome] = contagem.get(nome, 0) + 1
        duplicatas = [nome for nome, qtd in contagem.items() if qtd > 1]
        if not duplicatas:
            await interaction.response.send_message("Sem duplicatas para reciclar.", ephemeral=True)
            return

        nome = duplicatas[0]
        dados[uid]["personagens"].remove(nome)
        dados[uid]["coracoes"] += 3
        salvar_dados(dados)
        await interaction.response.send_message(f"♻️ Reciclou um {nome} e ganhou 3💗.", ephemeral=True)

# View da loja (compra e possível resgate da Hello Kitty)
class LojaView(View):
    def __init__(self, uid):
        super().__init__(timeout=60)
        self.uid = uid

    @discord.ui.button(label="Comprar Convite 💗", style=discord.ButtonStyle.success, custom_id="comprar_convite")
    async def comprar(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if uid not in dados:
            await interaction.response.send_message("Use o painel primeiro.", ephemeral=True)
            return

        desconto = obter_desconto(uid, dados)
        preco = int(10 * (1 - desconto))
        if dados[uid]["coracoes"] < preco:
            await interaction.response.send_message("💔 Corações insuficientes!", ephemeral=True)
            return

        dados[uid]["coracoes"] -= preco
        dados[uid]["fitas"] += 1
        # Cashback Badtz-Maru
        if tem_efeito(uid, dados, "badtz_maru"):
            dados[uid]["coracoes"] += 5
        salvar_dados(dados)
        msg = f"✨ Convite comprado! Convites: {dados[uid]['fitas']} | Corações: {dados[uid]['coracoes']}"
        if tem_efeito(uid, dados, "badtz_maru"):
            msg += " (+5💗 do Badtz-Maru)"
        await interaction.response.send_message(msg, ephemeral=True)

    @discord.ui.button(label="Resgatar Hello Kitty (100 fragmentos) 👑", style=discord.ButtonStyle.danger, custom_id="resgatar_hello")
    async def resgatar_hello(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if dados[uid].get("fragmentos", 0) < 100:
            await interaction.response.send_message("Você precisa de 100 fragmentos da Hello Kitty.", ephemeral=True)
            return

        dados[uid]["fragmentos"] -= 100
        dados[uid]["personagens"].append("Hello Kitty")
        salvar_dados(dados)
        await interaction.response.send_message("👑✨ Você resgatou a **Hello Kitty**! Parabéns!", ephemeral=True)

# =================== COMANDO SLASH ===================
@bot.tree.command(name="hellokitty", description="Mostra o painel do jogo Hello Kitty: Amigos da Sanrio 🎀")
async def hellokitty(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎀 Hello Kitty: Amigos da Sanrio 🎀",
        description="**Clique nos botões abaixo para jogar!**\n\n"
                    "🎁 Conheça novos amigos.\n"
                    "👥 Veja sua turma e seus poderes.\n"
                    "🛍️ Compre convites na loja.\n"
                    "💎 Junte 100 fragmentos para resgatar a Hello Kitty!",
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
    print(f"🌸 {bot.user} está online com amigos da Sanrio!")
    bot.add_view(MenuPrincipal())
    if GUILD_ID:
        guild = discord.Object(id=int(GUILD_ID))
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"🌷 Comandos sincronizados no servidor {GUILD_ID}")
    else:
        await bot.tree.sync()
        print("🌷 Comandos sincronizados globalmente")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    dados = carregar_dados()
    uid = str(message.author.id)

    # Inicializa jogador se não existir
    if uid not in dados:
        dados[uid] = {
            "coracoes": 20,
            "fitas": fitas_iniciais(uid, dados),
            "personagens": [],
            "fragmentos": 0,
            "msg_count": 0,
            "coracoes_ganhos": 0
        }

    jogador = dados[uid]

    # Contadores de mensagens
    jogador["msg_count"] += 1

    # Efeito Dear Daniel (50 msgs -> +1 convite)
    if tem_efeito(uid, dados, "dear_daniel"):
        if jogador["msg_count"] % 50 == 0:
            jogador["fitas"] += 1

    # Efeito Little Twin Stars (10 msgs -> +1 convite)
    if tem_efeito(uid, dados, "twin_stars"):
        if jogador["msg_count"] % 10 == 0:
            jogador["fitas"] += 1

    # Corações por mensagem
    ganho_coracoes = calcular_coracoes_mensagem(uid, dados)
    jogador["coracoes"] += ganho_coracoes
    jogador["coracoes_ganhos"] += ganho_coracoes

    # Efeito Pochacco (a cada 20 corações ganhos, +1 convite)
    if tem_efeito(uid, dados, "pochacco"):
        if jogador["coracoes_ganhos"] >= 20:
            jogador["fitas"] += 1
            jogador["coracoes_ganhos"] -= 20

    salvar_dados(dados)
    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)