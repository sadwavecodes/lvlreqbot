import os
import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, InputText

# Get the token from the environment variable
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Define the bot with the command prefix '!'
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Define a dictionary to keep track of which questions are required
required_questions = [False] * 5

# Define the modal class with 5 questions
class SurveyModal(Modal):
    def __init__(self, required_status):
        super().__init__(title="Survey")
        self.required_status = required_status

        for i in range(5):
            self.add_item(InputText(label=f"Question {i+1}", required=self.required_status[i]))

    async def callback(self, interaction: discord.Interaction):
        # Create an embed with the responses
        embed = discord.Embed(title="Survey Responses", color=discord.Color.blue())
        embed.set_author(name=f"User ID: {interaction.user.id}")

        for i, item in enumerate(self.children):
            embed.add_field(name=f"Question {i+1}", value=item.value, inline=False)

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
