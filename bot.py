import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput
import random
import json
import os
import asyncio

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

# ---------- Personagens (10.000.000 de peso total) ----------
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
# Comuns (20 personagens)
PERSONAGENS_COMUNS = [
    "Spottie Dottie", "Landry", "Moppu", "Coro Chan", "Minna no Tabo",
    "Charmmy Kitty", "Sugar", "Tiny Chum", "Cathy", "George",
    "Fifi", "Rory", "Lulu", "Pipi", "Nana", "Mimi", "Sasa", "Kiki", "Lala", "Mocha"
]
peso_comum_base = 499567
for i, nome in enumerate(PERSONAGENS_COMUNS):
    peso = peso_comum_base if i < 19 else 9991347 - (19 * peso_comum_base)
    PERSONAGENS.append({"nome": nome, "peso": peso, "raridade": "Comum", "efeito": None})

TOTAL_PESOS = sum(p["peso"] for p in PERSONAGENS)
assert TOTAL_PESOS == 10000000, f"Pesos: {TOTAL_PESOS}"

# Nenê (Ultimate)
NENE = {"nome": "Nenê", "raridade": "Ultimate", "efeito": "nene"}
CHANCE_NENE = 1e-11  # 0,000000001%

DESCRICAO_EFEITOS = {
    "hello_kitty": "+2💗/msg, 20% desc., 10% frag. extra",
    "dear_daniel": "+1 🍬 a cada 50 msgs",
    "my_melody": "10% desc. na loja",
    "kuromi": "+15% chance Épico+",
    "pompompurin": "50% não gastar 🍬",
    "cinnamoroll": "Troca 2 duplicatas por 1 novo",
    "twin_stars": "+1 🍬 a cada 10 msgs",
    "keroppi": "Começa com 5 🍬",
    "badtz_maru": "+5💗 ao comprar 🍬",
    "tuxedo_sam": "30% +1 🍬 ao conhecer",
    "pochacco": "+1 🍬 a cada 20💗 ganhos",
    "chococat": "20% duplicar amigo",
    "hangyodon": "Reciclar duplicata = 3💗",
    "pekkle": "+5% chance Incomum+",
    "nene": "+5💗/msg, 50% desc., 50% frag. extra, +3 🍬 a cada 5 msgs"
}

# Troca entre jogadores (pendências)
trocas_pendentes = {}  # {id_solicitante: {alvo_id, personagem_oferecido}}

# ---------- Funções auxiliares ----------
def tem_efeito(uid, dados, efeito_nome):
    if uid not in dados:
        return False
    for nome in set(dados[uid]["personagens"]):
        for p in PERSONAGENS:
            if p["nome"] == nome and p.get("efeito") == efeito_nome:
                return True
    if efeito_nome == "nene" and "Nenê" in dados[uid].get("personagens", []):
        return True
    return False

def obter_desconto(uid, dados):
    desc = 0.0
    if tem_efeito(uid, dados, "my_melody"): desc = max(desc, 0.10)
    if tem_efeito(uid, dados, "hello_kitty"): desc = max(desc, 0.20)
    if tem_efeito(uid, dados, "nene"): desc = max(desc, 0.50)
    return desc

def calcular_coracoes_mensagem(uid, dados):
    base = 1
    if tem_efeito(uid, dados, "hello_kitty"): base += 2
    if tem_efeito(uid, dados, "nene"): base += 5
    return base

def doces_iniciais(uid, dados):
    return 5 if tem_efeito(uid, dados, "keroppi") else 3

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
                "doces": doces_iniciais(uid, dados),
                "personagens": [],
                "fragmentos": 0,
                "msg_count": 0,
                "coracoes_ganhos": 0
            }
        if dados[uid]["doces"] <= 0:
            await interaction.response.send_message("🌸 Você não tem Doces Mágicos! Compre na loja 🍬.", ephemeral=True)
            return

        gastar = True
        if tem_efeito(uid, dados, "pompompurin") and random.random() < 0.5:
            gastar = False
        if gastar:
            dados[uid]["doces"] -= 1

        # Nenê
        if random.random() < CHANCE_NENE:
            personagem = NENE
            dados[uid]["personagens"].append("Nenê")
            salvar_dados(dados)
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="💫 IMPOSSÍVEL! 💫",
                    description="**Nenê** apareceu!\nRaridade: Ultimate\nEfeito: +5💗/msg, 50% desc., 50% frag. extra, +3 🍬/5 msgs",
                    color=discord.Color.gold()
                ), ephemeral=False)
            return

        personagem = sortear_personagem(uid, dados)
        duplicar = tem_efeito(uid, dados, "chococat") and random.random() < 0.20
        dados[uid]["personagens"].append(personagem["nome"])
        if duplicar:
            dados[uid]["personagens"].append(personagem["nome"])

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

        salvar_dados(dados)
        msg = ""
        if not gastar:
            msg += "\n🍮 Pompompurin salvou seu doce!"
        if duplicar:
            msg += "\n🐱 Chococat duplicou!"

        embed = discord.Embed(
            title="🎁 Novo Amigo!",
            description=f"**{personagem['nome']}**\nRaridade: {personagem['raridade']}\nEfeito: {DESCRICAO_EFEITOS.get(personagem['efeito'], 'Nenhum')}{msg}",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        embed.set_footer(text=f"Doces: {dados[uid]['doces']} 🍬 | 💗: {dados[uid]['coracoes']} | Fragmentos: {dados[uid]['fragmentos']}")
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
            desc_efeito = DESCRICAO_EFEITOS.get(efeito, "—")
            desc += f"{nome} ×{qtd}  [{desc_efeito}]\n"

        embed = discord.Embed(title="👥 Sua Turma da Sanrio", description=desc, color=discord.Color.from_rgb(255, 105, 180))
        embed.set_footer(text=f"Total: {len(dados[uid]['personagens'])} | Fragmentos: {dados[uid].get('fragmentos', 0)}")
        await interaction.response.send_message(embed=embed, view=TurmaAcoesView(uid), ephemeral=True)

    @discord.ui.button(label="Personagens 📖", style=discord.ButtonStyle.secondary, custom_id="lista_personagens")
    async def lista_personagens(self, interaction: discord.Interaction, button: Button):
        # Lista paginada de todos os personagens (exceto comuns repetidos, mostra todos)
        all_chars = PERSONAGENS + [NENE]
        # Remove duplicatas de nomes? Não, cada um é único.
        pages = []
        chunk_size = 10
        for i in range(0, len(all_chars), chunk_size):
            chunk = all_chars[i:i+chunk_size]
            desc = ""
            for p in chunk:
                efeito = DESCRICAO_EFEITOS.get(p["efeito"], "—")
                desc += f"**{p['nome']}** ({p['raridade']}) - {efeito}\n"
            embed = discord.Embed(title="📖 Personagens Disponíveis", description=desc, color=discord.Color.from_rgb(255, 218, 185))
            embed.set_footer(text=f"Página {len(pages)+1}/{(len(all_chars)-1)//chunk_size+1}")
            pages.append(embed)
        if not pages:
            await interaction.response.send_message("Nenhum personagem cadastrado.", ephemeral=True)
            return
        await interaction.response.send_message(embed=pages[0], view=PaginaView(pages, 0), ephemeral=True)

    @discord.ui.button(label="Loja 🛍️", style=discord.ButtonStyle.primary, custom_id="loja")
    async def loja(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if uid not in dados:
            dados[uid] = {"coracoes": 20, "doces": doces_iniciais(uid, dados), "personagens": [], "fragmentos": 0, "msg_count": 0, "coracoes_ganhos": 0}
            salvar_dados(dados)

        desconto = obter_desconto(uid, dados)
        preco = max(1, int(10 * (1 - desconto)))
        embed = discord.Embed(
            title="🍬 Loja de Doces Mágicos",
            description=f"**Compre Doces para conhecer novos amigos!**\n\n"
                        f"Preço: **{preco}💗** por Doce 🍬\n"
                        f"Saldo: **{dados[uid]['coracoes']}💗** | Doces: **{dados[uid]['doces']}🍬**\n"
                        f"Fragmentos Hello: **{dados[uid]['fragmentos']}**",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url="https://i.imgur.com/5Q6Zk8L.png")  # uma imagem fofa da Hello Kitty (opcional)
        await interaction.response.send_message(embed=embed, view=LojaView(uid), ephemeral=True)

    @discord.ui.button(label="Ajuda ❓", style=discord.ButtonStyle.danger, custom_id="ajuda")
    async def ajuda(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🌸 Hello Kitty: Amigos da Sanrio",
            description=("🎁 **Conhecer Amigo** gasta um Doce Mágico 🍬.\n"
                         "💗 Ganhe corações conversando no servidor.\n"
                         "👑 Hello Kitty (0,00001%) é Mítico.\n"
                         "💫 Nenê (0,000000001%) é Ultimate!\n"
                         "💎 Fragmentos Hello (100) resgatam a Hello Kitty.\n"
                         "🤝 Use a Loja para trocar personagens com amigos."),
            color=discord.Color.from_rgb(255, 192, 203)
        )
        embed.set_image(url="attachment://Hello_kitty.png")
        await interaction.response.send_message(embed=embed, file=discord.File("Hello_kitty.png"), ephemeral=True)

# Paginação da lista de personagens
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

    @discord.ui.button(label="Comprar Doce 🍬", style=discord.ButtonStyle.success)
    async def comprar(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        desconto = obter_desconto(uid, dados)
        preco = max(1, int(10 * (1 - desconto)))
        if dados[uid]["coracoes"] < preco:
            await interaction.response.send_message("💔 Corações insuficientes!", ephemeral=True)
            return
        dados[uid]["coracoes"] -= preco
        dados[uid]["doces"] += 1
        if tem_efeito(uid, dados, "badtz_maru"):
            dados[uid]["coracoes"] += 5
        if tem_efeito(uid, dados, "nene"):
            dados[uid]["coracoes"] += 5
        salvar_dados(dados)
        await interaction.response.send_message(f"✨ Doce comprado! Doces: {dados[uid]['doces']} 🍬 | 💗: {dados[uid]['coracoes']}", ephemeral=True)

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

    @discord.ui.button(label="Trocar com Amigo 🤝", style=discord.ButtonStyle.primary)
    async def trocar_amigo(self, interaction: discord.Interaction, button: Button):
        # Abre modal para escolher o amigo e o personagem
        await interaction.response.send_modal(TrocaModal(self.uid))

class TrocaModal(Modal, title="Propor Troca"):
    amigo = TextInput(label="Mencione o amigo (@username)", placeholder="@amiguinho")
    personagem = TextInput(label="Personagem que você oferece", placeholder="Nome exato do personagem")

    def __init__(self, uid):
        super().__init__()
        self.uid = uid

    async def on_submit(self, interaction: discord.Interaction):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        # Valida menção
        mencionado = self.amigo.value.strip()
        if not mencionado.startswith("<@") or not mencionado.endswith(">"):
            await interaction.response.send_message("❌ Mencione um usuário válido.", ephemeral=True)
            return
        alvo_id = mencionado[2:-1].replace("!", "")
        if not alvo_id.isdigit():
            await interaction.response.send_message("❌ Usuário inválido.", ephemeral=True)
            return
        if alvo_id == uid:
            await interaction.response.send_message("❌ Você não pode trocar consigo mesmo.", ephemeral=True)
            return

        # Personagem oferecido
        nome_pers = self.personagem.value.strip()
        if nome_pers not in dados[uid]["personagens"]:
            await interaction.response.send_message(f"❌ Você não tem **{nome_pers}**.", ephemeral=True)
            return

        # Salva pedido de troca
        trocas_pendentes[uid] = {"alvo": alvo_id, "personagem": nome_pers}
        # Notifica o alvo
        canal = interaction.channel
        alvo_user = await bot.fetch_user(int(alvo_id))
        embed = discord.Embed(
            title="🤝 Proposta de Troca!",
            description=f"{interaction.user.mention} quer trocar **{nome_pers}** com você!\n"
                        f"Clique no botão abaixo para aceitar e escolher o que oferecer.",
            color=discord.Color.green()
        )
        view = AceitarTrocaView(uid, alvo_id, nome_pers)
        await canal.send(content=alvo_user.mention, embed=embed, view=view)
        await interaction.response.send_message("✅ Proposta de troca enviada!", ephemeral=True)

class AceitarTrocaView(View):
    def __init__(self, solicitante_id, alvo_id, personagem_oferecido):
        super().__init__(timeout=120)
        self.solicitante_id = solicitante_id
        self.alvo_id = alvo_id
        self.personagem_oferecido = personagem_oferecido

    @discord.ui.button(label="Aceitar Troca ✅", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != self.alvo_id:
            await interaction.response.send_message("❌ Esta troca não é para você.", ephemeral=True)
            return

        dados = carregar_dados()
        # Verifica se solicitante ainda tem o personagem
        if self.personagem_oferecido not in dados[self.solicitante_id]["personagens"]:
            await interaction.response.send_message("❌ O solicitante não tem mais esse personagem.", ephemeral=True)
            return

        # Abre select para o alvo escolher seu personagem
        personagens_alvo = list(set(dados[self.alvo_id]["personagens"]))
        if not personagens_alvo:
            await interaction.response.send_message("❌ Você não tem personagens para oferecer.", ephemeral=True)
            return

        options = [discord.SelectOption(label=nome, value=nome) for nome in personagens_alvo[:25]]
        select = Select(placeholder="Escolha um personagem seu...", options=options)

        async def select_callback(interaction_select: discord.Interaction):
            personagem_escolhido = select.values[0]
            # Realiza a troca
            dados[self.solicitante_id]["personagens"].remove(self.personagem_oferecido)
            dados[self.alvo_id]["personagens"].remove(personagem_escolhido)
            dados[self.solicitante_id]["personagens"].append(personagem_escolhido)
            dados[self.alvo_id]["personagens"].append(self.personagem_oferecido)
            salvar_dados(dados)
            # Remove pedido pendente
            trocas_pendentes.pop(self.solicitante_id, None)
            await interaction_select.response.send_message(
                f"✅ Troca realizada! {interaction_select.user.mention} deu **{personagem_escolhido}** "
                f"e recebeu **{self.personagem_oferecido}** de <@{self.solicitante_id}>.",
                ephemeral=False
            )
            # Desabilita o botão original
            self.aceitar.disabled = True
            await interaction.message.edit(view=self)

        select.callback = select_callback
        view_select = View(timeout=60)
        view_select.add_item(select)
        await interaction.response.send_message("Escolha qual personagem oferecer:", view=view_select, ephemeral=True)

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
            "doces": doces_iniciais(uid, dados),
            "personagens": [],
            "fragmentos": 0,
            "msg_count": 0,
            "coracoes_ganhos": 0
        }

    jogador = dados[uid]
    jogador["msg_count"] += 1

    if tem_efeito(uid, dados, "dear_daniel") and jogador["msg_count"] % 50 == 0:
        jogador["doces"] += 1
    if tem_efeito(uid, dados, "twin_stars") and jogador["msg_count"] % 10 == 0:
        jogador["doces"] += 1
    if tem_efeito(uid, dados, "nene") and jogador["msg_count"] % 5 == 0:
        jogador["doces"] += 3

    ganho = calcular_coracoes_mensagem(uid, dados)
    jogador["coracoes"] += ganho
    jogador["coracoes_ganhos"] += ganho

    if tem_efeito(uid, dados, "pochacco") and jogador["coracoes_ganhos"] >= 20:
        jogador["doces"] += 1
        jogador["coracoes_ganhos"] -= 20

    salvar_dados(dados)
    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)