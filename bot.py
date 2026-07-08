import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import random
import json
import os

# =================== CONFIGURAÇÕES POR VARIÁVEIS DE AMBIENTE ===================
TOKEN = os.getenv("TOKEN")
CANAL_ID = int(os.getenv("CANAL_ID"))                 # ID do canal onde o painel aparecerá
ARQUIVO_DADOS = os.getenv("DATA_PATH", "lacos.json") # Caminho do arquivo de dados
GUILD_ID = os.getenv("GUILD_ID")                     # ID do servidor para sync rápido (opcional)
# ==============================================================================

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

# ---------- Itens (laços) ----------
LACOS = [
    {"nome": "Laço de Moranguinho 🍓", "raridade": "Comum", "emoji": "🍓", "chance": 50},
    {"nome": "Laço de Maçã do Amor 🍎", "raridade": "Comum", "emoji": "🍎", "chance": 50},
    {"nome": "Laço de Carrossel 🎠", "raridade": "Raro", "emoji": "🎠", "chance": 30},
    {"nome": "Laço da My Melody 🎀", "raridade": "Raro", "emoji": "🎀", "chance": 30},
    {"nome": "Laço de Estrelinhas ✨", "raridade": "Épico", "emoji": "✨", "chance": 15},
    {"nome": "Laço do Arco-Íris 🌈", "raridade": "Épico", "emoji": "🌈", "chance": 15},
    {"nome": "Laço da Hello Kitty 👑", "raridade": "Lendário", "emoji": "👑", "chance": 5},
]

PRECO_FITA = 10  # corações por fita

def sortear_laco():
    total = sum(item["chance"] for item in LACOS)
    rolagem = random.randint(1, total)
    acumulado = 0
    for item in LACOS:
        acumulado += item["chance"]
        if rolagem <= acumulado:
            return item
    return LACOS[0]

# =================== VIEW PRINCIPAL (PERSISTENTE) ===================
class MenuPrincipal(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir Laço 🎀", style=discord.ButtonStyle.success, custom_id="abrir_laco")
    async def abrir_laco(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if uid not in dados:
            dados[uid] = {"coracoes": 20, "fitas": 3, "lacos": []}
        if dados[uid]["fitas"] <= 0:
            await interaction.response.send_message(
                "🌸 Você não tem fitas mágicas! Compre na **Loja de Fitas** ou ganhe corações participando.",
                ephemeral=True
            )
            return

        dados[uid]["fitas"] -= 1
        laço = sortear_laco()
        dados[uid]["lacos"].append(laço["nome"])
        salvar_dados(dados)

        embed = discord.Embed(
            title="✨ Você abriu um laço!",
            description=f"**{laço['nome']}**\nRaridade: **{laço['raridade']}** {laço['emoji']}",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        embed.set_footer(text=f"Fitas restantes: {dados[uid]['fitas']} | Corações: {dados[uid]['coracoes']} 💗")
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @discord.ui.button(label="Minha Coleção 📒", style=discord.ButtonStyle.primary, custom_id="colecao")
    async def colecao(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if uid not in dados or not dados[uid]["lacos"]:
            await interaction.response.send_message("📒 Sua coleção está vazia! Abra alguns laços primeiro.", ephemeral=True)
            return

        lacos = dados[uid]["lacos"]
        contagem = {}
        for l in lacos:
            contagem[l] = contagem.get(l, 0) + 1
        descricao = "\n".join([f"{l} ×{qtd}" for l, qtd in contagem.items()])
        embed = discord.Embed(
            title="🎀 Sua Coleção de Laços",
            description=descricao,
            color=discord.Color.from_rgb(255, 105, 180)
        )
        embed.set_footer(text=f"Total de laços: {len(lacos)}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Loja de Fitas 🛍️", style=discord.ButtonStyle.secondary, custom_id="loja")
    async def loja(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if uid not in dados:
            dados[uid] = {"coracoes": 20, "fitas": 3, "lacos": []}
            salvar_dados(dados)

        embed = discord.Embed(
            title="🛍️ Loja de Fitas Mágicas",
            description=f"**1 Fita Mágica = {PRECO_FITA} Corações 💗**\n\n"
                        f"Seu saldo: **{dados[uid]['coracoes']}** corações\n"
                        f"Suas fitas: **{dados[uid]['fitas']}**",
            color=discord.Color.gold()
        )
        view = CompraView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Como Jogar ❓", style=discord.ButtonStyle.danger, custom_id="ajuda")
    async def ajuda(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🌸 Bem-vinda ao Mundo dos Laços!",
            description=(
                "**Olá, amiguinho!** Aqui você coleciona laços mágicos.\n\n"
                "🎀 Use suas **fitas** para abrir laços.\n"
                "💗 Ganhe **corações** participando do servidor.\n"
                "🛍️ Compre mais fitas na loja.\n"
                "✨ Complete sua coleção e troque com amigos!"
            ),
            color=discord.Color.from_rgb(255, 192, 203)
        )
        embed.set_image(url="attachment://Hello_kitty.png")
        await interaction.response.send_message(
            embed=embed,
            file=discord.File("Hello_kitty.png"),
            ephemeral=True
        )

class CompraView(View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Comprar Fita 💗", style=discord.ButtonStyle.success)
    async def comprar(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        uid = str(interaction.user.id)
        if uid not in dados:
            dados[uid] = {"coracoes": 20, "fitas": 3, "lacos": []}
        if dados[uid]["coracoes"] < PRECO_FITA:
            await interaction.response.send_message("💔 Corações insuficientes!", ephemeral=True)
            return
        dados[uid]["coracoes"] -= PRECO_FITA
        dados[uid]["fitas"] += 1
        salvar_dados(dados)
        await interaction.response.send_message(
            f"✨ Compra realizada! Fitas: **{dados[uid]['fitas']}** | Corações: **{dados[uid]['coracoes']}**",
            ephemeral=True
        )

# =================== COMANDO SLASH /hellokitty ===================
@bot.tree.command(name="hellokitty", description="Mostra o painel do jogo Hello Kitty: Laços da Amizade 🎀")
async def hellokitty(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎀 Hello Kitty: Laços da Amizade 🎀",
        description="**Clique nos botões abaixo para jogar!**\n\n"
                    "🌸 Abra laços, complete sua coleção e troque com amigos.\n"
                    "💌 Use as fitas mágicas e ganhe corações!",
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
    print(f"🌸 {bot.user} está online e fofa!")

    # Registra a view persistente para que botões funcionem após reinicializações
    bot.add_view(MenuPrincipal())

    # Sincroniza os comandos slash
    if GUILD_ID:
        guild = discord.Object(id=int(GUILD_ID))
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"🌷 Comandos sincronizados no servidor {GUILD_ID}")
    else:
        await bot.tree.sync()
        print("🌷 Comandos sincronizados globalmente (pode levar até 1 hora)")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    # Ganha 1 coração por mensagem enviada
    dados = carregar_dados()
    uid = str(message.author.id)
    if uid not in dados:
        dados[uid] = {"coracoes": 20, "fitas": 3, "lacos": []}
    else:
        dados[uid]["coracoes"] += 1
    salvar_dados(dados)
    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)