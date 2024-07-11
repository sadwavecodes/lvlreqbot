import os
import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput

# Get the token from the environment variable
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Define the bot with the command prefix '!'
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Define a list to keep track of which questions are required
required_questions = [False] * 5

# Define a set to store used Level IDs
used_level_ids = set()

# Define the modal class with specified questions
class SurveyModal(Modal):
    def __init__(self, required_status):
        super().__init__(title="Survey")
        self.required_status = required_status

        self.add_item(TextInput(label="Level Name", required=self.required_status[0]))
        self.add_item(TextInput(label="Level ID", required=self.required_status[1]))
        self.add_item(TextInput(label="Difficulty", required=self.required_status[2]))
        self.add_item(TextInput(label="Video", required=self.required_status[3]))
        self.add_item(TextInput(label="Note", required=self.required_status[4]))

    async def on_submit(self, interaction: discord.Interaction):
        level_id = self.children[1].value

        if level_id in used_level_ids:
            await interaction.response.send_message(f"Level ID {level_id} has already been used. Please use a unique Level ID.", ephemeral=True)
            return

        used_level_ids.add(level_id)

        # Create an embed with the responses
        embed = discord.Embed(title="Survey Responses", color=discord.Color.blue())
        embed.set_author(name=f"User ID: {interaction.user.id}", icon_url=interaction.user.avatar.url)

        embed.add_field(name="Level Name", value=self.children[0].value, inline=False)
        embed.add_field(name="Level ID", value=self.children[1].value, inline=False)
        embed.add_field(name="Difficulty", value=self.children[2].value, inline=False)
        embed.add_field(name="Video", value=self.children[3].value, inline=False)
        embed.add_field(name="Note", value=self.children[4].value, inline=False)

        await interaction.response.send_message(embed=embed)

# Command to toggle the required status of a question
@bot.command()
async def modalreq(ctx, question_number: int):
    if 1 <= question_number <= 5:
        required_questions[question_number - 1] = not required_questions[question_number - 1]
        await ctx.send(f"Question {question_number} required status toggled to {required_questions[question_number - 1]}")
    else:
        await ctx.send("Invalid question number. Please provide a number between 1 and 5.")

# Command to create the button
@bot.command()
async def reqbutton(ctx):
    button = Button(label="Open Survey", style=discord.ButtonStyle.primary)

    async def button_callback(interaction: discord.Interaction):
        modal = SurveyModal(required_questions)
        await interaction.response.send_modal(modal)

    button.callback = button_callback

    view = View()
    view.add_item(button)
    await ctx.send("Click the button to open the survey:", view=view)

# Run the bot
bot.run(DISCORD_TOKEN)
