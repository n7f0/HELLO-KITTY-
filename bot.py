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
GUILD_ID = os.getenv("GUILD_ID")
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

# ---------- Personagens com pesos exatos (total 10.000.000) ----------
PERSONAGENS = [
    # Mítico (Hello Kitty)
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

# Comuns (20 personagens, completando 10.000.000)
# Soma necessária: 10.000.000 - 8653 = 9.991.347
# 19 comuns com peso 525.000 = 9.975.000; último com 16.347
# Ajuste para distribuir igual: 20 comuns = 9.991.347 / 20 ≈ 499.567,35
# Faremos 19 com peso 499.567 e o último com 499.567 + ajuste:
# 19 * 499.567 = 9.491.773; falta 499.574 para o último
PERSONAGENS_COMUNS = [
    "Spottie Dottie", "Landry", "Moppu", "Coro Chan", "Minna no Tabo",
    "Charmmy Kitty", "Sugar", "Tiny Chum", "Cathy", "George",
    "Fifi", "Rory", "Lulu", "Pipi", "Nana", "Mimi", "Sasa", "Kiki", "Lala", "Mocha"
]
# Existem 20 nomes, então:
peso_comum_base = 499567
for i, nome in enumerate(PERSONAGENS_COMUNS):
    if i < 19:
        peso = peso_comum_base
    else:
        # Último: complemento para exatamente 9.991.347
        peso = 9991347 - (19 * peso_comum_base)  # = 9991347 - 9.491.773 = 499.574
    PERSONAGENS.append({"nome": nome, "peso": peso, "raridade": "Comum", "efeito": None})

# Verificação final
TOTAL_PESOS = sum(p["peso"] for p in PERSONAGENS)
assert TOTAL_PESOS == 10000000, f"Pesos não somam 10.000.000! ({TOTAL_PESOS})"

# Personagem Ultimate (Nenê) – chance separada: 0,000000001% (1 em 100 bilhões)
NENE = {"nome": "Nenê", "raridade": "Ultimate", "efeito": "nene"}
CHANCE_NENE = 1e-11  # 0,000000001% = 1/100 bilhões

# ---------- Descrições de efeitos ----------
DESCRICAO_EFEITOS = {
    "hello_kitty": "+2💗/msg, 20% desc., 10% frag. extra",
    "dear_daniel": "+1 convite a cada 50 msgs",
    "my_melody": "10% desc. na loja",
    "kuromi": "+15% chance Épico+",
    "pompompurin": "50% não gastar convite",
    "cinnamoroll": "Troca 2 duplicatas por 1 novo",
    "twin_stars": "+1 convite a cada 10 msgs",
    "keroppi": "Começa com 5 convites",
    "badtz_maru": "+5💗 ao comprar",
    "tuxedo_sam": "30% +1 convite ao conhecer",
    "pochacco": "+1 convite a cada 20💗 ganhos",
    "chococat": "20% duplicar amigo encontrado",
    "hangyodon": "Reciclar duplicata = 3💗",
    "pekkle": "+5% chance Incomum+",
    "nene": "+5💗/msg, 50% desc., 50% frag. extra, +3 convites a cada 5 msgs"
}

# ---------- Funções auxiliares ----------
def tem_efeito(uid, dados, efeito_nome):
    if uid not in dados:
        return False
    for nome in set(dados[uid]["personagens"]):
        for p in PERSONAGENS:
            if p["nome"] == nome and p.get("efeito") == efeito_nome:
                return True
    # Nenê é tratada separadamente
    if efeito_nome == "nene" and "Nenê" in dados[uid].get("personagens", []):
        return True
    return False

def obter_desconto(uid, dados):
    desc = 0.0
    if tem_efeito(uid, dados, "my_melody"):
        desc = max(desc, 0.10)
    if tem_efeito(uid, dados, "hello_kitty"):
        desc = max(desc, 0.20)
    if tem_efeito(uid, dados, "nene"):
        desc = max(desc, 0.50)
    return desc

def calcular_coracoes_mensagem(uid, dados):
    base = 1
    if tem_efeito(uid, dados, "hello_kitty"):
        base += 2
    if tem_efeito(uid, dados, "nene"):
        base += 5
    return base

def fitas_iniciais(uid, dados):
    return 5 if tem_efeito(uid, dados, "keroppi") else 3

# ---------- Sorteio normal (com modificadores) ----------
def sortear_personagem(uid, dados):
    # Modificadores de Kuromi e Pekkle
    multiplicadores = {}
    if tem_efeito(uid, dados, "kuromi"):
        for p in PERSONAGENS:
            if p["raridade"] in ("Épico", "Lendário", "Mítico"):
                multiplicadores[p["nome"]] = 1.15
    if tem_efeito(uid, dados, "pekkle"):
        for p in PERSONAGENS:
            if p["raridade"] in ("Incomum", "Raro", "Épico", "Lendário", "Mítico"):
                multiplicadores[p["nome"]] = multiplicadores.get(p["nome"], 1.0) * 1.05

    pesos = []
    for p in PERSONAGENS:
        w = p["peso"]
        if p["nome"] in multiplicadores:
            w = int(w * multiplicadores[p["nome"]])
        pesos.append(w)

    total = sum(pesos)
    rolagem = random.randint(1, total)
    acumulado = 0
    for i, p in enumerate(PERSONAGENS):
        acumulado += pesos[i]
        if rolagem <= acumulado:
            return p
    return PERSONAGENS[0]

# =================== VIEW PRINCIPAL ===================
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
        if dados[uid]["fitas"] <= 0:
            await interaction.response.send_message("🌸 Sem convites! Compre na loja.", ephemeral=True)
            return

        gastar = True
        if tem_efeito(uid, dados, "pompompurin") and random.random() < 0.5:
            gastar = False
        if gastar:
            dados[uid]["fitas"] -= 1

        # Verifica Nenê (1 em 100 bilhões)
        if random.random() < CHANCE_NENE:
            personagem = NENE
            # Adiciona o efeito poderoso
            dados[uid]["personagens"].append("Nenê")
            salvar_dados(dados)
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="💫 IMPOSSÍVEL! 💫",
                    description="**Nenê** apareceu!\nRaridade: **Ultimate**\n"
                                "✨ Efeito: +5💗/msg, 50% desc., 50% frag. extra, +3 convites/5 msgs",
                    color=discord.Color.gold()
                ),
                ephemeral=False
            )
            return

        # Sorteio normal
        personagem = sortear_personagem(uid, dados)
        duplicar = tem_efeito(uid, dados, "chococat") and random.random() < 0.20
        dados[uid]["personagens"].append(personagem["nome"])
        if duplicar:
            dados[uid]["personagens"].append(personagem["nome"])

        # Fragmentos por duplicata Lendário/Mítico
        if dados[uid]["personagens"].count(personagem["nome"]) > 1:
            if personagem["raridade"] == "Mítico":
                dados[uid]["fragmentos"] += 10
            elif personagem["raridade"] == "Lendário":
                dados[uid]["fragmentos"] += 1

        if tem_efeito(uid, dados, "tuxedo_sam") and random.random() < 0.30:
            dados[uid]["fitas"] += 1
        if tem_efeito(uid, dados, "hello_kitty") and random.random() < 0.10:
            dados[uid]["fragmentos"] += 1
        if tem_efeito(uid, dados, "nene") and random.random() < 0.50:
            dados[uid]["fragmentos"] += 1

        salvar_dados(dados)

        msg = ""
        if not gastar:
            msg += "\n🍮 Pompompurin poupou seu convite!"
        if duplicar:
            msg += "\n🐱 Chococat duplicou!"

        embed = discord.Embed(
            title="🎁 Novo Amigo!",
            description=f"**{personagem['nome']}**\nRaridade: {personagem['raridade']}\n"
                        f"Efeito: {DESCRICAO_EFEITOS.get(personagem['efeito'], 'Nenhum')}{msg}",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        embed.set_footer(text=f"Convites: {dados[uid]['fitas']} | 💗: {dados[uid]['coracoes']} | Fragmentos: {dados[uid]['fragmentos']}")
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @discord.ui.button(label="Minha Turma 👥", style=discord.ButtonStyle.primary, custom_id="turma")
    async def turma(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if uid not in dados or not dados[uid]["personagens"]:
            await interaction.response.send_message("👥 Sua turma está vazia!", ephemeral=True)
            return

        contagem = {}
        for nome in dados[uid]["personagens"]:
            contagem[nome] = contagem.get(nome, 0) + 1

        desc = ""
        for nome, qtd in contagem.items():
            efeito = next((p["efeito"] for p in PERSONAGENS if p["nome"] == nome), None)
            if nome == "Nenê":
                efeito = "nene"
            desc_efeito = DESCRICAO_EFEITOS.get(efeito, "—")
            desc += f"{nome} ×{qtd}  [{desc_efeito}]\n"

        embed = discord.Embed(
            title="👥 Sua Turma da Sanrio",
            description=desc,
            color=discord.Color.from_rgb(255, 105, 180)
        )
        embed.set_footer(text=f"Total: {len(dados[uid]['personagens'])} | Fragmentos: {dados[uid].get('fragmentos', 0)}")
        view = TurmaAcoesView(uid)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Loja 🛍️", style=discord.ButtonStyle.secondary, custom_id="loja")
    async def loja(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if uid not in dados:
            dados[uid] = {"coracoes": 20, "fitas": fitas_iniciais(uid, dados), "personagens": [], "fragmentos": 0, "msg_count": 0, "coracoes_ganhos": 0}
            salvar_dados(dados)

        desconto = obter_desconto(uid, dados)
        preco = max(1, int(10 * (1 - desconto)))  # mínimo 1
        embed = discord.Embed(
            title="🛍️ Loja de Convites",
            description=f"**1 Convite = {preco}💗**\nSaldo: {dados[uid]['coracoes']}💗 | Convites: {dados[uid]['fitas']}\nFragmentos: {dados[uid]['fragmentos']}",
            color=discord.Color.gold()
        )
        view = LojaView(uid)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Ajuda ❓", style=discord.ButtonStyle.danger, custom_id="ajuda")
    async def ajuda(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🌸 Hello Kitty: Amigos da Sanrio",
            description=(
                "🎁 **Conhecer Amigo** gasta um convite.\n"
                "💗 Ganhe corações conversando no servidor.\n"
                "👑 Hello Kitty (0,00001%) é Mítico.\n"
                "💫 Nenê (0,000000001%) é Ultimate, quase impossível!\n"
                "💎 Fragmentos Hello permitem resgatar a Hello Kitty."
            ),
            color=discord.Color.from_rgb(255, 192, 203)
        )
        embed.set_image(url="attachment://Hello_kitty.png")
        await interaction.response.send_message(embed=embed, file=discord.File("Hello_kitty.png"), ephemeral=True)

class TurmaAcoesView(View):
    def __init__(self, uid):
        super().__init__(timeout=60)
        self.uid = uid

    @discord.ui.button(label="Trocar 2 duplicatas (Cinnamoroll) 🔄", style=discord.ButtonStyle.primary)
    async def trocar(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if not tem_efeito(uid, dados, "cinnamoroll"):
            await interaction.response.send_message("🌸 Você não tem o Cinnamoroll.", ephemeral=True)
            return

        contagem = {}
        for nome in dados[uid]["personagens"]:
            contagem[nome] = contagem.get(nome, 0) + 1
        trocaveis = [nome for nome, qtd in contagem.items() if qtd >= 2]
        if not trocaveis:
            await interaction.response.send_message("Sem 2 cópias de um mesmo amigo.", ephemeral=True)
            return

        nome = trocaveis[0]
        for _ in range(2):
            dados[uid]["personagens"].remove(nome)
        novo = sortear_personagem(uid, dados)
        dados[uid]["personagens"].append(novo["nome"])
        salvar_dados(dados)
        await interaction.response.send_message(f"🔄 Trocou 2× {nome} por {novo['nome']}!", ephemeral=True)

    @discord.ui.button(label="Reciclar duplicata (Hangyodon) ♻️", style=discord.ButtonStyle.secondary)
    async def reciclar(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if not tem_efeito(uid, dados, "hangyodon"):
            await interaction.response.send_message("Você não tem o Hangyodon.", ephemeral=True)
            return

        contagem = {}
        for nome in dados[uid]["personagens"]:
            contagem[nome] = contagem.get(nome, 0) + 1
        dups = [nome for nome, qtd in contagem.items() if qtd > 1]
        if not dups:
            await interaction.response.send_message("Sem duplicatas.", ephemeral=True)
            return
        nome = dups[0]
        dados[uid]["personagens"].remove(nome)
        dados[uid]["coracoes"] += 3
        salvar_dados(dados)
        await interaction.response.send_message(f"♻️ {nome} reciclado, +3💗.", ephemeral=True)

class LojaView(View):
    def __init__(self, uid):
        super().__init__(timeout=60)
        self.uid = uid

    @discord.ui.button(label="Comprar Convite 💗", style=discord.ButtonStyle.success)
    async def comprar(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if uid not in dados:
            await interaction.response.send_message("Use /hellokitty primeiro.", ephemeral=True)
            return
        desconto = obter_desconto(uid, dados)
        preco = max(1, int(10 * (1 - desconto)))
        if dados[uid]["coracoes"] < preco:
            await interaction.response.send_message("💔 Corações insuficientes!", ephemeral=True)
            return
        dados[uid]["coracoes"] -= preco
        dados[uid]["fitas"] += 1
        if tem_efeito(uid, dados, "badtz_maru"):
            dados[uid]["coracoes"] += 5
        if tem_efeito(uid, dados, "nene"):
            dados[uid]["coracoes"] += 5  # bônus extra da Nenê
        salvar_dados(dados)
        await interaction.response.send_message(
            f"✨ Convite comprado! Convites: {dados[uid]['fitas']} | 💗: {dados[uid]['coracoes']}",
            ephemeral=True
        )

    @discord.ui.button(label="Resgatar Hello Kitty (100 frags) 👑", style=discord.ButtonStyle.danger)
    async def resgatar(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if dados[uid].get("fragmentos", 0) < 100:
            await interaction.response.send_message("Precisa de 100 fragmentos.", ephemeral=True)
            return
        dados[uid]["fragmentos"] -= 100
        dados[uid]["personagens"].append("Hello Kitty")
        salvar_dados(dados)
        await interaction.response.send_message("👑✨ Hello Kitty resgatada!", ephemeral=True)

# =================== COMANDO SLASH ===================
@bot.tree.command(name="hellokitty", description="Abre o painel do jogo Hello Kitty: Amigos da Sanrio 🎀")
async def hellokitty(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎀 Hello Kitty: Amigos da Sanrio 🎀",
        description="**Clique nos botões abaixo para jogar!**\n"
                    "🎁 Conheça amigos, colecione e use seus poderes!\n"
                    "💫 Nenê é quase impossível... mas existe!",
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
    print(f"🌸 {bot.user} online!")
    bot.add_view(MenuPrincipal())
    if GUILD_ID:
        guild = discord.Object(id=int(GUILD_ID))
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"🌷 Comandos sincronizados em {GUILD_ID}")
    else:
        await bot.tree.sync()
        print("🌷 Comandos sincronizados globalmente")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    dados = carregar_dados()
    uid = str(message.author.id)

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
    jogador["msg_count"] += 1

    # Efeitos de convite por mensagens
    if tem_efeito(uid, dados, "dear_daniel") and jogador["msg_count"] % 50 == 0:
        jogador["fitas"] += 1
    if tem_efeito(uid, dados, "twin_stars") and jogador["msg_count"] % 10 == 0:
        jogador["fitas"] += 1
    # Nenê: +3 convites a cada 5 mensagens
    if tem_efeito(uid, dados, "nene") and jogador["msg_count"] % 5 == 0:
        jogador["fitas"] += 3

    ganho = calcular_coracoes_mensagem(uid, dados)
    jogador["coracoes"] += ganho
    jogador["coracoes_ganhos"] += ganho

    if tem_efeito(uid, dados, "pochacco") and jogador["coracoes_ganhos"] >= 20:
        jogador["fitas"] += 1
        jogador["coracoes_ganhos"] -= 20

    salvar_dados(dados)
    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)