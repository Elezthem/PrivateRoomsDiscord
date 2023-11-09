import asyncio
import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View, button

name_changes = {}

class PrivateRoomsView(View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @button(label="Закрыть доступ", style=nextcord.ButtonStyle.gray)
    async def close_channel(self, button: Button, interaction: nextcord.Interaction):
        user = interaction.user

        if user.voice and user.voice.channel:
            voice_channel = user.voice.channel
            overwrites = voice_channel.overwrites or {}
            role = interaction.guild.default_role
            overwrites[role] = nextcord.PermissionOverwrite(view_channel=False, connect=False)
            await voice_channel.edit(overwrites=overwrites)
            await interaction.response.send_message(f"Доступ к голосовому каналу '{voice_channel.name}' закрыт.")
        else:
            await interaction.response.send_message("Вы должны быть в голосовом канале, чтобы закрыть его доступ.")

    @button(label="Изменить название", style=nextcord.ButtonStyle.gray)
    async def change_name(self, button: Button, interaction: nextcord.Interaction):
        user = interaction.user

        if user.voice and user.voice.channel:
            voice_channel = user.voice.channel

            await interaction.response.send_message("Введите новое название для комнаты.")

            def check(m):
                return m.author == user and m.channel == voice_channel

            try:
                response = await self.bot.wait_for('message', check=check, timeout=60)
                new_name = response.content

                await voice_channel.edit(name=new_name)
                await interaction.response.send_message(f"Название голосового канала изменено на: {new_name}")
            except asyncio.TimeoutError:
                await interaction.response.send_message("Время ожидания истекло, повторите попытку.")
        else:
            await interaction.response.send_message("Вы должны быть в голосовом канале, чтобы изменить его название.")

    @button(label="Открыть доступ", style=nextcord.ButtonStyle.gray)
    async def open_channel(self, button: Button, interaction: nextcord.Interaction):
        user = interaction.user

        if user.voice and user.voice.channel:
            voice_channel = user.voice.channel
            overwrites = voice_channel.overwrites or {}
            role = interaction.guild.default_role
            overwrites[role] = nextcord.PermissionOverwrite(view_channel=True, connect=True)
            await voice_channel.edit(overwrites=overwrites)
            await interaction.response.send_message(f"Доступ к голосовому каналу '{voice_channel.name}' открыт.")
        else:
            await interaction.response.send_message("Вы должны быть в голосовом канале, чтобы открыть его доступ.")


class PrivateRooms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def private_rooms(self, ctx):
        category = await ctx.guild.create_category('Приватные комнаты')
        text_channel = await ctx.guild.create_text_channel('приватные-комнаты', category=category)
        voice_channel = await ctx.guild.create_voice_channel('приватный-голосовой-канал', category=category)

        embed = nextcord.Embed(title='Приватные комнаты', description='Добро пожаловать в приватные комнаты!')
        embed.add_field(name='Закрыть доступ', value="🔒👥", inline=False)
        embed.add_field(name='Изменить название', value="✏️", inline=False)
        embed.add_field(name='Открыть доступ', value="🔓👥", inline=False)

        message = await text_channel.send(embed=embed, view=PrivateRoomsView(self.bot))
        await ctx.send('Приватные комнаты успешно созданы!')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel and after.channel.name == 'приватный-голосовой-канал':
            channel_name = f'{member.display_name}\'s Room'
            category = after.channel.category
            new_voice_channel = await category.create_voice_channel(channel_name)
            await member.move_to(new_voice_channel)
        if before.channel and before.channel.name != 'приватный-голосовой-канал' and not before.channel.members:
            await before.channel.delete()

        # Применение запрошенных изменений названия, если пользователь находится в голосовом канале
        if member.voice and member.id in name_changes:
            new_name = name_changes[member.id]
            await member.voice.channel.edit(name=new_name)
            del name_changes[member.id]

def setup(bot):
    bot.add_cog(PrivateRooms(bot))
