import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput
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
intents.members = True  # para listar membros do servidor
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

# ---------- Efeitos e descrições ----------
EFEITOS_DESC = {
    # Mítico / Ultimate / Lendários / Épicos / Raros / Incomuns (já existentes)
    "hello_kitty": "+2💗/msg, 20% desc., 10% frag extra",
    "dear_daniel": "+1 🍬 a cada 50 msgs",
    "my_melody": "10% desc. na loja",
    "kuromi": "+15% chance Épico+",
    "pompompurin": "50% não gastar 🍬",
    "cinnamoroll": "Troca 2 duplicatas por 1 novo",
    "twin_stars": "+1 🍬 a cada 10 msgs",
    "keroppi": "Começa com 5 🍬",
    "badtz_maru": "+5💗 ao comprar 🍬",
    "tuxedo_sam": "30% +1 🍬 ao fazer amizade",
    "pochacco": "+1 🍬 a cada 20💗 ganhos",
    "chococat": "20% duplicar amigo encontrado",
    "hangyodon": "Reciclar duplicata = 3💗",
    "pekkle": "+5% chance Incomum+",
    "nene": "+5💗/msg, 50% desc., 50% frag extra, +3 🍬/5 msgs",
    # Comuns (20 efeitos únicos)
    "spottie_dottie": "+1💗 a cada 15 msgs",
    "landry": "5% de duplicar amigo encontrado",
    "moppu": "3% de desconto na loja",
    "coro_chan": "5% de ganhar 1 fragmento extra",
    "minna_tabo": "10% de não gastar 🍬",
    "charmmy_kitty": "+1 🍬 inicial",
    "sugar": "5% de ganhar +1🍬 ao comprar",
    "tiny_chum": "+2💗 inicial",
    "cathy": "2% de chance Épico+",
    "george": "+1 fragmento a cada 100 msgs",
    "fifi": "+1💗 a cada 20 msgs",
    "rory": "5% de ganhar +1🍬 ao fazer amizade",
    "lulu": "1% de desconto extra",
    "pipi": "+1🍬 a cada 80 msgs",
    "nana": "+1💗 a cada 25 msgs",
    "mimi": "5% de receber 1💗 extra ao comprar",
    "sasa": "+1 fragmento a cada 50 msgs",
    "kiki": "2% de duplicar",
    "lala": "10% de ganhar +1💗 ao fazer amizade",
    "mocha": "+1🍬 a cada 60 msgs"
}

# ---------- Personagens ----------
PERSONAGENS = [
    {"nome": "Hello Kitty",           "peso": 1,        "raridade": "Mítico",   "efeito": "hello_kitty"},
    {"nome": "Dear Daniel",           "peso": 2,        "raridade": "Lendário", "efeito": "dear_daniel"},
    {"nome": "My Melody",             "peso": 5,        "raridade": "Lendário", "efeito": "my_melody"},
    {"nome": "Kuromi",                "peso": 5,        "raridade": "Lendário", "efeito": "kuromi"},
    {"nome": "Pompompurin",           "peso": 10,       "raridade": "Épico",    "efeito": "pompompurin"},
    {"nome": "Cinnamoroll",           "peso": 10,       "raridade": "Épico",    "efeito": "cinnamoroll"},
    {"nome": "Little Twin Stars",     "peso": 20,       "raridade": "Épico",    "efeito": "twin_stars"},
    {"nome": "Keroppi",               "peso": 200,      "raridade": "Raro",     "efeito": "keroppi"},
    {"nome": "Badtz-Maru",            "peso": 200,      "raridade": "Raro",     "efeito": "badtz_maru"},
    {"nome": "Tuxedo Sam",            "peso": 200,      "raridade": "Raro",     "efeito": "tuxedo_sam"},
    {"nome": "Pochacco",              "peso": 2000,     "raridade": "Incomum",  "efeito": "pochacco"},
    {"nome": "Chococat",              "peso": 2000,     "raridade": "Incomum",  "efeito": "chococat"},
    {"nome": "Hangyodon",             "peso": 2000,     "raridade": "Incomum",  "efeito": "hangyodon"},
    {"nome": "Pekkle",                "peso": 2000,     "raridade": "Incomum",  "efeito": "pekkle"},
]
# Comuns (20 personagens com efeitos individuais)
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

TOTAL_PESOS = sum(p["peso"] for p in PERSONAGENS)
assert TOTAL_PESOS == 10000000, f"Pesos errados: {TOTAL_PESOS}"

NENE = {"nome": "Nenê", "raridade": "Ultimate", "efeito": "nene"}
CHANCE_NENE = 1e-11

# ---------- Funções auxiliares ----------
def tem_efeito(uid, dados, efeito_nome):
    if uid not in dados:
        return False
    for nome in set(dados[uid]["personagens"]):
        for p in PERSONAGENS:
            if p["nome"] == nome and p["efeito"] == efeito_nome:
                return True
        if nome == "Nenê" and efeito_nome == "nene":
            return True
    return False

def obter_desconto(uid, dados):
    desc = 0.0
    if tem_efeito(uid, dados, "my_melody"): desc += 0.10
    if tem_efeito(uid, dados, "hello_kitty"): desc += 0.20
    if tem_efeito(uid, dados, "nene"): desc += 0.50
    if tem_efeito(uid, dados, "moppu"): desc += 0.03
    if tem_efeito(uid, dados, "lulu"): desc += 0.01
    return min(desc, 0.9)  # máximo 90% de desconto

def calcular_coracoes_mensagem(uid, dados):
    base = 1
    if tem_efeito(uid, dados, "hello_kitty"): base += 2
    if tem_efeito(uid, dados, "nene"): base += 5
    if tem_efeito(uid, dados, "spottie_dottie"): base += 1 if dados[uid]["msg_count"] % 15 == 0 else 0
    if tem_efeito(uid, dados, "fifi"): base += 1 if dados[uid]["msg_count"] % 20 == 0 else 0
    if tem_efeito(uid, dados, "nana"): base += 1 if dados[uid]["msg_count"] % 25 == 0 else 0
    return base

def doces_iniciais(uid, dados):
    doces = 3
    if tem_efeito(uid, dados, "keroppi"): doces = 5
    if tem_efeito(uid, dados, "charmmy_kitty"): doces += 1
    return doces

def sortear_personagem(uid, dados):
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

    @discord.ui.button(label="Visitar o Café ☕", style=discord.ButtonStyle.success, custom_id="visitar_cafe")
    async def visitar_cafe(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if uid not in dados:
            dados[uid] = {
                "coracoes": 20,
                "doces": doces_iniciais(uid, dados),
                "personagens": [],
                "fragmentos": 0,
                "msg_count": 0,
                "coracoes_ganhos": 0,
                "cafe_count": 0  # contador de visitas
            }
        if dados[uid]["doces"] <= 0:
            await interaction.response.send_message("🌸 Você não tem Doces Mágicos 🍬! Compre na Loja do Café.", ephemeral=True)
            return

        gastar = True
        if tem_efeito(uid, dados, "pompompurin") and random.random() < 0.5:
            gastar = False
        if tem_efeito(uid, dados, "minna_tabo") and random.random() < 0.10:
            gastar = False
        if gastar:
            dados[uid]["doces"] -= 1

        # Nenê
        if random.random() < CHANCE_NENE:
            personagem = NENE
            dados[uid]["personagens"].append("Nenê")
            salvar_dados(dados)
            await interaction.response.send_message(
                embed=discord.Embed(title="💫 IMPOSSÍVEL! 💫", description="**Nenê** apareceu!\nRaridade: Ultimate\nEfeito: +5💗/msg, 50% desc., 50% frag extra, +3 🍬/5 msgs", color=discord.Color.gold()), ephemeral=False)
            return

        personagem = sortear_personagem(uid, dados)
        duplicar = False
        if tem_efeito(uid, dados, "chococat") and random.random() < 0.20:
            duplicar = True
        if tem_efeito(uid, dados, "landry") and random.random() < 0.05:
            duplicar = True
        if tem_efeito(uid, dados, "kiki") and random.random() < 0.02:
            duplicar = True

        dados[uid]["personagens"].append(personagem["nome"])
        if duplicar:
            dados[uid]["personagens"].append(personagem["nome"])

        # Fragmentos
        if dados[uid]["personagens"].count(personagem["nome"]) > 1:
            if personagem["raridade"] == "Mítico":
                dados[uid]["fragmentos"] += 10
            elif personagem["raridade"] == "Lendário":
                dados[uid]["fragmentos"] += 1

        if tem_efeito(uid, dados, "tuxedo_sam") and random.random() < 0.30:
            dados[uid]["doces"] += 1
        if tem_efeito(uid, dados, "hello_kitty") and random.random() < 0.10:
            dados[uid]["fragmentos"] += 1
        if tem_efeito(uid, dados, "nene") and random.random() < 0.50:
            dados[uid]["fragmentos"] += 1
        if tem_efeito(uid, dados, "coro_chan") and random.random() < 0.05:
            dados[uid]["fragmentos"] += 1
        if tem_efeito(uid, dados, "george") and dados[uid]["msg_count"] % 100 == 0:
            dados[uid]["fragmentos"] += 1
        if tem_efeito(uid, dados, "sasa") and dados[uid]["msg_count"] % 50 == 0:
            dados[uid]["fragmentos"] += 1
        if tem_efeito(uid, dados, "rory") and random.random() < 0.05:
            dados[uid]["doces"] += 1
        if tem_efeito(uid, dados, "lala") and random.random() < 0.10:
            dados[uid]["coracoes"] += 1

        dados[uid]["cafe_count"] += 1
        salvar_dados(dados)

        msg = ""
        if not gastar:
            msg += "\n🍮 Pompompurin/Minna no Tabo salvou seu doce!"
        if duplicar:
            msg += "\n🐱 Chococat/Landry/Kiki duplicou!"

        embed = discord.Embed(
            title="☕ Novo amigo no Café!",
            description=f"**{personagem['nome']}**\nRaridade: {personagem['raridade']}\nEfeito: {EFEITOS_DESC.get(personagem['efeito'], 'Nenhum')}{msg}",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        embed.set_footer(text=f"Doces: {dados[uid]['doces']} 🍬 | 💗: {dados[uid]['coracoes']} | Fragmentos Hello: {dados[uid]['fragmentos']}")
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
            if nome == "Nenê": efeito = "nene"
            desc_efeito = EFEITOS_DESC.get(efeito, "—")
            desc += f"{nome} ×{qtd}  [{desc_efeito}]\n"
        embed = discord.Embed(title="👥 Turma do HELLO KITTY Café", description=desc, color=discord.Color.from_rgb(255, 105, 180))
        embed.set_footer(text=f"Total: {len(dados[uid]['personagens'])} | Fragmentos: {dados[uid].get('fragmentos', 0)}")
        await interaction.response.send_message(embed=embed, view=TurmaAcoesView(uid), ephemeral=True)

    @discord.ui.button(label="Cardápio de Amigos 📖", style=discord.ButtonStyle.secondary, custom_id="cardapio")
    async def cardapio(self, interaction: discord.Interaction, button: Button):
        all_chars = PERSONAGENS + [NENE]
        pages = []
        for i in range(0, len(all_chars), 10):
            chunk = all_chars[i:i+10]
            desc = ""
            for p in chunk:
                efeito = EFEITOS_DESC.get(p["efeito"], "—")
                desc += f"**{p['nome']}** ({p['raridade']}) - {efeito}\n"
            embed = discord.Embed(title="📖 Cardápio de Amigos do Café", description=desc, color=discord.Color.from_rgb(255, 218, 185))
            embed.set_footer(text=f"Página {len(pages)+1}/{(len(all_chars)-1)//10+1}")
            pages.append(embed)
        if not pages:
            await interaction.response.send_message("Nenhum amigo no cardápio.", ephemeral=True)
            return
        await interaction.response.send_message(embed=pages[0], view=PaginaView(pages, 0), ephemeral=True)

    @discord.ui.button(label="Loja do Café 🛍️", style=discord.ButtonStyle.primary, custom_id="loja_cafe")
    async def loja(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if uid not in dados:
            dados[uid] = {"coracoes": 20, "doces": doces_iniciais(uid, dados), "personagens": [], "fragmentos": 0, "msg_count": 0, "coracoes_ganhos": 0, "cafe_count": 0}
            salvar_dados(dados)

        desconto = obter_desconto(uid, dados)
        preco_doce = max(1, int(10 * (1 - desconto)))
        preco_cupom = max(5, int(50 * (1 - desconto)))  # Cupom da Sorte: aumenta chance de raridade por 1 hora (simplificado como 1 doce de alta qualidade)
        preco_supremo = max(20, int(200 * (1 - desconto)))  # Doce Supremo: chance muito alta de Lendário+
        embed = discord.Embed(
            title="🛍️ Loja do HELLO KITTY Café",
            description=(
                f"**Produtos:**\n"
                f"🍬 Doce Mágico – **{preco_doce}💗** (use para visitar o café)\n"
                f"🍀 Cupom da Sorte – **{preco_cupom}💗** (próximo amigo terá 2x mais chance de ser raro!)\n"
                f"🌟 Doce Supremo – **{preco_supremo}💗** (garante raridade Épico ou superior)\n"
                f"👑 Resgatar Hello Kitty – **100 fragmentos**\n"
                f"🤝 Trocar com amigo – **grátis**\n\n"
                f"Seu saldo: **{dados[uid]['coracoes']}💗** | Doces: **{dados[uid]['doces']}🍬** | Fragmentos: **{dados[uid]['fragmentos']}**"
            ),
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, view=LojaCafeView(uid), ephemeral=True)

    @discord.ui.button(label="Ajuda ❓", style=discord.ButtonStyle.danger, custom_id="ajuda_cafe")
    async def ajuda(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🌸 HELLO KITTY Café – Como Jogar",
            description=(
                "☕ **Visitar o Café** gasta um Doce Mágico 🍬 e traz um amigo aleatório.\n"
                "💗 Ganhe corações conversando no servidor.\n"
                "🛍️ Compre doces, cupons e doces supremos na Loja.\n"
                "👑 Hello Kitty (0,00001%) é Mítico. Nenê (0,000000001%) é Ultimate.\n"
                "💎 Fragmentos Hello (100) resgatam a Hello Kitty.\n"
                "🤝 Use a Loja para trocar personagens com amigos de forma segura."
            ),
            color=discord.Color.from_rgb(255, 192, 203)
        )
        embed.set_image(url="attachment://Hello_kitty.png")
        await interaction.response.send_message(embed=embed, file=discord.File("Hello_kitty.png"), ephemeral=True)

# Paginação
class PaginaView(View):
    def __init__(self, pages, current):
        super().__init__(timeout=60)
        self.pages = pages
        self.current = current
        self.children[0].disabled = current == 0
        self.children[1].disabled = current == len(pages) - 1

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

    def update_buttons(self):
        self.children[0].disabled = self.current == 0
        self.children[1].disabled = self.current == len(self.pages) - 1

class TurmaAcoesView(View):
    def __init__(self, uid):
        super().__init__(timeout=60)
        self.uid = uid

    @discord.ui.button(label="Trocar 2 duplicatas (Cinnamoroll) 🔄", style=discord.ButtonStyle.primary)
    async def trocar_cinnamoroll(self, interaction: discord.Interaction, button: Button):
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
            await interaction.response.send_message("Sem 2 cópias.", ephemeral=True)
            return
        nome = trocaveis[0]
        for _ in range(2):
            dados[uid]["personagens"].remove(nome)
        novo = sortear_personagem(uid, dados)
        dados[uid]["personagens"].append(novo["nome"])
        salvar_dados(dados)
        await interaction.response.send_message(f"🔄 2× {nome} → {novo['nome']}!", ephemeral=True)

    @discord.ui.button(label="Reciclar duplicata (Hangyodon) ♻️", style=discord.ButtonStyle.secondary)
    async def reciclar(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if not tem_efeito(uid, dados, "hangyodon"):
            await interaction.response.send_message("Sem Hangyodon.", ephemeral=True)
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
        await interaction.response.send_message(f"♻️ {nome} → +3💗", ephemeral=True)

class LojaCafeView(View):
    def __init__(self, uid):
        super().__init__(timeout=60)
        self.uid = uid

    @discord.ui.button(label="Comprar Doce 🍬", style=discord.ButtonStyle.success)
    async def comprar_doce(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        desconto = obter_desconto(uid, dados)
        preco = max(1, int(10 * (1 - desconto)))
        if dados[uid]["coracoes"] < preco:
            await interaction.response.send_message("💔 Corações insuficientes!", ephemeral=True)
            return
        dados[uid]["coracoes"] -= preco
        dados[uid]["doces"] += 1
        if tem_efeito(uid, dados, "badtz_maru"): dados[uid]["coracoes"] += 5
        if tem_efeito(uid, dados, "nene"): dados[uid]["coracoes"] += 5
        if tem_efeito(uid, dados, "sugar") and random.random() < 0.05: dados[uid]["doces"] += 1
        if tem_efeito(uid, dados, "mimi") and random.random() < 0.05: dados[uid]["coracoes"] += 1
        salvar_dados(dados)
        await interaction.response.send_message(f"✨ Doce comprado! 🍬: {dados[uid]['doces']} | 💗: {dados[uid]['coracoes']}", ephemeral=True)

    @discord.ui.button(label="Cupom da Sorte 🍀", style=discord.ButtonStyle.primary)
    async def cupom_sorte(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        preco = max(5, int(50 * (1 - obter_desconto(uid, dados))))
        if dados[uid]["coracoes"] < preco:
            await interaction.response.send_message("💔 Corações insuficientes!", ephemeral=True)
            return
        dados[uid]["coracoes"] -= preco
        # Efeito: flag "sorte_ativa" para próxima visita (simplificado: já aumenta chance em sortear_personagem)
        dados[uid]["sorte_ativa"] = True  # será consumido na próxima visita
        salvar_dados(dados)
        await interaction.response.send_message("🍀 Cupom da Sorte ativado! Sua próxima visita terá o dobro de chance para amigos raros.", ephemeral=True)

    @discord.ui.button(label="Doce Supremo 🌟", style=discord.ButtonStyle.success)
    async def doce_supremo(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        preco = max(20, int(200 * (1 - obter_desconto(uid, dados))))
        if dados[uid]["coracoes"] < preco:
            await interaction.response.send_message("💔 Corações insuficientes!", ephemeral=True)
            return
        dados[uid]["coracoes"] -= preco
        # Força raridade Épico ou superior
        # Simula sorteio apenas entre Épico+
        pool = [p for p in PERSONAGENS if p["raridade"] in ("Épico", "Lendário", "Mítico")]
        personagem = random.choice(pool)
        dados[uid]["personagens"].append(personagem["nome"])
        salvar_dados(dados)
        await interaction.response.send_message(f"🌟 Doce Supremo usado! Você recebeu **{personagem['nome']}** ({personagem['raridade']})!", ephemeral=False)

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

    @discord.ui.button(label="Trocar com Amigo 🤝", style=discord.ButtonStyle.secondary)
    async def trocar_amigo(self, interaction: discord.Interaction, button: Button):
        # Primeiro pede para escolher o personagem que quer oferecer (modal com select)
        dados = carregar_dados()
        uid = str(interaction.user.id)
        personagens = list(set(dados[uid]["personagens"]))
        if not personagens:
            await interaction.response.send_message("Você não tem personagens para trocar.", ephemeral=True)
            return
        options = [discord.SelectOption(label=nome, value=nome) for nome in personagens[:25]]
        select = Select(placeholder="Escolha um personagem para oferecer...", options=options)
        async def select_callback(interaction_select: discord.Interaction):
            personagem_oferecido = select.values[0]
            # Agora seleciona o amigo (lista de membros do servidor)
            membros = [m for m in interaction.guild.members if not m.bot and m.id != interaction.user.id]
            if not membros:
                await interaction_select.response.send_message("Nenhum amigo disponível no servidor.", ephemeral=True)
                return
            membro_options = [discord.SelectOption(label=m.display_name, value=str(m.id)) for m in membros[:25]]
            select_membro = Select(placeholder="Escolha um amigo...", options=membro_options)
            async def membro_callback(interaction_membro: discord.Interaction):
                alvo_id = select_membro.values[0]
                alvo_user = await bot.fetch_user(int(alvo_id))
                # Salva pedido de troca
                trocas_pendentes[uid] = {"alvo": alvo_id, "personagem": personagem_oferecido}
                # Envia notificação ao alvo
                embed = discord.Embed(
                    title="🤝 Proposta de Troca no Café!",
                    description=f"{interaction.user.mention} quer trocar **{personagem_oferecido}** com você!",
                    color=discord.Color.green()
                )
                view = AceitarRecusarView(uid, alvo_id, personagem_oferecido)
                await interaction.channel.send(content=alvo_user.mention, embed=embed, view=view)
                await interaction_membro.response.send_message("✅ Pedido de troca enviado!", ephemeral=True)
            select_membro.callback = membro_callback
            view_membro = View(timeout=60)
            view_membro.add_item(select_membro)
            await interaction_select.response.send_message("Agora escolha o amigo:", view=view_membro, ephemeral=True)
        select.callback = select_callback
        view_select = View(timeout=60)
        view_select.add_item(select)
        await interaction.response.send_message("Escolha o personagem que deseja oferecer:", view=view_select, ephemeral=True)

# View de aceitar/recusar troca (para o alvo)
class AceitarRecusarView(View):
    def __init__(self, solicitante_id, alvo_id, personagem_oferecido):
        super().__init__(timeout=120)
        self.solicitante_id = solicitante_id
        self.alvo_id = alvo_id
        self.personagem_oferecido = personagem_oferecido

    @discord.ui.button(label="Aceitar ✅", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != self.alvo_id:
            await interaction.response.send_message("❌ Esta troca não é para você.", ephemeral=True)
            return
        dados = carregar_dados()
        # Verifica se solicitante ainda tem o personagem
        if self.personagem_oferecido not in dados[self.solicitante_id]["personagens"]:
            await interaction.response.send_message("❌ O amigo não tem mais esse personagem.", ephemeral=True)
            return
        # Pede para o alvo escolher um personagem seu
        personagens_alvo = list(set(dados[self.alvo_id]["personagens"]))
        if not personagens_alvo:
            await interaction.response.send_message("Você não tem personagens para oferecer.", ephemeral=True)
            return
        options = [discord.SelectOption(label=nome, value=nome) for nome in personagens_alvo[:25]]
        select = Select(placeholder="Escolha um personagem seu para oferecer...", options=options)
        async def select_alvo_callback(interaction_select: discord.Interaction):
            personagem_alvo = select.values[0]
            # Realiza a troca
            dados[self.solicitante_id]["personagens"].remove(self.personagem_oferecido)
            dados[self.alvo_id]["personagens"].remove(personagem_alvo)
            dados[self.solicitante_id]["personagens"].append(personagem_alvo)
            dados[self.alvo_id]["personagens"].append(self.personagem_oferecido)
            salvar_dados(dados)
            trocas_pendentes.pop(self.solicitante_id, None)
            await interaction_select.response.send_message(
                f"✅ Troca concluída! {interaction_select.user.mention} deu **{personagem_alvo}** e recebeu **{self.personagem_oferecido}** de <@{self.solicitante_id}>.",
                ephemeral=False
            )
            self.disable_all_items()
            await interaction.message.edit(view=self)
        select.callback = select_alvo_callback
        view_select = View(timeout=60)
        view_select.add_item(select)
        await interaction.response.send_message("Escolha qual personagem oferecer em troca:", view=view_select, ephemeral=True)

    @discord.ui.button(label="Recusar ❌", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != self.alvo_id:
            await interaction.response.send_message("❌ Esta troca não é para você.", ephemeral=True)
            return
        trocas_pendentes.pop(self.solicitante_id, None)
        self.disable_all_items()
        await interaction.message.edit(view=self)
        await interaction.response.send_message("❌ Troca recusada.", ephemeral=True)

    def disable_all_items(self):
        for item in self.children:
            item.disabled = True

# Dicionário global de trocas pendentes
trocas_pendentes = {}

# =================== COMANDO SLASH ===================
@bot.tree.command(name="hellokitty", description="Abre o painel do HELLO KITTY Café ☕")
async def hellokitty(interaction: discord.Interaction):
    embed = discord.Embed(
        title="☕ HELLO KITTY Café 🎀",
        description="**Clique nos botões para explorar o café e fazer amigos!**\n\n"
                    "🌸 Visite o café com um Doce Mágico.\n"
                    "🍬 Compre guloseimas na loja.\n"
                    "💫 Nenê está em algum lugar...",
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
    print(f"🌸 {bot.user} está no Café!")
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
            "doces": doces_iniciais(uid, dados),
            "personagens": [],
            "fragmentos": 0,
            "msg_count": 0,
            "coracoes_ganhos": 0,
            "cafe_count": 0,
            "sorte_ativa": False
        }

    jogador = dados[uid]
    jogador["msg_count"] += 1

    # Efeitos de mensagens
    if tem_efeito(uid, dados, "dear_daniel") and jogador["msg_count"] % 50 == 0:
        jogador["doces"] += 1
    if tem_efeito(uid, dados, "twin_stars") and jogador["msg_count"] % 10 == 0:
        jogador["doces"] += 1
    if tem_efeito(uid, dados, "nene") and jogador["msg_count"] % 5 == 0:
        jogador["doces"] += 3
    if tem_efeito(uid, dados, "pipi") and jogador["msg_count"] % 80 == 0:
        jogador["doces"] += 1
    if tem_efeito(uid, dados, "mocha") and jogador["msg_count"] % 60 == 0:
        jogador["doces"] += 1

    ganho = calcular_coracoes_mensagem(uid, dados)
    jogador["coracoes"] += ganho
    jogador["coracoes_ganhos"] += ganho

    if tem_efeito(uid, dados, "pochacco") and jogador["coracoes_ganhos"] >= 20:
        jogador["doces"] += 1
        jogador["coracoes_ganhos"] -= 20

    salvar_dados(dados)
    await bot.process_commands(message)

# Adaptação no sortear_personagem para usar Cupom da Sorte
def sortear_personagem(uid, dados):
    if dados[uid].get("sorte_ativa", False):
        # Dobra chance de Épico+ temporariamente
        multiplicadores = {}
        for p in PERSONAGENS:
            if p["raridade"] in ("Épico", "Lendário", "Mítico"):
                multiplicadores[p["nome"]] = 2.0
        dados[uid]["sorte_ativa"] = False
        salvar_dados(dados)
    else:
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

if __name__ == "__main__":
    bot.run(TOKEN)